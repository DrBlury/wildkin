"""Kin 107-112 (rare). Owner: KIN-R2.

PLACEHOLDER data and art: stats, learnsets, traits and descriptions
were generated from docs/EXPANSION.md; replace every entry with the real
design (keep id, name, types, rarity and growth), give it a model, and
set placeholder=False (then its base stat total is checked by tier).
The art lives in tools/kin/art_rare_b.py.
"""

from kin import KinSpec
from kin import art_rare_b as art


def _m(name):
    """Model function for a species, or None while it is still unpainted."""
    return getattr(art, name, None)


SPECIES = [
    KinSpec(107, 'GAUNTLING', ('RELIC', 'METAL'), 'R', base=(32, 49, 105, 65, 57, 32), catch=190, xp=60, evo=('LEVEL', 36, 'HOLLOWHELM'),
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_TRINKET_TOSS'), (5, 'M_RIVET_SHOT'), (10, 'M_CLATTER'), (15, 'M_IRON_TAP'), (20, 'M_MAGNET_PULL'), (25, 'M_STEEL_SHELL'), (30, 'M_TARNISH'), (35, 'M_FORGE_FLASH'), (40, 'M_POLTERGUST'), (45, 'M_GILDED_GLEAM')],
            traits=('HOARDER', 'BRUISER'), field=(),
            desc='A gauntlet that walks on its fingers.',
            concept='a gauntlet that walks on its fingers', placeholder=True),
    KinSpec(108, 'HOLLOWHELM', ('RELIC', 'METAL'), 'R', base=(53, 78, 140, 102, 90, 52), catch=45, xp=220, evo=None,
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_TRINKET_TOSS'), (1, 'M_RIVET_SHOT'), (1, 'M_CLATTER'), (14, 'M_IRON_TAP'), (20, 'M_MAGNET_PULL'), (26, 'M_STEEL_SHELL'), (32, 'M_TARNISH'), (38, 'M_FORGE_FLASH'), (44, 'M_POLTERGUST'), (50, 'M_GILDED_GLEAM')],
            traits=('HOARDER', 'BRUISER'), field=('STRENGTH',),
            desc='An empty suit of armour.',
            concept='an empty suit of armour', placeholder=True),
    KinSpec(109, 'WICKLET', ('RELIC', 'BLAZE'), 'R', base=(33, 41, 83, 83, 50, 50), catch=190, xp=60, evo=('LEVEL', 32, 'LAMPGHAST'),
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_TRINKET_TOSS'), (5, 'M_CINDER_FLICK'), (10, 'M_CLATTER'), (15, 'M_LAST_EMBER'), (20, 'M_LANTERN_LURE'), (25, 'M_TARNISH'), (30, 'M_POLTERGUST'), (35, 'M_SEAR_BITE'), (40, 'M_GILDED_GLEAM'), (45, 'M_EMBER_STORM')],
            traits=('HOARDER', 'EMBERSKIN'), field=('LIGHT',),
            desc='A candle wick sprite.',
            concept='a candle wick sprite', placeholder=True),
    KinSpec(110, 'LAMPGHAST', ('RELIC', 'BLAZE'), 'R', base=(50, 63, 126, 126, 75, 75), catch=45, xp=220, evo=None,
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_TRINKET_TOSS'), (1, 'M_CINDER_FLICK'), (1, 'M_CLATTER'), (14, 'M_LAST_EMBER'), (20, 'M_LANTERN_LURE'), (26, 'M_TARNISH'), (32, 'M_POLTERGUST'), (38, 'M_SEAR_BITE'), (44, 'M_GILDED_GLEAM'), (50, 'M_EMBER_STORM')],
            traits=('HOARDER', 'EMBERSKIN'), field=('LIGHT',),
            desc='Paper lantern ghost (chochin-obake).',
            concept='paper lantern ghost (chochin-obake)', placeholder=True),
    KinSpec(111, 'METEORB', ('ASTRAL', 'STONE'), 'R', base=(76, 51, 60, 85, 34, 34), catch=190, xp=60, evo=('LEVEL', 38, 'BOLIDON'),
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_TWINKLE'), (5, 'M_GRIT_KICK'), (10, 'M_NEBULA_VEIL'), (15, 'M_STARDUST'), (20, 'M_STONESKIN'), (25, 'M_PEBBLE_PELT'), (30, 'M_MUD_PIE'), (35, 'M_MOONBEAM'), (40, 'M_SANDBLAST'), (45, 'M_ROCKFALL')],
            traits=('FOCUSED', 'STUBBORN'), field=(),
            desc='A meteorite with stubby legs.',
            concept='a meteorite with stubby legs', placeholder=True),
    KinSpec(112, 'BOLIDON', ('ASTRAL', 'STONE'), 'R', base=(115, 77, 90, 129, 52, 52), catch=45, xp=220, evo=None,
            category='KIN', height=10, weight=100,
            learnset=[(1, 'M_BONK'), (1, 'M_TWINKLE'), (1, 'M_GRIT_KICK'), (1, 'M_NEBULA_VEIL'), (14, 'M_STARDUST'), (20, 'M_STONESKIN'), (26, 'M_PEBBLE_PELT'), (32, 'M_MUD_PIE'), (38, 'M_MOONBEAM'), (44, 'M_SANDBLAST'), (50, 'M_ROCKFALL'), (46, 'M_METEOR_FALL')],
            traits=('FOCUSED', 'STUBBORN'), field=('STRENGTH', 'LIGHT'),
            desc='Fireball meteor beast.',
            concept='fireball meteor beast', placeholder=True),
]
