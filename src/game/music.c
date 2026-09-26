/*
 * Background music: a small software synthesizer on Direct Sound A.
 *
 * Songs (src/music_data.h, written by tools/gen_music.py from the MML in
 * tools/music/) are byte streams, one per channel: notes with lengths in
 * ticks (48 per quarter note), instrument, volume and gate changes, and a
 * loop point. Once per frame the sequencer advances every channel by the
 * song's tempo and turns it into a voice: a sample source (a 64-step
 * waveform, a 4096-step noise loop or a one-shot drum sample), a phase step
 * and a volume from the channel's envelope. The mixer then renders the next
 * frame of signed 8-bit PCM (MUS_MIX_LEN samples at 13379 Hz) that DMA1
 * feeds to FIFO A whenever timer 0 overflows.
 *
 * On the GBA the sequencer and mixer run in the VCOUNT interrupt at line 0,
 * after the vblank uploads, so the music keeps going through frames where
 * the game logic runs long. The mixer is ARM code in IWRAM. The PSG
 * channels stay with the sound effects (sfx.c); while a fanfare plays
 * there the music ducks.
 *
 * DMA restart: the timer ticks exactly MUS_MIX_LEN times per frame, so at
 * each interrupt the DMA is pointed at the buffer mixed during the last one.
 * The FIFO keeps whatever it had queued (the tail of the previous buffer),
 * and because the buffers are a multiple of 16 bytes long the refills line
 * up with the buffer ends frame after frame. Starting with 8 bytes already
 * in the FIFO puts the refills half-way between two interrupts, so the
 * interrupt can run late by up to 8 samples without a glitch.
 *
 * Host builds run the same sequencer and mixer from game_frame(); the tests
 * and tools/render_music.c hear exactly what the cartridge plays.
 */

/* ---------------- registers ---------------- */

#define MREG_SOUNDCNT_H REG16(0x082)
#define MREG_FIFO_A     REG32(0x0A0)
#define MREG_DMA1SAD    REG32(0x0BC)
#define MREG_DMA1DAD    REG32(0x0C0)
#define MREG_DMA1CNT_H  REG16(0x0C6)
#define MREG_TM0CNT_L   REG16(0x100)
#define MREG_TM0CNT_H   REG16(0x102)
#define MREG_IE         REG16(0x200)
#define MREG_IF         REG16(0x202)
#define MREG_IME        REG16(0x208)

#define IRQ_VCOUNT      0x0004
#define MUS_IRQ_LINE    0          /* after the vblank uploads in present() */
#define DMA_FIFO_START  0xB640     /* enable, sound FIFO timing, 32-bit, repeat, fixed dest */

/* ---------------- data types (filled in by music_data.h) ---------------- */

enum { MK_OFF, MK_WAVE, MK_NOISE, MK_PCM, MK_KIT };

/*
 * An instrument. Envelope levels are 8.8 (0..0xFF00): attack adds `atk`
 * per frame (0 = instant); decay moves toward `sus` by dec/65536 of the
 * distance per frame; while held the level shrinks by fade/65536 per frame
 * (plucked and struck sounds); after the note ends it shrinks by rel/65536.
 * Vibrato: after vib_delay frames, a sine of vib_depth/64 semitones at
 * vib_speed/256 cycles per frame. sweep slides the pitch every frame.
 */
typedef struct {
    u8 kind, src, vol, sus;
    u16 atk, dec, fade, rel;
    u8 vib_delay, vib_depth, vib_speed;
    s8 sweep;
} MusInstr;

typedef struct { const s8 *data; u16 len; u8 base, pad; } MusSample;
typedef struct { u8 sample, vol; s8 pitch; u8 pad; } MusDrum;

#define MUS_CHANNELS 8

typedef struct {
    const u8 *ch[MUS_CHANNELS];
    u16 loop[MUS_CHANNELS];    /* loop point offset, 0xFFFF = play once */
    u8 count;                  /* channels in use */
    u8 num, den;               /* tempo: num/den ticks per frame */
    u8 level;                  /* song mix level, 128 = 1.0 */
} MusSong;

#include "../music_data.h"

#define HAVE_MUSIC      /* script.c: field.c's music_map_changed() lives in music_map.c */

/* ---------------- state ---------------- */

enum { ENV_OFF, ENV_ATK, ENV_DEC, ENV_SUS, ENV_REL };

enum {
    OP_END = 0x00, OP_REST = 0x80, OP_INSTR, OP_VOL, OP_GATE, OP_DETUNE, OP_PORTA,
    OP_ARP, OP_LEGATO, OP_TEMPO, OP_VIB,
};

/* What the mixer reads: one per channel. */
typedef struct {
    const s8 *data;
    u32 pos, inc;       /* loops: index = pos >> shift (wraps); one-shots: 16.16 */
    u16 vol, count;     /* volume 0..255; samples to mix this frame */
    u8 shift, pad[3];
} MusVoice;

typedef struct {
    const u8 *pc, *loop;
    u16 wait;           /* ticks until the next event */
    u16 gate_left;      /* ticks until the note is released (0 = held) */
    s16 pitch, target;  /* 1/64 semitones */
    u16 env;            /* envelope level, 8.8 */
    u16 pcm_len;        /* one-shot length in samples */
    u8 stage, instr, vol, gate;
    s8 detune;
    u8 porta, arp_n, arp_i;
    u8 arp[4];
    u8 vib_t, vib_ph, kit_vol, sounded;
} MusChan;

static MusVoice mus_voice[MUS_CHANNELS];
static MusChan mus_ch[MUS_CHANNELS];
static s32 mus_acc[MUS_MIX_LEN];
/* two frames of output, then a little silence for a late DMA restart */
static s8 mus_buf[MUS_MIX_LEN * 2 + 32] __attribute__((aligned(4)));

static struct {
    u8 song, next;      /* playing song, song to start after the fade */
    u8 fading, play_buf, started, silent;   /* silent: buffers cleared since the mix went quiet */
    u8 num, den;
    u16 tacc;
    s16 fade;           /* 0..256 */
    s16 duck;           /* 0..256 */
    u16 master;         /* last computed master gain */
    u32 frames;         /* frames since the song started */
} mus = { SONG_NONE, SONG_NONE, 0, 0, 0, 2, 1, 1, 0, 256, 256, 0, 0 };

/* Requests from the game (main thread) to the interrupt. */
enum { MREQ_FADE = 1, MREQ_NOW };
static volatile u8 mus_req_song = SONG_NONE, mus_req_mode, mus_req_seq;
static u8 mus_req_seen;
static u8 mus_want = SONG_NONE;     /* main thread: the song last asked for */
static volatile u16 mus_prof_lines; /* GBA: scanlines the last interrupt took */

/* Music volume (opt.music_vol): 0 = full (the default), 1 = low, 2 = mid. */
static const u16 MUS_VOL_GAIN[3] = { 256, 96, 170 };

static int mus_option_gain(void)
{
    return opt.music ? MUS_VOL_GAIN[opt.music_vol < 3 ? opt.music_vol : 0] : 0;
}

/* ---------------- pitch ---------------- */

/* Phase step for a pitch in 1/64 semitones (MIDI note * 64). */
static u32 mus_pitch_inc(int p)
{
    p = clampi(p, 0, 107 * 64 + 63);
    int oct = p / 768;
    return MUS_OCT_INC[p - oct * 768] >> (8 - oct);
}

/* 16.16 step for a one-shot sample recorded at MIDI note `base`. */
static u32 mus_pcm_inc(int note, int base)
{
    u32 inc = mus_pitch_inc((note - base + 60) * 64);
    return inc / ((MUS_OCT_INC[0] >> 3) >> 16);
}

/* ---------------- sequencer ---------------- */

static void mus_voice_off(int i)
{
    mus_ch[i].stage = ENV_OFF;
    mus_voice[i].vol = 0;
    mus_voice[i].count = 0;
}

static void mus_release(MusChan *c)
{
    if (c->stage != ENV_OFF) c->stage = ENV_REL;
    c->gate_left = 0;
}

static void mus_note_on(int i, int note, int dur, int legato)
{
    MusChan *c = &mus_ch[i];
    MusVoice *v = &mus_voice[i];
    const MusInstr *in = &MUS_INSTRS[c->instr];
    int g = c->gate >= 8 ? 0 : dur * c->gate / 8;
    c->gate_left = (u16)(c->gate >= 8 ? 0 : (g > 0 ? g : 1));
    if (in->kind == MK_PCM || in->kind == MK_KIT) {
        const MusSample *s;
        int pitch = note, vol = 255;
        if (in->kind == MK_KIT) {
            const MusDrum *d = &MUS_KIT[note < (int)(sizeof(MUS_KIT) / sizeof(MUS_KIT[0])) ? note : 0];
            if (!d->vol) return;
            s = &MUS_SAMPLES[d->sample];
            pitch = s->base + d->pitch;
            vol = d->vol;
        } else {
            s = &MUS_SAMPLES[in->src];
        }
        v->data = s->data;
        v->shift = 16;
        v->pos = 0;
        v->inc = mus_pcm_inc(pitch, s->base);
        c->pcm_len = s->len;
        c->kit_vol = (u8)vol;
        c->env = 0xFF00;
        c->stage = ENV_SUS;
        c->sounded = 1;
        return;
    }
    int target = note * 64 + c->detune;
    if (legato && c->stage != ENV_OFF && c->stage != ENV_REL) {
        c->target = (s16)target;
        if (!c->porta) c->pitch = (s16)target;
        return;
    }
    c->target = (s16)target;
    if (!c->porta || !c->sounded) c->pitch = (s16)target;
    c->sounded = 1;
    c->vib_t = 0;
    c->vib_ph = 0;
    c->arp_i = 0;
    c->kit_vol = 255;
    if (in->kind == MK_WAVE) {
        v->data = mus_waves[in->src];
        v->shift = MUS_WAVE_SHIFT;
        v->pos = 0;
    } else {
        v->data = mus_noises[in->src];
        v->shift = MUS_NOISE_SHIFT;
    }
    if (in->atk) {
        c->env = 0;
        c->stage = ENV_ATK;
    } else if (in->dec) {
        c->env = 0xFF00;
        c->stage = ENV_DEC;
    } else {
        c->env = (u16)(in->sus << 8);
        c->stage = ENV_SUS;
    }
}

static int mus_read_dur(MusChan *c)
{
    int d = *c->pc++;
    if (d) return d;
    d = c->pc[0] | c->pc[1] << 8;
    c->pc += 2;
    return d;
}

/* One tick of channel i: count down, then read events until a timed one. */
static void mus_chan_tick(int i)
{
    MusChan *c = &mus_ch[i];
    if (!c->pc) return;
    if (c->gate_left && --c->gate_left == 0) mus_release(c);
    if (c->wait > 1) {
        c->wait--;
        return;
    }
    for (int guard = 0; guard < 64; guard++) {
        int op = *c->pc++;
        if (op == OP_END) {
            if (!c->loop) {
                c->pc = 0;
                mus_release(c);
                return;
            }
            c->pc = c->loop;
            continue;
        }
        if (op < 0x80) {
            int d = mus_read_dur(c);
            mus_note_on(i, op, d, 0);
            c->wait = (u16)d;
            return;
        }
        switch (op) {
        case OP_REST:
            c->wait = (u16)mus_read_dur(c);
            mus_release(c);
            return;
        case OP_LEGATO: {
            int n = *c->pc++;
            int d = mus_read_dur(c);
            mus_note_on(i, n, d, 1);
            c->wait = (u16)d;
            return;
        }
        case OP_INSTR: c->instr = *c->pc++; break;
        case OP_VOL: c->vol = *c->pc++; break;
        case OP_GATE: c->gate = *c->pc++; break;
        case OP_DETUNE: c->detune = (s8)*c->pc++; break;
        case OP_PORTA: c->porta = *c->pc++; break;
        case OP_ARP: {
            int n = *c->pc++;
            c->arp_n = (u8)(n > 4 ? 4 : n);
            for (int k = 0; k < n; k++) {
                u8 o = *c->pc++;
                if (k < 4) c->arp[k] = o;
            }
            c->arp_i = 0;
            break;
        }
        case OP_TEMPO:
            mus.num = *c->pc++;
            mus.den = *c->pc++;
            break;
        default:
            c->pc = 0;          /* corrupt stream: stop this channel */
            mus_release(c);
            return;
        }
    }
    c->pc = 0;                  /* a loop with no timed event */
}

/* Once per frame: envelope, pitch effects and the voice the mixer plays. */
static void mus_chan_frame(int i, int master)
{
    MusChan *c = &mus_ch[i];
    MusVoice *v = &mus_voice[i];
    if (c->stage == ENV_OFF) {
        v->vol = 0;
        v->count = 0;
        return;
    }
    const MusInstr *in = &MUS_INSTRS[c->instr];
    s32 e = c->env;
    switch (c->stage) {
    case ENV_ATK:
        e += in->atk;
        if (e >= 0xFF00) {
            e = 0xFF00;
            if (in->dec) {
                c->stage = ENV_DEC;
            } else {
                e = in->sus << 8;
                c->stage = ENV_SUS;
            }
        }
        break;
    case ENV_DEC: {
        s32 s = in->sus << 8;
        e -= (s32)(((u32)(e - s) * in->dec) >> 16) + 1;
        if (e <= s) {
            e = s;
            c->stage = ENV_SUS;
        }
        break;
    }
    case ENV_SUS:
        if (in->fade) e -= (s32)(((u32)e * in->fade) >> 16) + 1;
        break;
    default:
        e -= (s32)(((u32)e * in->rel) >> 16) + 24;
        break;
    }
    if (e <= 0 || (c->stage == ENV_REL && e < 0x200)) {
        mus_voice_off(i);
        c->env = 0;
        return;
    }
    c->env = (u16)e;

    if (in->kind == MK_WAVE || in->kind == MK_NOISE) {
        if (c->pitch != c->target) {
            int d = c->target - c->pitch, s = c->porta ? c->porta : 0x7FFF;
            c->pitch = (s16)(c->pitch + (d > s ? s : d < -s ? -s : d));
        }
        if (in->sweep) {
            c->pitch = (s16)clampi(c->pitch + in->sweep, 0, 107 * 64);
            c->target = c->pitch;
        }
        int p = c->pitch;
        if (c->arp_n) {
            p += c->arp[c->arp_i] * 64;
            if (++c->arp_i >= c->arp_n) c->arp_i = 0;
        }
        if (in->vib_depth && c->vib_t >= in->vib_delay) {
            c->vib_ph = (u8)(c->vib_ph + in->vib_speed);
            p += MUS_SINE[c->vib_ph >> 2] * in->vib_depth / 128;
        }
        if (c->vib_t < 255) c->vib_t++;
        u32 inc = mus_pitch_inc(p);
        v->inc = in->kind == MK_NOISE ? inc >> 4 : inc;
        v->count = MUS_MIX_LEN;
    } else {
        u32 end = (u32)c->pcm_len << 16;
        if (v->pos >= end) {
            mus_voice_off(i);
            return;
        }
        u32 left = (end - v->pos + v->inc - 1) / v->inc;
        v->count = (u16)(left < MUS_MIX_LEN ? left : MUS_MIX_LEN);
    }
    int lvl = (e >> 8) * c->vol >> 7;
    lvl = lvl * in->vol >> 8;
    lvl = lvl * c->kit_vol >> 8;
    v->vol = (u16)(lvl * master >> 8);
}

static void mus_begin(int song)
{
    for (int i = 0; i < MUS_CHANNELS; i++) {
        MusChan *c = &mus_ch[i];
        mus_voice_off(i);
        c->pc = 0;
        c->loop = 0;
        c->wait = 0;
        c->gate_left = 0;
        c->instr = 0;
        c->vol = 100;
        c->gate = 7;
        c->detune = 0;
        c->porta = 0;
        c->arp_n = 0;
        c->sounded = 0;
        c->kit_vol = 255;
    }
    mus.song = (u8)song;
    mus.fading = 0;
    mus.fade = 256;
    mus.frames = 0;
    if (song <= SONG_NONE || song >= SONG_COUNT) {
        mus.song = SONG_NONE;
        return;
    }
    const MusSong *s = &MUS_SONGS[song];
    for (int i = 0; i < s->count && i < MUS_CHANNELS; i++) {
        mus_ch[i].pc = s->ch[i];
        mus_ch[i].loop = s->loop[i] == 0xFFFF ? 0 : s->ch[i] + s->loop[i];
    }
    mus.num = s->num;
    mus.den = s->den;
    mus.tacc = s->den;          /* the first frame reads the first events */
}

/* The whole sequencer step for one frame (the interrupt calls this). */
static void mus_frame(void)
{
    if (mus_req_seq != mus_req_seen) {
        mus_req_seen = mus_req_seq;
        int s = mus_req_song;
        if (mus_req_mode == MREQ_NOW || mus.song == SONG_NONE) {
            mus_begin(s);
        } else {
            mus.next = (u8)s;
            mus.fading = 1;
        }
    }
    if (mus.fading) {
        mus.fade -= 20;
        if (mus.fade <= 0) mus_begin(mus.next);
    }
    int duck_to = sfx_fanfare ? 40 : 256;
    if (mus.duck > duck_to) mus.duck = (s16)(mus.duck - 36 < duck_to ? duck_to : mus.duck - 36);
    else if (mus.duck < duck_to) mus.duck = (s16)(mus.duck + 6 > duck_to ? duck_to : mus.duck + 6);

    if (mus.song == SONG_NONE) {
        for (int i = 0; i < MUS_CHANNELS; i++) mus_voice_off(i);
        mus.master = 0;
        return;
    }
    mus.frames++;
    mus.tacc = (u16)(mus.tacc + mus.num);
    while (mus.tacc >= mus.den) {
        mus.tacc = (u16)(mus.tacc - mus.den);
        for (int i = 0; i < MUS_CHANNELS; i++) mus_chan_tick(i);
    }
    int master = mus_option_gain() * MUS_SONGS[mus.song].level >> 7;
    master = master * (mus.fade > 0 ? mus.fade : 0) >> 8;
    master = master * mus.duck >> 8;
    mus.master = (u16)master;
    int alive = 0;
    for (int i = 0; i < MUS_CHANNELS; i++) {
        mus_chan_frame(i, master);
        if (mus_ch[i].pc || mus_ch[i].stage != ENV_OFF) alive = 1;
    }
    if (!alive) mus.song = SONG_NONE;     /* a jingle finished */
}

/* ---------------- mixer ---------------- */

#define MIX_SHIFT 9

/* Render one frame of every voice into out[MUS_MIX_LEN]. */
static void IWRAM_CODE mus_mix(s8 *out)
{
    s32 *acc = mus_acc;
    int any = 0;
    for (int k = 0; k < MUS_CHANNELS; k++) {
        MusVoice *v = &mus_voice[k];
        int n = v->count, vol = v->vol;
        if (!n) continue;
        u32 pos = v->pos, inc = v->inc;
        if (!vol) {
            v->pos = pos + inc * (u32)n;
            continue;
        }
        const s8 *d = v->data;
        int sh = v->shift;
        s32 *a = acc;
        any = 1;
        while (n >= 4) {
            a[0] += d[pos >> sh] * vol; pos += inc;
            a[1] += d[pos >> sh] * vol; pos += inc;
            a[2] += d[pos >> sh] * vol; pos += inc;
            a[3] += d[pos >> sh] * vol; pos += inc;
            a += 4;
            n -= 4;
        }
        while (n--) {
            *a++ += d[pos >> sh] * vol;
            pos += inc;
        }
        v->pos = pos;
    }
    if (!any) {
        /* clear each of the two buffers once: a stale frame left in the
         * other one would be replayed every other frame as a 30 Hz buzz */
        if (mus.silent < 2) {
            u32 *o = (u32 *)out;
            for (int i = 0; i < MUS_MIX_LEN / 4; i++) o[i] = 0;
            mus.silent++;
        }
        return;
    }
    mus.silent = 0;
    for (int i = 0; i < MUS_MIX_LEN; i++) {
        int s = acc[i] >> MIX_SHIFT;
        acc[i] = 0;
        out[i] = (s8)(s > 127 ? 127 : s < -128 ? -128 : s);
    }
}

/* ---------------- interrupt (GBA) ---------------- */

#ifdef GBA
#define REG_ISR_MAIN (*(void (*volatile *)(void))0x03007FFC)
#define REG_IFBIOS   (*(volatile u16 *)0x03007FF8)

/* The interrupt is ARM code in IWRAM; the sequencer is Thumb code in ROM,
 * out of branch range, so it is called through a pointer. */
static void (*volatile mus_frame_fn)(void) = mus_frame;

static void IWRAM_CODE mus_isr(void)
{
    u16 f = (u16)(MREG_IF & MREG_IE);
    MREG_IF = f;
    REG_IFBIOS |= f;
    if (!(f & IRQ_VCOUNT)) return;
    int line0 = REG_VCOUNT;
    s8 *play = mus_buf + mus.play_buf * MUS_MIX_LEN;
    if (mus.started) {
        MREG_DMA1CNT_H = 0;
        MREG_DMA1SAD = (u32)play;
        MREG_DMA1CNT_H = DMA_FIFO_START;
    } else {
        MREG_SOUNDCNT_H = SNDCNT_H_MIX | 0x0800;   /* clear FIFO A */
        MREG_FIFO_A = 0;
        MREG_FIFO_A = 0;                           /* 8 samples of lead-in */
        MREG_DMA1SAD = (u32)play;
        MREG_DMA1DAD = (u32)&MREG_FIFO_A;
        MREG_DMA1CNT_H = DMA_FIFO_START;
        MREG_TM0CNT_H = 0;
        MREG_TM0CNT_L = (u16)(65536 - MUS_RATE_CYCLES);
        MREG_TM0CNT_H = 0x0080;
        mus.started = 1;
    }
    mus.play_buf ^= 1;
    mus_frame_fn();
    mus_mix(mus_buf + mus.play_buf * MUS_MIX_LEN);
    int line1 = REG_VCOUNT;
    mus_prof_lines = (u16)(line1 >= line0 ? line1 - line0 : line1 + 228 - line0);
}
#endif

/* ---------------- game interface ---------------- */

/* Power the sound hardware and start the music interrupt (once, at boot). */
static void music_init(void)
{
    snd_power_on();
#ifdef GBA
    MREG_IME = 0;
    REG_ISR_MAIN = mus_isr;
    REG_DISPSTAT = (u16)((REG_DISPSTAT & 0x00FF) | 0x0020 | (MUS_IRQ_LINE << 8));
    MREG_IE = (u16)(MREG_IE | IRQ_VCOUNT);
    MREG_IF = 0xFFFF;
    MREG_IME = 1;
#endif
}

static void music_request(int song, int mode)
{
    mus_want = (u8)song;
    mus_req_song = (u8)song;
    mus_req_mode = (u8)mode;
    mus_req_seq++;
}

/* Fade out whatever is playing, then start `song` (no-op if it already is). */
static void music_play(int song)
{
    if (song == mus_want) return;
    music_request(song, MREQ_FADE);
}

/* Cut straight to `song`, restarting it even if it is playing. */
static void music_play_now(int song)
{
    music_request(song, MREQ_NOW);
}

static void music_stop(void)
{
    music_play(SONG_NONE);
}

/* The song the game asked for last (SONG_NONE after music_stop). */
MAYBE_UNUSED static int music_current(void)
{
    return mus_want;
}

/* Host builds: one frame of sequencer and mixer (the GBA does this in the
 * interrupt). Returns the rendered frame. */
MAYBE_UNUSED static const s8 *music_host_frame(void)
{
    mus.play_buf ^= 1;
    mus_frame();
    s8 *out = mus_buf + mus.play_buf * MUS_MIX_LEN;
    mus_mix(out);
    return out;
}
