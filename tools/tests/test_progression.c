/* Baseline graph check. The contract-order solver needs region milestones and gates;
 * until those data exist, an early Cindermoor visit is an expected failure. */
#include "harness.h"

static u8 reachable[MAP_COUNT];
static void graph_flood(void)
{
    int queue[MAP_COUNT], head = 0, tail = 0;
    reachable[MAP_TOWN] = 1;
    queue[tail++] = MAP_TOWN;
    while (head < tail) {
        int m = queue[head++];
        for (int d = 0; d < 4; d++) {
            int dest = MAPS[m].link[d];
            if (dest < MAP_COUNT && !reachable[dest]) {
                reachable[dest] = 1;
                queue[tail++] = dest;
            }
        }
        for (int i = 0; i < WARP_COUNT; i++)
            if (WARPS[i].map == m && WARPS[i].dest < MAP_COUNT && !reachable[WARPS[i].dest]) {
                reachable[WARPS[i].dest] = 1;
                queue[tail++] = WARPS[i].dest;
            }
    }
}

int main(void)
{
    fresh_game();
    flag_set(FLAG_STARTER);
    graph_flood();
    CHECK(reachable[MAP_MEADOW] && reachable[MAP_WOOD] && reachable[MAP_LAKE],
          "Act I home maps are linked from Maple");
    if (reachable[MAP_CINDERMOOR])
        printf("XFAIL progression order: Cindermoor graph reachable after starter before TIDE crest (region G3 pending)\n");
    else
        CHECK(0, "baseline expected Cindermoor shortcut changed; update contract-order assertions");
    return failures ? 1 : 0;
}
