"""Kin 107-112 (rare). Owner: KIN-R2.

Three rare two-stage lines (docs/EXPANSION.md 4): GAUNTLING -> HOLLOWHELM
(a haunted gauntlet that becomes an empty suit of plate), WICKLET ->
LAMPGHAST (a candle stub that becomes a paper lantern ghost) and METEORB ->
BOLIDON (a fallen meteorite that becomes a comet-maned rock rhino).
The art lives in tools/kin/art_rare_b.py.
"""

from kin import KinSpec
from kin import art_rare_b as art


def _m(name):
    """Model function for a species, or None while it is still unpainted."""
    return getattr(art, name, None)


SPECIES = [
    KinSpec(107, 'GAUNTLING', ('RELIC', 'METAL'), 'R', base=(45, 74, 82, 30, 46, 50), catch=45, xp=64,
            evo=('LEVEL', 36, 'HOLLOWHELM'),
            category='GAUNTLET', height=4, weight=90,
            learnset=[(1, 'M_BONK'), (1, 'M_CLATTER'), (5, 'M_RIVET_SHOT'), (9, 'M_IRON_TAP'),
                      (13, 'M_MAGNET_PULL'), (17, 'M_TRINKET_TOSS'), (21, 'M_STEEL_SHELL'),
                      (25, 'M_HAMMER_FIST'), (30, 'M_TARNISH'), (35, 'M_GEAR_GRIND')],
            traits=('STUBBORN', 'HOARDER'), field=(),
            desc='A knight\'s gauntlet that never let go of its sword. It scuttles through the SPIRE on its '
                 'fingertips, and whatever it grabs, it keeps.',
            concept='a gauntlet that walks on its fingers', model=_m('gauntling')),
    KinSpec(108, 'HOLLOWHELM', ('RELIC', 'METAL'), 'R', base=(80, 125, 132, 60, 85, 48), catch=45, xp=220,
            evo=None,
            category='EMPTY SUIT', height=19, weight=1600,
            learnset=[(1, 'M_BONK'), (1, 'M_CLATTER'), (1, 'M_RIVET_SHOT'), (1, 'M_IRON_TAP'),
                      (13, 'M_MAGNET_PULL'), (17, 'M_TRINKET_TOSS'), (21, 'M_STEEL_SHELL'),
                      (25, 'M_POLTERGUST'), (30, 'M_TARNISH'), (36, 'M_GEAR_GRIND'), (42, 'M_HEIRLOOM'),
                      (48, 'M_ANVIL_DROP')],
            traits=('STUBBORN', 'BRUISER'), field=('STRENGTH',),
            desc='A suit of plate with nobody inside, held together by a kernel-light that glows through '
                 'every joint. It still keeps the oath its knight swore.',
            concept='an empty suit of armour', model=_m('hollowhelm')),
    KinSpec(109, 'WICKLET', ('RELIC', 'BLAZE'), 'R', base=(40, 34, 46, 76, 60, 70), catch=45, xp=64,
            evo=('LEVEL', 32, 'LAMPGHAST'),
            category='CANDLE', height=2, weight=3,
            learnset=[(1, 'M_CINDER_FLICK'), (1, 'M_LANTERN_LURE'), (5, 'M_CLATTER'), (9, 'M_LAST_EMBER'),
                      (13, 'M_TARNISH'), (17, 'M_HAUNT'), (21, 'M_SEAR_BITE'), (25, 'M_POLTERGUST'),
                      (29, 'M_GILDED_GLEAM')],
            traits=('EMBERSKIN', 'WAKEFUL'), field=(),
            desc='A candle stub left burning on a MIRE grave. It wanders at night in its brass dish, '
                 'and it shrinks a little every time it gets angry.',
            concept='a candle wick sprite', model=_m('wicklet')),
    KinSpec(110, 'LAMPGHAST', ('RELIC', 'BLAZE'), 'R', base=(68, 58, 70, 130, 108, 96), catch=45, xp=220,
            evo=None,
            category='PAPER LAMP', height=12, weight=20,
            learnset=[(1, 'M_CINDER_FLICK'), (1, 'M_LANTERN_LURE'), (1, 'M_CLATTER'), (1, 'M_LAST_EMBER'),
                      (13, 'M_TARNISH'), (17, 'M_HAUNT'), (21, 'M_SEAR_BITE'), (25, 'M_POLTERGUST'),
                      (32, 'M_GILDED_GLEAM'), (38, 'M_KILN_BREATH'), (44, 'M_EMBER_STORM'),
                      (50, 'M_CURSED_CURIO')],
            traits=('EMBERSKIN', 'GLOWER'), field=('LIGHT',),
            desc='A paper lantern that burned for a hundred years and woke up. It licks travellers with '
                 'its long tongue and cackles at their screams.',
            concept='paper lantern ghost (chochin-obake)', model=_m('lampghast')),
    KinSpec(111, 'METEORB', ('ASTRAL', 'STONE'), 'R', base=(50, 72, 88, 48, 45, 27), catch=45, xp=64,
            evo=('LEVEL', 38, 'BOLIDON'),
            category='METEORITE', height=5, weight=650,
            learnset=[(1, 'M_BONK'), (1, 'M_TWINKLE'), (5, 'M_GRIT_KICK'), (9, 'M_PEBBLE_PELT'),
                      (13, 'M_STONESKIN'), (17, 'M_STARDUST'), (21, 'M_ROCKFALL'), (25, 'M_NEBULA_VEIL'),
                      (30, 'M_COMET_DASH'), (35, 'M_MOONBEAM')],
            traits=('BEDROCK', 'STUBBORN'), field=(),
            desc='It fell on a starry night and sprouted legs. Its cracks still glow with the heat of '
                 'the fall, and on clear nights it stares up, homesick.',
            concept='a meteorite with stubby legs', model=_m('meteorb')),
    KinSpec(112, 'BOLIDON', ('ASTRAL', 'STONE'), 'R', base=(100, 132, 116, 66, 68, 50), catch=45, xp=220,
            evo=None,
            category='FIREBALL', height=21, weight=4200,
            learnset=[(1, 'M_BONK'), (1, 'M_TWINKLE'), (1, 'M_GRIT_KICK'), (1, 'M_PEBBLE_PELT'),
                      (13, 'M_STONESKIN'), (17, 'M_STARDUST'), (21, 'M_ROCKFALL'), (25, 'M_NEBULA_VEIL'),
                      (30, 'M_COMET_DASH'), (38, 'M_METEOR_FALL'), (44, 'M_FAULTLINE'), (52, 'M_SUPERNOVA')],
            traits=('MOMENTUM', 'BEDROCK'), field=('STRENGTH', 'LIGHT'),
            desc='When it charges, the air ignites and its mane streams back like a comet\'s tail. '
                 'A herd crossing the sky at night looks like a meteor shower.',
            concept='fireball meteor beast', model=_m('bolidon')),
]
