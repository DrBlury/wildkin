/*
 * world/fusion/data.h -- map rows, stamps, decor, objects and wild slots.
 * Owner: FUSION system.
 */

/* The machines of the RESONANCE WORKS (W-EAST's MAP_RESONANCE_WORKS, an
 * 11x9 interior: wall rows 0-1, door at 5,8). Each stands with its top row
 * over the lower wall; examining one opens its screen (fusion_examine).
 * ENGINEER NELL (world/fusion/npcs.inc) waits at 8,5. */
static const DecorPlace WORKS_DECOR[] = {
    DP(FZ_EXTRACTOR, 0, 1), DP(FZ_MIXER, 2, 1), DP(FZ_LOOM, 4, 1), DP(FZ_TANKS, 8, 1),
    DP(PLANT, 10, 1),
};
