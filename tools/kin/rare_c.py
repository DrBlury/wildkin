"""Kin 113-120 (rare). Owner: KIN-R3.

PLACEHOLDER data and art: stats, learnsets, traits and descriptions
were generated from docs/EXPANSION.md; replace every entry with the real
design (keep id, name, types, rarity and growth), give it a model, and
set placeholder=False (then its base stat total is checked by tier).
The art lives in tools/kin/art_rare_c.py.
"""

from kin import KinSpec
from kin import art_rare_c as art


def _m(name):
    """Model function for a species, or None while it is still unpainted."""
    return getattr(art, name, None)


SPECIES = [
    KinSpec(113, 'KELPYRE', ('TIDE', 'DUSK'), 'R', base=(103, 51, 77, 115, 77, 77), catch=30, xp=190, evo=None,
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_FIZZ'), (1, 'M_SLIPSTREAM'), (1, 'M_STARE_DOWN'), (14, 'M_SNAP'), (20, 'M_UNDERTOW'), (26, 'M_HAUNT'), (32, 'M_SHADE_CUT'), (38, 'M_RIPTIDE'), (44, 'M_GLOOM_ORB'), (50, 'M_GNASH')],
            traits=('SURGE', 'SLIPPERY'), field=('SURF',),
            desc='Kelpie water horse.',
            concept='kelpie water horse', placeholder=True),
    KinSpec(114, 'TENGALE', ('GALE', 'BRAWL'), 'R', base=(74, 138, 50, 50, 50, 138), catch=30, xp=190, evo=None,
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_PUMMEL'), (1, 'M_ONE_TWO'), (1, 'M_BEAK_JAB'), (14, 'M_DRAFT'), (20, 'M_UPDRAFT'), (26, 'M_WAR_CRY'), (32, 'M_HAMMER_FIST'), (38, 'M_COUNTERJAB'), (44, 'M_FEATHER_CUT'), (50, 'M_CROSSWIND')],
            traits=('DRIFTER', 'STUBBORN'), field=('FLY',),
            desc='Tengu, long nose and a feather fan.',
            concept='tengu, long nose and a feather fan', placeholder=True),
    KinSpec(115, 'SLUMBAKU', ('DREAM', 'BEAST'), 'R', base=(76, 62, 50, 125, 112, 75), catch=30, xp=190, evo=None,
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_SWIPE'), (1, 'M_DART'), (1, 'M_BRACE'), (14, 'M_CATNAP'), (20, 'M_LULLABY'), (26, 'M_POUT'), (32, 'M_STILL_POND'), (38, 'M_DAYDREAM'), (44, 'M_SNARL'), (50, 'M_GLINT')],
            traits=('FOCUSED', 'MOMENTUM'), field=('TELEPORT',),
            desc='Baku dream-eater tapir.',
            concept='baku dream-eater tapir', placeholder=True),
    KinSpec(116, 'WENDIGAUNT', ('FROST', 'HOLLOW'), 'R', base=(63, 51, 103, 103, 103, 77), catch=30, xp=190, evo=None,
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_HAILSTONES'), (1, 'M_BONE_RATTLE'), (1, 'M_FLURRY'), (14, 'M_RIME_SHOT'), (20, 'M_LAST_RITES'), (26, 'M_SNOWDRIFT'), (32, 'M_SHROUD'), (36, 'M_GRAVE_CHILL'), (40, 'M_MARROW_SIP'), (45, 'M_OSSIFY'), (50, 'M_WINTER_RAY')],
            traits=('THICK FUR', 'SELFMEND'), field=(),
            desc='Wendigo, antlered and gaunt.',
            concept='wendigo, antlered and gaunt', placeholder=True),
    KinSpec(117, 'LAMPJINN', ('RELIC', 'GALE'), 'R', base=(49, 73, 122, 98, 73, 85), catch=30, xp=190, evo=None,
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_TRINKET_TOSS'), (1, 'M_BEAK_JAB'), (1, 'M_CLATTER'), (14, 'M_DRAFT'), (20, 'M_TARNISH'), (26, 'M_UPDRAFT'), (32, 'M_FEATHER_CUT'), (38, 'M_POLTERGUST'), (44, 'M_GILDED_GLEAM'), (50, 'M_CROSSWIND')],
            traits=('HOARDER', 'MOMENTUM'), field=('TELEPORT',),
            desc='A genie rising from an oil lamp.',
            concept='a genie rising from an oil lamp', placeholder=True),
    KinSpec(118, 'GARGOLITH', ('STONE', 'DUSK'), 'R', base=(73, 98, 122, 85, 49, 73), catch=30, xp=190, evo=None,
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_GRIT_KICK'), (1, 'M_STARE_DOWN'), (1, 'M_STONESKIN'), (14, 'M_PEBBLE_PELT'), (20, 'M_MUD_PIE'), (26, 'M_SNAP'), (32, 'M_HAUNT'), (38, 'M_SANDBLAST'), (44, 'M_SHADE_CUT'), (50, 'M_ROCKFALL')],
            traits=('BEDROCK', 'SLIPPERY'), field=('FLY',),
            desc='Gargoyle.',
            concept='gargoyle', placeholder=True),
    KinSpec(119, 'HOPSHI', ('HOLLOW', 'BRAWL'), 'R', base=(100, 88, 100, 50, 100, 62), catch=30, xp=190, evo=None,
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_PUMMEL'), (1, 'M_ONE_TWO'), (1, 'M_BONE_RATTLE'), (14, 'M_LAST_RITES'), (20, 'M_SHROUD'), (26, 'M_WAR_CRY'), (32, 'M_HAMMER_FIST'), (38, 'M_GRAVE_CHILL'), (44, 'M_COUNTERJAB'), (50, 'M_MARROW_SIP')],
            traits=('STUBBORN', 'KEEN EYE'), field=(),
            desc='Hopping vampire (jiangshi).',
            concept='hopping vampire (jiangshi)', placeholder=True),
    KinSpec(120, 'QILUMEN', ('ASTRAL', 'SPARK'), 'R', base=(106, 54, 54, 140, 54, 92), catch=30, xp=190, evo=None,
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_STATIC_POP'), (1, 'M_TWINKLE'), (1, 'M_NEBULA_VEIL'), (14, 'M_TINGLE'), (20, 'M_LIVE_WIRE'), (26, 'M_MOONBEAM'), (32, 'M_ARC_FLASH'), (38, 'M_COMET_DASH'), (44, 'M_STARDUST'), (50, 'M_FORKED_BOLT')],
            traits=('FOCUSED', 'CONDUCTOR'), field=('TELEPORT', 'LIGHT'),
            desc='Kirin with a star-lit mane.',
            concept='kirin with a star-lit mane', placeholder=True),
]
