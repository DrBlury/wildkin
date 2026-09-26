# WILDKIN expansion: design and contracts

This is the plan for WILDKIN's second big update: new kin, new types,
fusion, crafting, farming, new regions, gyms (Halls), traversal and QoL. It
is also the contract every contributor follows: names, ids and file
ownership are fixed here. `docs/WORLD.md` stays the lore bible; this file
adds what is new.

---

## 1. Goals

- **174 kin**: the 32 we have, plus 69 new common/uncommon kin (100 in
  total), 20 rare, 9 more legendaries (10 in total) and 44 fusion kin.
- **4 new types** (18 in total): HOLLOW, RELIC, METAL, ASTRAL.
- **Energy and fusion**: unbind kin into typed energy, mix energies, and
  weave them on the Fusion Loom for a chance at a fusion kin.
- **Crafting with minigames**: cooking, brewing, forging and energy tuning.
- **Farming**: buy a plot, till, plant, water, fertilise, harvest, sell,
  cook. Kin can work the farm (automation). Wild berry patches on routes.
- **A bigger world**: six Hall towns with themed puzzle Halls, caves with
  darkness, the grim Ashen March, the coast with boats and an island,
  snowy mountains, a volcano, a dream town, and a lair for every legend.
- **Traversal**: bike, surf, fly, teleport, light, strength; seamless map
  edges; location banners; day and night.
- **Quality**: an asset viewer, automated art lints, and tests for every
  system. Every new feature ships with QoL.

---

## 2. Types

Four new pump bands (see WORLD.md section 2 for how types work):

| # | Type | Pump band (in-world science) | Kin |
| --- | --- | --- | --- |
| 14 | HOLLOW | A kernel that outlived its body can only pump from the slow radiogenic heat of old bone and stone. It precipitates a new body from what is at hand: bone (apatite), grave dust, peat. | skeletons, zombies, wraiths, mummies |
| 15 | RELIC | A kernel lost in a well-used object for a century seeds its body *from* the object. It pumps from the hum and warmth of handling (vibration and body heat). | mimics, tsukumogami: umbrellas, teapots, lanterns, armour, dolls, books |
| 16 | METAL | Magnetite kernels, like real magnetotactic bacteria, pump from magnetic fields and induced currents, and grow iron armour. | iron beetles, armadillos, clockwork, foundry drakes |
| 17 | ASTRAL | Kernels that pump from cosmic-ray muons, which pass through anything. The flux is tiny, so ASTRAL kin are rare, slow-growing and huge. | star moths, meteor beasts, moon hares, star whales |

### Type chart (attacker rows, defender columns)

`+` strikes a weak spot (x2), `-` shrugged off (x0.5), `0` no effect.

```
          Be Bl Ti Bo Sp Fr Br Ve St Ga Dr Sw Du Wy Ho Re Me As
BEAST     .  .  .  .  .  .  .  .  -  .  .  .  0  .  -  .  -  .
BLAZE     .  -  -  +  .  +  .  .  -  .  .  +  +  -  +  +  +  -
TIDE      .  +  -  -  .  .  .  .  +  .  .  .  .  -  .  .  +  .
BLOOM     .  -  +  -  .  .  .  -  +  -  .  -  .  -  -  .  -  .
SPARK     .  .  +  -  -  .  .  .  0  +  .  .  .  -  .  .  .  .
FROST     .  -  -  +  .  -  .  .  +  +  .  .  .  +  .  .  -  .
BRAWL     +  .  .  .  .  +  .  -  +  -  -  -  +  .  -  +  +  -
VENOM     .  .  +  +  .  .  .  -  -  .  .  .  -  .  0  -  0  .
STONE     .  +  .  -  +  +  .  +  .  .  .  -  .  .  .  .  -  .
GALE      .  .  .  +  -  .  +  .  -  .  .  +  .  .  .  .  -  -
DREAM     .  .  .  .  .  .  +  +  .  .  -  .  -  .  -  -  -  .
SWARM     .  -  .  +  .  .  -  -  .  -  +  .  +  .  +  +  -  .
DUSK      0  +  .  .  .  .  -  .  .  .  +  .  +  .  .  .  .  +
WYRM      .  .  .  .  .  .  .  .  .  .  .  .  .  +  .  .  -  .
HOLLOW    .  -  .  +  .  .  .  .  .  .  +  .  -  .  .  -  -  -
RELIC     .  -  .  .  .  .  .  .  -  .  +  .  .  .  +  .  -  .
METAL     .  -  -  .  -  +  .  .  +  .  .  .  .  .  .  .  -  +
ASTRAL    .  -  .  .  .  .  .  .  .  .  .  .  +  +  +  .  -  -
```

The existing 14x14 block is unchanged. The new columns and rows follow the
physics and the folklore:

- Heat cremates the HOLLOW, burns RELIC paper and wood, and forges METAL.
- Water rusts METAL.
- Carrion beetles clean bones, and woodworm eats old objects: SWARM beats
  HOLLOW and RELIC.
- Talismans ward off the dead: RELIC beats HOLLOW.
- Starlight scours decay and swallows the dark: ASTRAL beats HOLLOW, DUSK
  and WYRM.
- A magnetic field bends cosmic rays: METAL beats ASTRAL.
- Poison can't touch the dead or iron.

---

## 3. Rarity

`Species.rarity`: `R_COMMON`, `R_UNCOMMON`, `R_RARE`, `R_LEGEND`, `R_FUSION`.

- Common and uncommon kin roam wild zones.
- Rare kin appear at 1-4% weight, at night, in special spots, or as
  mimic chests.
- Each legend is a single static encounter in its lair.
- Fusion kin come only from the Fusion Loom.

The Almanac shows rarity as a coloured gem: grey, green, blue, gold, and a
purple spiral for fusion.

---

## 4. The roster (ids are fixed)

`Lv` = grows at that level; `SH:X` = grows when it touches an X SHARD;
`BD` = grows on a level-up with bond 220 or more. Field abilities: S surf,
F fly, T teleport, L light, P strength (push). Region codes are in
section 9.

### 4.1 Existing (0-31), unchanged ids

| id | name | types | grows | notes |
| --- | --- | --- | --- | --- |
| 0 | FLARIX | BLAZE | Lv16 | starter, L |
| 1 | PYREFOX | BLAZE | Lv34 | L |
| 2 | INFERNOX | BLAZE/DUSK | - | L |
| 3 | AQUAPO | TIDE | Lv16 | starter |
| 4 | AXOLURK | TIDE | Lv34 | S |
| 5 | TIDALOTL | TIDE/WYRM | - | S |
| 6 | DANDELAMB | BLOOM | Lv16 | starter |
| 7 | PUFFLEECE | BLOOM | Lv34 | |
| 8 | ZEPHRAM | BLOOM/GALE | - | F |
| 9 | CINDERUB | BLAZE | Lv30 | L |
| 10 | MAGMAUL | BLAZE/STONE | - | P, L |
| 11 | BUBBLIN | TIDE | SH:FROST | |
| 12 | GLACIBLOB | TIDE/FROST | - | S |
| 13 | THORNIP | BLOOM | SH:BLOOM | |
| 14 | BRAMBLOR | BLOOM/VENOM | - | |
| 15 | MOSSHELL | BLOOM | Lv30 | |
| 16 | TERRASHELL | BLOOM/STONE | - | P |
| 17 | ZAPPET | SPARK/GALE | Lv28 | L |
| 18 | STORMHAWK | SPARK/GALE | - | F, L |
| 19 | VOLTUX | SPARK | SH:SPARK | L |
| 20 | VOLTLOPE | SPARK/BRAWL | - | P, L |
| 21 | GOLEMIT | STONE | Lv30 | |
| 22 | BOULDRON | STONE/BRAWL | - | P |
| 23 | PUFFOWL | GALE | Lv24 | |
| 24 | HOOTLORD | GALE/DREAM | - | F, T |
| 25 | SKYWISP | SWARM/GALE | SH:DUSK | |
| 26 | LUMOTH | SWARM/DREAM | - | T, L |
| 27 | NIBBIT | BEAST | Lv25 | |
| 28 | GNAWLORD | BEAST/DUSK | - | P |
| 29 | FROSTOAT | FROST | - | |
| 30 | WISPIRE | DUSK | - | L, T |
| 31 | DRAKORA | WYRM/GALE | - | legend (Stormstone Rise), F |

### 4.2 New common / uncommon (32-100)

| id | name | types | rar | grows | concept | where |
| --- | --- | --- | --- | --- | --- | --- |
| 32 | PRICKLET | BEAST | C | Lv20 | hedgehog kit that rolls into a burr | MEADOW, WOOD |
| 33 | QUILLDRUM | BEAST/BRAWL | U | - | hedgehog that drums its quills as a warning; P | WOOD, E1 |
| 34 | SNUFFLET | BEAST | C | Lv22 | truffle piglet with a leaf on its snout | WOOD, FARM |
| 35 | TRUFFLOAR | BEAST/BLOOM | U | - | boar with a mossy garden on its back; digs up buried items; P | E1, ELDER |
| 36 | RACCOIN | BEAST/DUSK | C | Lv24 | masked raccoon hoarding shiny coins | VILLAGE night, E1 |
| 37 | BANDIRACC | BEAST/DUSK | U | - | bandit raccoon with a bandana and a coin sack | LUMEN outskirts |
| 38 | PEBBOTTER | TIDE | C | Lv24 | otter juggling river stones | LAKE, W1 |
| 39 | TORRENTTER | TIDE/BRAWL | U | - | river otter with a stone club; S, P | W1, SEA |
| 40 | JELLUME | TIDE/SPARK | C | Lv26 | jellyfish whose bell glows like a lamp; L | SEA |
| 41 | MEDUSHOCK | TIDE/SPARK | U | - | tall jellyfish whose tendrils arc; L, S | SEA |
| 42 | LURELING | TIDE/DUSK | U | Lv30 | anglerfish fry; its lure is a tiny kernel; L | SEA night, CAVE lake |
| 43 | ABYSSLURE | TIDE/DUSK | U | - | deep anglerfish, lure like a lantern; L, S | SEA night |
| 44 | RADISHOO | BLOOM | C | Lv22 | radish sprite with a leafy tuft | FARM, MEADOW |
| 45 | MANDRAGOR | BLOOM/DREAM | U | - | mandrake whose scream is a lullaby; T | E1, DREAM |
| 46 | PUMPKLING | BLOOM | C | Lv28 | pumpkin sprout with a carved grin | FARM, ASH |
| 47 | JACKOGRIM | BLOOM/HOLLOW | U | - | vine-bodied jack-o'-lantern with a lantern head; L | ASH night |
| 48 | SHROOMLET | BLOOM/VENOM | C | Lv30 | mushroom-cap tot that puffs spores | WOOD, GRAVE |
| 49 | MYCOLOSSUS | BLOOM/VENOM | U | - | walking giant fungus; P | GRAVE, ELDER |
| 50 | BLINKET | SWARM/SPARK | C | Lv22 | firefly with a blinking tail; L | WOOD night, CAVE |
| 51 | BEACONFLY | SWARM/SPARK | U | - | big firefly with a lantern abdomen; L | E1 night |
| 52 | STATICKO | SPARK | C | Lv25 | gecko that sticks to walls with static | E1, LUMEN |
| 53 | FULGECKO | SPARK/BEAST | U | - | frilled lightning lizard; L | E1, VOLC |
| 54 | FLURRABBIT | FROST | C | SH:ASTRAL | snow hare | SNOW |
| 55 | MOONHARE | FROST/ASTRAL | U | - | moon rabbit with a mochi mallet; T | SNOW night |
| 56 | TUXFLAKE | FROST/TIDE | C | Lv30 | penguin chick in a snow puff | SNOW, W1 cold |
| 57 | EMPERICE | FROST/TIDE | U | - | emperor penguin with an ice crown; S | SNOW |
| 58 | YAKLING | FROST/BEAST | C | Lv32 | shaggy yak calf | SNOW |
| 59 | GLACIYAK | FROST/BEAST | U | - | glacier yak with icicle horns; P | SNOW |
| 60 | RAMBLET | BRAWL | C | Lv26 | lamb that headbutts everything | RISE, SNOW |
| 61 | CRAGHORN | BRAWL/STONE | U | - | mountain ram with rock-hard horns; P | SNOW, PEAK |
| 62 | STINGLET | VENOM | C | Lv27 | scorpling | VOLC |
| 63 | SCORCHION | VENOM/BLAZE | U | - | ember-tailed scorpion; L | VOLC |
| 64 | DIGGET | STONE | C | SH:HOLLOW | mole with a tiny lantern | CAVE, ASH |
| 65 | SEXTONE | STONE/HOLLOW | U | - | gravedigger mole with a spade and a lantern; P | GRAVE |
| 66 | QUARTZLING | STONE/SWARM | U | Lv30 | crystal grub | CAVE |
| 67 | QUARTZPEDE | STONE/SWARM | U | - | crystal centipede; L | CAVE |
| 68 | FLYSQUIRL | GALE/BEAST | C | Lv24 | flying squirrel | WOOD, E1 |
| 69 | GALESQUIRL | GALE/BEAST | U | - | big glider squirrel, cape-like membrane | ELDER |
| 70 | DOZLOTH | DREAM/BEAST | C | Lv32 | sloth that naps upside down | WOOD, DREAM |
| 71 | SOMNISLOTH | DREAM/BEAST | U | - | moss-draped sloth with a sleep aura; T | DREAM |
| 72 | SCYTHLING | SWARM | C | Lv30 | mantis nymph | MEADOW, ASH |
| 73 | REAPMANTIS | SWARM/HOLLOW | U | - | reaper mantis with bone scythes | ASH, GRAVE |
| 74 | MAGNITICK | SWARM/METAL | C | Lv28 | iron beetle grub that sticks to metal | E1, VOLC |
| 75 | LODEHORN | SWARM/METAL | U | - | rhinoceros beetle with a lodestone horn; P | VOLC |
| 76 | HUMBEE | SWARM/BLOOM | C | Lv26 | glow-bee | MEADOW, FARM |
| 77 | COMBQUEEN | SWARM/BLOOM | U | - | hive queen in a honeycomb gown; L | ELDER |
| 78 | WEBBIT | SWARM/VENOM | C | Lv28 | fuzzy spiderling | WOOD, GRAVE |
| 79 | LACEWIDOW | SWARM/VENOM | U | - | spider in a lace veil | GRAVE night |
| 80 | SQUEAKLE | DUSK/GALE | C | Lv26 | bat pup | CAVE |
| 81 | NOCTAVE | DUSK/GALE | U | - | sonar bat with tuning-fork ears; F | CAVE, GRAVE |
| 82 | NOXKIT | DUSK | C | BD | black kitten with glowing eyes | VILLAGE night, MIRE |
| 83 | UMBRAKAT | DUSK/BEAST | U | - | shadow panther | MIRE night |
| 84 | CALCIPUP | HOLLOW | C | Lv28 | skeletal puppy that rattles when happy | ASH |
| 85 | OSSIHOUND | HOLLOW/BEAST | U | - | bone hound with ember eyes; P | GRAVE |
| 86 | MUDDLE | HOLLOW/TIDE | C | Lv30 | bog-mud zombie blob | MIRE |
| 87 | BOGSHAMBLE | HOLLOW/BLOOM | U | - | shambling peat zombie with mushrooms | MIRE |
| 88 | DREGCROW | HOLLOW/GALE | C | Lv27 | scraggly carrion crow | ASH |
| 89 | CAWDAVER | HOLLOW/GALE | U | - | skeletal crow with a tattered cloak; F | ASH, GRAVE |
| 90 | CRANICRAB | TIDE/HOLLOW | C | Lv29 | hermit crab living in a skull | W1 beach, MIRE |
| 91 | CRYPTCLAW | TIDE/HOLLOW | U | - | hermit crab in a crypt urn | ISLE, OSSUARY |
| 92 | PARASOLE | RELIC/GALE | C | Lv25 | one-eyed hopping umbrella (kasa-obake) | W1 rain, LUMEN |
| 93 | STORMBRELA | RELIC/GALE | U | - | storm umbrella, spokes crackling; F | COAST |
| 94 | KETTLEKIN | RELIC/TIDE | C | Lv26 | teapot with a tail and paws | VILLAGE, LUMEN |
| 95 | TANUKETTLE | RELIC/BEAST | U | - | tanuki-teapot (bunbuku chagama); S | DREAM |
| 96 | STRAWSPECT | RELIC/BLOOM | C | - | living scarecrow (a great farm worker) | FARM, ASH |
| 97 | RIVETILLO | METAL/STONE | C | Lv30 | armadillo with riveted plates | VOLC, E1 |
| 98 | FORTADILLO | METAL/STONE | U | - | fortress armadillo; P | VOLC |
| 99 | SALAMBER | BLAZE | C | Lv30 | ember salamander; L | VOLC |
| 100 | FOUNDRAKE | BLAZE/METAL | U | - | foundry drake with ingot scales; L, P | VOLC |

### 4.3 Rare (101-120)

| id | name | types | grows | concept | where |
| --- | --- | --- | --- | --- | --- |
| 101 | KOIRIN | TIDE | Lv35 | koi that climbs waterfalls | LAKE 2%, W1 river |
| 102 | RYUKOI | TIDE/WYRM | - | the koi became a dragon; S, F | - |
| 103 | TRINKIT | RELIC | SH:RELIC | a jewellery box with teeth (mimic) | mimic chests, OSSUARY |
| 104 | HOARDMAW | RELIC/BEAST | - | a treasure-chest mimic on legs | - |
| 105 | RATTLEBONE | HOLLOW | SH:METAL | skeleton squire with a pot helmet | OSSUARY |
| 106 | OSSIGUARD | HOLLOW/METAL | - | skeleton knight; P | - |
| 107 | GAUNTLING | RELIC/METAL | Lv36 | a gauntlet that walks on its fingers | SPIRE |
| 108 | HOLLOWHELM | RELIC/METAL | - | an empty suit of armour; P | - |
| 109 | WICKLET | RELIC/BLAZE | Lv32 | a candle wick sprite; L | MIRE night |
| 110 | LAMPGHAST | RELIC/BLAZE | - | paper lantern ghost (chochin-obake); L | - |
| 111 | METEORB | ASTRAL/STONE | Lv38 | a meteorite with stubby legs | RISE night 3%, STARFALL |
| 112 | BOLIDON | ASTRAL/STONE | - | fireball meteor beast; P, L | - |
| 113 | KELPYRE | TIDE/DUSK | - | kelpie water horse; S | LAKE night 1%, SEA |
| 114 | TENGALE | GALE/BRAWL | - | tengu, long nose and a feather fan; F | PEAK |
| 115 | SLUMBAKU | DREAM/BEAST | - | baku dream-eater tapir; T | DREAM night |
| 116 | WENDIGAUNT | FROST/HOLLOW | - | wendigo, antlered and gaunt | PEAK night |
| 117 | LAMPJINN | RELIC/GALE | - | a genie rising from an oil lamp; T | ISLE, LIBRARY |
| 118 | GARGOLITH | STONE/DUSK | - | gargoyle; F | LUMEN rooftops, SPIRE |
| 119 | HOPSHI | HOLLOW/BRAWL | - | hopping vampire (jiangshi) | GRAVE night |
| 120 | QILUMEN | ASTRAL/SPARK | - | kirin with a star-lit mane; T, L | STARFALL, DREAM |

### 4.4 Legendary (121-129, plus DRAKORA 31)

| id | name | types | lair (map) | concept |
| --- | --- | --- | --- | --- |
| 121 | CALDERON | BLAZE/METAL | CALDERA HEART | colossal forge salamander |
| 122 | NOCTHALE | TIDE/ASTRAL | DROWNED BELL | star whale that sings under the sea |
| 123 | HOARFANG | FROST/DUSK | WHITECROWN PEAK | the winter wolf |
| 124 | OSSUREX | HOLLOW/WYRM | BONE THRONE | bone dragon of the Ossuary |
| 125 | SELENOTH | ASTRAL/DREAM | STARFALL GROTTO | moon moth |
| 126 | SYLVARCH | BLOOM/BEAST | ELDERWOOD HEART | great forest stag |
| 127 | HOROLOGOS | METAL/RELIC | CLOCKWORK SPIRE | clockwork titan |
| 128 | SCRIPTORA | RELIC/DREAM | DUST LIBRARY | serpent of living pages |
| 129 | SKYLORN | GALE/ASTRAL | SKY ISLE | sky manta above the clouds |

### 4.5 Fusion (130-173)

Fusion kin never appear in the wild. Each has a **signature**: the two
energy types that can weave it on the Fusion Loom.

| id | name | types | signature | concept |
| --- | --- | --- | --- | --- |
| 130 | STEAMOTH | GALE/BLAZE | BLAZE+TIDE | moth of steam with brass wings |
| 131 | VOLTORTLE | SPARK/STONE | SPARK+STONE | tortoise with a lightning-rod shell |
| 132 | EMBERIME | BLAZE/FROST | BLAZE+FROST | fox with one fire tail and one ice tail |
| 133 | OSSIFLORA | HOLLOW/BLOOM | HOLLOW+BLOOM | skeletal deer overgrown with flowers |
| 134 | COGHIVE | METAL/SWARM | METAL+SWARM | clockwork bee hive queen |
| 135 | HOARDWYRM | RELIC/WYRM | RELIC+WYRM | a dragon made of a treasure hoard |
| 136 | STARSQUID | ASTRAL/TIDE | ASTRAL+TIDE | squid with nebula ink |
| 137 | VOLTSHARK | TIDE/SPARK | TIDE+SPARK | shark with a dynamo fin |
| 138 | DULLAHAN | HOLLOW/BEAST | HOLLOW+BEAST | headless horse carrying its lantern-head |
| 139 | CHIMERAX | BEAST/VENOM | BEAST+VENOM | lion, goat and serpent in one |
| 140 | RIDDLEON | DREAM/STONE | DREAM+STONE | sphinx that asks riddles |
| 141 | GRIFFALON | GALE/BEAST | GALE+BEAST | griffin |
| 142 | MANTICLAW | VENOM/BRAWL | VENOM+BRAWL | manticore |
| 143 | INKRAKEN | TIDE/DUSK | TIDE+DUSK | young kraken of ink and dark |
| 144 | OBSIDRAKE | STONE/WYRM | STONE+WYRM | obsidian drake |
| 145 | AURORELK | FROST/ASTRAL | FROST+ASTRAL | elk with aurora antlers |
| 146 | RAIJUKO | SPARK/BEAST | SPARK+BEAST | raiju, the thunder beast |
| 147 | SPOREGHOUL | VENOM/HOLLOW | VENOM+HOLLOW | ghoul sprouting mushrooms |
| 148 | CLOCKOWL | METAL/DREAM | METAL+DREAM | owl with a clock-face chest |
| 149 | CINDERANT | BLAZE/SWARM | BLAZE+SWARM | fire ant colony in one armour |
| 150 | STARWEAVER | ASTRAL/SWARM | ASTRAL+SWARM | spider weaving constellations |
| 151 | NOSFERBAT | DUSK/HOLLOW | DUSK+HOLLOW | vampire bat noble |
| 152 | BARKOLEM | BLOOM/STONE | BLOOM+STONE | stump golem with a birdhouse |
| 153 | PORCELYNX | RELIC/FROST | RELIC+FROST | porcelain lynx with frost glaze |
| 154 | KABUTORAI | METAL/BRAWL | METAL+BRAWL | samurai beetle |
| 155 | DROWNJELLY | TIDE/HOLLOW | TIDE+HOLLOW | drowned jellyfish lantern |
| 156 | SUNMANE | BLOOM/BLAZE | BLOOM+BLAZE | lion with a sunflower mane |
| 157 | DREAMKITE | DREAM/GALE | DREAM+GALE | kite-shaped dream spirit |
| 158 | BOGNEWT | VENOM/TIDE | VENOM+TIDE | toxic bog newt |
| 159 | RIMEGOLEM | FROST/STONE | FROST+STONE | ice golem |
| 160 | DYNAMOLE | METAL/SPARK | METAL+SPARK | mole with a dynamo |
| 161 | LULLABOX | RELIC/DREAM | RELIC+DREAM | music box that sings lullabies |
| 162 | KITSUFLAME | BLAZE/DREAM | BLAZE+DREAM | nine-tailed fox of foxfire |
| 163 | WYVERNIX | GALE/WYRM | GALE+WYRM | wyvern |
| 164 | TRIHYDRA | VENOM/WYRM | VENOM+WYRM | three-headed hydra |
| 165 | PHOENEX | BLAZE/ASTRAL | BLAZE+ASTRAL | phoenix of starfire |
| 166 | IRONHOWL | METAL/BEAST | METAL+BEAST | armoured wolf |
| 167 | NIMBWHALE | GALE/TIDE | GALE+TIDE | cloud whale |
| 168 | JOLLYROGUE | HOLLOW/RELIC | HOLLOW+RELIC | skeleton pirate with a ship in a bottle |
| 169 | RUNELITH | RELIC/STONE | RELIC+STONE | walking rune stone |
| 170 | FAEFLY | DREAM/SWARM | DREAM+SWARM | fairy dragonfly |
| 171 | SNOWBRUTE | FROST/BRAWL | FROST+BRAWL | yeti brawler |
| 172 | TESLAROSE | BLOOM/SPARK | BLOOM+SPARK | rose that sparks |
| 173 | NOCTMARE | DUSK/DREAM | DUSK+DREAM | the nightmare horse |

**Rules for kin art and data**:

- Names are at most 10 characters.
- Every design is original. Draw on real animals, folklore and objects;
  never copy an existing franchise creature.
- A line's forms read as one family.
- Base stat totals by tier:

  | tier | base stat total |
  | --- | --- |
  | first stage | 280-340 |
  | middle stage | 380-430 |
  | final stage | 470-530 |
  | single-stage common or uncommon | 400-480 |
  | rare | 480-540 |
  | fusion | 490-560 |
  | legend | 570-620 |

---

## 5. Moves

The 74 existing moves stay. New moves (ids appended before `M_LAST_GASP`;
names are at most 12 characters):

| move | type | cat | pow | acc | uses | effect |
| --- | --- | --- | --- | --- | --- | --- |
| BONE RATTLE | HOLLOW | phys | 40 | 100 | 30 | 10% flinch |
| GRAVE CHILL | HOLLOW | spec | 55 | 100 | 25 | 20% lower SPEED |
| MARROW SIP | HOLLOW | spec | 60 | 100 | 15 | drain |
| SHROUD | HOLLOW | status | - | - | 20 | +1 DEF, +1 WILL |
| OSSIFY | HOLLOW | phys | 80 | 100 | 15 | 30% lower DEF |
| DEATH KNELL | HOLLOW | spec | 90 | 90 | 10 | 20% sleep |
| REQUIEM | HOLLOW | spec | 110 | 85 | 5 | - |
| LAST RITES | HOLLOW | status | - | - | 10 | heal half |
| CLATTER | RELIC | phys | 40 | 100 | 35 | - |
| TRINKET TOSS | RELIC | phys | 18 | 95 | 20 | hits 2-5 |
| TARNISH | RELIC | status | - | 100 | 30 | -1 foe ATK |
| GILDED GLEAM | RELIC | spec | 70 | 100 | 15 | high crit |
| CHEST CHOMP | RELIC | phys | 80 | 95 | 15 | 20% flinch |
| POLTERGUST | RELIC | spec | 65 | 100 | 20 | 10% numb |
| CURSED CURIO | RELIC | spec | 95 | 90 | 10 | double vs status |
| HEIRLOOM | RELIC | phys | 120 | 100 | 5 | user -1 DEF, -1 WILL |
| IRON TAP | METAL | phys | 40 | 100 | 30 | priority +1 |
| MAGNET PULL | METAL | status | - | 100 | 20 | -2 foe SPEED |
| RIVET SHOT | METAL | phys | 20 | 95 | 20 | hits 2-5 |
| STEEL SHELL | METAL | status | - | - | 15 | +2 DEF |
| GEAR GRIND | METAL | phys | 80 | 95 | 15 | high crit |
| LODE BEAM | METAL | spec | 90 | 100 | 10 | 10% lower WILL |
| ANVIL DROP | METAL | phys | 110 | 85 | 5 | - |
| FORGE FLASH | METAL | spec | 60 | 100 | 20 | 10% burn |
| TWINKLE | ASTRAL | spec | 40 | 100 | 30 | - |
| STARDUST | ASTRAL | status | - | 90 | 20 | -1 foe ACC |
| MOONBEAM | ASTRAL | spec | 65 | 100 | 15 | drain |
| COMET DASH | ASTRAL | phys | 80 | 100 | 15 | recoil |
| NEBULA VEIL | ASTRAL | status | - | - | 15 | +1 FOCUS, +1 WILL |
| MUON RAIN | ASTRAL | spec | 90 | 100 | 10 | 10% lower DEF |
| METEOR FALL | ASTRAL | phys | 100 | 90 | 10 | 20% flinch |
| SUPERNOVA | ASTRAL | spec | 130 | 90 | 5 | user -2 FOCUS |
| SNARL | BEAST | spec | 55 | 95 | 15 | -1 foe FOCUS |
| EMBER STORM | BLAZE | spec | 75 | 95 | 15 | 20% burn |
| RIPTIDE | TIDE | phys | 75 | 100 | 15 | - |
| THORN WALL | BLOOM | status | - | - | 15 | +1 DEF, +1 WILL |
| ARC FLASH | SPARK | spec | 70 | 100 | 15 | 20% numb |
| SNOWDRIFT | FROST | status | - | 90 | 20 | -1 foe SPEED, -1 foe ACC |
| COUNTERJAB | BRAWL | phys | 60 | 100 | 20 | priority +1 |
| ACID SPIT | VENOM | spec | 60 | 100 | 20 | 30% lower WILL |
| SANDBLAST | STONE | spec | 70 | 95 | 15 | -1 foe ACC 20% |
| CROSSWIND | GALE | spec | 75 | 100 | 15 | high crit |
| LULLABY | DREAM | status | - | 60 | 15 | sleep |
| SWARM RUSH | SWARM | phys | 75 | 100 | 15 | - |
| SHADE CUT | DUSK | phys | 70 | 100 | 15 | high crit |
| WYRM DANCE | WYRM | status | - | - | 15 | +1 ATK, +1 SPEED |
| RUNE BOLT | ASTRAL | spec | 50 | 100 | 25 | - |
| SIGIL SNARE | RELIC | status | - | 95 | 20 | -2 foe SPEED |
| ALGIZ WARD | RELIC | status | - | - | 15 | +1 DEF, +1 WILL |
| KENAZ FLARE | BLAZE | spec | 80 | 100 | 15 | 10% burn |
| RUNE ORBIT | ASTRAL | spec | 110 | 85 | 5 | - |
| THURS SPIKE | STONE | phys | 85 | 95 | 10 | high crit |
| RAIDO RUSH | RELIC | phys | 70 | 100 | 15 | user +1 SPEED |
| ISA SEAL | FROST | spec | 70 | 100 | 15 | 10% freeze |
| SOWILO BEAM | RELIC | spec | 90 | 100 | 10 | 10% burn |
| RUNE SIPHON | ASTRAL | spec | 75 | 100 | 10 | drain |

The last ten are the RUNE set: runes of the elder row, drawn in the
RUNESTONE's arcane style (src/game/anim_rune.c, art from
tools/gen_rune_gfx.py). Each has its own pseudo-3D animation: runes on
inclined orbits with depth (bright and in front of the kin, dim behind),
circles lying on the ground or standing across the path as gates, runes
turning on their axis and scaling with distance between the two kin.

---

## 6. Items

There are 7 bag pockets: SUPPLIES, LANTERNS, SHARDS, FOOD, FARM, MATERIALS
and KEY. Items 0-16 keep their ids. Everything is listed in
`src/game/items/*.inc`; each owner edits only their own file.

- **SUPPLIES** (core, battle/UI owner): the existing ones, plus:
  - VIGOR DRAUGHT, CLARITY BREW, REVIVAL BREW (brewed potions)
  - SWIFT COIL, FOCUS COIL, WILL COIL (battle boosts)
  - LURE INCENSE (rare kin more likely for 200 steps)
  - WAYSTONE (warps to the last Hearth Hall)
- **LANTERNS** (craft owner): the existing ones, plus DUSK LANTERN, TIDE
  LANTERN, HEAVY LANTERN, QUICK LANTERN and BONE LANTERN.
- **SHARDS** (kin owner): the existing ones, plus HOLLOW SHARD, RELIC
  SHARD, METAL SHARD and ASTRAL SHARD.
- **FOOD** (craft owner):
  - dishes: BERRY TART, HONEY BUN, VEGGIE STEW, CHILI POT, PUMPKIN PIE,
    MOONCAKE, TRUFFLE RICE, CAMP SKEWER, SUN SALAD, KERNEL CANDY
  - drinks: BERRY JUICE, APPLE PRESS, PEACH NECTAR
- **FARM** (farm owner):
  - seeds: GLOWBERRY, EMBERBERRY, TIDEBERRY, RADISH, CARROT, POTATO,
    PUMPKIN, CHILI, TOMATO, CORN, SUNFLOWER, MOTEBLOOM
  - saplings: APPLE, PEACH
  - fertilisers: FERTILIZER, RICH COMPOST, GROW MULCH
  - crops: one for each seed and sapling
  - other: SPRINKLER
- **MATERIALS** (craft/fusion owners): MOTE DUST, GLOW HONEY, HEARTGLASS
  SAND, IRON ORE, COAL, BONE MEAL, SILK THREAD, SALT, MINT LEAF, GLOWCAP,
  STARDUST CHIP, OLD COIN
- **KEY** (UI owner; granted by systems): BIKE, WATERING CAN, HOE, FARM
  DEED, FERRY PASS, TOWN MAP, CREST CASE, RECIPE BOOK, ENERGY FLASK

---

## 7. Systems

### 7.1 Time and day (farm owner)

- Game time runs at one minute per real second in the field, menus
  paused. A day is 24 minutes of play.
- Night runs 20:00-05:59. Outdoor palettes tint toward blue at dusk, night
  and dawn.
- Sleeping in any bed skips to 06:00 the next day. The day rolls over by
  itself too; nothing ever forces the player home.
- Some wild slots are day-only or night-only (`WildSlot.when`).
- The clock shows on the START menu, plus an optional HUD clock.

### 7.2 Farming (farm owner)

**The plot.** WILLOW ACRE lies south of Maple Village. It is fenced off
until you buy the FARM DEED from REEVE at the LAND OFFICE (15,000c, or
10,000c after her quest). The deed comes with a farmhouse (bed, kitchen,
storage chest, work board), the HOE, the WATERING CAN and 8 seeds.

**Working the land.**

- **Soil**: cells with `A_SOIL` can be tilled and planted. Crops grow over
  days; wild berry patches on routes grow the same way.
- **The farm ring**: on the farm, L/R cycle HOE / CAN / seed / fertiliser,
  and A uses the one selected. Each action has an animation and a sound.
- **Watering**: the can holds 20 uses; refill it at any water.
- **Growth**: rain waters everything. Fertiliser speeds growth or raises
  quality. Crops have stages and some regrow; fruit trees take longer but
  keep giving.
- **Selling**: put produce in the SHIPPING BIN and you are paid the next
  morning. "Ship all produce" is a QoL option.

**Kin workers.** The WORK BOARD assigns up to 4 kin from the Shelf. Each
job suits certain types, and jobs run at the start of each day:

| job | suited types | what it does |
| --- | --- | --- |
| WATER | TIDE | waters crops |
| TEND | BLOOM | speeds growth |
| HARVEST | BEAST, BRAWL | brings in ripe crops |
| GUARD | RELIC scarecrows, DUSK | keeps crows off |
| FORAGE | any | brings back materials |
| HONEY | SWARM | fills the beehives |

Workers walk around the farm as overworld sprites and gain bond and XP.

**Processors** (preserves jar, press, drier) turn crops into goods over time.

### 7.3 Crafting (craft owner)

Four interactive minigames, each with its own screen, animation and sound.
The result quality (OK / GREAT / PERFECT) scales the yield or strength.

| minigame | where | how it plays |
| --- | --- | --- |
| **Cooking** | a kitchen: home, farmhouse, inns | Toss the pan: A on the heat-gauge sweet spot, three times. Then stir by rolling the D-pad in circles. |
| **Brewing** | a cauldron: Duskmere apothecary, farmhouse upgrade | Hold A to heat and release to cool, keeping the needle in a moving band. Then A at the bubble peak to bottle. |
| **Forging** | an anvil: Cindermoor forge | A on the beat as marks reach the anvil: lanterns, a sprinkler, can upgrades. |
| **Energy tuning** | the Resonance Works mixer | Match two waveforms: LEFT/RIGHT sets frequency, UP/DOWN sets amplitude. |

**Recipes** live in the RECIPE BOOK. They are learned from NPCs, books and
lore, and the book lists the ingredients you are missing.

**Dishes** grant a *meal buff* for the next few bouts (ATK+, WILL+, XP+,
catch+, lure). **Potions** are SUPPLIES usable in bouts.

### 7.4 Energy and fusion (fusion owner)

Everything happens at the RESONANCE WORKS in Lumen City.

**Energy.** There are 18 typed energy pools (`u16`, capped at 9999).

**Unbinding** a kin from the Shelf converts it into energy of its types:

- Amount: `8 + level / 2`, times x1.5 for rare, x4 for legend and x2 for
  lustrous.
- Dual types split 60/40.
- Fusion kin return their signature types.
- The kin goes back to its home wild. Say so in text, and animate it:
  motes flow into the flask.
- Confirm twice for legends and lustrous kin.

**Mixing.** Two energies become a third, following a fixed recipe table
(for example BLAZE + TIDE → GALE, "steam"). The tuning minigame sets the
yield from 60% to 120%.

**The Fusion Loom** is the gamble:

- Pick up to 3 energy types and a stake per weave (10, 30 or 60 units).
- The candidates are the fusions whose signature types are all among the
  picked types.
- Chance per weave: `base 6% + stake bonus + harmony bonus + pity`.
  - Harmony means the picked amounts are balanced.
  - Pity adds 3% per miss and guarantees a fusion at 25 misses.
- The chance and the candidate list are always shown on screen.
- A hit picks a candidate weighted toward ones not yet owned. The new kin
  precipitates in a big animation and joins the team or the Shelf.
- A miss gives MOTE DUST and a 30% energy refund.
- The reels, the ring spin and the spark shower all animate.

### 7.5 Traversal and field objects (traversal owner)

**Field abilities** need a CREST and a kin in the team with the matching
species flag (and, for SURF, FLY and STRENGTH, level 20+ / 30+ / 20+ and
size AVERAGE or bigger):

| ability | crest | what it does |
| --- | --- | --- |
| LIGHT | VOLT CREST (Lumen) | widens the light radius in dark maps |
| SURF | TIDE CREST (Port Brine) | cross `A_WATER`, with its own wild kin on water |
| STRENGTH | ANVIL CREST (Cindermoor) | push boulders |
| FLY | RIME CREST (Frosthollow) | fly to visited towns (map screen) and the SKY ISLE |
| TELEPORT | DREAM CREST (Dreamspire) | back to the last Hearth Hall |

**No HM slots**: abilities are used by facing the obstacle and pressing A,
or from a FIELD menu on START.

**Getting around:**

- **BIKE** (key item, registered to R): twice the walking speed. It can't
  be used indoors.
- **Boats**: a harbour master rents a boat (500c) or, after a quest, gives
  a FERRY PASS. The ride is a short sailing cutscene.
- **Dark maps** (`MF_DARK`): the player sees a light circle. Outside it
  the screen is dimmed, not black. LIGHT widens the radius.

**Puzzle tiles:**

- ice: `A_ICE`, you slide until blocked.
- currents and wind: `A_CURRENT` plus a direction, pushing you along.
- teleport pads (`OBJ_PAD`).
- floor switches and barriers (`OBJ_SWITCH` / `OBJ_BARRIER`).
- boulders and pressure plates (`OBJ_BOULDER` / `OBJ_PLATE` / `OBJ_GATE`).

**Transitions:**

- **Seamless edges**: walking over an edge between maps with the same
  tileset needs no fade; the neighbour map is drawn beyond the edge.
  Tileset changes use a quick 8-frame dip.
- **Location banners** slide in on entering a named area.

**Map objects** (`MapObj`, per map):

- BOULDER, PLATE, GATE, SWITCH, BARRIER, PAD
- BERRY (a wild berry patch)
- FERRY (a harbour spot)
- LEGEND (a static legend encounter)
- CHEST (may be a mimic)
- LADDER

### 7.6 UI and QoL (UI owner)

- **Bag**: seven pockets, sorting, a register for key items (SELECT or R),
  and item descriptions with icons.
- **Shelf**: 8 boxes of 30. Deposit, withdraw, move, release, and sort by
  number, level, type or rarity. A search mode, and a "sort into boxes by
  type" option.
- **Almanac**: 174 entries with filters (seen, owned, type, rarity,
  region). Fusion entries show their signature once discovered.
- **Town map**: shows where you are and the visited towns, and doubles as
  the FLY destination picker.
- **Quest log** for NPC quests. **Crest case** for the Hall crests.
- **Options**: HUD clock, bike auto-run, text speed, battle speed (x2
  anims), autosave.

---

## 8. Halls (gyms)

Each Hall has a Master and 3-5 wardens. Beat the Master for a crest.

| town | Hall | type | puzzle | crest |
| --- | --- | --- | --- | --- |
| LUMEN CITY | VOLT HALL | SPARK | Floor switches toggle crackling barriers; find the sequence. | VOLT (LIGHT) |
| PORT BRINE | CURRENT HALL | TIDE | Water currents push you; choose which current to ride. | TIDE (SURF) |
| CINDERMOOR | ANVIL HALL | METAL/BLAZE | Push boulders onto plates to open the gates. | ANVIL (STRENGTH) |
| FROSTHOLLOW | RIME HALL | FROST | Slide across ice until you hit a rock. | RIME (FLY) |
| DUSKMERE | LANTERN CRYPT | HOLLOW | A dark maze; only a small light circle, with hidden walls. | LANTERN (opens the OSSUARY) |
| DREAMSPIRE | MIRROR HALL | DREAM | Teleport pads that swap between mirrored rooms. | DREAM (TELEPORT) |

---

## 9. World map

```
                        [SKY ISLE] (FLY)
          [WHITECROWN PEAK]
               |
         FROSTHOLLOW ---- GLIMMER CAVERNS -- [STARFALL GROTTO]
               |
         FROSTPINE PASS                       DREAMSPIRE -- [DUST LIBRARY]
               |                                   |
        STORMSTONE RISE                      MOONVEIL PATH
               |                                   |
         WHISPER MEADOW                        LUMEN CITY ---- CINDER ROAD ---- CINDERMOOR -- EMBER TUNNEL -- [CALDERA HEART]
               |                               /   |                             |
 PORT BRINE - SALTWIND - MIRROR LAKE - MAPLE - BRAMBLEWOOD - COPPERLINE ROAD     [CLOCKWORK SPIRE]
    |                        VILLAGE     |       |
 SEA ROUTE                     |    [ELDERWOOD   ASHEN FIELDS - GRAVEWOOD - DUSKMERE - THE OSSUARY - [BONE THRONE]
    |                    WILLOW ACRE    HEART]
 GULL ISLE - [DROWNED BELL]    (farm)
```

Region codes used in the roster: VILLAGE, MEADOW, WOOD, LAKE, RISE (the
existing areas); FARM (Willow Acre); E1 (Copperline Road); LUMEN; W1
(Saltwind Trail); COAST (Port Brine); SEA (Sea Route); ISLE (Gull Isle);
SNOW (Frostpine Pass); PEAK (Whitecrown); CAVE (Glimmer Caverns); STARFALL;
ASH (Ashen Fields); GRAVE (Gravewood); MIRE (Duskmere surroundings);
OSSUARY; VOLC (Cinder Road, Ember Tunnel); SPIRE; DREAM (Moonveil Path,
Dreamspire); LIBRARY; ELDER (Elderwood Heart).

### Region ownership (world owners)

| owner | maps | tilesets owned |
| --- | --- | --- |
| **W-EAST** | COPPERLINE ROAD, LUMEN CITY (+ interiors: hearth hall, market, VOLT HALL, RESONANCE WORKS, bike shop, 2 houses), CLOCKWORK SPIRE (+ lair), ELDERWOOD HEART (from Bramblewood); the Land Office building in Maple Village | `city` |
| **W-WEST** | SALTWIND TRAIL, PORT BRINE (+ interiors, CURRENT HALL, harbour office, inn), SEA ROUTE, GULL ISLE (+ interiors), DROWNED BELL | `coast` |
| **W-NORTH** | FROSTPINE PASS, FROSTHOLLOW (+ interiors, RIME HALL, hot spring), GLIMMER CAVERNS (2 floors), STARFALL GROTTO, WHITECROWN PEAK, SKY ISLE | `snow`, `cave` |
| **W-GRIM** | ASHEN FIELDS, GRAVEWOOD, DUSKMERE (+ interiors, apothecary, LANTERN CRYPT), THE OSSUARY (2 floors), BONE THRONE | `grim`, `crypt` |
| **W-FAR** | CINDER ROAD, CINDERMOOR (+ interiors, forge, ANVIL HALL), EMBER TUNNEL, CALDERA HEART, MOONVEIL PATH, DREAMSPIRE (+ interiors, MIRROR HALL), DUST LIBRARY | `volcanic`, `dream` |
| **FARM** | WILLOW ACRE, FARMHOUSE, wild berry patches placed by the world owners | `farm` |

**Edge contracts.** An edge link needs both sides to agree on the opening:

- Offsets are 0 unless stated.
- The walkable gap of the exit must be at the same x (for N/S edges) or
  the same y (for E/W edges) on both maps.
- For existing maps (owned by the core):
  - Maple Village's south edge opens at x 19-20 into WILLOW ACRE.
  - Bramblewood's east edge opens at y 17-18 into COPPERLINE ROAD.
  - Mirror Lake's west edge opens at y 31-32 into SALTWIND TRAIL.
  - Stormstone Rise's north edge opens at x 11-12 into FROSTPINE PASS.
  - Bramblewood's south edge opens at x 30-31 into the ELDERWOOD HEART
    path. It is blocked by a STRENGTH boulder.
- Between regions:
  - COPPERLINE ROAD's south edge links to ASHEN FIELDS' north edge at
    x 20-21.
  - LUMEN CITY's east edge links to CINDER ROAD at y 20-21.
  - LUMEN CITY's north edge links to MOONVEIL PATH at x 24-25.

Each region owner documents their other exits in their region header.

---

## 10. Technical contracts

### 10.1 Tilesets

- **Registry.** Tilesets live in `tools/tilesets/` (one module each). The
  order in `tools/tilesets/__init__.py` fixes the `TS_*` ids:
  town, wild, interior, city, coast, snow, cave, grim, crypt, volcanic,
  dream, farm, debug.
- **What a module provides:** `build()` returns banks, terrain names and
  images, per-terrain attributes, the map-character legend, stamps
  (buildings) with door cells, animations, the out-of-bounds terrain and
  the backdrop colour.
- **Overlay terrain** (trees, pines, cacti, dead trees): the art is
  transparent around the object. The engine draws the ground under it
  (inferred from the nearest non-overlay neighbour) on BG0, the overlay
  bottom on BG2 and the overlay top on BG3. **Never bake ground into an
  object** — the art lint fails the build.
- **Budget:** tileset tiles plus the decor kinds a map uses must be at
  most 512 per map (checked by `make test`). Each tileset has 8 palette
  banks of 15 colours.
- **Decor:** each owner keeps a catalogue module (`tools/decor_<owner>.py`)
  registered in `gen_field_gfx.all_decor()`. `Decor(..., examine="text")`
  gives it an examine line automatically.

### 10.2 Maps

- **Where they live:** `src/game/world/<region>/`. Each region has:
  - `data.h` — rows, stamps, decor, objects and wild slots
  - `ids.inc` — `MAP_*` ids
  - `maps.inc` — `[MAP_X] = { ... }` entries
  - `warps.inc`, `npcs.inc`, `signs.inc`, `satchels.inc`
  - `trainer_ids.inc` / `trainers.inc`
  - `zone_ids.inc` / `zones.inc`
  - `flag_ids.inc` — story flags
  - `scripts.c` / `script_ids.inc` / `script_table.inc`
  - `lore_ids.inc` / `lore.inc` / `lsrc_ids.inc`
- **Size:** maps may be up to 64x64 cells.
- **Elevation** (optional): a height layer with derived cliff faces,
  stairs, ledges, bridges walked over and under, tunnels and hidden
  passages — `ELEV(rows, features)` in `maps.inc`; see docs/ELEVATION.md.
- **Visible characters:** at most 7 distinct NPC characters on screen per
  map, and at most 24 NPCs per map (tested).
- **Attributes (`u16`):**

  | bit | attribute |
  | --- | --- |
  | 1 | SOLID |
  | 2 | GRASS (kin roam) |
  | 4 | DOOR |
  | 8 | WATER (surfable) |
  | 16 | COUNTER |
  | 32 | EXIT |
  | 64 | SIGN |
  | 128 | LEDGE |
  | 256 | ICE |
  | 512 | SOIL |
  | 1024 | CURRENT |
  | 2048 | DIR_LO |
  | 4096 | DIR_HI |
  | 8192 | PAD |
  | 16384 | SWITCH |
  | 32768 | DEEP (no surf) |

- **Map flags (`u16`):**

  | bit | flag |
  | --- | --- |
  | 1 | OUTDOOR |
  | 2 | HEAL |
  | 4 | DARK |
  | 8 | NOFLY |
  | 16 | TOWN (fly point) |
  | 32 | ASH (ash-fall particles, grim tint) |
  | 64 | SNOW (snowfall) |
  | 128 | RAIN (always) |
  | 256 | NIGHTLESS (interiors) |
  | 512 | DEBUG |

### 10.3 OBJ VRAM in the field (tiles)

| tiles | use |
| --- | --- |
| 0-7 | player |
| 8-199 | 24 NPC slots |
| 200-219 | emotes |
| 220-223 | satchel |
| 224-255 | misc |
| 256-511 | traversal: mounts, boulders, particles, banners |
| 512-639 | farm and crafting overlays |
| 640-767 | free |
| 768-1023 | overworld kin (16 x 16) |

OBJ palettes: 0 player, 1-7 NPC characters, 8 satchel and misc, 9-14 kin,
15 emotes.

In a bout:

| tiles | use |
| --- | --- |
| 0-215 | RUNE move art (src/gfx_rune.h), loaded when a RUNE move starts |
| 256-383 | the two kin (64 x 64) |
| 384-399 | lantern capsule |
| 400-679 | move particles (16 x 16) |
| 680-745 | big particles, lantern marks |
| 746-1023 | free |

OBJ palettes in a bout: 2-6 RUNE moves (element at three depths, arcane
full and dim), 9 capsule, 10-11 kin, 12-14 particles, 15 lantern light.

### 10.4 Save (version 4)

- Two slots of up to 16 KB each, at SRAM offsets 0 and 16384, each
  checksummed and verified.
- The party holds 6 full `Monster`s.
- The Shelf holds 240 `BoxMon`s: 20 bytes each, healed, with PP restored
  on deposit.
- Bag counts, story, satchel and warden flag bit arrays, the Almanac
  bits, lore, options, and the module states: time, farm, craft, fusion,
  travel, quest.
- Each module provides `X_reset()` and `X_validate()`, which clamps bad
  data instead of failing the load.
- Version 3 saves are migrated.

### 10.5 Tests

`make test` must stay green. Every owner adds tests for their system:

- rules
- screens that open and close
- saves that round-trip
- maps that are reachable, including with abilities and puzzle solutions
- art lints

---

## 11. Story beyond the storm

After DRAKORA is answered, the Keeper finds that old kernels are waking in
the **Ashen March**. A century ago, OSSUREX brimmed there and scorched the
land, and the ash is full of hollow kernels rebuilding bodies from bone.

The Keeper asks you to earn the six crests: the Wardens' Accord only lets
crest-holders into the Ossuary. Along the way:

- Lumen's **Resonance Works** shows how energy can be *woven* (fusion).
- **Reeve** sells you land, so you can feed your team from your own farm.
- Each town has a legend story.

The finale is the **Bone Throne**: answer OSSUREX, and the Ashen March
begins to heal (it gets a clear-weather version, like the storm).
