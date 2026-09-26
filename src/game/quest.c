/*
 * NPC quests and the quest log (docs/EXPANSION.md 7.6). Owner: UI system;
 * regions add quest ids in world/<region>/ and advance them in scripts.
 */

#define QUEST_MAX 48
typedef char QuestsFit[QUEST_COUNT <= QUEST_MAX ? 1 : -1];

typedef struct {
    u8 stage[QUEST_MAX];     /* 0 = not started, 255 = done */
    u8 pad[16];
} QuestState;

static QuestState quest;

static void quest_reset(void)
{
    u8 *raw = (u8 *)&quest;
    for (unsigned i = 0; i < sizeof(quest); i++) raw[i] = 0;
}

static void quest_validate(void)
{
}

MAYBE_UNUSED static int quest_get(int q) { return q > 0 && q < QUEST_COUNT ? quest.stage[q] : 0; }
MAYBE_UNUSED static void quest_set(int q, int stage) { if (q > 0 && q < QUEST_COUNT) quest.stage[q] = (u8)stage; }
MAYBE_UNUSED static int quest_done(int q) { return quest_get(q) == 255; }

/* The quest log screen (UI owner). */
MAYBE_UNUSED static void quest_log_open(void)
{
    dlg_say("QUEST LOG: nothing yet.");
}
