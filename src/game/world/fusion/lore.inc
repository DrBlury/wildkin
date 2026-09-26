/* world/fusion/lore.inc -- Lorebook entries: [LORE_X] = { LCH_..., LSRC_..., "TITLE", "page", "talk" },. Owner: FUSION system. */

    [LORE_RESONANCE_WORKS] = { LCH_PLACES, LSRC_WORKS, "RESONANCE WORKS",
        "The Resonance Works stands in Lumen City, where the copper lines from "
        "the old power station meet. It began as a lamp-maker's shop. Lumen's "
        "glassblowers wanted a steadier glow than any flame, and found it in "
        "the motes that leak from kin kernels.\n\n"
        "Today it holds four machines. The EXTRACTOR unbinds a kin's kernel "
        "into a flask of typed energy. The MIXER turns two energies into a "
        "third. The ENERGY TANKS keep count of what you have. And in the "
        "middle stands the FUSION LOOM, the only place in the Vale where new "
        "kernels are woven on purpose.\n\n"
        "ENGINEER NELL runs the front desk. She has unbound more kin than anyone "
        "alive, and she thanks every one of them by name.",
        "Welcome to the Works! Everything here runs on motes: the lamps, the "
        "pumps, even the kettle.\fThe big ring in the middle is the Loom. "
        "Don't touch it until you've had the tour!" },

    [LORE_TYPED_ENERGY] = { LCH_ENERGY, LSRC_WORKS, "TYPED ENERGY",
        "When a kernel lets go of its condensate, the motes don't vanish at "
        "once. For a moment they keep ringing at the frequency of their pump "
        "band. A heartglass flask can catch them while they ring, and a "
        "flask of BLAZE motes stays warm for years.\n\n"
        "The Works calls this typed energy. There are eighteen kinds, one for "
        "every band. They can be stored, measured, mixed and woven. Each pool "
        "holds up to 9999 units before the glass starts to sing.\n\n"
        "REAL SCIENCE: light trapped between two good mirrors keeps its colour "
        "while it bounces back and forth. Such traps are called optical "
        "cavities, and the best ones hold light for a long time.\n\n"
        "VALE ONLY: heartglass that holds motes for years.",
        "Every kernel rings like a bell, and each type has its own note. When "
        "a kernel comes unbound, the note keeps ringing for a while.\fOur "
        "flasks catch that ringing. We call it typed energy." },

    [LORE_TUNING] = { LCH_ENERGY, LSRC_WORKS, "TUNING A MIX",
        "Two kinds of typed energy poured into the MIXER can join into a "
        "third. BLAZE and TIDE make GALE, the way a kettle makes steam. SPARK "
        "and STONE make METAL, as a smelter does. There are 26 known pairs, "
        "and together they reach every one of the eighteen types.\n\n"
        "The mix only takes when the two energies ring in step. The tuner "
        "shows both waves on its screen: turn the pitch knob and the phase "
        "knob until your wave lies on the target. A perfect match yields 120 "
        "units for every 100 you put in, and a clumsy one only 60.\n\n"
        "REAL SCIENCE: some crystals can join two beams of light into a new "
        "colour. It only works well when the waves stay in step as they "
        "travel through the crystal. Physicists call this phase matching.\n\n"
        "VALE ONLY: doing it with the energy of living kernels.",
        "The MIXER is fussy. Two energies only join if they ring together.\f"
        "Watch the scope and line your wave up with the gold one. Get it "
        "right and you'll get back more than you put in!" },

    [LORE_FUSION_LOOM] = { LCH_ENERGY, LSRC_WORKS, "THE FUSION LOOM",
        "The FUSION LOOM is a ring of heartglass with three sockets. Pour two "
        "or three energies into it and set a stake. The ring spins the motes "
        "together, and if they lock in step, a new kernel nucleates in the "
        "middle and precipitates a body around itself: a fusion kin.\n\n"
        "Nobody can force it. Nucleation is chance, so the Loom always shows "
        "the odds. A bigger stake helps, and so do balanced stores. Each "
        "failed weave also leaves the heartglass a little more ordered.\n\n"
        "REAL SCIENCE: very pure water can be cooled below zero and stay "
        "liquid until a crystal happens to nucleate. That moment is random, "
        "but a seed makes it far more likely.\n\n"
        "VALE ONLY: kernels nucleated from typed energy.",
        "The Loom never promises. It spins, the motes try to lock, and "
        "sometimes a kernel is born.\fIt always shows you the odds, and it "
        "remembers every miss. Keep at it!" },

    [LORE_SIGNATURES] = { LCH_ENERGY, LSRC_WORKS, "SIGNATURES",
        "Every fusion kin has a signature: the two energy types its kernel "
        "was woven from. STEAMOTH is BLAZE and TIDE, VOLTORTLE is SPARK and "
        "STONE, and so on for all 44 known fusions. The Loom only weaves a "
        "kin when both of its signature types are in the sockets.\n\n"
        "With three types in the sockets, up to three signatures can answer "
        "at once, and the Loom shows every candidate. When there is more than "
        "one, a kin you have never had is three times as likely to form: the "
        "Loom seems to prefer new tunes.\n\n"
        "Unbind a fusion kin and it gives back its signature energies, half "
        "and half.",
        "Each fusion kin has a signature, two energies that belong together.\f"
        "Put both in the sockets and the Loom can weave it. Put in three, and "
        "you might get one of several!" },

    [LORE_UNBINDING] = { LCH_ENERGY, LSRC_STORY, "UNBINDING",
        "The EXTRACTOR's dome slowly detunes a kin's kernel until its "
        "condensate lets go. The motes stream up the copper pipe into the "
        "flask as typed energy, and the kin's body, no longer held by the "
        "kernel's field, is released.\n\n"
        "It does not hurt. The body wanders home to the wild it came from, "
        "and in time a new kernel kindles there. Woven kin have no home in "
        "the wild; their motes simply scatter.\n\n"
        "A kin gives 8 units plus half its level. Rare and fusion kin give "
        "half again as much, legends four times as much, and lustrous kin "
        "twice as much. A kin with two types gives 60% to its first type and "
        "40% to its second.\n\n"
        "VALE ONLY: unbinding, and every part of it.",
        0 },

    [LORE_MIX_TABLE] = { LCH_ENERGY, LSRC_STORY, "THE MIXING TABLE",
        "BLAZE+TIDE: GALE (steam). SPARK+STONE: METAL (smelting). "
        "HOLLOW+DREAM: RELIC (memory). BLOOM+DUSK: VENOM (rot). "
        "BLOOM+BRAWL: BEAST (grazing). VENOM+GALE: BLAZE (marsh gas). "
        "SPARK+BLOOM: BLAZE (wildfire). FROST+BLAZE: TIDE (melt). "
        "TIDE+STONE: BLOOM (soil). GALE+FROST: SPARK (stormcloud). "
        "DUSK+TIDE: FROST (hoarfrost). STONE+BEAST: BRAWL (hauling).\n\n"
        "SWARM+TIDE: STONE (reef). METAL+TIDE: STONE (rust). HOLLOW+TIDE: "
        "STONE (fossil). SWARM+SPARK: DREAM (neurons). BEAST+DUSK: DREAM "
        "(slumber). RELIC+SPARK: DREAM (echo). BLOOM+GALE: SWARM (pollen). "
        "BLAZE+BLOOM: DUSK (charcoal). GALE+TIDE: WYRM (storm).\n\n"
        "BEAST+VENOM: HOLLOW (decay). WYRM+STONE: HOLLOW (deep time). "
        "METAL+BRAWL: RELIC (handwork). ASTRAL+STONE: METAL (meteorite). "
        "SPARK+DUSK: ASTRAL (aurora).\n\n"
        "Starting from BEAST, BLAZE, TIDE, BLOOM, SPARK, GALE and STONE, "
        "mixing reaches all eighteen types.",
        0 },

    [LORE_LOOM_ODDS] = { LCH_ENERGY, LSRC_STORY, "THE LOOM'S ODDS",
        "Every weave has a 6% base chance. A stake of 30 of each energy adds "
        "6%, and a stake of 60 adds 14%. Harmony adds up to 8% more: the "
        "closer your picked stores are to each other, the better they lock.\n\n"
        "Each miss adds 3% to the next weave, and after 25 misses in a row "
        "the Loom is sure to weave. A miss is not wasted either: the motes "
        "settle as MOTE DUST (1, 2 or 3 by stake), and 30% of the stake "
        "flows back into your flask.\n\n"
        "A woven kin starts at level 15, 25 or 40, by stake.",
        0 },

    [LORE_WOVEN_KIN] = { LCH_ENERGY, LSRC_STORY, "WOVEN KIN",
        "A woven kernel has never known the wild. Fusion kin bond with the "
        "first face they see, and they tend to be proud, strong and a little "
        "strange: a moth made of steam, a tortoise that drinks lightning.\n\n"
        "They never appear in the wild, and they don't grow into anything "
        "else. They are already everything they will be.\n\n"
        "VALE ONLY: kin woven from energy.",
        0 },
