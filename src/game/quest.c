/*
 * NPC quests and the quest log (docs/EXPANSION.md 7.6). Owner: UI system;
 * regions add quest ids in world/<region>/ and advance them in scripts.
 */

#define QUEST_MAX 48

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
