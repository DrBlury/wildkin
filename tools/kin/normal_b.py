"""Kin 67-100. Owner: KIN-B (new common/uncommon kin 67-100).

Data here; the art (one model function per species) lives in
tools/kin/art_normal_b.py. Ids, names, types, rarity and growth follow
docs/EXPANSION.md 4.2.
"""

from kin import KinSpec
from kin import art_normal_b as art


def _kin(id, name, types, rarity, **kw):
    """KinSpec with the model looked up by name (art_normal_b.<name>)."""
    model = getattr(art, name.lower(), None)
    return KinSpec(id, name, types, rarity, model=model, placeholder=model is None, **kw)


SPECIES = [
    # ---- QUARTZLING line (66 is in normal_a) --------------------------------
    _kin(67, 'QUARTZPEDE', ('STONE', 'SWARM'), 'U', base=(70, 100, 120, 75, 70, 75), catch=45, xp=196, evo=None,
         category='CRYSTAL', height=16, weight=820,
         learnset=[(1, 'M_PINCER'), (1, 'M_GRIT_KICK'), (1, 'M_PEBBLE_PELT'), (1, 'M_SILK_SNARE'), (30, 'M_ROCKFALL'),
                   (34, 'M_STONESKIN'), (38, 'M_SWARM_RUSH'), (42, 'M_SANDBLAST'), (47, 'M_PRISM_RAY'), (52, 'M_FAULTLINE')],
         traits=('BEDROCK', 'GLOWER'), field=('LIGHT',),
         desc='A quartz crystal grows on every segment and stores light the way a kernel stores motes. In deep caves it glows '
              'end to end, and miners follow it home.',
         concept='crystal centipede'),
    # ---- flying squirrels ----------------------------------------------------
    _kin(68, 'FLYSQUIRL', ('GALE', 'BEAST'), 'C', base=(45, 52, 40, 42, 46, 85), catch=200, xp=56,
         evo=('LEVEL', 24, 'GALESQUIRL'), category='GLIDER', height=3, weight=12,
         learnset=[(1, 'M_SWIPE'), (1, 'M_POUT'), (5, 'M_DRAFT'), (9, 'M_DART'), (13, 'M_FEATHER_CUT'), (17, 'M_UPDRAFT'),
                   (21, 'M_CATNAP'), (26, 'M_CROSSWIND'), (31, 'M_STOOP')],
         traits=('DRIFTER', 'HOARDER'), field=(),
         desc='It glides from tree to tree on the breeze its kernel pumps from. It buries nuts in a hundred places and '
              'forgets most of them, which is how new woods grow.',
         concept='flying squirrel'),
    _kin(69, 'GALESQUIRL', ('GALE', 'BEAST'), 'U', base=(75, 95, 65, 70, 70, 120), catch=45, xp=178, evo=None,
         category='CAPE GLIDER', height=11, weight=240,
         learnset=[(1, 'M_SWIPE'), (1, 'M_DRAFT'), (1, 'M_DART'), (1, 'M_FEATHER_CUT'), (17, 'M_UPDRAFT'), (21, 'M_CATNAP'),
                   (24, 'M_SNARL'), (29, 'M_CROSSWIND'), (35, 'M_BELLY_FLOP'), (41, 'M_STOOP'), (48, 'M_RECKLESS_RUSH')],
         traits=('DRIFTER', 'MOMENTUM'), field=(),
         desc='It wraps its gliding membrane around itself like a cape. Unfurled, it catches enough wind to cross a whole '
              'valley without a single flap.',
         concept='big glider squirrel, cape-like membrane'),
    # ---- sloths -----------------------------------------------------------------
    _kin(70, 'DOZLOTH', ('DREAM', 'BEAST'), 'C', base=(70, 40, 55, 55, 60, 25), catch=190, xp=58,
         evo=('LEVEL', 32, 'SOMNISLOTH'), category='NAP SLOTH', height=5, weight=45,
         learnset=[(1, 'M_BONK'), (1, 'M_POUT'), (5, 'M_DAYDREAM'), (9, 'M_CATNAP'), (13, 'M_SWIPE'), (17, 'M_LULLABY'),
                   (21, 'M_PRISM_RAY'), (26, 'M_STILL_POND'), (29, 'M_BELLY_FLOP'), (35, 'M_DREAMQUAKE')],
         traits=('BASKER', 'THICK FUR'), field=(),
         desc='It naps upside down, clinging to a puff of dream it pumped from sleepers nearby. It sleeps twenty hours a '
              'day and still yawns.',
         concept='sloth that naps upside down'),
    _kin(71, 'SOMNISLOTH', ('DREAM', 'BEAST'), 'U', base=(105, 70, 90, 95, 100, 40), catch=45, xp=186, evo=None,
         category='MOSS SLOTH', height=15, weight=520,
         learnset=[(1, 'M_BONK'), (1, 'M_DAYDREAM'), (1, 'M_CATNAP'), (1, 'M_LULLABY'), (21, 'M_PRISM_RAY'),
                   (26, 'M_STILL_POND'), (32, 'M_SAP_SIP'), (36, 'M_DREAMQUAKE'), (42, 'M_BELLY_FLOP'),
                   (48, 'M_DROWSY_POLLEN'), (55, 'M_BRIM_BURST')],
         traits=('BASKER', 'THICK FUR'), field=('TELEPORT',),
         desc='Moss grows thick on its slow body. Its kernel drinks the minds around it and gives back drowsiness, so '
              'travelers who sit near it wake hours later, well rested.',
         concept='moss-draped sloth with a sleep aura'),
    # ---- mantises -----------------------------------------------------------------
    _kin(72, 'SCYTHLING', ('SWARM',), 'C', base=(40, 68, 40, 35, 40, 87), catch=190, xp=58,
         evo=('LEVEL', 30, 'REAPMANTIS'), category='SICKLE', height=4, weight=18,
         learnset=[(1, 'M_SWIPE'), (1, 'M_BRACE'), (5, 'M_PINCER'), (9, 'M_DART'), (13, 'M_COUNTERJAB'), (18, 'M_WINGDUST'),
                   (23, 'M_REED_BLADE'), (27, 'M_SWARM_RUSH'), (33, 'M_SHADE_CUT')],
         traits=('KEEN EYE', 'MOMENTUM'), field=(),
         desc='It sways like a leaf in the wind, then strikes with its little sickle arms. It sheds its skin five times '
              'before its wings grow in.',
         concept='mantis nymph'),
    _kin(73, 'REAPMANTIS', ('SWARM', 'HOLLOW'), 'U', base=(70, 120, 70, 55, 70, 115), catch=45, xp=190, evo=None,
         category='REAPER', height=17, weight=380,
         learnset=[(1, 'M_PINCER'), (1, 'M_DART'), (1, 'M_COUNTERJAB'), (1, 'M_BONE_RATTLE'), (30, 'M_OSSIFY'),
                   (34, 'M_SWARM_RUSH'), (38, 'M_SHADE_CUT'), (43, 'M_SHROUD'), (48, 'M_MARROW_SIP'), (54, 'M_DEATH_KNELL')],
         traits=('KEEN EYE', 'GLOWER'), field=(),
         desc='In the ash of the March its kernel stopped growing shell and began to grow bone. It stands so still that '
              'crows land on its scythes, and then it moves.',
         concept='reaper mantis with bone scythes'),
    # ---- iron beetles ----------------------------------------------------------------
    _kin(74, 'MAGNITICK', ('SWARM', 'METAL'), 'C', base=(45, 54, 70, 35, 50, 44), catch=190, xp=58,
         evo=('LEVEL', 28, 'LODEHORN'), category='IRON GRUB', height=3, weight=90,
         learnset=[(1, 'M_BONK'), (1, 'M_IRON_TAP'), (5, 'M_MAGNET_PULL'), (9, 'M_SILK_SNARE'), (13, 'M_PINCER'),
                   (17, 'M_RIVET_SHOT'), (21, 'M_STEEL_SHELL'), (25, 'M_SWARM_RUSH'), (31, 'M_GEAR_GRIND')],
         traits=('STUBBORN', 'CONDUCTOR'), field=(),
         desc='Its magnetite kernel pumps from the pull of the earth. It clings to fences, kettles and belt buckles, and '
              'must be peeled off very gently.',
         concept='iron beetle grub that sticks to metal'),
    _kin(75, 'LODEHORN', ('SWARM', 'METAL'), 'U', base=(85, 125, 120, 45, 70, 55), catch=45, xp=192, evo=None,
         category='LODESTONE', height=14, weight=1250,
         learnset=[(1, 'M_IRON_TAP'), (1, 'M_MAGNET_PULL'), (1, 'M_PINCER'), (1, 'M_RIVET_SHOT'), (28, 'M_GEAR_GRIND'),
                   (32, 'M_SWARM_RUSH'), (36, 'M_STEEL_SHELL'), (40, 'M_LODE_BEAM'), (45, 'M_RECKLESS_RUSH'),
                   (52, 'M_ANVIL_DROP')],
         traits=('STUBBORN', 'BRUISER'), field=('STRENGTH',),
         desc='Its horn is one great lodestone bristling with iron filings. Compasses spin when it charges, and it can '
              'drag a loaded cart by pulling on the axle.',
         concept='rhinoceros beetle with a lodestone horn'),
    # ---- bees -----------------------------------------------------------------------------
    _kin(76, 'HUMBEE', ('SWARM', 'BLOOM'), 'C', base=(42, 45, 40, 62, 48, 73), catch=200, xp=58,
         evo=('LEVEL', 26, 'COMBQUEEN'), category='GLOW BEE', height=3, weight=8,
         learnset=[(1, 'M_BONK'), (1, 'M_POUT'), (5, 'M_SAP_SIP'), (9, 'M_BARB'), (13, 'M_DROWSY_POLLEN'), (17, 'M_WINGDUST'),
                   (21, 'M_BASK'), (25, 'M_SWARM_RUSH'), (31, 'M_SUNSHAFT')],
         traits=('HOARDER', 'SELFMEND'), field=(),
         desc='A hive of HUMBEE flashes in perfect time, every kernel in step. Their glow honey refuels a tired kin, and '
              'farmers leave clover by the hives to say thanks.',
         concept='glow-bee'),
    _kin(77, 'COMBQUEEN', ('SWARM', 'BLOOM'), 'U', base=(80, 65, 85, 105, 100, 70), catch=45, xp=190, evo=None,
         category='HIVE QUEEN', height=15, weight=280,
         learnset=[(1, 'M_SAP_SIP'), (1, 'M_BARB'), (1, 'M_DROWSY_POLLEN'), (1, 'M_WINGDUST'), (26, 'M_THORN_WALL'),
                   (30, 'M_BASK'), (35, 'M_GLINT'), (40, 'M_SILK_SNARE'), (45, 'M_SUNSHAFT'), (51, 'M_GILDED_GLEAM')],
         traits=('HOARDER', 'FOCUSED'), field=('LIGHT',),
         desc='Her gown is a living honeycomb, every cell aglow with honey. When she hums, every hive in the meadow '
              'answers, and their lights pulse as one.',
         concept='hive queen in a honeycomb gown'),
    # ---- spiders ---------------------------------------------------------------------------
    _kin(78, 'WEBBIT', ('SWARM', 'VENOM'), 'C', base=(45, 50, 45, 55, 50, 65), catch=200, xp=58,
         evo=('LEVEL', 28, 'LACEWIDOW'), category='SPIDERLING', height=2, weight=6,
         learnset=[(1, 'M_BONK'), (1, 'M_SILK_SNARE'), (5, 'M_BARB'), (9, 'M_POUT'), (13, 'M_PINCER'), (17, 'M_SPORE_CLOUD'),
                   (21, 'M_ACID_SPIT'), (25, 'M_FESTER'), (30, 'M_BOG_BOMB')],
         traits=('SELFMEND', 'SLIPPERY'), field=(),
         desc='Its fuzz catches the faintest breeze, and on warm evenings it sails away on a silk thread. Its bite only '
              'tickles, but the itch lasts all day.',
         concept='fuzzy spiderling'),
    _kin(79, 'LACEWIDOW', ('SWARM', 'VENOM'), 'U', base=(70, 85, 70, 100, 85, 90), catch=45, xp=190, evo=None,
         category='LACE WEAVER', height=12, weight=230,
         learnset=[(1, 'M_SILK_SNARE'), (1, 'M_BARB'), (1, 'M_PINCER'), (1, 'M_ACID_SPIT'), (28, 'M_FESTER'),
                   (32, 'M_WINGDUST'), (36, 'M_HAUNT'), (41, 'M_BOG_BOMB'), (46, 'M_DEATH_KNELL'), (52, 'M_SWARM_RUSH')],
         traits=('SPORESKIN', 'KEEN EYE'), field=(),
         desc='It weaves its veil from silk so fine it passes for lace. It keeps to old graveyards, and mourners say its '
              'webs glitter like tears at dawn.',
         concept='spider in a lace veil'),
    # ---- bats ---------------------------------------------------------------------------------
    _kin(80, 'SQUEAKLE', ('DUSK', 'GALE'), 'C', base=(42, 45, 35, 58, 40, 88), catch=200, xp=56,
         evo=('LEVEL', 26, 'NOCTAVE'), category='BAT PUP', height=2, weight=5,
         learnset=[(1, 'M_BONK'), (1, 'M_POUT'), (4, 'M_DRAFT'), (8, 'M_SNAP'), (12, 'M_STARE_DOWN'), (16, 'M_UPDRAFT'),
                   (20, 'M_HAUNT'), (24, 'M_CROSSWIND'), (29, 'M_GLOOM_ORB')],
         traits=('WAKEFUL', 'DRIFTER'), field=(),
         desc='It squeaks too high for people to hear, and the echoes paint the dark for it. Whole caves of them squeak '
              'at once, so no two ever bump into each other.',
         concept='bat pup'),
    _kin(81, 'NOCTAVE', ('DUSK', 'GALE'), 'U', base=(70, 70, 65, 110, 75, 115), catch=45, xp=190, evo=None,
         category='SONAR BAT', height=11, weight=160,
         learnset=[(1, 'M_DRAFT'), (1, 'M_SNAP'), (1, 'M_STARE_DOWN'), (1, 'M_HAUNT'), (26, 'M_CROSSWIND'),
                   (30, 'M_GLOOM_ORB'), (35, 'M_UPDRAFT'), (40, 'M_DREAMQUAKE'), (46, 'M_SHADE_CUT'), (52, 'M_PRIMAL_ROAR')],
         traits=('WAKEFUL', 'KEEN EYE'), field=('FLY',),
         desc='Its ears ring like tuning forks. One pure note bounced off the cave walls shows it every stone; a second, '
              'a little off key, leaves foes too dizzy to stand.',
         concept='sonar bat with tuning-fork ears'),
    # ---- cats -------------------------------------------------------------------------------------
    _kin(82, 'NOXKIT', ('DUSK',), 'C', base=(45, 55, 40, 55, 50, 82), catch=190, xp=60,
         evo=('BOND', 0, 'UMBRAKAT'), category='NIGHT KIT', height=3, weight=30,
         learnset=[(1, 'M_SWIPE'), (1, 'M_STARE_DOWN'), (5, 'M_SNAP'), (9, 'M_DART'), (13, 'M_CATNAP'), (17, 'M_HAUNT'),
                   (21, 'M_SHADE_CUT'), (26, 'M_GNASH'), (31, 'M_GLOOM_ORB')],
         traits=('SLIPPERY', 'GLOWER'), field=(),
         desc='Its fur drinks even starlight, so at night only its eyes show. It follows wardens home, and it only grows '
              'for one it trusts completely.',
         concept='black kitten with glowing eyes'),
    _kin(83, 'UMBRAKAT', ('DUSK', 'BEAST'), 'U', base=(75, 110, 70, 85, 70, 115), catch=45, xp=196, evo=None,
         category='SHADOW CAT', height=13, weight=520,
         learnset=[(1, 'M_SWIPE'), (1, 'M_SNAP'), (1, 'M_STARE_DOWN'), (1, 'M_DART'), (22, 'M_SHADE_CUT'), (28, 'M_GNASH'),
                   (33, 'M_SNARL'), (38, 'M_HAUNT'), (44, 'M_GLOOM_ORB'), (50, 'M_RECKLESS_RUSH')],
         traits=('SLIPPERY', 'MOMENTUM'), field=(),
         desc='A broadband kernel darker than any shadow. It crosses the mire without a sound; the only warning is a pair '
              'of eyes that were not there a moment ago.',
         concept='shadow panther'),
    # ---- HOLLOW: skeletons and zombies ----------------------------------------------------------------
    _kin(84, 'CALCIPUP', ('HOLLOW',), 'C', base=(56, 64, 58, 35, 45, 62), catch=190, xp=58,
         evo=('LEVEL', 28, 'OSSIHOUND'), category='BONE PUP', height=4, weight=40,
         learnset=[(1, 'M_POUT'), (1, 'M_BONK'), (4, 'M_BONE_RATTLE'), (8, 'M_DART'), (12, 'M_GRAVE_CHILL'), (16, 'M_SHROUD'),
                   (21, 'M_CATNAP'), (25, 'M_MARROW_SIP'), (31, 'M_OSSIFY')],
         traits=('STUBBORN', 'SELFMEND'), field=(),
         desc='A kernel that outlived its body rebuilt it from old bone and grave dust. It rattles all over when it is '
              'happy, which is nearly always.',
         concept='skeletal puppy that rattles when happy'),
    _kin(85, 'OSSIHOUND', ('HOLLOW', 'BEAST'), 'U', base=(85, 115, 95, 55, 75, 90), catch=45, xp=194, evo=None,
         category='BONE HOUND', height=14, weight=360,
         learnset=[(1, 'M_BONE_RATTLE'), (1, 'M_DART'), (1, 'M_SHROUD'), (1, 'M_GRAVE_CHILL'), (28, 'M_OSSIFY'),
                   (32, 'M_SNARL'), (36, 'M_MARROW_SIP'), (40, 'M_SEAR_BITE'), (45, 'M_LAST_RITES'), (51, 'M_RECKLESS_RUSH')],
         traits=('STUBBORN', 'GLOWER'), field=('STRENGTH',),
         desc='It keeps watch over Gravewood and never sleeps. The embers in its eyes are the slow heat of old bone, '
              'pumped to a glow. It still loves to fetch.',
         concept='bone hound with ember eyes'),
    _kin(86, 'MUDDLE', ('HOLLOW', 'TIDE'), 'C', base=(70, 45, 55, 50, 55, 28), catch=190, xp=58,
         evo=('LEVEL', 30, 'BOGSHAMBLE'), category='BOG BLOB', height=5, weight=180,
         learnset=[(1, 'M_BONK'), (1, 'M_FIZZ'), (5, 'M_MUD_PIE'), (9, 'M_BONE_RATTLE'), (13, 'M_SHROUD'), (17, 'M_UNDERTOW'),
                   (21, 'M_GRAVE_CHILL'), (26, 'M_LAST_RITES'), (33, 'M_SWELL')],
         traits=('SOAKER', 'STUBBORN'), field=(),
         desc='Bog mud and grave dust piled up around a hollow kernel and a few stray bones. It is squishy, smells like '
              'a pond and badly wants a hug.',
         concept='bog-mud zombie blob'),
    _kin(87, 'BOGSHAMBLE', ('HOLLOW', 'BLOOM'), 'U', base=(115, 95, 95, 70, 90, 35), catch=45, xp=190, evo=None,
         category='PEAT HULK', height=18, weight=1100,
         learnset=[(1, 'M_MUD_PIE'), (1, 'M_BONE_RATTLE'), (1, 'M_SHROUD'), (1, 'M_SAP_SIP'), (30, 'M_SPORE_CLOUD'),
                   (34, 'M_OSSIFY'), (38, 'M_THORN_WALL'), (42, 'M_MARROW_SIP'), (47, 'M_BELLY_FLOP'), (53, 'M_REQUIEM')],
         traits=('SPORESKIN', 'STUBBORN'), field=(),
         desc='Peat and moss have piled on its bones for years, and mushrooms sprout from its shoulders. The mire grows '
              'greener wherever it shambles.',
         concept='shambling peat zombie with mushrooms'),
    _kin(88, 'DREGCROW', ('HOLLOW', 'GALE'), 'C', base=(45, 58, 42, 45, 45, 68), catch=190, xp=58,
         evo=('LEVEL', 27, 'CAWDAVER'), category='ASH CROW', height=4, weight=22,
         learnset=[(1, 'M_BEAK_JAB'), (1, 'M_POUT'), (5, 'M_BONE_RATTLE'), (9, 'M_DRAFT'), (13, 'M_STARE_DOWN'),
                   (17, 'M_SHROUD'), (21, 'M_GRAVE_CHILL'), (25, 'M_FEATHER_CUT'), (30, 'M_MARROW_SIP')],
         traits=('HOARDER', 'KEEN EYE'), field=(),
         desc='A scruffy crow held together with bone and grave dust. It collects lost buttons and teeth, and scolds any '
              'warden who does not share lunch.',
         concept='scraggly carrion crow'),
    _kin(89, 'CAWDAVER', ('HOLLOW', 'GALE'), 'U', base=(75, 95, 70, 90, 75, 100), catch=45, xp=192, evo=None,
         category='GRAVE CROW', height=15, weight=190,
         learnset=[(1, 'M_BEAK_JAB'), (1, 'M_BONE_RATTLE'), (1, 'M_DRAFT'), (1, 'M_SHROUD'), (27, 'M_CROSSWIND'),
                   (31, 'M_GRAVE_CHILL'), (35, 'M_OSSIFY'), (40, 'M_DEATH_KNELL'), (46, 'M_STOOP'), (52, 'M_REQUIEM')],
         traits=('HOARDER', 'GLOWER'), field=('FLY',),
         desc='Its wings are bare bone hung with a tattered cloak of feathers. When it circles the Ashen March, old '
              'kernels in the ash stir and start to rebuild.',
         concept='skeletal crow with a tattered cloak'),
    _kin(90, 'CRANICRAB', ('TIDE', 'HOLLOW'), 'C', base=(50, 60, 82, 35, 48, 28), catch=190, xp=58,
         evo=('LEVEL', 29, 'CRYPTCLAW'), category='SKULL CRAB', height=3, weight=60,
         learnset=[(1, 'M_BONK'), (1, 'M_BRACE'), (5, 'M_FIZZ'), (9, 'M_PINCER'), (13, 'M_BONE_RATTLE'), (17, 'M_SLIPSTREAM'),
                   (21, 'M_SHROUD'), (25, 'M_RIPTIDE'), (31, 'M_OSSIFY')],
         traits=('BEDROCK', 'SOAKER'), field=(),
         desc='It moves into skulls that wash up in the mire and peeks out through the eye holes. When it outgrows one, '
              'it leaves it on a doorstep as a gift.',
         concept='hermit crab living in a skull'),
    _kin(91, 'CRYPTCLAW', ('TIDE', 'HOLLOW'), 'U', base=(85, 115, 125, 55, 80, 40), catch=45, xp=190, evo=None,
         category='URN CRAB', height=12, weight=950,
         learnset=[(1, 'M_FIZZ'), (1, 'M_PINCER'), (1, 'M_BONE_RATTLE'), (1, 'M_SLIPSTREAM'), (29, 'M_RIPTIDE'),
                   (33, 'M_STONESKIN'), (37, 'M_OSSIFY'), (42, 'M_HAMMER_FIST'), (47, 'M_GEYSER'), (53, 'M_HEIRLOOM')],
         traits=('BEDROCK', 'STUBBORN'), field=(),
         desc='It carries an old crypt urn and lifts the lid only to peek out. Over the years the urn has grown into its '
              'shell, and nothing can pry it loose.',
         concept='hermit crab in a crypt urn'),
    # ---- RELIC: tsukumogami -------------------------------------------------------------------------------
    _kin(92, 'PARASOLE', ('RELIC', 'GALE'), 'C', base=(45, 48, 55, 58, 52, 62), catch=190, xp=58,
         evo=('LEVEL', 25, 'STORMBRELA'), category='UMBRELLA', height=6, weight=9,
         learnset=[(1, 'M_CLATTER'), (1, 'M_POUT'), (5, 'M_DRAFT'), (9, 'M_TARNISH'), (13, 'M_TRINKET_TOSS'),
                   (17, 'M_POLTERGUST'), (21, 'M_UPDRAFT'), (26, 'M_CROSSWIND'), (31, 'M_GILDED_GLEAM')],
         traits=('DRIFTER', 'SOAKER'), field=(),
         desc='A paper umbrella forgotten by a door for a hundred years. A kernel lost in its ribs grew one big eye. It '
              'hops along beside travelers to keep the rain off.',
         concept='one-eyed hopping umbrella (kasa-obake)'),
    _kin(93, 'STORMBRELA', ('RELIC', 'GALE'), 'U', base=(75, 80, 80, 110, 85, 90), catch=45, xp=194, evo=None,
         category='STORMSHADE', height=14, weight=40,
         learnset=[(1, 'M_CLATTER'), (1, 'M_DRAFT'), (1, 'M_POLTERGUST'), (1, 'M_TARNISH'), (25, 'M_ARC_FLASH'),
                   (29, 'M_CROSSWIND'), (34, 'M_UPDRAFT'), (39, 'M_CURSED_CURIO'), (45, 'M_FORKED_BOLT'),
                   (51, 'M_OVERCHARGE')],
         traits=('DRIFTER', 'STATIC FUR'), field=('FLY',),
         desc='A gale blew it inside out, and it decided it liked that better. Static builds on its spokes until they '
              'crackle, and it rides thunderheads like a kite.',
         concept='storm umbrella, spokes crackling'),
    _kin(94, 'KETTLEKIN', ('RELIC', 'TIDE'), 'C', base=(60, 40, 72, 62, 58, 26), catch=190, xp=58,
         evo=('LEVEL', 26, 'TANUKETTLE'), category='TEAPOT', height=3, weight=55,
         learnset=[(1, 'M_BONK'), (1, 'M_FIZZ'), (5, 'M_CLATTER'), (9, 'M_POUT'), (13, 'M_TARNISH'), (17, 'M_SLIPSTREAM'),
                   (21, 'M_TRINKET_TOSS'), (25, 'M_CATNAP'), (30, 'M_SWELL')],
         traits=('EMBERSKIN', 'SOAKER'), field=(),
         desc='A teapot that sat on a warm hearth for a century. The kernel in its glaze pumps from the warmth of hands, '
              'and it pours tea for guests, invited or not.',
         concept='teapot with a tail and paws'),
    _kin(95, 'TANUKETTLE', ('RELIC', 'BEAST'), 'U', base=(95, 85, 105, 85, 90, 50), catch=45, xp=192, evo=None,
         category='KETTLE', height=10, weight=640,
         learnset=[(1, 'M_CLATTER'), (1, 'M_FIZZ'), (1, 'M_TARNISH'), (1, 'M_SWIPE'), (26, 'M_CHEST_CHOMP'), (30, 'M_SWELL'),
                   (34, 'M_DAYDREAM'), (38, 'M_BELLY_FLOP'), (43, 'M_GILDED_GLEAM'), (49, 'M_CURSED_CURIO'),
                   (55, 'M_HEIRLOOM')],
         traits=('THICK FUR', 'HOARDER'), field=('SURF',),
         desc='A tanuki grew out of an old iron kettle and never quite got out. It floats down rivers on its round belly '
              'and drums on it to call its friends.',
         concept='tanuki-teapot (bunbuku chagama)'),
    _kin(96, 'STRAWSPECT', ('RELIC', 'BLOOM'), 'C', base=(75, 80, 75, 60, 75, 70), catch=120, xp=150, evo=None,
         category='SCARECROW', height=16, weight=85,
         learnset=[(1, 'M_CLATTER'), (1, 'M_STARE_DOWN'), (5, 'M_BRAMBLE_LASH'), (9, 'M_TARNISH'), (13, 'M_BURR_VOLLEY'),
                   (18, 'M_TRINKET_TOSS'), (23, 'M_REED_BLADE'), (28, 'M_POLTERGUST'), (33, 'M_THORN_WALL'),
                   (38, 'M_CURSED_CURIO'), (44, 'M_SUNSHAFT')],
         traits=('GLOWER', 'BASKER'), field=(),
         desc='It stood in the same field for a hundred summers until a kernel lost in its straw woke up. It still guards '
              'the crops, and the crows now bring it gifts.',
         concept='living scarecrow (a great farm worker)'),
    # ---- METAL -------------------------------------------------------------------------------------------------
    _kin(97, 'RIVETILLO', ('METAL', 'STONE'), 'C', base=(50, 62, 88, 30, 50, 35), catch=190, xp=60,
         evo=('LEVEL', 30, 'FORTADILLO'), category='ARMADILLO', height=4, weight=160,
         learnset=[(1, 'M_BONK'), (1, 'M_BRACE'), (5, 'M_IRON_TAP'), (9, 'M_GRIT_KICK'), (13, 'M_RIVET_SHOT'),
                   (17, 'M_PEBBLE_PELT'), (21, 'M_STEEL_SHELL'), (25, 'M_ROCKFALL'), (31, 'M_GEAR_GRIND')],
         traits=('BEDROCK', 'STUBBORN'), field=(),
         desc='It draws iron out of the soil and rivets it into plates. Rolled up it is a perfect ball, and it bounces '
              'off walls with a loud clang.',
         concept='armadillo with riveted plates'),
    _kin(98, 'FORTADILLO', ('METAL', 'STONE'), 'U', base=(90, 105, 145, 50, 75, 40), catch=45, xp=194, evo=None,
         category='FORTRESS', height=15, weight=2600,
         learnset=[(1, 'M_IRON_TAP'), (1, 'M_GRIT_KICK'), (1, 'M_RIVET_SHOT'), (1, 'M_STEEL_SHELL'), (30, 'M_ROCKFALL'),
                   (34, 'M_GEAR_GRIND'), (38, 'M_STONESKIN'), (42, 'M_FAULTLINE'), (48, 'M_LODE_BEAM'),
                   (54, 'M_ANVIL_DROP')],
         traits=('BEDROCK', 'STUBBORN'), field=('STRENGTH',),
         desc='Its shell has grown battlements. Small kin shelter on its back when storms roll in, and the first forts of '
              'Cindermoor were built to copy its shape.',
         concept='fortress armadillo'),
    _kin(99, 'SALAMBER', ('BLAZE',), 'C', base=(45, 50, 42, 65, 48, 70), catch=190, xp=60,
         evo=('LEVEL', 30, 'FOUNDRAKE'), category='EMBER NEWT', height=4, weight=26,
         learnset=[(1, 'M_BONK'), (1, 'M_POUT'), (4, 'M_CINDER_FLICK'), (8, 'M_DART'), (12, 'M_LANTERN_LURE'),
                   (16, 'M_SEAR_BITE'), (20, 'M_LAST_EMBER'), (25, 'M_EMBER_STORM'), (31, 'M_KILN_BREATH')],
         traits=('EMBERSKIN', 'SURGE'), field=('LIGHT',),
         desc='Its spots glow like coals when it is happy. It likes to sleep in hearths, so villagers bank the fire at '
              'night and leave it a little warm ash.',
         concept='ember salamander'),
    _kin(100, 'FOUNDRAKE', ('BLAZE', 'METAL'), 'U', base=(85, 110, 95, 100, 70, 60), catch=45, xp=198, evo=None,
         category='FOUNDRY', height=17, weight=2200,
         learnset=[(1, 'M_CINDER_FLICK'), (1, 'M_SEAR_BITE'), (1, 'M_IRON_TAP'), (1, 'M_LANTERN_LURE'),
                   (30, 'M_FORGE_FLASH'), (34, 'M_GEAR_GRIND'), (38, 'M_EMBER_STORM'), (43, 'M_KILN_BREATH'),
                   (48, 'M_ANVIL_DROP'), (54, 'M_SUNFLARE')],
         traits=('EMBERSKIN', 'BRUISER'), field=('LIGHT', 'STRENGTH'),
         desc='Its scales are ingots cast in its own belly furnace. Smiths in Cindermoor say a blade quenched in its '
              'breath will never rust.',
         concept='foundry drake with ingot scales'),
]
