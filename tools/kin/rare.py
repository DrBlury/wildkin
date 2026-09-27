"""Kin 101-106 (rare). Owner: KIN-R1.

Three rare two-stage lines: the waterfall koi that becomes a dragon, the
jewellery-box mimic that becomes a treasure chest on legs, and the pot-helmet
skeleton squire that becomes a rusted knight. First stages sit in the
'first' BST tier, the grown forms in 'final'. The art lives in
tools/kin/art_rare.py.
"""

from kin import KinSpec
from kin import art_rare as art


def _m(name):
    """Model function for a species, or None while it is still unpainted."""
    return getattr(art, name, None)


SPECIES = [
    KinSpec(101, 'KOIRIN', ('TIDE',), 'R', base=(50, 55, 48, 47, 50, 80), catch=45, xp=64,
            evo=('LEVEL', 35, 'RYUKOI'),
            category='LEAPING KOI', height=6, weight=45,
            learnset=[(1, 'M_SLIPSTREAM'), (1, 'M_POUT'), (6, 'M_FIZZ'), (10, 'M_DART'), (15, 'M_UNDERTOW'),
                      (20, 'M_GLINT'), (25, 'M_BRACE'), (29, 'M_RIPTIDE'), (34, 'M_SWELL')],
            traits=('SURGE', 'SLIPPERY'), field=(),
            desc='It leaps at the waterfall all day and falls back every time, never discouraged. They say '
                 'the one that reaches the top of the falls will become a dragon.',
            concept='kohaku koi leaping up a falls', model=_m('koirin'), placeholder=False),
    KinSpec(102, 'RYUKOI', ('TIDE', 'WYRM'), 'R', base=(85, 82, 78, 104, 90, 86), catch=45, xp=220,
            evo=None,
            category='KOI DRAGON', height=48, weight=1650,
            learnset=[(1, 'M_SLIPSTREAM'), (1, 'M_FIZZ'), (1, 'M_WYRM_DANCE'), (1, 'M_WYRMBREATH'),
                      (20, 'M_UNDERTOW'), (29, 'M_RIPTIDE'), (35, 'M_SCALE_REND'), (40, 'M_SWELL'),
                      (46, 'M_GEYSER'), (53, 'M_STARFALL')],
            traits=('SURGE', 'KEEN EYE'), field=('SURF', 'FLY'),
            desc='The koi that cleared the falls. Its fins unfurled into silk banners and its whiskers into '
                 'gold. It rides the spray into the sky and brings the rain clouds home.',
            concept='elegant white-red-gold koi dragon', model=_m('ryukoi'), placeholder=False),
    KinSpec(103, 'TRINKIT', ('RELIC',), 'R', base=(45, 62, 78, 42, 55, 40), catch=45, xp=64,
            evo=('ITEM', 'RELIC_SHARD', 'HOARDMAW'),
            category='MIMIC BOX', height=3, weight=28,
            learnset=[(1, 'M_BONK'), (1, 'M_TRINKET_TOSS'), (5, 'M_CLATTER'), (10, 'M_TARNISH'),
                      (15, 'M_POLTERGUST'), (20, 'M_GILDED_GLEAM'), (25, 'M_CHEST_CHOMP'),
                      (30, 'M_CURSED_CURIO'), (36, 'M_HEIRLOOM')],
            traits=('HOARDER', 'BEDROCK'), field=(),
            desc='It sits very still on a dresser and waits for a hand to reach in. Whatever it bites, it '
                 'keeps: rings, keys, buttons. Shake it and the whole hoard rattles.',
            concept='a jewellery box with teeth (mimic)', model=_m('trinkit'), placeholder=False),
    KinSpec(104, 'HOARDMAW', ('RELIC', 'BEAST'), 'R', base=(92, 115, 118, 58, 80, 42), catch=45, xp=220,
            evo=None,
            category='CHEST BEAST', height=14, weight=2400,
            learnset=[(1, 'M_SWIPE'), (1, 'M_TRINKET_TOSS'), (1, 'M_CLATTER'), (1, 'M_TARNISH'), (15, 'M_POLTERGUST'), (20, 'M_CHEST_CHOMP'), (26, 'M_SNARL'), (31, 'M_RAIDO_RUSH'), (32, 'M_GILDED_GLEAM'), (38, 'M_CATNAP'), (44, 'M_CURSED_CURIO'), (50, 'M_HEIRLOOM')],
            traits=('HOARDER', 'MOMENTUM'), field=(),
            desc='A treasure chest that walked out of the crypt on its own legs. It sleeps with its lid '
                 'open and its gold on show. Anyone who reaches for a coin gets eaten.',
            concept='iron-banded treasure chest on beast legs', model=_m('hoardmaw'), placeholder=False),
    KinSpec(105, 'RATTLEBONE', ('HOLLOW',), 'R', base=(50, 58, 72, 35, 55, 42), catch=45, xp=64,
            evo=('ITEM', 'METAL_SHARD', 'OSSIGUARD'),
            category='SQUIRE', height=7, weight=110,
            learnset=[(1, 'M_BONK'), (1, 'M_BONE_RATTLE'), (5, 'M_BRACE'), (10, 'M_SHROUD'),
                      (15, 'M_LAST_RITES'), (20, 'M_GRAVE_CHILL'), (25, 'M_OSSIFY'), (30, 'M_MARROW_SIP'),
                      (36, 'M_DEATH_KNELL')],
            traits=('STUBBORN', 'SELFMEND'), field=(),
            desc='It wears a cooking pot for a helmet and carries a lid for a shield. Each night it drills '
                 'its sword swings in the OSSUARY, waiting for a knight to serve.',
            concept='pot-helmet skeleton squire', model=_m('rattlebone'), placeholder=False),
    KinSpec(106, 'OSSIGUARD', ('HOLLOW', 'METAL'), 'R', base=(80, 112, 128, 50, 88, 52), catch=45, xp=220,
            evo=None,
            category='BONE KNIGHT', height=19, weight=1450,
            learnset=[(1, 'M_BONE_RATTLE'), (1, 'M_IRON_TAP'), (1, 'M_SHROUD'), (1, 'M_BRACE'),
                      (20, 'M_RIVET_SHOT'), (26, 'M_STEEL_SHELL'), (32, 'M_OSSIFY'), (38, 'M_MAGNET_PULL'),
                      (44, 'M_GRAVE_CHILL'), (50, 'M_ANVIL_DROP'), (56, 'M_REQUIEM')],
            traits=('STUBBORN', 'BRUISER'), field=('STRENGTH',),
            desc='The squire kept its vow long after its knight fell. Its rusted plates clank with every '
                 'step, and a pale flame burns where its heart used to be.',
            concept='rusty skeleton knight', model=_m('ossiguard'), placeholder=False),
]
