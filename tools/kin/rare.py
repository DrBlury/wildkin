"""Kin 101-106 (rare). Owner: KIN-R1.

PLACEHOLDER data and art: stats, learnsets, traits and descriptions
were generated from docs/EXPANSION.md; replace every entry with the real
design (keep id, name, types, rarity and growth), give it a model, and
set placeholder=False (then its base stat total is checked by tier).
The art lives in tools/kin/art_rare.py.
"""

from kin import KinSpec
from kin import art_rare as art


def _m(name):
    """Model function for a species, or None while it is still unpainted."""
    return getattr(art, name, None)


SPECIES = [
    KinSpec(101, 'KOIRIN', ('TIDE',), 'R', base=(80, 40, 60, 60, 60, 40), catch=190, xp=60, evo=('LEVEL', 35, 'RYUKOI'),
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_FIZZ'), (5, 'M_SLIPSTREAM'), (10, 'M_UNDERTOW'), (15, 'M_RIPTIDE'), (20, 'M_SWELL'), (25, 'M_GEYSER')],
            traits=('SURGE', 'SOAKER'), field=(),
            desc='Koi that climbs waterfalls.',
            concept='koi that climbs waterfalls', placeholder=True),
    KinSpec(102, 'RYUKOI', ('TIDE', 'WYRM'), 'R', base=(119, 79, 79, 106, 79, 53), catch=45, xp=220, evo=None,
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_FIZZ'), (1, 'M_SLIPSTREAM'), (1, 'M_WYRM_DANCE'), (14, 'M_WYRMBREATH'), (20, 'M_UNDERTOW'), (26, 'M_RIPTIDE'), (32, 'M_SCALE_REND'), (38, 'M_SWELL'), (44, 'M_GEYSER'), (50, 'M_STARFALL')],
            traits=('SURGE', 'KEEN EYE'), field=('SURF', 'FLY'),
            desc='The koi became a dragon.',
            concept='the koi became a dragon', placeholder=True),
    KinSpec(103, 'TRINKIT', ('RELIC',), 'R', base=(37, 38, 94, 76, 57, 38), catch=190, xp=60, evo=('ITEM', 'RELIC_SHARD', 'HOARDMAW'),
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_TRINKET_TOSS'), (5, 'M_CLATTER'), (10, 'M_TARNISH'), (15, 'M_POLTERGUST'), (20, 'M_GILDED_GLEAM'), (25, 'M_CHEST_CHOMP'), (30, 'M_CURSED_CURIO'), (35, 'M_HEIRLOOM')],
            traits=('HOARDER', 'BEDROCK'), field=(),
            desc='A jewellery box with teeth (mimic).',
            concept='a jewellery box with teeth (mimic)', placeholder=True),
    KinSpec(104, 'HOARDMAW', ('RELIC', 'BEAST'), 'R', base=(73, 61, 123, 98, 86, 74), catch=45, xp=220, evo=None,
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_TRINKET_TOSS'), (1, 'M_CLATTER'), (1, 'M_TARNISH'), (14, 'M_SWIPE'), (20, 'M_POLTERGUST'), (26, 'M_CATNAP'), (32, 'M_CHEST_CHOMP'), (38, 'M_GILDED_GLEAM'), (44, 'M_SNARL'), (50, 'M_CURSED_CURIO')],
            traits=('HOARDER', 'MOMENTUM'), field=(),
            desc='A treasure-chest mimic on legs.',
            concept='a treasure-chest mimic on legs', placeholder=True),
    KinSpec(105, 'RATTLEBONE', ('HOLLOW',), 'R', base=(60, 40, 80, 40, 80, 40), catch=190, xp=60, evo=('ITEM', 'METAL_SHARD', 'OSSIGUARD'),
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_BONE_RATTLE'), (5, 'M_LAST_RITES'), (10, 'M_SHROUD'), (15, 'M_GRAVE_CHILL'), (20, 'M_MARROW_SIP'), (25, 'M_OSSIFY'), (30, 'M_DEATH_KNELL'), (35, 'M_REQUIEM')],
            traits=('STUBBORN', 'SELFMEND'), field=(),
            desc='Skeleton squire with a pot helmet.',
            concept='skeleton squire with a pot helmet', placeholder=True),
    KinSpec(106, 'OSSIGUARD', ('HOLLOW', 'METAL'), 'R', base=(77, 78, 140, 52, 116, 52), catch=45, xp=220, evo=None,
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_RIVET_SHOT'), (1, 'M_BONE_RATTLE'), (1, 'M_IRON_TAP'), (14, 'M_LAST_RITES'), (20, 'M_MAGNET_PULL'), (26, 'M_SHROUD'), (32, 'M_STEEL_SHELL'), (38, 'M_GRAVE_CHILL'), (44, 'M_FORGE_FLASH'), (50, 'M_MARROW_SIP')],
            traits=('STUBBORN', 'BRUISER'), field=('STRENGTH',),
            desc='Skeleton knight.',
            concept='skeleton knight', placeholder=True),
]
