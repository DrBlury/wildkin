/* cc -std=c11 -o /tmp/test_worldpos tools/tests/test_worldpos.c && /tmp/test_worldpos */
#define WORLD_LAYOUT_TEST
#include "../render_world.c"
#include <assert.h>

int main(void)
{
    WorldMap maps[4] = {
        { .w=20, .h=12, .outdoor=1, .link={255,255,255,1} },
        { .w=10, .h=12, .outdoor=1, .link={255,255,0,255} },
        { .w=8, .h=8, .outdoor=1, .link={255,255,255,255} },
        { .w=8, .h=8, .outdoor=1, .link={255,255,255,255} },
    };
    WorldPlace pos[4];
    WorldHint hints[] = { {2, 1, 10, 0}, {3, 2, 0, 8} };
    assert(world_layout(maps, 4, hints, 2, pos, stderr) == 0);
    assert(pos[1].placed && pos[1].x == 20);
    assert(pos[2].placed && pos[2].x == 30);
    assert(pos[3].placed && pos[3].y == 8);
    hints[0].dx = -5;
    assert(world_layout(maps, 4, hints, 2, pos, stderr) == 4);
    hints[0].map = 8;
    assert(world_layout(maps, 4, hints, 2, pos, stderr) == -1);
    puts("worldpos: ok");
    return 0;
}
