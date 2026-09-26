/*
 * Hardware layer: types, memory map, registers and small helpers.
 *
 * On the GBA (built with -DGBA) the addresses are the real memory map.
 * Host test builds redirect every region to plain static arrays so the
 * whole game -- including drawing into VRAM/OAM/palette RAM -- can be
 * exercised by the unit tests without an emulator.
 */

typedef unsigned char  u8;
typedef unsigned short u16;
typedef unsigned int   u32;
typedef signed char    s8;
typedef signed short   s16;
typedef signed int     s32;

#ifdef GBA
#define MEM_IO   0x04000000u
#define MEM_PAL  0x05000000u
#define MEM_VRAM 0x06000000u
#define MEM_OAM  0x07000000u
#define MEM_SRAM 0x0E000000u
/* Large buffers live in the 256 KiB EWRAM (.sbss is zeroed by crt0). */
#define EWRAM_BSS __attribute__((section(".sbss")))
/* Hot code runs as 32-bit ARM from the fast IWRAM (crt0 copies it there
 * with .data). Calls from there back into ROM go through function pointers. */
#define IWRAM_CODE __attribute__((section(".iwram"), target("arm"), noinline))
#else
static u8 host_io[0x400] __attribute__((aligned(4)));
static u8 host_pal[0x400] __attribute__((aligned(4)));
static u8 host_vram[0x18000] __attribute__((aligned(4)));
static u8 host_oam[0x400] __attribute__((aligned(4)));
static u8 host_sram[0x8000] __attribute__((aligned(4)));
#define MEM_IO   ((unsigned long)host_io)
#define MEM_PAL  ((unsigned long)host_pal)
#define MEM_VRAM ((unsigned long)host_vram)
#define MEM_OAM  ((unsigned long)host_oam)
#define MEM_SRAM ((unsigned long)host_sram)
#define EWRAM_BSS
#define IWRAM_CODE
#endif

/* Entry points a module offers before anyone calls them. */
#define MAYBE_UNUSED __attribute__((unused))

#define REG16(off) (*(volatile u16 *)(MEM_IO + (off)))
#define REG32(off) (*(volatile u32 *)(MEM_IO + (off)))

#define REG_DISPCNT   REG16(0x000)
#define REG_DISPSTAT  REG16(0x004)
#define REG_VCOUNT    REG16(0x006)
#define REG_BG0CNT    REG16(0x008)
#define REG_BG1CNT    REG16(0x00A)
#define REG_BG2CNT    REG16(0x00C)
#define REG_BG3CNT    REG16(0x00E)
#define REG_BG0HOFS   REG16(0x010)
#define REG_BG0VOFS   REG16(0x012)
#define REG_BG1HOFS   REG16(0x014)
#define REG_BG1VOFS   REG16(0x016)
#define REG_BG2HOFS   REG16(0x018)
#define REG_BG2VOFS   REG16(0x01A)
#define REG_BG3HOFS   REG16(0x01C)
#define REG_BG3VOFS   REG16(0x01E)
#define REG_WIN0H     REG16(0x040)
#define REG_WIN1H     REG16(0x042)
#define REG_WIN0V     REG16(0x044)
#define REG_WIN1V     REG16(0x046)
#define REG_WININ     REG16(0x048)
#define REG_WINOUT    REG16(0x04A)
#define REG_MOSAIC    REG16(0x04C)
#define REG_BLDCNT    REG16(0x050)
#define REG_BLDALPHA  REG16(0x052)
#define REG_BLDY      REG16(0x054)
#define REG_DMA3SAD   REG32(0x0D4)
#define REG_DMA3DAD   REG32(0x0D8)
#define REG_DMA3CNT   REG32(0x0DC)
#define REG_KEYINPUT  REG16(0x130)
#define REG_WAITCNT   REG16(0x204)

#define SCREEN_WIDTH  240
#define SCREEN_HEIGHT 160

#define DCNT_MODE0   0x0000
#define DCNT_OBJ_1D  0x0040
#define DCNT_BLANK   0x0080
#define DCNT_BG0     0x0100
#define DCNT_BG1     0x0200
#define DCNT_BG2     0x0400
#define DCNT_BG3     0x0800
#define DCNT_OBJ     0x1000
#define DCNT_WIN0    0x2000

#define BGCNT_PRIO(n)        ((n) & 3)
#define BGCNT_CHARBLOCK(n)   ((n) << 2)
#define BGCNT_SCREENBLOCK(n) ((n) << 8)
#define BGCNT_SIZE_32x64     0x8000

#define KEY_A      0x0001
#define KEY_B      0x0002
#define KEY_SELECT 0x0004
#define KEY_START  0x0008
#define KEY_RIGHT  0x0010
#define KEY_LEFT   0x0020
#define KEY_UP     0x0040
#define KEY_DOWN   0x0080
#define KEY_R      0x0100
#define KEY_L      0x0200

/* OAM attribute bits */
#define ATTR0_TALL    0x8000
#define ATTR0_WIDE    0x4000
#define ATTR0_BLEND   0x0400
#define ATTR0_HIDE    0x0200
#define ATTR1_HFLIP   0x1000
#define ATTR1_VFLIP   0x2000
#define ATTR1_SIZE(n) ((n) << 14)
#define ATTR2_PRIO(n) ((n) << 10)
#define ATTR2_BANK(n) ((n) << 12)

#define RGB15(r, g, b) ((u16)((r) | ((g) << 5) | ((b) << 10)))

static u16 *const bg_palette = (u16 *)(MEM_PAL);
static u16 *const obj_palette = (u16 *)(MEM_PAL + 0x200);
static volatile u16 *const oam = (volatile u16 *)MEM_OAM;

/*
 * VRAM layout (mode 0):
 *   0x0000..0x5FFF        scene tiles (SCENE_TILE_MAX): field tileset + decor,
 *                         or the battle background; BGs use charblock 0
 *   0x6000..0xDF1F        UI: canvas cells 0..599, scroll panel 600..1016
 *                         (VRAM_UI_TILES; the canvas BG uses charblock 1, so
 *                         its tile numbers are UI_TILE_BASE + cell, and the
 *                         panel BG charblock 2, numbers PANEL_BG_BASE + tile)
 *   screenblock 28        BG0 map (field bottom / battle scene)
 *   screenblock 29        BG3 map (field top layer)
 *   screenblock 30        BG1 map (UI canvas)
 *   screenblock 31        BG2 map (field mid layer / catalogue scroll panel)
 *   0x10000..0x17FFF      OBJ tiles
 */
#define SCENE_TILE_MAX    768
#define UI_TILE_BASE      256    /* tile number of UI tile 0 from charblock 1 */
#define PANEL_BG_BASE     (-256) /* ... and from charblock 2 */
#define VRAM_SCENE_TILES  ((u32 *)(MEM_VRAM))
#define VRAM_UI_TILES     ((u32 *)(MEM_VRAM + 0x6000))
#define VRAM_MAP(sb)      ((u16 *)(MEM_VRAM + (sb) * 2048))
#define VRAM_OBJ_TILES    ((u32 *)(MEM_VRAM + 0x10000))
#define SB_FIELD_BOTTOM   28
#define SB_FIELD_TOP      29
#define SB_UI             30
#define SB_PANEL          31

static int clampi(int v, int lo, int hi)
{
    return v < lo ? lo : (v > hi ? hi : v);
}

static int absi(int v)
{
    return v < 0 ? -v : v;
}

/* Word copy via DMA3 on hardware, plain loop on the host. */
static void copy32(void *dst, const void *src, unsigned words)
{
    if (!words) return;
#ifdef GBA
    REG_DMA3CNT = 0;
    REG_DMA3SAD = (u32)src;
    REG_DMA3DAD = (u32)dst;
    REG_DMA3CNT = words | 0x84000000u; /* enable, 32-bit */
    /* The transfer only starts two cycles after the enable; a copy32 right
     * behind this one would clear DMA3CNT first and cancel it. Wait until
     * the enable bit drops (the CPU is halted while the transfer runs). */
    while (REG_DMA3CNT & 0x80000000u) {
    }
#else
    u32 *d = dst;
    const u32 *s = src;
    while (words--) *d++ = *s++;
#endif
}

static void fill32(void *dst, u32 value, unsigned words)
{
    u32 *d = dst;
    while (words--) *d++ = value;
}

static void copy16(void *dst, const void *src, unsigned halfwords)
{
    u16 *d = dst;
    const u16 *s = src;
    while (halfwords--) *d++ = *s++;
}

static void vsync(void)
{
#ifdef GBA
    while (REG_VCOUNT >= SCREEN_HEIGHT) {
    }
    while (REG_VCOUNT < SCREEN_HEIGHT) {
    }
#endif
}

/* ---------------- input ---------------- */

static u16 keys_now, keys_prev;
static u16 key_repeat_timer;

static int key_down(int key)
{
    return keys_now & key;
}

static int key_hit(int key)
{
    return (keys_now & key) && !(keys_prev & key);
}

/* Menu navigation: a hit, then auto-repeat while the key stays held. */
static int key_rep(int key)
{
    if (key_hit(key)) return 1;
    return (keys_now & key) && key_repeat_timer >= 18 && (key_repeat_timer & 3) == 0;
}

/* ---------------- deterministic RNG ---------------- */

static u32 rng_state = 1;

static void rng_seed(u32 seed)
{
    rng_state = seed ? seed : 0xA5A5A5A5u;
}

static unsigned rng_next(void)
{
    rng_state = rng_state * 1664525u + 1013904223u;
    return (unsigned)(rng_state >> 8) & 0xFFFFFFu;
}

static unsigned rng_range(unsigned n)
{
    return n ? rng_next() % n : 0;
}

/* ---------------- strings ---------------- */

static unsigned str_len(const char *s)
{
    unsigned n = 0;
    while (s[n]) n++;
    return n;
}

static void str_copy(char *dst, const char *src)
{
    unsigned n = str_len(src);
    for (unsigned i = 0; i < n; i++) dst[i] = src[i];
    dst[n] = 0;
}

static void str_put(char *dst, const char *src)
{
    str_copy(dst + str_len(dst), src);
}

static void fmt_int(char *dst, int v)
{
    char tmp[12];
    int n = 0;
    if (v < 0) {
        *dst++ = '-';
        v = -v;
    }
    do {
        tmp[n++] = (char)('0' + v % 10);
        v /= 10;
    } while (v);
    for (int i = 0; i < n; i++) dst[i] = tmp[n - 1 - i];
    dst[n] = 0;
}

static void str_put_int(char *dst, int v)
{
    fmt_int(dst + str_len(dst), v);
}

static void str_put_int3(char *dst, int v)
{
    char tmp[4];
    tmp[0] = (char)('0' + v / 100 % 10);
    tmp[1] = (char)('0' + v / 10 % 10);
    tmp[2] = (char)('0' + v % 10);
    tmp[3] = 0;
    str_put(dst, tmp);
}

static int str_eq(const char *a, const char *b)
{
    while (*a && *a == *b) {
        a++;
        b++;
    }
    return *a == *b;
}

static unsigned long long isqrt64(unsigned long long v)
{
    unsigned long long r = 0, bit = 1ull << 62;
    while (bit > v) bit >>= 2;
    while (bit) {
        if (v >= r + bit) {
            v -= r + bit;
            r = (r >> 1) + bit;
        } else {
            r >>= 1;
        }
        bit >>= 2;
    }
    return r;
}

