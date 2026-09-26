/*
 * Energy and fusion at the RESONANCE WORKS: unbinding kin into typed energy,
 * mixing energies and the Fusion Loom (docs/EXPANSION.md 7.4). Owner: FUSION
 * system.
 */

typedef struct {
    u16 energy[TYPE_COUNT];   /* 0..9999 each */
    u16 pity;                 /* misses since the last fusion */
    u16 weaves;               /* total weaves */
    u8 pad[8];
} FusionState;

static FusionState fusion;

static void fusion_reset(void)
{
    u8 *raw = (u8 *)&fusion;
    for (unsigned i = 0; i < sizeof(fusion); i++) raw[i] = 0;
}

static void fusion_validate(void)
{
    for (int t = 0; t < TYPE_COUNT; t++)
        if (fusion.energy[t] > 9999) fusion.energy[t] = 9999;
}
