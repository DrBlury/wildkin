"""Kin 113-120 (rare singles). Owner: KIN-R3.

Eight lone rares out of folklore, each met in one or two places only
(docs/EXPANSION.md 4.3). Base stat totals sit in the 'rare' tier
(440-545); the art is in tools/kin/art_rare_c.py.
"""

from kin import KinSpec
from kin import art_rare_c as art


def _m(name):
    """Model function for a species, or None while it is still unpainted."""
    return getattr(art, name, None)


SPECIES = [
    KinSpec(113, 'KELPYRE', ('TIDE', 'DUSK'), 'R', base=(95, 105, 75, 90, 75, 85), catch=30, xp=190, evo=None,
            category='KELP HORSE', height=18, weight=2400,
            learnset=[(1, 'M_SLIPSTREAM'), (1, 'M_STARE_DOWN'), (1, 'M_FIZZ'), (8, 'M_SNAP'), (15, 'M_UNDERTOW'),
                      (22, 'M_HAUNT'), (29, 'M_SHADE_CUT'), (36, 'M_RIPTIDE'), (43, 'M_GLOOM_ORB'),
                      (50, 'M_GNASH'), (56, 'M_SWELL')],
            traits=('SURGE', 'SLIPPERY'), field=('SURF',),
            desc='It grazes at the LAKE shore on moonless nights, its kelp mane dripping. Riders who climb on '
                 'its back are carried down to the lake bed.',
            model=_m('kelpyre'), placeholder=False),
    KinSpec(114, 'TENGALE', ('GALE', 'BRAWL'), 'R', base=(80, 125, 70, 70, 70, 115), catch=30, xp=190, evo=None,
            category='WIND GOBLIN', height=15, weight=450,
            learnset=[(1, 'M_BEAK_JAB'), (1, 'M_ONE_TWO'), (1, 'M_DRAFT'), (9, 'M_PUMMEL'), (16, 'M_UPDRAFT'),
                      (22, 'M_COUNTERJAB'), (28, 'M_FEATHER_CUT'), (34, 'M_WAR_CRY'), (40, 'M_HAMMER_FIST'),
                      (46, 'M_CROSSWIND'), (52, 'M_HAYMAKER'), (58, 'M_STOOP')],
            traits=('DRIFTER', 'STUBBORN'), field=('FLY',),
            desc='It trains alone on the highest ledges of the PEAK. One sweep of its feather fan turns a gale, '
                 'and it scolds any climber who litters.',
            model=_m('tengale'), placeholder=False),
    KinSpec(115, 'SLUMBAKU', ('DREAM', 'BEAST'), 'R', base=(105, 70, 80, 115, 105, 55), catch=30, xp=190,
            evo=None, category='DREAM EATER', height=11, weight=1300,
            learnset=[(1, 'M_SWIPE'), (1, 'M_DAYDREAM'), (1, 'M_BRACE'), (8, 'M_DART'), (14, 'M_LULLABY'),
                      (20, 'M_PRISM_RAY'), (26, 'M_CATNAP'), (32, 'M_STILL_POND'), (38, 'M_SNARL'),
                      (44, 'M_GLINT'), (50, 'M_DREAMQUAKE'), (56, 'M_BELLY_FLOP')],
            traits=('WAKEFUL', 'SELFMEND'), field=('TELEPORT',),
            desc='It snuffles through the dreams of sleepers and eats their nightmares. Each one it swallows '
                 'floats off as a bubble, and the dreamer wakes up smiling.',
            model=_m('slumbaku'), placeholder=False),
    KinSpec(116, 'WENDIGAUNT', ('FROST', 'HOLLOW'), 'R', base=(80, 110, 75, 105, 70, 85), catch=30, xp=190,
            evo=None, category='FROST HAUNT', height=26, weight=380,
            learnset=[(1, 'M_BONE_RATTLE'), (1, 'M_FLURRY'), (1, 'M_RIME_SHOT'), (8, 'M_HAILSTONES'),
                      (14, 'M_GRAVE_CHILL'), (20, 'M_SNOWDRIFT'), (26, 'M_LAST_RITES'), (32, 'M_SHROUD'),
                      (38, 'M_MARROW_SIP'), (44, 'M_OSSIFY'), (50, 'M_WINTER_RAY'), (56, 'M_DEATH_KNELL')],
            traits=('THICK FUR', 'SELFMEND'), field=(),
            desc='It stalks the PEAK on the longest nights, its deer-skull face white with frost. It is never '
                 'full, and it calls in the voices of lost climbers.',
            model=_m('wendigaunt'), placeholder=False),
    KinSpec(117, 'LAMPJINN', ('RELIC', 'GALE'), 'R', base=(70, 60, 80, 125, 100, 95), catch=30, xp=190, evo=None,
            category='LAMP GENIE', height=14, weight=90,
            learnset=[(1, 'M_DRAFT'), (1, 'M_TRINKET_TOSS'), (1, 'M_TARNISH'), (9, 'M_CLATTER'),
                      (15, 'M_POLTERGUST'), (21, 'M_UPDRAFT'), (27, 'M_GILDED_GLEAM'), (33, 'M_CROSSWIND'),
                      (39, 'M_CURSED_CURIO'), (45, 'M_STILL_POND'), (51, 'M_HEIRLOOM')],
            traits=('HOARDER', 'DRIFTER'), field=('TELEPORT',),
            desc='It sleeps curled in an old brass lamp in the LIBRARY stacks. Rub the lamp and it billows out '
                 'in smoke, but it only grants wishes to those who polish it daily.',
            model=_m('lampjinn'), placeholder=False),
    KinSpec(118, 'GARGOLITH', ('STONE', 'DUSK'), 'R', base=(85, 115, 125, 55, 80, 60), catch=30, xp=190,
            evo=None, category='ROOF GUARD', height=12, weight=1800,
            learnset=[(1, 'M_PEBBLE_PELT'), (1, 'M_STARE_DOWN'), (1, 'M_STONESKIN'), (1, 'M_GRIT_KICK'),
                      (9, 'M_SNAP'), (15, 'M_MUD_PIE'), (21, 'M_ROCKFALL'), (27, 'M_HAUNT'), (33, 'M_SHADE_CUT'),
                      (39, 'M_SANDBLAST'), (45, 'M_GNASH'), (52, 'M_FAULTLINE')],
            traits=('BEDROCK', 'WAKEFUL'), field=('FLY',),
            desc='By day it crouches on the LUMEN rooftops, still as the eaves. At dusk its stone skin softens '
                 'and it glides off to guard the town until dawn.',
            model=_m('gargolith'), placeholder=False),
    KinSpec(119, 'HOPSHI', ('HOLLOW', 'BRAWL'), 'R', base=(95, 120, 100, 50, 90, 55), catch=30, xp=190, evo=None,
            category='TALISMAN', height=16, weight=520,
            learnset=[(1, 'M_PUMMEL'), (1, 'M_BONE_RATTLE'), (1, 'M_ONE_TWO'), (8, 'M_SHROUD'),
                      (14, 'M_GRAVE_CHILL'), (20, 'M_HAMMER_FIST'), (26, 'M_LAST_RITES'), (32, 'M_WAR_CRY'),
                      (38, 'M_COUNTERJAB'), (44, 'M_MARROW_SIP'), (50, 'M_HAYMAKER'), (56, 'M_REQUIEM')],
            traits=('STUBBORN', 'KEEN EYE'), field=(),
            desc='Its knees never bend, so it hops through the GRAVEYARD at night with its arms held out. The '
                 'paper talisman on its hat keeps it calm.',
            model=_m('hopshi'), placeholder=False),
    KinSpec(120, 'QILUMEN', ('ASTRAL', 'SPARK'), 'R', base=(90, 70, 75, 115, 85, 80), catch=25, xp=200, evo=None,
            category='STAR KIRIN', height=20, weight=2600,
            learnset=[(1, 'M_TWINKLE'), (1, 'M_STATIC_POP'), (1, 'M_NEBULA_VEIL'), (8, 'M_TINGLE'),
                      (14, 'M_LIVE_WIRE'), (20, 'M_MOONBEAM'), (26, 'M_STARDUST'), (32, 'M_ARC_FLASH'),
                      (38, 'M_COMET_DASH'), (44, 'M_FORKED_BOLT'), (50, 'M_MUON_RAIN'), (56, 'M_SUPERNOVA')],
            traits=('FOCUSED', 'CONDUCTOR'), field=('TELEPORT', 'LIGHT'),
            desc='It walks on starlight without bending a blade of grass, and shows itself at STARFALL only in '
                 'peaceful years. Its mane crackles with tiny stars.',
            model=_m('qilumen'), placeholder=False),
]
