"""Kin 121-129: the nine new legends. Owner: KIN-C.

Each is a single static encounter in its lair (docs/EXPANSION.md 4.4). Base
stat totals sit near 600 with a clear identity; the art is in art_legend.py.
"""

from kin import KinSpec
from kin import art_legend as A

SPECIES = [
    KinSpec(121, 'CALDERON', ('BLAZE', 'METAL'), 'L', base=(105, 125, 130, 95, 85, 60), catch=3, xp=255,
            evo=None, category='SALAMANDER', height=62, weight=38000,
            learnset=[(1, 'M_SEAR_BITE'), (1, 'M_IRON_TAP'), (1, 'M_CINDER_FLICK'), (1, 'M_MAGNET_PULL'),
                      (12, 'M_FORGE_FLASH'), (20, 'M_STEEL_SHELL'), (28, 'M_EMBER_STORM'), (36, 'M_GEAR_GRIND'),
                      (44, 'M_KILN_BREATH'), (50, 'M_FAULTLINE'), (56, 'M_ANVIL_DROP'), (62, 'M_SUNFLARE')],
            traits=('EMBERSKIN', 'BEDROCK'), field=(),
            desc='It sleeps in the magma of the CALDERA HEART, and its kernel pumps on the heat and the iron '
                 'in its blood. Every scale it sheds cools into a perfect ingot.',
            model=A.calderon, placeholder=False),
    KinSpec(122, 'NOCTHALE', ('TIDE', 'ASTRAL'), 'L', base=(150, 70, 90, 125, 110, 60), catch=3, xp=255,
            evo=None, category='STAR WHALE', height=240, weight=65000,
            learnset=[(1, 'M_FIZZ'), (1, 'M_TWINKLE'), (1, 'M_LULLABY'), (1, 'M_NEBULA_VEIL'),
                      (12, 'M_MOONBEAM'), (20, 'M_UNDERTOW'), (28, 'M_STILL_POND'), (36, 'M_SWELL'),
                      (44, 'M_MUON_RAIN'), (50, 'M_BELLY_FLOP'), (56, 'M_GEYSER'), (62, 'M_SUPERNOVA')],
            traits=('SOAKER', 'SELFMEND'), field=(),
            desc='Its kernel pumps on cosmic-ray muons, which reach even the sea floor. Its song rings the '
                 'DROWNED BELL, and every star in the tide pools answers.',
            model=A.nocthale, placeholder=False),
    KinSpec(123, 'HOARFANG', ('FROST', 'DUSK'), 'L', base=(90, 125, 85, 95, 85, 125), catch=3, xp=255,
            evo=None, category='WINTER WOLF', height=28, weight=1900,
            learnset=[(1, 'M_RIME_SHOT'), (1, 'M_SNAP'), (1, 'M_STARE_DOWN'), (1, 'M_FLURRY'),
                      (12, 'M_HAILSTONES'), (20, 'M_SNOWDRIFT'), (28, 'M_SHADE_CUT'), (36, 'M_SNARL'),
                      (44, 'M_GNASH'), (50, 'M_WINTER_RAY'), (56, 'M_GLOOM_ORB'), (62, 'M_PRIMAL_ROAR')],
            traits=('THICK FUR', 'KEEN EYE'), field=(),
            desc='It pumps by shedding heat, so a blizzard follows its steps. Its shadow runs a moment ahead '
                 'of it. Winter on WHITECROWN PEAK ends only when it sleeps.',
            model=A.hoarfang, placeholder=False),
    KinSpec(124, 'OSSUREX', ('HOLLOW', 'WYRM'), 'L', base=(110, 100, 110, 120, 110, 60), catch=3, xp=255,
            evo=None, category='BONE WYRM', height=71, weight=9800,
            learnset=[(1, 'M_BONE_RATTLE'), (1, 'M_WYRMBREATH'), (1, 'M_SHROUD'), (1, 'M_GRAVE_CHILL'),
                      (12, 'M_MARROW_SIP'), (20, 'M_SCALE_REND'), (28, 'M_WYRM_DANCE'), (36, 'M_OSSIFY'),
                      (40, 'M_LAST_RITES'), (44, 'M_KILN_BREATH'), (50, 'M_DEATH_KNELL'),
                      (56, 'M_REQUIEM'), (62, 'M_STARFALL')],
            traits=('STUBBORN', 'GLOWER'), field=(),
            desc='A century ago OSSUREX brimmed and scorched the ASHEN MARCH. Its kernel outlived its body '
                 'and pumps on the slow heat of old bone, waiting on the BONE THRONE.',
            model=A.ossurex, placeholder=False),
    KinSpec(125, 'SELENOTH', ('ASTRAL', 'DREAM'), 'L', base=(95, 60, 85, 140, 115, 105), catch=3, xp=255,
            evo=None, category='LUNAR MOTH', height=38, weight=220,
            learnset=[(1, 'M_TWINKLE'), (1, 'M_DAYDREAM'), (1, 'M_STARDUST'), (1, 'M_LULLABY'),
                      (12, 'M_MOONBEAM'), (20, 'M_PRISM_RAY'), (28, 'M_NEBULA_VEIL'), (36, 'M_WINGDUST'),
                      (44, 'M_MUON_RAIN'), (50, 'M_DREAMQUAKE'), (56, 'M_STILL_POND'), (62, 'M_SUPERNOVA')],
            traits=('DRIFTER', 'FOCUSED'), field=(),
            desc='Its wing dust is fallen starlight, each mote a tiny muon-pumped kernel. When it sleeps in '
                 'the STARFALL GROTTO, the whole Vale dreams of the same moon.',
            model=A.selenoth, placeholder=False),
    KinSpec(126, 'SYLVARCH', ('BLOOM', 'BEAST'), 'L', base=(115, 122, 100, 90, 100, 92), catch=3, xp=255,
            evo=None, category='ELDER STAG', height=44, weight=8200,
            learnset=[(1, 'M_BRAMBLE_LASH'), (1, 'M_BRACE'), (1, 'M_SAP_SIP'), (1, 'M_DROWSY_POLLEN'),
                      (12, 'M_LEAF_FLURRY'), (20, 'M_SNARL'), (28, 'M_BASK'), (34, 'M_THORN_WALL'),
                      (38, 'M_SUNSHAFT'), (42, 'M_BELLY_FLOP'), (48, 'M_REED_BLADE'), (62, 'M_PRIMAL_ROAR')],
            traits=('BASKER', 'THICK FUR'), field=(),
            desc='The roots of ELDERWOOD HEART are one great web, and SYLVARCH is the kernel it pumps. '
                 'Seeds sprout in its hoofprints, and birds nest in its antlers.',
            model=A.sylvarch, placeholder=False),
    KinSpec(127, 'HOROLOGOS', ('METAL', 'RELIC'), 'L', base=(100, 125, 145, 80, 100, 50), catch=3, xp=255,
            evo=None, category='CLOCKWORK', height=98, weight=52000,
            learnset=[(1, 'M_IRON_TAP'), (1, 'M_CLATTER'), (1, 'M_TARNISH'), (1, 'M_MAGNET_PULL'),
                      (12, 'M_RIVET_SHOT'), (20, 'M_STEEL_SHELL'), (28, 'M_GEAR_GRIND'), (36, 'M_LODE_BEAM'),
                      (44, 'M_CURSED_CURIO'), (50, 'M_FAULTLINE'), (56, 'M_ANVIL_DROP'), (62, 'M_HEIRLOOM')],
            traits=('BEDROCK', 'STUBBORN'), field=(),
            desc='The tower clock kept the valley\'s time for three hundred years, until a magnetite kernel '
                 'woke in its gears. Its pendulum heart has never missed a beat.',
            model=A.horologos, placeholder=False),
    KinSpec(128, 'SCRIPTORA', ('RELIC', 'DREAM'), 'L', base=(95, 65, 90, 135, 125, 95), catch=3, xp=255,
            evo=None, category='LIVING TOME', height=120, weight=1800,
            learnset=[(1, 'M_DAYDREAM'), (1, 'M_CLATTER'), (1, 'M_TARNISH'), (1, 'M_LULLABY'),
                      (12, 'M_POLTERGUST'), (20, 'M_PRISM_RAY'), (28, 'M_SILK_SNARE'), (36, 'M_GILDED_GLEAM'),
                      (44, 'M_STILL_POND'), (50, 'M_DREAMQUAKE'), (56, 'M_CURSED_CURIO'), (62, 'M_BRIM_BURST')],
            traits=('QUICK STUDY', 'WAKEFUL'), field=(),
            desc='A kernel lost in the DUST LIBRARY for a thousand years wove a body from every page. Read '
                 'one of its scales and you will dream the whole book.',
            model=A.scriptora, placeholder=False),
    KinSpec(129, 'SKYLORN', ('GALE', 'ASTRAL'), 'L', base=(95, 105, 80, 110, 90, 125), catch=3, xp=255,
            evo=None, category='SKY MANTA', height=160, weight=12000,
            learnset=[(1, 'M_DRAFT'), (1, 'M_TWINKLE'), (1, 'M_FEATHER_CUT'), (1, 'M_UPDRAFT'),
                      (12, 'M_STARDUST'), (20, 'M_COMET_DASH'), (28, 'M_CROSSWIND'), (36, 'M_NEBULA_VEIL'),
                      (44, 'M_MUON_RAIN'), (50, 'M_STOOP'), (56, 'M_METEOR_FALL'), (62, 'M_SUPERNOVA')],
            traits=('DRIFTER', 'MOMENTUM'), field=(),
            desc='It never lands. It glides so high above the SKY ISLE that the air runs out and muons rain '
                 'on its back. The clouds below are only its shadow.',
            model=A.skylorn, placeholder=False),
]
