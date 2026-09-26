/*
 * Lorebook content: chapters, entries, and who reveals each entry in the world.
 *
 * Every entry is revealed by one source (a person, a sign or a bookshelf;
 * script.c does the wiring). Pages about how the world works end with two
 * notes: REAL SCIENCE (true in our world too, can be looked up) and VALE
 * ONLY (the game's own invention, built to obey the same rules). The
 * science and the world follow docs/WORLD.md; matchups follow TYPE_CHART in
 * data.h.
 *
 * Text rules: ASCII only, never { | } ~ (they are UI glyphs). Pages use
 * "\n\n" between paragraphs and are word-wrapped by the Lorebook panel.
 * Talk uses "\f" between pages (<= ~150 characters each, < 400 in total).
 */

enum { LCH_FIRST_STEPS, LCH_KINSHIP, LCH_BIOLOGY, LCH_LANTERNS, LCH_TYPES,
       LCH_GROWTH, LCH_WEATHER, LCH_LEGENDS, LCH_PLACES, LORE_CHAPTER_COUNT };

static const char *const LORE_CHAPTER_NAMES[LORE_CHAPTER_COUNT] = {
    "FIRST STEPS", "THE KINSHIP", "HOW KIN WORK", "LANTERNS", "TYPES",
    "GROWTH", "WEATHER", "LEGENDS", "PLACES",
};

/* Who reveals an entry. script.c wires each source to an NPC, sign or bookshelf.
 * Entries with the same source are revealed one per conversation, in table order. */
enum { LSRC_START, LSRC_STORY, LSRC_KEEPER, LSRC_AIDE, LSRC_TENDER, LSRC_MARLO,
       LSRC_BAKER, LSRC_GARDENER, LSRC_ELDER, LSRC_GRAN, LSRC_CLERK, LSRC_KID,
       LSRC_SHEPHERD, LSRC_KITEFLYER, LSRC_STORMSTONE, LSRC_WOODWARD, LSRC_FORAGER,
       LSRC_HERMIT, LSRC_FISHER, LSRC_RESEARCHER, LSRC_LAKEKID, LSRC_BOOK_HOME,
       LSRC_BOOK_ALMANAC, LSRC_BOOK_STATION, LSRC_BOOK_CABIN, LSRC_COUNT };

/* One id per entry, grouped by chapter. The LSRC_STORY entries are unlocked
 * by script.c at these moments:
 *   LORE_KINDLING         after choosing a first kin at the Almanac House
 *   LORE_RING_SASH        after beating Warden Marlo (RING SASH)
 *   LORE_CLEAR_SKIES      after DRAKORA is calmed (won or befriended)
 *   LORE_BOUT_RING        the first time you talk to Warden Marlo
 *   LORE_STORMSTONE_RISE  on first reaching the top of Stormstone Rise */
enum {
    /* FIRST STEPS */
    LORE_CONTROLS, LORE_LOREBOOK, LORE_BOUTS, LORE_BEFRIENDING,
    LORE_TYPE_CHART, LORE_STATUS, LORE_SHELF, LORE_CODE, LORE_TEMPERAMENT,
    LORE_POTENTIAL, LORE_LUSTRE, LORE_BOND, LORE_SUPPLIES, LORE_HUSH_BELL,
    /* THE KINSHIP */
    LORE_KINSHIP, LORE_KINDLING, LORE_RING_SASH, LORE_ANSWER_BRIM,
    LORE_PARENTS, LORE_OPEN_DOOR, LORE_PRIMER,
    /* HOW KIN WORK */
    LORE_KERNEL, LORE_PUMPING, LORE_DOZING, LORE_TONICS, LORE_FOXFIRE,
    LORE_POLARITONS, LORE_BOSONS, LORE_CONDENSATES, LORE_SUPERSOLIDS,
    /* LANTERNS */
    LORE_HEARTGLASS, LORE_KIN_CHOOSE, LORE_SHEDDING, LORE_NO_COPIES,
    LORE_TWIN_CRYSTALS, LORE_Q_FACTOR, LORE_DECOHERENCE, LORE_QUANTUM_MEMORY,
    LORE_SPEED_LIMIT,
    /* TYPES */
    LORE_PUMP_BANDS, LORE_TYPE_BLAZE_BEAST, LORE_TYPE_TIDE_SPARK,
    LORE_TYPE_BLOOM_STONE, LORE_TYPE_GALE_SWARM, LORE_TYPE_FROST,
    LORE_TYPE_VENOM, LORE_TYPE_DREAM_BRAWL, LORE_TYPE_DUSK, LORE_TYPE_WYRM,
    /* GROWTH */
    LORE_GROWING, LORE_SHARDS, LORE_SUPERCOOLED, LORE_GROWTH_PAPER,
    /* WEATHER */
    LORE_RAIN, LORE_LIGHTNING, LORE_PRESSURE, LORE_STORM_SIGNS,
    LORE_CLEAR_SKIES,
    /* LEGENDS */
    LORE_BURNING_YEARS, LORE_DROWNED_VALLEYS, LORE_DRAKORA, LORE_FIRST_OATH,
    LORE_SKIES_GRUMBLE, LORE_MARSH_LIGHTS, LORE_RIVER_DRAKE, LORE_STORM_RHYME,
    LORE_LAST_ANSWER,
    /* PLACES */
    LORE_MAPLE_VILLAGE, LORE_HEARTHS, LORE_BOUT_RING, LORE_STORMSTONE_RISE,
    LORE_ALMANAC, LORE_WHISPER_MEADOW, LORE_BRAMBLEWOOD, LORE_MIRROR_LAKE,
    LORE_COUNT
};

typedef struct {
    u8 chapter, source;
    const char *title;   /* <= 18 characters, UPPERCASE */
    const char *text;    /* the Lorebook page */
    const char *talk;    /* what the source says in the world when it reveals this entry; 0 for LSRC_START / LSRC_STORY */
} LoreEntry;

static const LoreEntry LORE[LORE_COUNT] = {

    /* ============================================================ */
    /*  FIRST STEPS                                                 */
    /* ============================================================ */

    [LORE_CONTROLS] = { LCH_FIRST_STEPS, LSRC_START, "CONTROLS",
        "Walk with the D-Pad. Hold B while you walk to run.\n\n"
        "A talks to people, reads signs, opens satchels and confirms a choice. "
        "B goes back. Hold A or B while text is showing to speed it up.\n\n"
        "START opens the menu: your TEAM, your BAG, the ALMANAC of every kin you "
        "have met, this LOREBOOK, the options and SAVE. Once you carry a TWIN "
        "CRYSTAL, the LANTERN SHELF opens from there too.\n\n"
        "In a bout, FIGHT picks a move, BAG uses an item, TEAM sends in another "
        "kin and RUN leaves a wild bout. Press L to throw your best lantern "
        "straight away.\n\n"
        "In the options you can change the text speed, turn bout animations and "
        "sound on or off, and choose whether your lead kin walks along behind you.",
        0 },

    [LORE_LOREBOOK] = { LCH_FIRST_STEPS, LSRC_START, "YOUR LOREBOOK",
        "This book keeps everything you learn about kin and the Vale, sorted into "
        "chapters. People all over the Vale know things worth hearing, so talk to "
        "everyone, and more than once: many of them have more to tell. "
        "Bookshelves are worth a look too.\n\n"
        "Many pages end with two notes.\n\n"
        "REAL SCIENCE marks things that are true in our own world as well. "
        "Scientists have measured them, and you can look them up.\n\n"
        "VALE ONLY marks the Vale's own wonders: living crystals, lanterns, the "
        "kin themselves. They are made up, but they are built to obey the same "
        "rules as the real science around them. See if you can spot where one "
        "ends and the other begins!",
        0 },

    [LORE_BOUTS] = { LCH_FIRST_STEPS, LSRC_START, "BOUTS",
        "A bout is a friendly clash between two kin. Each blow is one kin's field "
        "striking the other's and knocking some of its motes loose. HP shows how "
        "much of a kin's field is still holding together.\n\n"
        "Physical moves pit ATTACK against DEFENSE. Other moves are aimed with "
        "FOCUS and resisted with WILL. Every move has a limited number of uses; "
        "a rest at a Hearth Hall refills them.\n\n"
        "A move that strikes a weak spot does double damage. One that is shrugged "
        "off does half. The move menu shows how each move will land on the kin "
        "in front of you. Now and then a kin lands a perfect strike for extra "
        "damage.\n\n"
        "At 0 HP a kin dozes off. It isn't hurt, only out of energy.\n\n"
        "Every kin that took part in a bout earns XP, and kin on the bench earn "
        "half. Befriending a kin earns XP too. With enough XP, a kin gains a level.",
        0 },

    [LORE_BEFRIENDING] = { LCH_FIRST_STEPS, LSRC_START, "BEFRIENDING",
        "Wild kin can't be forced into a lantern. They choose. A lantern only "
        "holds a kin that is calm enough to settle inside, and a lively kin will "
        "simply shake it off.\n\n"
        "So have a bout first. A tired kin with little HP left is much calmer. A "
        "kin that is asleep or frozen is calmest of all, twice as easy to "
        "befriend. Any other status problem helps a little too.\n\n"
        "Then throw a lantern from your BAG, or press L to throw your best one. "
        "If the kin breaks free, it wasn't ready. Keep trying!\n\n"
        "Better lanterns help: a PRISM LANTERN works half again as well as a "
        "plain LANTERN, and a STAR LANTERN twice as well. Some kin, especially "
        "big old ones, are very choosy.\n\n"
        "In a wild bout, a lantern mark beside a kin's name means you have "
        "already befriended one of its kind.",
        0 },

    [LORE_TYPE_CHART] = { LCH_FIRST_STEPS, LSRC_KEEPER, "THE TYPE CHART",
        "Every kin soaks up one kind of energy: its type. When types clash, they "
        "follow the same rules as the rest of the world.\n\n"
        "TIDE quenches BLAZE and wears down STONE. BLAZE melts FROST, withers "
        "BLOOM, scatters SWARM and banishes DUSK. SPARK races through TIDE and "
        "splits GALE, but can't touch STONE at all: the ground swallows it. "
        "STONE smothers BLAZE, grounds SPARK, cracks FROST and buries VENOM. "
        "BLOOM drinks TIDE and its roots crack STONE. FROST chills BLOOM, GALE, "
        "STONE and even WYRM. VENOM fouls TIDE and BLOOM. GALE strips BLOOM, "
        "blows away SWARM and throws BRAWL. BRAWL breaks BEAST, FROST, STONE and "
        "DUSK. DREAM outwits BRAWL and VENOM. SWARM feeds on BLOOM, DREAM and "
        "DUSK. DUSK bites back at BLAZE and DREAM. BEAST and DUSK can't touch "
        "each other.\n\n"
        "Many types shrug off their own kind, but DUSK and WYRM strike their own "
        "kind hard.\n\n"
        "You needn't learn it all by heart: the move menu shows how each move "
        "will land. The TYPES chapter explains why each rule holds.",
        "Types can seem like a lot to remember when you're new. But they aren't "
        "arbitrary, you know.\f"
        "Each rule is just the world being itself: water puts out fire, the "
        "ground swallows a spark. Here, let me write them out for you." },

    [LORE_STATUS] = { LCH_FIRST_STEPS, LSRC_TENDER, "STATUS PROBLEMS",
        "A status problem is a kin's field running wrong. Each one has its own "
        "cause.\n\n"
        "BURN: runaway heating in the condensate. The kin loses a little HP every "
        "turn, and its physical blows land only half as hard.\n\n"
        "POISON: impurities in the kernel knock motes out of step. The kin loses "
        "a little HP every turn.\n\n"
        "NUMB: an outside charge has locked the field in place so it can't move "
        "freely. SPEED drops sharply, and sometimes the kin can't act at all.\n\n"
        "SLEEP: the pump has stalled. The kin wakes by itself after a few "
        "turns.\n\n"
        "FROZEN: the condensate is stuck in a metastable state, like a ball "
        "resting in a dip halfway down a hill. Each turn it may jolt free.\n\n"
        "No kin catches a problem of its own type: BLAZE kin never burn, VENOM "
        "kin are never poisoned, SPARK kin never go numb and FROST kin never "
        "freeze.\n\n"
        "A TUNING FORK cures any of them, and so does a rest at a Hearth Hall.",
        "Has your kin ever come back from a bout singed, or queasy, or stiff "
        "with frost? Don't fret, dear.\f"
        "A status problem is only a field misbehaving, and every field can be "
        "set right again. Let me tell you what to watch for." },

    [LORE_SHELF] = { LCH_FIRST_STEPS, LSRC_TENDER, "LANTERN SHELF",
        "Up to six kin can travel with you. When you befriend a seventh, its "
        "lantern goes straight to the LANTERN SHELF: the racks of lanterns kept "
        "safe at every Hearth Hall.\n\n"
        "With a TWIN CRYSTAL you can reach the Shelf from anywhere. Open it from "
        "the START menu to swap kin between your team and the racks.\n\n"
        "Kin resting on the Shelf are kept calm and cool. They don't get tired or "
        "hungry while they wait, and they don't mind the rest one bit. Most of "
        "them sleep through the whole thing.\n\n"
        "The Shelf moves kin between halls by teleportation, using twin crystals "
        "and the telegraph wire. The page TWIN CRYSTALS in the LANTERNS chapter "
        "explains how that really works.",
        "Six kin is about as many as one warden can look after on the road. The "
        "rest can wait here with us, snug on the racks.\f"
        "And with a TWIN CRYSTAL in your pocket, the racks are never far away. "
        "Let me show you." },

    [LORE_CODE] = { LCH_FIRST_STEPS, LSRC_MARLO, "THE WARDEN'S CODE",
        "Every warden in the Vale learns the same five rules, and Warden Marlo "
        "makes every challenger say them out loud.\n\n"
        "ONE: Answer a brimming kin. A kin that runs at you is asking for a bout. "
        "Turning your back is bad manners and bad for the land.\n\n"
        "TWO: Stop when it dozes. A dozing kin is out of the bout, and you never "
        "strike it again.\n\n"
        "THREE: Kin choose. Offer a lantern, never force one. If a kin breaks "
        "free, it said no.\n\n"
        "FOUR: Rest your team. A tired kin gets a Hearth Hall, not another "
        "bout.\n\n"
        "FIVE: Leave the land better. Every bout feeds the soil and waters the "
        "fields. Walk lightly, and share what you learn.",
        "HOLD IT, rookie! Nobody fights in MY ring without knowing the code! You "
        "DO know the code?\f"
        "HA! Nobody does on day one. Five rules. Easy to learn, impossible to "
        "forget. Repeat after me!" },

    [LORE_TEMPERAMENT] = { LCH_FIRST_STEPS, LSRC_MARLO, "TEMPERAMENT",
        "Every kin has a temperament, shown on its summary. Most temperaments "
        "raise one stat by a tenth and lower another by a tenth. There are "
        "sixteen:\n\n"
        "FIERY: ATTACK up, WILL down. STEADY: DEFENSE up, SPEED down. CURIOUS: "
        "FOCUS up, ATTACK down. DREAMY: WILL up, SPEED down. NIMBLE: SPEED up, "
        "DEFENSE down. SCRAPPY: ATTACK up, FOCUS down. STUBBORN: DEFENSE up, "
        "FOCUS down. CLEVER: FOCUS up, DEFENSE down. SUNNY: SPEED up, WILL down. "
        "GRUMPY: ATTACK up, SPEED down. PATIENT: WILL up, ATTACK down. RESTLESS: "
        "SPEED up, ATTACK down. PROUD: FOCUS up, WILL down. SHY: WILL up, FOCUS "
        "down. SLEEPY: DEFENSE up, ATTACK down. EVEN: no change at all.\n\n"
        "Marlo's rule: fit the moves to the kin. A CLEVER kin should lead with "
        "moves aimed by FOCUS. A GRUMPY one wants to hit hard and doesn't care "
        "who goes first.",
        "HA! You're squinting at your kin's summary like it's a riddle! That "
        "word on there? TEMPERAMENT!\f"
        "It tells you what your kin's great at and what it's lazy about. Learn "
        "it, and fight to it!" },

    [LORE_POTENTIAL] = { LCH_FIRST_STEPS, LSRC_MARLO, "TRAITS & POTENTIAL",
        "POTENTIAL: every kin is born with six hidden values from 0 to 31, one "
        "each for HP, ATTACK, DEFENSE, FOCUS, WILL and SPEED. They add to its "
        "stats the way deep roots help a tree. The summary grades each one: DUD "
        "(0-9), DECENT (10-19), GREAT (20-27), STELLAR (28-30) or PERFECT (31). A "
        "DUD grade doesn't make a dud kin: levels and good moves count for far "
        "more.\n\n"
        "TRAITS: every kind of kin has two possible traits, and each kin has one "
        "of them. A trait is a knack. SURGE makes moves of its own type hit 1.5x "
        "harder when its HP runs low. THICK FUR halves damage from BLAZE and "
        "FROST. DRIFTER floats out of reach of STONE moves. SOAKER drinks TIDE "
        "moves as HP. HOARDER sometimes finds an item after a bout. There are "
        "many more.\n\n"
        "Marlo's rule: two kin of the same kind can fight very differently. Get "
        "to know yours.",
        "Two FLARIX can be as different as two wardens! Some are born with more "
        "in the tank. Some have a trick up their fur!\f"
        "POTENTIAL and TRAITS, rookie. Here's the short version." },

    [LORE_LUSTRE] = { LCH_FIRST_STEPS, LSRC_KID, "LUSTRE AND SIZE",
        "LUSTROUS KIN: about one kin in every 128 is lustrous. Its colours are "
        "shifted to a rare hue, and it sparkles when it comes out of its lantern. "
        "A lustrous kin is no stronger than any other, only rarer.\n\n"
        "Why does it happen? The colour of light a kernel holds depends on how "
        "far apart its mirror walls are, the way the length of a flute sets its "
        "note. The Vale's scholars think a lustrous kin's kernel grew its walls "
        "a tiny bit off the usual spacing, so its glow, and the body it builds, "
        "come out a different hue.\n\n"
        "SIZE: every kin also has a size: TINY, SMALL, AVERAGE, LARGE or HUGE. A "
        "HUGE kin can be nearly twice as tall and heavy as a TINY one of the same "
        "kind. Size doesn't change how well it fights.\n\n"
        "REAL SCIENCE: in a real mirror cavity, the gap between the mirrors sets "
        "which colours of light it can hold.\n\n"
        "VALE ONLY: kernels, and lustrous kin.",
        "Psst! Did you know some kin are LUSTROUS? They're a totally different "
        "colour and they SPARKLE!\f"
        "My cousin saw one once. Well, he SAYS he did. Oh, and some kin are HUGE "
        "and some are TINY. I collect tiny ones!" },

    [LORE_BOND] = { LCH_FIRST_STEPS, LSRC_KID, "BOND",
        "Bond is how close a kin feels to you, from 0 to 255. A newly "
        "befriended kin starts out a little shy.\n\n"
        "Bond grows when you have bouts together, when you walk together and "
        "when you give it tonics. It dips a little each time your kin dozes "
        "off, so try not to let it be knocked out too often.\n\n"
        "A kin with a high bond earns a little extra XP. Sometimes it hangs on "
        "with 1 HP left instead of dozing off, and sometimes it shakes off a "
        "status problem all by itself, because it doesn't want to let you "
        "down.\n\n"
        "You can check your kin's bond on its summary.",
        "My NIBBIT follows me EVERYWHERE. Mum says it's because we've got a "
        "really strong BOND.\f"
        "Once it got hit super hard and it just... didn't doze off! It hung on "
        "for me! Bond is the best." },

    [LORE_SUPPLIES] = { LCH_FIRST_STEPS, LSRC_CLERK, "SUPPLIES",
        "GLOW TONIC, BRIGHT TONIC, RADIANT TONIC: luciferin drinks whose cold "
        "chemical light pumps a kernel. They restore 20, 60 and 120 HP.\n\n"
        "TUNING FORK: its pure tone brings a kin's field back into step and cures "
        "any status problem.\n\n"
        "IGNITER: a piezo flash that re-seeds a collapsed field. It wakes a "
        "dozing kin with half its HP.\n\n"
        "HONEY DROP: glow-bee honey that refuels tired modes. It gives back 10 "
        "uses to every move.\n\n"
        "SUNSEED: a seed that stored a whole summer. A kernel absorbs it and the "
        "kin gains a level.\n\n"
        "AMP COIL and GUARD COIL: clip-on coils that boost a kin's pump or "
        "stiffen its outer field. ATTACK or DEFENSE rises sharply for the "
        "bout.\n\n"
        "REAL SCIENCE: fireflies glow with luciferin, and squeezing some "
        "crystals, like quartz, makes a spark. Click-lighters on stoves use "
        "that.\n\n"
        "VALE ONLY: what any of it does to a kin.",
        "Welcome, welcome! First time buying for a kin? Don't be shy, I'll walk "
        "you along the shelves.\f"
        "Everything here works WITH a kin's field, never against it. That's the "
        "secret of a good shop!" },

    [LORE_HUSH_BELL] = { LCH_FIRST_STEPS, LSRC_CLERK, "HUSH BELL",
        "Ring a HUSH BELL and wild kin will ignore you for 150 steps.\n\n"
        "Wild kin notice wardens by the fields of the kin they carry, the way you "
        "might notice a friend humming. The bell rings an anti-phase hum: a tone "
        "that swells exactly when your team's field dips, and dips when it "
        "swells. The two cancel out, and to the wild kin around you, your team "
        "goes quiet.\n\n"
        "Brimming kin still need their bouts, so don't hush forever! But when "
        "your team is tired and the Hearth Hall is far away, the bell is a good "
        "friend.\n\n"
        "REAL SCIENCE: two waves that are exactly out of step cancel each other "
        "out. This is called destructive interference, and noise-cancelling "
        "headphones use it to erase sound.\n\n"
        "VALE ONLY: a bell that can hide a kin's field.",
        "Tired team, long way home? What you need is a HUSH BELL! Very popular "
        "with wardens.\f"
        "One ring and the wild kin simply don't notice you. It's rather clever, "
        "actually. Let me explain how it works." },

    /* ============================================================ */
    /*  THE KINSHIP                                                 */
    /* ============================================================ */

    [LORE_KINSHIP] = { LCH_KINSHIP, LSRC_ELDER, "THE KINSHIP",
        "The Kinship is the old bargain between people and kin, sworn long ago "
        "at the Old Hearth in the plaza of Maple Village.\n\n"
        "People promised to guide the bouts that kin need, to give each kin a "
        "name and food, and to offer it a lantern to rest in. Kin promised to "
        "share their strength, and to let their surplus out in bouts instead of "
        "in fires and floods.\n\n"
        "The bargain holds because both sides want it. Kin love a good bout the "
        "way a sheepdog loves to run, and wardens love their kin. When kin bout, "
        "the loose energy settles gently into the land as warm soil, soft rain "
        "and food for plants, and the seasons stay kind.\n\n"
        "People who travel with kin are called wardens. Not owners. Wardens. A "
        "warden keeps watch, and keeps the promise.",
        "Sit a moment, young warden. These old stones have heard a great many "
        "promises, but only one that has lasted.\f"
        "Do you know what the Kinship really is? Not just a word. A bargain. Let "
        "me tell it properly." },

    [LORE_KINDLING] = { LCH_KINSHIP, LSRC_STORY, "THE KINDLING",
        "Today you received your first kin and became a warden. That is your "
        "Kindling.\n\n"
        "In Maple Village, young people are Kindled at the Almanac House, where "
        "the Keeper looks after the record of every kin, season and storm. You "
        "chose a partner, took your first lanterns and tonics, and received the "
        "ALMANAC and this LOREBOOK.\n\n"
        "Your ALMANAC lists every kin you have met and every kin you have "
        "befriended. Your LOREBOOK keeps what you learn.\n\n"
        "A warden's first duties are simple: answer the kin who ask for bouts, "
        "and look after the kin who travel with you. The rest you will learn on "
        "the road.\n\n"
        "The Keeper says the sky has been grumbling for weeks. Keep an eye on it.",
        0 },

    [LORE_RING_SASH] = { LCH_KINSHIP, LSRC_STORY, "THE RING SASH",
        "You beat Warden Marlo in the Bout Ring and earned the RING SASH.\n\n"
        "The sash is woven with the Kinship's old pattern of two linked rings: "
        "one for people, one for kin. It isn't a prize so much as a promise. A "
        "warden who wears it has shown they can answer a brimming kin of any "
        "size, keep a cool head, and stop the moment a bout is won.\n\n"
        "Marlo tied it on you personally and announced, far louder than "
        "necessary, that no rookie had ever improved so fast. Then, much more "
        "quietly: \"Now go up that hill. The sky won't wait.\"\n\n"
        "With the sash, Keeper Linden will send you to the Stormstone.",
        0 },

    [LORE_ANSWER_BRIM] = { LCH_KINSHIP, LSRC_MARLO, "ANSWER THE BRIM",
        "A kernel can only hold so much. When a wild kin has soaked up more than "
        "it can hold, it brims: the surplus starts leaking out as heat, static, "
        "frost or floodwater, and the kin gets restless and goes looking for a "
        "bout.\n\n"
        "That's why a brimming kin runs at you in the grass. It isn't angry. "
        "It's asking. A bout lets it spill its surplus safely, and afterwards it "
        "wanders off lighter and happier.\n\n"
        "Ignore brimming kin and the surplus pools. A few brimming CINDERUB in a "
        "dry summer is how wildfires start. A crowd of brimming BUBBLIN in spring "
        "is how rivers burst their banks.\n\n"
        "Kin that live with wardens hardly ever brim: their bouts keep them "
        "topped up but never too full. That's why kin love wardens and wardens "
        "love bouts. Everybody wins. Even the weather.",
        "Why do we bout? HA! Ask a sheepdog why it runs! Kin NEED it, rookie!\f"
        "And when a wild one charges you in the grass, you ANSWER it. Every "
        "time. Here's why." },

    [LORE_PARENTS] = { LCH_KINSHIP, LSRC_GRAN, "YOUR PARENTS",
        "Your mother and father are wardens, and have been since before you were "
        "born. They travel the Vale answering brimming kin wherever the land "
        "needs it: the dry hills in summer, the river towns in the spring "
        "floods, the high passes when the snow grows restless.\n\n"
        "Travelling wardens are rarely home for long. They send telegrams from "
        "the Hearth Halls, and a parcel now and then, and Gran reads every word "
        "twice.\n\n"
        "Gran says you have your mother's stubbornness and your father's knack "
        "with kin, and that both will come in handy.\n\n"
        "They always meant for you to have your Kindling here at home, in Maple "
        "Village, the way they did. Somewhere out there, they will hear that you "
        "have become a warden, and they will be very proud.",
        "Come sit by the stove, sweetpea. Have I ever told you how your parents "
        "met? No? Well, pour yourself some tea.\f"
        "They were both wardens, just like you are now. And they still are, out "
        "there somewhere..." },

    [LORE_OPEN_DOOR] = { LCH_KINSHIP, LSRC_HERMIT, "THE OPEN DOOR",
        "The Hermit of Bramblewood has one saying he repeats to anyone who will "
        "listen: \"A lantern is a door, and a door opens both ways.\"\n\n"
        "He means that no kin is ever truly caught. A kin enters a lantern "
        "because it is calm and chooses to, and it can always refuse. And any "
        "kin can be let go: a released kin rebuilds its body in a flash and "
        "walks home, none the worse.\n\n"
        "He also says: \"The kin that stays when the door is open is the only "
        "kin you truly have.\" Oddly, wardens who let a kin go when it wants to "
        "leave are the ones whose kin never want to.\n\n"
        "He has lived alone in the wood for forty years, if you don't count the "
        "LUMOTH, the NIBBIT under the floor and the old HOOTLORD on the roof. He "
        "says he never counts them. They count him.",
        "You carry lanterns. Good. Now tell me, little warden: which way does a "
        "door open?\f"
        "Hm. Wrong. Or right. Both, in fact. Sit down. The kettle's on." },

    [LORE_PRIMER] = { LCH_KINSHIP, LSRC_BOOK_HOME, "MY FIRST KIN BOOK",
        "From a children's picture book, much read and a little sticky:\n\n"
        "\"MY FIRST BOOK OF KIN.\n\n"
        "Kin are animals with a little glowing crystal inside. The crystal is "
        "called a KERNEL. It is full of light that is ALSO a tiny bit of "
        "stuff!\n\n"
        "Every kin eats one kind of energy. FLARIX eats warmth. DANDELAMB eats "
        "sunshine. AQUAPO eats the splish and splash of water.\n\n"
        "When a kin eats too much, it BRIMS, and it wants to play. Playing is "
        "called a BOUT. After a bout, the extra energy goes into the ground and "
        "the sky and makes the rain soft and the soil warm.\n\n"
        "If a kin gets tired, it DOZES. Shh! It is only resting.\n\n"
        "What do kin want? A NAME, a MEAL and a LANTERN. What do people want? "
        "KIND WEATHER! That is the KINSHIP.\"\n\n"
        "On the last page, in very wobbly letters: I WILL BE A WARDEN.",
        "Squeezed between Gran's cookbooks is a battered little picture book.\f"
        "MY FIRST BOOK OF KIN! You learned to read with this one." },

    /* ============================================================ */
    /*  HOW KIN WORK                                                */
    /* ============================================================ */

    [LORE_KERNEL] = { LCH_BIOLOGY, LSRC_KEEPER, "THE KERNEL",
        "At the heart of every kin is a kernel: a living crystal about the size "
        "of a pebble. Hold a kin up to a dark window and you can sometimes see "
        "it glow.\n\n"
        "Inside, the kernel's walls act as mirrors, making a tiny chamber that "
        "traps light. There the trapped light mixes with the crystal itself to "
        "make motes: particles that are half light and half matter. A kernel "
        "holds billions of them, and every one shares the same quantum state, "
        "moving in perfect step. That shared state is called a condensate.\n\n"
        "The condensate is a kin's life force. Its field shapes the body, powers "
        "every move and holds the kin together. HP is really a measure of how "
        "well the condensate is holding together.\n\n"
        "REAL SCIENCE: light-matter particles like motes are real. Scientists "
        "call them exciton-polaritons, and they make condensates of them in "
        "tiny mirror chambers.\n\n"
        "VALE ONLY: crystals that grow such chambers inside living animals.",
        "May I show you something? Hold your kin up to the window. Gently. "
        "There. Do you see that faint glow in its chest?\f"
        "That is its kernel. Everything a kin is begins there." },

    [LORE_PUMPING] = { LCH_BIOLOGY, LSRC_KEEPER, "PUMPING",
        "A condensate is never still. Motes leak out through the kernel's mirror "
        "walls all the time as a faint glow, and each one lasts only a tiny "
        "fraction of a second. If nothing replaced them, the condensate would "
        "fade in a blink.\n\n"
        "So a kin must keep pumping: soaking up energy to make new motes as fast "
        "as old ones leak away. Each kin pumps from one kind of energy, and that "
        "is its type.\n\n"
        "Pump harder than the kernel leaks and the condensate grows. Past a point "
        "called the threshold, the motes suddenly fall into step and the "
        "condensate switches on. If pumping falls below threshold, it switches "
        "off and the kin dozes. Pump far more than the kernel can hold and the "
        "surplus spills out: the kin brims.\n\n"
        "REAL SCIENCE: polariton condensates are \"driven-dissipative\". They "
        "leak light constantly and only live while they are pumped, like a "
        "fountain that stands only while the water runs. They switch on sharply "
        "at a threshold, just as a laser does. Labs pump them with lasers.\n\n"
        "VALE ONLY: pumping from heat, sunlight or water.",
        "Have you noticed that kin always drift towards their element? FLARIX "
        "to the fire, DANDELAMB to a sunbeam, AQUAPO to a puddle.\f"
        "There's a good reason for it. A kernel is always leaking." },

    [LORE_DOZING] = { LCH_BIOLOGY, LSRC_TENDER, "DOZING OFF",
        "When a kin's HP reaches 0, it dozes off. Its field has been knocked "
        "about until the condensate drops below its threshold and collapses into "
        "a tiny seed of motes deep in the kernel. The kin goes cool and limp, "
        "like a candle blown out to a glowing wick.\n\n"
        "It isn't hurt. The blows in a bout are field striking field: they "
        "scatter motes, not flesh. But a dozing kin can't pump on its own until "
        "something re-seeds it.\n\n"
        "A rest at a Hearth Hall pumps every kernel back to full. On the road, "
        "an IGNITER does the job: its sharp flash re-seeds the condensate and "
        "wakes the kin with half its HP.\n\n"
        "A kin's bond dips a little when it dozes. It doesn't blame you, but it "
        "does remember. Let a tired kin rest before it's knocked out.",
        "Oh, don't look so worried, dear. Dozing off looks dreadful, all limp "
        "and dim, but it's nothing of the sort.\f"
        "Come, I'll tell you what's really going on inside." },

    [LORE_TONICS] = { LCH_BIOLOGY, LSRC_BAKER, "GLOW TONICS",
        "Every tonic in the Vale starts with luciferin, the same stuff fireflies "
        "glow with. Mix luciferin with a dash of the right enzyme and a breath of "
        "air, and it gives off light with almost no heat at all. That is called "
        "chemiluminescence: light made straight from a chemical reaction.\n\n"
        "A kernel drinks that cold light the way we drink soup. The new motes top "
        "up the condensate, and HP comes back. The stronger the brew, the more "
        "light: GLOW TONIC, BRIGHT TONIC, RADIANT TONIC.\n\n"
        "HONEY DROPS come from glow-bees, which sip nectar from night-blooming "
        "flowers and store it as pale honey that shimmers in the dark. A drop "
        "refuels the tired parts of a kin's field and gives back uses to its "
        "moves.\n\n"
        "REAL SCIENCE: luciferin and the enzyme luciferase really are how "
        "fireflies, glow-worms and many deep-sea animals make light.\n\n"
        "VALE ONLY: glow-bees, and kernels that drink the light.",
        "Mind the oven, hon! Ooh, is that a new kin? Come here, let me show you "
        "my secret shelf. No, not the cakes. The TONICS!\f"
        "You didn't think the shop brews them all, did you?" },

    [LORE_FOXFIRE] = { LCH_BIOLOGY, LSRC_FORAGER, "FOXFIRE",
        "On damp nights in Bramblewood, rotting logs glow a soft green. Foragers "
        "call it foxfire.\n\n"
        "Foxfire is made by fungi. As they digest dead wood they use a luciferin "
        "of their own, and the reaction gives off a steady, cold light. Nobody "
        "is quite sure why the fungi bother. One idea is that the glow draws in "
        "insects, which then carry the fungi's spores away.\n\n"
        "The kin don't wonder why. Glowing logs are where VENOM kin gather to "
        "pump, and where plenty of other kin come to nibble a little light. A "
        "fallen tree in Bramblewood is a feast hall.\n\n"
        "The Forager's rule: rot is the forest cooking. Nothing that dies in the "
        "wood is wasted. Fungi turn it into soil, soil feeds new trees, and the "
        "glow of it all feeds kin along the way.\n\n"
        "REAL SCIENCE: glowing fungi are real, and people have written about "
        "foxfire for over two thousand years.\n\n"
        "VALE ONLY: kin feasting on it.",
        "Shh! Don't step on that log! Look closer. See? It's glowing!\f"
        "Mushrooms, friend. The finest cooks in the forest. Let me tell you "
        "about foxfire." },

    [LORE_POLARITONS] = { LCH_BIOLOGY, LSRC_RESEARCHER, "LIGHT MEETS MATTER",
        "Motes are what scientists call exciton-polaritons. To make one you need "
        "two ingredients.\n\n"
        "First, an exciton. In certain crystals, a flash of light can knock an "
        "electron loose, leaving a gap called a hole behind. The electron and "
        "the hole still pull on each other and circle together as a pair. That "
        "pair is an exciton.\n\n"
        "Second, a trap for light: two mirrors facing each other, less than a "
        "thousandth of a millimetre apart. Light bounces between them.\n\n"
        "Put the crystal between the mirrors, and the exciton and the light "
        "start trading energy back and forth so fast that they stop being two "
        "things. They become one new particle, part light and part matter: a "
        "polariton. It can be a hundred thousand times lighter than an electron, "
        "and it lives only a few trillionths of a second before it leaks out "
        "through a mirror as light.\n\n"
        "REAL SCIENCE: all of this. Polaritons in mirror chambers were first seen "
        "in 1992.\n\n"
        "VALE ONLY: kernels that make them inside kin.",
        "A new warden! At my station! Oh, sit, sit, mind the cables. Tell me: "
        "what IS a mote, actually?\f"
        "Nobody knows! Well. I do. Mostly. It's the most wonderful particle in "
        "the world. Half light! Half matter!" },

    [LORE_BOSONS] = { LCH_BIOLOGY, LSRC_RESEARCHER, "BOSONS & FERMIONS",
        "Every particle in the universe belongs to one of two families.\n\n"
        "FERMIONS are the loners. Electrons, protons and neutrons are fermions, "
        "and they obey a strict rule called the Pauli exclusion principle: no "
        "two of them can ever share exactly the same state. That is why the "
        "electrons in an atom stack up in shells instead of all crowding into "
        "the lowest one, and a big part of why solid things take up space.\n\n"
        "BOSONS are the crowders. Particles of light are bosons, and any number "
        "of them can share one state. Better still, they like to: the more "
        "bosons already in a state, the more likely others are to join them. "
        "Lasers work this way.\n\n"
        "An exciton is made of two fermions, an electron and a hole, and a pair "
        "of fermions stuck together behaves like a boson. So polaritons are "
        "bosons, and billions of them can pile into a single state. That is what "
        "makes a condensate possible.\n\n"
        "REAL SCIENCE: every word of it.\n\n"
        "VALE ONLY: nothing on this page!",
        "Quick question! Why can't you walk through a wall? No, not \"because "
        "it's solid\". WHY is it solid?\f"
        "Because electrons refuse to share! And motes? Motes LOVE to share. That "
        "difference is everything. Listen!" },

    [LORE_CONDENSATES] = { LCH_BIOLOGY, LSRC_RESEARCHER, "CONDENSATES",
        "Every particle is also a little wave. The colder a gas is, and the "
        "lighter its particles, the longer those waves stretch. Chill a crowd of "
        "bosons until their waves are longer than the gaps between them, and "
        "something remarkable happens: the waves overlap and merge, and a huge "
        "number of particles drop into the very same state. They stop acting "
        "like a crowd and act like one giant wave. That is a Bose-Einstein "
        "condensate.\n\n"
        "For atoms this takes astonishing cold: less than a millionth of a "
        "degree above absolute zero. But polaritons are so light that their "
        "waves are huge, so they can condense at far warmer temperatures. In some "
        "materials they condense even at room temperature.\n\n"
        "Condensates are strange. They can flow without any friction, and if you "
        "stir one, it forms tiny whirlpools called vortices.\n\n"
        "REAL SCIENCE: predicted by Bose and Einstein in 1924-25, first made with "
        "atoms in 1995 and with polaritons in 2006, and at room temperature in "
        "the years since.\n\n"
        "VALE ONLY: a condensate as a creature's life force.",
        "Imagine a whole crowd of people, all jostling. Now imagine every single "
        "one of them suddenly doing the same dance, in perfect step.\f"
        "That's a condensate! Only with particles. And it's REAL. I've made "
        "them! Well. Helped. Listen!" },

    [LORE_SUPERSOLIDS] = { LCH_BIOLOGY, LSRC_RESEARCHER, "SUPERSOLIDS",
        "Here is a puzzle: a kin's body is mostly water, carbon and silica, yet "
        "it keeps its shape, and flows back together after a blow. How?\n\n"
        "A supersolid might be the answer. It is a state of matter that is two "
        "opposite things at once. Its particles line up in a regular pattern "
        "like a solid crystal, and yet the whole thing also flows without "
        "friction, like a superfluid. For decades physicists argued about "
        "whether such a thing could exist.\n\n"
        "It can. Since 2019, scientists have made supersolids from clouds of "
        "ultracold atoms, and in 2025 a team reported signs of a supersolid made "
        "of polaritons, the very particles motes are made of.\n\n"
        "Dr. Vass's idea is that a kin's condensate is a supersolid: stiff enough "
        "to hold a body in shape like a scaffold, yet free to flow and heal. It "
        "would explain why a blow scatters motes but never breaks bones.\n\n"
        "REAL SCIENCE: supersolids exist, in atoms and, it seems, in "
        "polaritons.\n\n"
        "VALE ONLY: a supersolid scaffold holding a body together.",
        "Riddle for you! What's solid like a crystal, but flows like water with "
        "no friction at all? Give up?\f"
        "A SUPERSOLID! For years we thought it was impossible. And I think your "
        "kin might be made of one!" },

    /* ============================================================ */
    /*  LANTERNS                                                    */
    /* ============================================================ */

    [LORE_HEARTGLASS] = { LCH_LANTERNS, LSRC_AIDE, "HEARTGLASS",
        "A lantern doesn't squash a kin into a little box. It records it.\n\n"
        "The heart of every lantern is a pair of heartglass mirrors facing each "
        "other, so perfect that light trapped between them can bounce for years "
        "before it escapes. That makes a cavity that can hold a condensate with "
        "almost no loss.\n\n"
        "A kin's identity isn't in its flesh. It's in the quantum pattern of its "
        "kernel and condensate. Motes are bosons, so all of them fit into one "
        "single pattern a few thousandths of a millimetre wide. The kernel slips "
        "into the cavity, and the kin rests there, calm and cool, until you let "
        "it out.\n\n"
        "Lanterns are graded by finesse: how sharp and clean their mirrors are. "
        "A higher finesse can hold a livelier, noisier kin. A PRISM LANTERN works "
        "half again as well as a plain LANTERN; a STAR LANTERN, twice as well.\n\n"
        "REAL SCIENCE: mirror cavities that store light, and finesse as a "
        "measure of how good they are.\n\n"
        "VALE ONLY: heartglass, and mirrors that hold anything for years.",
        "Oh! Hi! I'm PIP, the Keeper's aide. I polish the lanterns. Want to know "
        "a secret? A lantern isn't a cage at all!\f"
        "It's more like a very, very good mirror. Okay, let me explain properly." },

    [LORE_KIN_CHOOSE] = { LCH_LANTERNS, LSRC_AIDE, "KIN CHOOSE",
        "Why must a kin be tired before it will settle in a lantern? Because only "
        "a calm condensate can make the move.\n\n"
        "To slip into the cavity, a kin's condensate has to mode-match: take on "
        "exactly the shape of the pattern the mirrors can hold, like a key "
        "sliding into a lock. A fresh, excited kin is a storm of jostling motes, "
        "far too noisy to fit. A tired, sleepy or frozen kin is near its ground "
        "state, its quietest pattern, and slides in easily.\n\n"
        "And here's the important part: a kin can always refuse. By driving its "
        "own field out of tune, it breaks the match, and the lantern can't hold "
        "it. When you see \"It broke free!\", that is what happened. It said "
        "no.\n\n"
        "That's why the Kinship says befriending, not catching. Every kin in a "
        "lantern chose to be there.\n\n"
        "REAL SCIENCE: mode-matching is a real part of optics. Light only enters "
        "a cavity well if its shape fits the cavity's pattern.\n\n"
        "VALE ONLY: kin that choose.",
        "The Keeper made me learn this on my very first day: you can't force a "
        "kin into a lantern. Ever. It's physically impossible!\f"
        "Isn't that lovely? Here, let me show you why." },

    [LORE_SHEDDING] = { LCH_LANTERNS, LSRC_AIDE, "SHED AND REBUILT",
        "When a kin settles into a lantern, only its kernel and condensate go "
        "inside. The rest of its body, mostly water, carbon and silica held in "
        "shape by its field, is shed as a puff of glittering mist.\n\n"
        "When you let it out, the lantern pumps the kernel hard. The field swells "
        "back to full size and pulls matter from the air and the ground, and a "
        "body forms around the kernel in a second or two, the way a snowflake "
        "grows around a speck of dust. That is the flash you see when a kin "
        "comes out.\n\n"
        "It explains a few odd things wardens notice. A kin let out in a desert "
        "is always thirsty: there was hardly any water to build with. A kin let "
        "out by the sea sometimes comes out a little salty. And a kin always "
        "comes out clean, every burr and scrape gone.\n\n"
        "REAL SCIENCE: snowflakes and raindrops really do grow around tiny "
        "specks.\n\n"
        "VALE ONLY: bodies that grow the same way.",
        "Did you ever notice that sparkly mist when a kin goes into its lantern? "
        "That's its body! Well, most of it.\f"
        "Don't worry, that's supposed to happen! It builds a fresh one when it "
        "comes out. Here's how." },

    [LORE_NO_COPIES] = { LCH_LANTERNS, LSRC_AIDE, "NO COPIES",
        "If a lantern can record a kin, why can't we copy one? One FLARIX in, two "
        "FLARIX out?\n\n"
        "Because the universe forbids it. A law of physics called the no-cloning "
        "theorem says that nothing, however clever, can make a perfect copy of "
        "an unknown quantum state. You can move a quantum state. You can destroy "
        "one. You can never duplicate one.\n\n"
        "The idea behind the proof is short. Suppose a machine could copy two "
        "different states, A and B. Quantum rules are strict about blends: fed "
        "a blend of A and B, the machine must give the same blend of its "
        "answers, \"two A's\" mixed with \"two B's\". But two copies of the blend "
        "is something different. So no machine can copy every state.\n\n"
        "That makes every kin one of a kind, forever. Nobody can forge a "
        "lustrous kin, and nobody can ever copy yours.\n\n"
        "REAL SCIENCE: the no-cloning theorem was proven in 1982. It's also why "
        "secret quantum messages can't be copied without being noticed.\n\n"
        "VALE ONLY: the kin, of course.",
        "Someone asked me yesterday if we could make TWO of their favourite kin. "
        "Ha! I get that a lot.\f"
        "The answer is no, and not because nobody's tried. It's a law! The "
        "universe itself says no. Listen to this." },

    [LORE_TWIN_CRYSTALS] = { LCH_LANTERNS, LSRC_AIDE, "TWIN CRYSTALS",
        "How does the LANTERN SHELF send a kin from one Hearth Hall to another, "
        "or to you on the road? By quantum teleportation.\n\n"
        "Every hall grows twin crystals: pairs whose inner states are entangled, "
        "linked so closely that they act as one thing even far apart. One twin "
        "stays on the rack. The other goes to another hall.\n\n"
        "To send a kin, the hall measures the kin's kernel pattern together with "
        "its twin crystal. That destroys the pattern here, and gives a short "
        "result, which goes out over the telegraph wire. At the other end, the "
        "message says exactly how to adjust the other twin, and the kin's "
        "pattern appears there, perfect. Then the body rebuilds as usual.\n\n"
        "Each send uses up one twin pair, so the halls grow new ones every night. "
        "(How your own TWIN CRYSTAL stays stocked on the road is a Hearth Hall "
        "secret. Pip has asked, and was told to go polish something.)\n\n"
        "REAL SCIENCE: quantum states of light have been teleported since 1997, "
        "even from the ground up to a satellite.\n\n"
        "VALE ONLY: teleporting a whole kin.",
        "Okay, this is my FAVOURITE thing. You know how you can reach the Shelf "
        "from anywhere with a TWIN CRYSTAL?\f"
        "The kin doesn't travel down the wire. It's TELEPORTED. For real! Here's "
        "how it works." },

    [LORE_Q_FACTOR] = { LCH_LANTERNS, LSRC_RESEARCHER, "QUALITY FACTOR",
        "A mirror chamber for light is called a cavity, and a very small one is a "
        "microcavity. Real mirrors for them are built from stacks of dozens of "
        "thin layers, each reflecting a little, so that together they reflect "
        "almost everything.\n\n"
        "How good is a cavity? Physicists measure its quality factor, or Q. "
        "Roughly, Q tells you how many times the light wave swings back and "
        "forth before most of it has leaked away. A poor cavity manages a few "
        "hundred swings; a good one, millions. It's like a bell: a cracked bell "
        "goes \"thunk\", a fine one rings on and on.\n\n"
        "Even the very best cavities ever built hold on to their light for a "
        "second or so at most, and most for far, far less.\n\n"
        "Heartglass holds a condensate for years. Its Q would have to be "
        "enormously higher than anything ever built by hand. No one has managed "
        "to make heartglass in a workshop. Lantern-makers grow it, slowly, and "
        "even they don't fully understand why it works.\n\n"
        "REAL SCIENCE: microcavities, layered mirrors and Q.\n\n"
        "VALE ONLY: heartglass.",
        "Your lantern! May I? Oh, look at that heartglass. Do you know how good "
        "these mirrors are? Nobody does! They're off our charts!\f"
        "Let me tell you how we grade mirrors, and you'll see why I'm so jealous." },

    [LORE_DECOHERENCE] = { LCH_LANTERNS, LSRC_RESEARCHER, "DECOHERENCE",
        "Quantum states are fragile. A condensate keeps its shared state only as "
        "long as nothing jostles it too much. Every stray bump from the outside "
        "world, a warm atom or a passing scrap of light, carries a little "
        "information about the state away into the surroundings, and each leak "
        "blurs it. Physicists call this decoherence.\n\n"
        "Decoherence is why the everyday world doesn't look quantum. A chair, a "
        "cat or a kin's body is bumped by trillions of air molecules every "
        "instant, so any quantum strangeness is smeared out almost at once. Only "
        "small, carefully shielded or carefully built things stay coherent for "
        "long.\n\n"
        "It's also why befriending needs a calm kin. A struggling, excited "
        "condensate would decohere the moment it met the lantern's mirrors, so it "
        "can't cross over. A kin near its ground state can.\n\n"
        "REAL SCIENCE: decoherence is real and measured, and it's the biggest "
        "enemy of everyone building quantum computers.\n\n"
        "VALE ONLY: kin, lanterns, and calm as a way of staying coherent.",
        "Ever tried to carry a very full cup of tea across a room while someone "
        "keeps bumping your elbow? That's my whole job!\f"
        "Keeping quantum states from spilling. We call the spilling DECOHERENCE, "
        "and everything wants to do it." },

    [LORE_QUANTUM_MEMORY] = { LCH_LANTERNS, LSRC_RESEARCHER, "QUANTUM MEMORY",
        "Can light be stored? It can!\n\n"
        "In a quantum memory, a pulse of light is sent into a special crystal, "
        "often one sprinkled with rare atoms. The atoms soak up the light's "
        "quantum state and hold it as a pattern in themselves, like a held "
        "breath. Later, a signal makes them let it go, and the same light comes "
        "out again, its delicate wave pattern intact.\n\n"
        "Early memories held light for tiny fractions of a second. The best now "
        "hold it for about an hour, in crystals cooled deep and shielded from "
        "every disturbance. Scientists want such memories for quantum networks, "
        "so fragile states can wait safely at stations along the line.\n\n"
        "A lantern is a quantum memory for a whole kin: it stores a kernel's "
        "pattern and gives it back unchanged. The Lantern Shelf is a quantum "
        "network. Dr. Vass likes to say the Vale has been running for centuries "
        "what the rest of the world is still trying to build.\n\n"
        "REAL SCIENCE: quantum memories in crystals, and an hour of storage.\n\n"
        "VALE ONLY: storing a living pattern for years.",
        "Here's a party trick: I can catch a flash of light in a crystal, keep "
        "it, and let it go again later. Exactly as it was!\f"
        "Your lanterns do the same with a whole kin. Honestly, I'm a little "
        "envious. Let me explain." },

    [LORE_SPEED_LIMIT] = { LCH_LANTERNS, LSRC_RESEARCHER, "LIGHT SPEED LIMIT",
        "People sometimes think entanglement lets you send messages instantly. "
        "It doesn't, and teleportation shows why.\n\n"
        "When a Hearth Hall measures a kin together with a twin crystal, the "
        "far twin does end up holding the kin's pattern, but scrambled in one "
        "of several possible ways, and nobody at the far end can tell which. To "
        "them it looks exactly like random noise. Only the short message sent "
        "over the telegraph wire says how to unscramble it.\n\n"
        "So a kin can never arrive faster than that message, and no message can "
        "travel faster than light. Entanglement gives the link; the wire gives "
        "the key. Neither works alone.\n\n"
        "And the pattern here is destroyed by the measurement before it is "
        "rebuilt there, so the Shelf never makes a copy, just as the no-cloning "
        "law demands.\n\n"
        "REAL SCIENCE: this is exactly how real quantum teleportation works. It "
        "always needs an ordinary message too, so it never beats the speed of "
        "light.\n\n"
        "VALE ONLY: sending kin.",
        "Teleportation! Everyone gets so excited. Instant travel! Faster than "
        "light! Nope. Sorry. Never.\f"
        "But the reason WHY is even better. Hand me that telegraph slip, I'll "
        "show you." },

    /* ============================================================ */
    /*  TYPES                                                       */
    /* ============================================================ */

    [LORE_PUMP_BANDS] = { LCH_TYPES, LSRC_KEEPER, "PUMP BANDS",
        "Every kernel absorbs one kind of energy far better than any other. "
        "That is its pump band, and it is what we call a kin's type.\n\n"
        "BLAZE drinks heat, the invisible infrared glow of warm things. BLOOM "
        "drinks sunlight through leaf-green pigments. SPARK drinks electric "
        "charge. TIDE drinks the push and pull of water. STONE drinks strain in "
        "rock. GALE drinks wind and air pressure. FROST pumps by shedding heat. "
        "VENOM drinks the chemical energy of rot. DREAM drinks the faint electric "
        "hum of minds. DUSK drinks every colour, even starlight. SWARM kin have "
        "many tiny kernels that flash together. BEAST kin run on plain food, "
        "weak but steady. BRAWL kin pump from the strain in their own bones. "
        "WYRM kernels are so vast they couple to whole weather systems.\n\n"
        "A move carries its user's band. Some bands disrupt others, as water "
        "quenches heat. Some barely touch them, as a flame hardly warms another "
        "flame.\n\n"
        "REAL SCIENCE: every material absorbs some kinds of light better than "
        "others. That is why things have colours.\n\n"
        "VALE ONLY: kernels with pump bands.",
        "You've seen FLARIX warming itself by a fire and DANDELAMB napping in "
        "the sun. Ever wondered why each kin is so particular?\f"
        "It's because every kernel is tuned. Like a harp string, it only answers "
        "its own note." },

    [LORE_TYPE_BLAZE_BEAST] = { LCH_TYPES, LSRC_BAKER, "BLAZE AND BEAST",
        "BLAZE kin pump on heat: the invisible infrared light that pours off "
        "anything warm. The bakery oven hasn't gone cold in years, because a "
        "CINDERUB sleeps on top of it. It soaks up the warmth, and on cold "
        "mornings it breathes some back.\n\n"
        "BLAZE moves wither BLOOM, melt FROST, scatter SWARM and banish DUSK, "
        "since light is the one thing darkness can't hide from. But TIDE quenches "
        "them, STONE smothers them, WYRM hardly notices, and other BLAZE kin "
        "just warm up. BLAZE kin fear TIDE, STONE and DUSK.\n\n"
        "BEAST kin run on ordinary food and ordinary muscle: a weak pump, but a "
        "very steady one. They have no elemental weak spot; only BRAWL hits them "
        "hard. The odd rule: BEAST and DUSK can't touch each other at all. Plain "
        "teeth pass straight through a DUSK kin's shadowy field, and DUSK's "
        "gloom finds nothing to grip in a BEAST's plain, steady one.\n\n"
        "REAL SCIENCE: everything warm glows in infrared, including you.\n\n"
        "VALE ONLY: kin that drink it.",
        "Careful, hon, don't wake him! That's my CINDERUB on the oven. Best "
        "baker's helper in the Vale.\f"
        "And the little thief under the counter? A NIBBIT. Two very different "
        "kin! Let me tell you about them." },

    [LORE_TYPE_TIDE_SPARK] = { LCH_TYPES, LSRC_FISHER, "TIDE AND SPARK",
        "TIDE kin pump on the push and pull of water: waves, currents, the "
        "pressure of the deep. An AQUAPO's frilly gills feel every ripple in the "
        "lake, and drink it.\n\n"
        "TIDE moves quench BLAZE and wear down STONE, the way rivers carve "
        "canyons. But BLOOM drinks them up, and TIDE barely troubles TIDE. TIDE "
        "kin fear BLOOM, VENOM and SPARK.\n\n"
        "SPARK kin pump on electric charge. They build it up by rubbing, by wind "
        "and by storms, and let it go in snaps and bolts. SPARK strikes TIDE "
        "hard, because charge races through water, and GALE, because it tears "
        "through the air. Against STONE it does nothing at all: the ground "
        "swallows every spark. BLOOM and other SPARK kin shrug it off, and SPARK "
        "kin fear only STONE.\n\n"
        "That's why a fisher gets off the lake when a storm rolls in, and why a "
        "TIDE warden keeps a STONE kin handy.\n\n"
        "REAL SCIENCE: lake and sea water carry electricity because of the salts "
        "dissolved in them, so lightning is deadly near water. And flowing water "
        "really does carve rock.\n\n"
        "VALE ONLY: kin that drink it all.",
        "Sit on the dock a spell. Fish won't bite for an hour yet. You know why "
        "an AQUAPO never stops smiling?\f"
        "It's tasting the lake. Every ripple. Let me tell you about water kin, "
        "and the one thing they fear." },

    [LORE_TYPE_BLOOM_STONE] = { LCH_TYPES, LSRC_GARDENER, "BLOOM AND STONE",
        "BLOOM kin pump on sunlight, drinking it through green pigments much as "
        "leaves do. A MOSSHELL naps in sunbeams so the moss on its shell can "
        "pump for it, and on bright days a PUFFLEECE's fleece bursts into "
        "flower.\n\n"
        "BLOOM moves drink up TIDE and crack STONE, just as roots split rocks "
        "over the years. But fire withers BLOOM, frost nips it, wind strips it, "
        "and SWARM and VENOM feed on it. BLOOM kin shrug off TIDE, SPARK, STONE "
        "and each other.\n\n"
        "STONE kin pump on strain in rock. Some crystals, like quartz, turn "
        "squeezing into electric charge, and STONE kernels drink that charge "
        "whenever the ground shifts, settles or is trodden on. STONE moves "
        "smother BLAZE, ground SPARK, crack FROST and bury VENOM. Water wears "
        "STONE down, roots split it, and FROST and BRAWL break it.\n\n"
        "REAL SCIENCE: squeezing quartz really does make electricity. It's called "
        "piezoelectricity, and quartz watches and gas-stove lighters use it.\n\n"
        "VALE ONLY: kin that feed on it.",
        "Mind the seedlings. Slow down, young one. A garden teaches patience.\f"
        "See that MOSSHELL on the path? It's working, believe it or not. Soaking "
        "up the sun. Let me explain." },

    [LORE_TYPE_GALE_SWARM] = { LCH_TYPES, LSRC_KITEFLYER, "GALE AND SWARM",
        "GALE kin pump on moving air: gusts, updrafts, the slow swell and sag of "
        "air pressure. A PUFFOWL puffs up to twice its size partly to catch more "
        "of it.\n\n"
        "GALE moves blow away SWARM, strip BLOOM and knock BRAWL kin clean off "
        "their feet. SPARK and STONE kin shrug them off, and GALE kin fear SPARK "
        "and FROST.\n\n"
        "SWARM kin are different: instead of one big kernel, a SWARM kin has "
        "hundreds of tiny ones. Alone, each is faint. But when they flash in "
        "perfect step, their light adds up far faster than you'd expect: twice "
        "as many kernels in step make a flash four times as bright. SKYWISP over "
        "the meadow flash together this way, like one enormous heartbeat of "
        "light.\n\n"
        "SWARM moves feed on BLOOM, pester DREAM and drive off DUSK. BLAZE and "
        "GALE are their bane.\n\n"
        "REAL SCIENCE: this is superradiance. When many emitters share one "
        "rhythm, their light adds in step and bursts out much brighter and "
        "faster than it would from all of them apart.\n\n"
        "VALE ONLY: moths that do it.",
        "Whoo! Feel that gust? Perfect kite weather! Hey, stick around till "
        "dusk, you HAVE to see the SKYWISP.\f"
        "They all flash at once, like the whole meadow blinking! Wind kin, swarm "
        "kin, let me tell you everything!" },

    [LORE_TYPE_FROST] = { LCH_TYPES, LSRC_LAKEKID, "FROST KIN",
        "FROST kin do something that sounds backwards: they pump by getting rid "
        "of heat.\n\n"
        "Here's the trick. A FROST kernel soaks up light of one colour and gives "
        "off light of a slightly bluer colour. Bluer light carries a little more "
        "energy, and the extra comes out of the kernel's own warmth, the "
        "jiggling of its atoms. So every flash carries a bit of heat away, the "
        "kernel gets colder, and the kin chills everything around it. That's why "
        "the ground frosts over wherever a FROSTOAT sleeps.\n\n"
        "FROST moves nip BLOOM, stiffen GALE, crack STONE and even chill mighty "
        "WYRM. But BLAZE melts FROST, and BRAWL and STONE smash it. BLAZE, TIDE "
        "and other FROST kin shrug FROST moves off.\n\n"
        "REAL SCIENCE: this is called anti-Stokes cooling, and it's real! It was "
        "first done in 1995, and since then scientists have used laser light to "
        "chill a crystal colder than minus 170 degrees Celsius this way.\n\n"
        "VALE ONLY: kernels that do it all by themselves.",
        "Brrr! Don't stand so close to my FROSTOAT, it'll freeze your boots! "
        "Know how it stays so cold?\f"
        "It glows the heat away! My big sister told me how. Now I'll tell you!" },

    [LORE_TYPE_VENOM] = { LCH_TYPES, LSRC_FORAGER, "VENOM KIN",
        "VENOM kin pump on the chemical energy of rot and ferment: the slow "
        "burning that happens when fungi and microbes break things down. In the "
        "Vale, some of that energy comes off as cold chemical light, and VENOM "
        "kernels drink it straight in.\n\n"
        "That's why VENOM kin gather on rotting logs and around fallen fruit, and "
        "why a BRAMBLOR's berries are so bitter. VENOM kin are recyclers: without "
        "them, and the fungi they follow, dead leaves would pile up forever.\n\n"
        "VENOM moves foul water, so they strike TIDE hard, and they wilt BLOOM. "
        "But STONE doesn't rot, DUSK doesn't care, and VENOM can't poison VENOM. "
        "VENOM kin shrug off BLOOM, BRAWL, SWARM and other VENOM, but STONE and "
        "DREAM hit them hard.\n\n"
        "A poisoned kin isn't being eaten. Its kernel has picked up impurities "
        "that knock motes out of step, bit by bit, until it's cured.\n\n"
        "REAL SCIENCE: rot is slow chemistry, and much of the world's soil is "
        "built by fungi and microbes breaking down dead things.\n\n"
        "VALE ONLY: kin that feed on it.",
        "Oh, you're back! Smell that? Rotting leaves, wet bark, a hint of "
        "fermenting plum. Glorious!\f"
        "The VENOM kin think so too. Everyone's scared of them. Nobody should "
        "be. Let me tell you why." },

    [LORE_TYPE_DREAM_BRAWL] = { LCH_TYPES, LSRC_HERMIT, "DREAM AND BRAWL",
        "Every living thing hums with electricity. Each heartbeat and each "
        "thought sends faint electric ripples through the body and out into the "
        "air around it.\n\n"
        "DREAM kin pump on that hum. They drink the fields of the minds around "
        "them, so they gather wherever people and kin think, dream and worry. A "
        "HOOTLORD perched over a library isn't reading. It is dining.\n\n"
        "BRAWL kin pump from their own bodies. Bone is a crystal too, and like "
        "quartz it makes a little charge when squeezed. Every punch, kick and "
        "stomp squeezes a BRAWL kin's bones, and its kernel drinks the charge. "
        "The harder it trains, the fuller it gets.\n\n"
        "Mind beats muscle: DREAM outwits BRAWL, shrugs off its blows and calms "
        "VENOM's churning. SWARM and DUSK trouble DREAM. BRAWL breaks BEAST, "
        "FROST, STONE and DUSK, but GALE and DREAM throw it.\n\n"
        "REAL SCIENCE: hearts and nerves really do make electric fields (doctors "
        "measure them), sharks can sense them, and bone really is "
        "piezoelectric.\n\n"
        "VALE ONLY: kin that feed on them.",
        "The owl on my roof is listening to you think. Does that trouble you? It "
        "shouldn't. It's only eating.\f"
        "And these old fists? They ate too, once. Mind and muscle, little "
        "warden. Two hungers. Sit." },

    [LORE_TYPE_DUSK] = { LCH_TYPES, LSRC_WOODWARD, "DUSK KIN",
        "DUSK kin are broadband absorbers. Where other kernels drink one narrow "
        "band, a DUSK kernel drinks every colour at once, even the faint light of "
        "stars on a moonless night. That's why DUSK kin look darker than the "
        "shadows around them: almost no light bounces back off them.\n\n"
        "In Bramblewood, WISPIRE drift through the hollows at dusk, and the "
        "darker the night, the livelier they get.\n\n"
        "DUSK moves bite back at BLAZE, muddle DREAM and strike other DUSK kin "
        "hard, since two light-eaters feed on each other. But a lit lantern "
        "banishes DUSK, BRAWL scatters it, and SWARM kin, flashing in step, cut "
        "straight through it. And BEAST and DUSK can't touch each other at "
        "all.\n\n"
        "REAL SCIENCE: some materials really are that dark. Coatings made of "
        "tiny carbon tubes swallow more than 99.9 percent of light, and some "
        "birds and deep-sea fish have feathers or skin nearly as black.\n\n"
        "VALE ONLY: kin that feed on starlight.",
        "Quiet now. See that patch of dark under the fern, darker than it ought "
        "to be? Don't point. That's a kin.\f"
        "DUSK kin drink the light. Even starlight. I've watched them thirty "
        "years, and they still give me shivers." },

    [LORE_TYPE_WYRM] = { LCH_TYPES, LSRC_ELDER, "WYRM KIN",
        "WYRM is the oldest and rarest type. A WYRM kernel is enormous, and a "
        "kernel that big stops pumping from any one thing. It couples to whole "
        "weather systems: the warm rising air of a summer afternoon, the "
        "pressure of a front rolling in, the charge of a thunderhead.\n\n"
        "That makes WYRM kin very hard to trouble. BLAZE, TIDE, BLOOM and SPARK "
        "moves are mostly shrugged off, the way a river doesn't mind a cup of "
        "water. Only two things hit a WYRM hard. FROST, because storms feed on "
        "warm, rising air, and cold starves them. And another WYRM, because only "
        "a field that vast can shake one. Nothing shrugs off a WYRM's own "
        "blows.\n\n"
        "A few kin can grow into WYRM if they grow long enough: the humble "
        "AQUAPO becomes TIDALOTL, the river drake of the old songs. And above "
        "them all is DRAKORA, the Stormwyrm.\n\n"
        "REAL SCIENCE: thunderstorms really are fed by warm, moist air rising, "
        "and cold, stable air stops them from forming.\n\n"
        "VALE ONLY: kin as big as the weather.",
        "You've heard the children's tales of dragons. Most of it is nonsense, "
        "mind. But not all of it.\f"
        "There is a type of kin older than any other: the WYRM. Sit, and I'll "
        "tell you what the Almanac says." },

    /* ============================================================ */
    /*  GROWTH                                                      */
    /* ============================================================ */

    [LORE_GROWING] = { LCH_GROWTH, LSRC_KEEPER, "GROWING",
        "Every time a kin pumps and then spills its surplus in a bout, a few more "
        "layers of crystal settle onto its kernel, like rings in a tree trunk. "
        "Slowly, the kernel gets bigger.\n\n"
        "Then, past a critical size, something sudden happens. The kernel's inner "
        "pattern rearranges all at once into a new, more complex symmetry, the "
        "way water turns to ice at one exact temperature. The condensate "
        "re-forms in the new pattern, and the body re-forms around it in a "
        "bigger shape. The kin grows!\n\n"
        "Most kin grow at a certain level: FLARIX, AQUAPO and DANDELAMB at 16 "
        "and again at 34, NIBBIT at 18, PUFFOWL at 20, ZAPPET at 22, CINDERUB at "
        "24, GOLEMIT at 25 and MOSSHELL at 26. A few can't cross the critical "
        "point on their own and need a shard instead.\n\n"
        "REAL SCIENCE: a sudden change of pattern at a critical point is called a "
        "phase transition. Freezing, boiling and a magnet losing its pull when "
        "heated are all phase transitions.\n\n"
        "VALE ONLY: kin that grow this way.",
        "Your kin will grow one day, you know. It can be startling the first "
        "time: a flash, and suddenly it's bigger!\f"
        "There's no need to be alarmed. It's a phase transition, the same thing "
        "that happens when water freezes. Let me explain." },

    [LORE_SHARDS] = { LCH_GROWTH, LSRC_GARDENER, "SHARDS",
        "Some kin can't cross their critical point on their own. Their kernels "
        "grow and grow, ready to change, but the new pattern never quite gets "
        "started. They need a nudge.\n\n"
        "A shard is that nudge: a seed crystal that already has the new "
        "symmetry. Touch it to a ready kernel and the change sweeps through the "
        "whole crystal at once, the way a speck of ice dropped into supercooled "
        "water freezes it solid in a heartbeat.\n\n"
        "There are four kinds. A BLOOM SHARD makes THORNIP grow into BRAMBLOR. A "
        "SPARK SHARD makes VOLTUX grow into VOLTLOPE. A DUSK SHARD makes SKYWISP "
        "grow into LUMOTH. A FROST SHARD makes BUBBLIN grow into GLACIBLOB, "
        "freezing it from the kernel out.\n\n"
        "Shards turn up in odd places: riverbeds, under old roots, and in flower "
        "beds that have seen plenty of bouts.\n\n"
        "REAL SCIENCE: starting a change from a seed is called nucleation. It's "
        "how hailstones, snowflakes and rock candy form.\n\n"
        "VALE ONLY: shards, and the kin they change.",
        "Found another shard in the tulip bed this morning. The soil here's seen "
        "a lot of bouts, you see.\f"
        "They're seeds, really. Not for plants. For kin. Let me explain what I "
        "mean." },

    [LORE_SUPERCOOLED] = { LCH_GROWTH, LSRC_LAKEKID, "SUPERCOOLED",
        "Water doesn't always freeze at zero degrees! Very still, very clean "
        "water can be cooled well below freezing and still stay liquid. That's "
        "called supercooled water.\n\n"
        "It stays liquid because ice has to start somewhere. The first few water "
        "molecules have to line up into the ice pattern by chance, and in still, "
        "clean water that's surprisingly hard. But give it a speck of dust, a "
        "scratch, a sharp tap or a tiny crystal of ice, and the pattern has a "
        "place to start. Then the ice races through the whole bottle in "
        "seconds.\n\n"
        "The lake kids bury bottles of clean water in the snow overnight, then "
        "tap them in the morning to watch them freeze. It's just like a kin and "
        "a shard: the kernel is ready to change, and the shard gives the change "
        "a place to start.\n\n"
        "REAL SCIENCE: all true! Tiny cloud droplets can stay liquid down to "
        "about minus 40 degrees Celsius, and snowflakes start on specks of dust. "
        "You can try the bottle trick with a freezer, with a grown-up's help.\n\n"
        "VALE ONLY: the kin part.",
        "Wanna see a magic trick? This bottle was in the snow all night and it's "
        "STILL water! Now watch...\f"
        "*tap* WHOOSH! Ice! Ha! It's not magic, though. It's called "
        "supercooling. Here's how it works!" },

    [LORE_GROWTH_PAPER] = { LCH_GROWTH, LSRC_BOOK_STATION, "A PAPER ON GROWTH",
        "A printed paper from the field station shelf, well thumbed. Its summary "
        "reads:\n\n"
        "\"ON THE GROWTH OF KIN KERNELS AS A NUCLEATED PHASE TRANSITION. Vass and "
        "the staff of the Mirror Lake Field Station.\n\n"
        "We followed 41 wild and warden-raised kin for three seasons, measuring "
        "the colour and width of the light leaking from each kernel. As kernels "
        "thickened, their light shifted slowly and smoothly. At growth, the "
        "pattern changed in a fraction of a second, with a bright flash carrying "
        "away the extra energy, as expected for a sudden change of symmetry.\n\n"
        "Kernels just below their growth point were metastable: ready to change, "
        "but waiting for a seed. A shard of matching symmetry triggered growth "
        "in every case tested (12 of 12). Shards of other symmetries did "
        "nothing.\n\n"
        "We conclude that growth is a nucleated phase transition of the kernel. "
        "Why some kinds of kin need a shard and others do not remains "
        "unknown.\"\n\n"
        "In the margin, in green ink: \"Ask the gardener where they find them!!\"",
        "A stack of printed papers sits on the station shelf. One is covered in "
        "green ink and exclamation marks.\f"
        "It's titled ON THE GROWTH OF KIN KERNELS. You read the summary." },

    /* ============================================================ */
    /*  WEATHER                                                     */
    /* ============================================================ */

    [LORE_RAIN] = { LCH_WEATHER, LSRC_SHEPHERD, "A BUCKET OF RAIN",
        "Farmers in the Vale have a saying: every bout is a bucket of rain.\n\n"
        "They mean it almost literally. When a blow scatters motes out of a "
        "kin's condensate, the loose energy doesn't vanish. It leaves as a little "
        "heat, a little light, and a spray of ions: bits of air with an electric "
        "charge. Charged specks are just what water vapour needs to gather on. "
        "Tiny droplets form around them, grow into clouds, and the clouds give "
        "gentle rain.\n\n"
        "So a meadow where kin bout often is a green meadow. The Shepherd's "
        "PUFFLEECE bout each other every evening in the long grass, and the grass "
        "grows back twice as thick.\n\n"
        "When nobody bouts, the energy stays pooled in brimming kin until it all "
        "comes out at once: a heat wave, a hailstorm, a flood.\n\n"
        "REAL SCIENCE: every raindrop starts on a tiny speck of dust, salt or "
        "soot. In a cloud chamber, droplets really do form on ions, and in the "
        "sky ions help such specks form.\n\n"
        "VALE ONLY: bouts as a way of making rain.",
        "Aye. You'll be the new warden. Mind the flock, they'll want a bout off "
        "you.\f"
        "Let 'em. Every bout's a bucket of rain, as my father said. And his "
        "father. Sit a while." },

    [LORE_LIGHTNING] = { LCH_WEATHER, LSRC_GARDENER, "LIGHTNING'S GIFT",
        "Plants need nitrogen to grow, and the air is almost four-fifths "
        "nitrogen. But plants can't use it straight from the air. Nitrogen gas "
        "is pairs of atoms clinging together so tightly that almost nothing can "
        "pull them apart.\n\n"
        "Lightning can. A bolt heats the air around it hotter than the surface "
        "of the sun, tearing nitrogen apart so it joins with oxygen. Rain washes "
        "it into the soil as a natural fertiliser.\n\n"
        "SPARK kin do the same in every bout, only smaller: every crackle and "
        "snap fixes a pinch of nitrogen. Add the warmth and rain from other "
        "bouts, and fields where kin bout often are the richest in the Vale. The "
        "gardener invites wardens to bout between the vegetable rows.\n\n"
        "REAL SCIENCE: lightning fixes millions of tonnes of nitrogen every year "
        "around the world. Some soil bacteria can fix nitrogen too.\n\n"
        "VALE ONLY: SPARK kin doing it on purpose.",
        "Storm last week, did you notice? Everything's twice as green today. "
        "That's no accident.\f"
        "Lightning feeds the soil. And a SPARK kin's bout is a little bit of "
        "lightning. Let me show you." },

    [LORE_PRESSURE] = { LCH_WEATHER, LSRC_KITEFLYER, "HIGH AND LOW",
        "Air has weight. The whole sky presses down on you all the time, and that "
        "press is called air pressure. It isn't the same everywhere. Where the "
        "sun warms the ground, air rises and leaves lower pressure behind. Where "
        "air cools, it sinks and piles up into higher pressure.\n\n"
        "Wind is air rushing from high pressure towards low, trying to even "
        "things out. The bigger the difference, the harder it blows. That's why "
        "the meadow gets gusty in the afternoon, after the sun has had all "
        "morning to warm the ground.\n\n"
        "GALE kin feel every change. When the pressure drops fast, a storm is "
        "coming: PUFFOWL fluff up and ZAPPET start to crackle. The kite flyer "
        "reads them like a weather vane.\n\n"
        "And lately? The pressure over the Stormstone has been dropping for "
        "weeks, but no storm ever breaks. Something big is holding it in.\n\n"
        "REAL SCIENCE: wind blows from high pressure to low, and a falling "
        "barometer means stormy weather is on its way.\n\n"
        "VALE ONLY: kin that feed on it, and a sky that holds in a storm.",
        "Feel the string tug? That's the sky pushing! Air's heavy, y'know. It "
        "presses on every bit of you, all the time.\f"
        "And when it pushes unevenly, you get wind! Best thing in the world. "
        "Let me explain!" },

    [LORE_STORM_SIGNS] = { LCH_WEATHER, LSRC_BOOK_CABIN, "HERMIT'S JOURNAL",
        "A journal lies open on the Hermit's table, the ink smudged. The latest "
        "pages read:\n\n"
        "\"Day 3. HOOTLORD did not hunt. Sat on the roof facing north all "
        "night.\n\n"
        "Day 9. NIBBIT moved its hoard deeper under the floor. It does this "
        "before hard winters. It is not winter.\n\n"
        "Day 14. Barometer low again. No rain. The air tastes of metal. My knees "
        "say storm. The sky says nothing.\n\n"
        "Day 20. LUMOTH will not settle. Dreamed of wind all night. Not my "
        "dream, I think. Something in the north is dreaming very loudly.\n\n"
        "Day 26. The kin know. They always know first. Someone should climb the "
        "Stormstone. Too old. Perhaps this year's Kindling.\"\n\n"
        "Below, a scrawl: \"Don't write that down. They'll say you're a "
        "crank.\"\n\n"
        "REAL SCIENCE: animals really can sense storms coming. In 2014, "
        "songbirds were tracked fleeing a huge storm a day before it arrived, "
        "probably warned by sounds too low for people to hear.",
        "A worn journal lies open on the table, a pencil stuck in its spine. The "
        "Hermit pretends not to see you reading it.\f"
        "The last pages are all about the weather." },

    [LORE_CLEAR_SKIES] = { LCH_WEATHER, LSRC_STORY, "CLEAR SKIES",
        "You answered DRAKORA's challenge on the Stormstone, and the storm it had "
        "carried for a hundred years spilled harmlessly into the Vale.\n\n"
        "It came down the way a bout's energy always does: as warm rain on the "
        "fields, as crackles of lightning that fed the soil, as a wind that blew "
        "itself out over the meadow. By evening the clouds had broken, and the "
        "Vale saw a bright sky for the first time in weeks.\n\n"
        "Nothing drowned. Nothing burned. The old bargain held, because somebody "
        "climbed the hill and answered.\n\n"
        "The village has been celebrating ever since. Keeper Linden has one more "
        "request: finish the ALMANAC. There are still kin out there you haven't "
        "met, and every one of them has a story.",
        0 },

    /* ============================================================ */
    /*  LEGENDS                                                     */
    /* ============================================================ */

    [LORE_BURNING_YEARS] = { LCH_LEGENDS, LSRC_ELDER, "THE BURNING YEARS",
        "Before the Kinship, nobody guided the bouts. People feared kin and kept "
        "away from them, and kin that met no challengers had nowhere to spill "
        "their surplus.\n\n"
        "So it pooled. Summers came as heat waves, when brimming BLAZE kin set "
        "whole hillsides alight. Springs came as floods. Winters froze the "
        "rivers solid in a single night. The Almanac calls those centuries the "
        "burning years, and its oldest pages are full of lost harvests and "
        "burned villages.\n\n"
        "Nobody knows for certain who held the first bout. The Elder's favourite "
        "version is that it was a shepherd's child, who saw two brimming kin "
        "tussling in a field and noticed that afterwards the air was cooler and "
        "the grass was wet. So the child set their own kin to play with a "
        "brimming stranger, and that night the rain fell soft.\n\n"
        "Word spread. People learned that kin need not be feared, only answered. "
        "And then someone made the first lantern, and that changed everything.",
        "You young ones have never seen a bad summer. Not a truly bad one. Be "
        "glad of it.\f"
        "There was a time when every summer was a bad one. The burning years, "
        "we call them. Listen." },

    [LORE_DROWNED_VALLEYS] = { LCH_LEGENDS, LSRC_ELDER, "DROWNED VALLEYS",
        "The worst of the burning years came at their very end, when DRAKORA, "
        "the Stormwyrm, brimmed.\n\n"
        "The Almanac says the sky grumbled for weeks. Thunder with no rain. Wind "
        "with no cloud. Then the storm broke all at once, and it rained for a "
        "whole season. The rivers rose and kept rising. Three valleys north of "
        "the Stormstone filled up like bowls, farms and villages and all, and "
        "they are long, deep lakes to this day.\n\n"
        "The people who were left climbed to the Stormstone with every kin they "
        "had and answered DRAKORA together. The bout lasted from dawn to dusk. "
        "When it ended, the rain stopped.\n\n"
        "That was when the Kinship was sworn, at the Old Hearth, by the first "
        "wardens: soaked to the skin and determined that it would never happen "
        "again. From then on, wardens climbed the Stormstone whenever the sky "
        "grumbled.\n\n"
        "The last time anyone did was a hundred years ago.",
        "Have you ever wondered why the Kinship was sworn here, in our little "
        "village? It wasn't chance.\f"
        "It was a flood. The worst the Vale ever saw. The Almanac remembers it, "
        "and so do these stones." },

    [LORE_DRAKORA] = { LCH_LEGENDS, LSRC_ELDER, "DRAKORA",
        "DRAKORA, the Stormwyrm, is the oldest kin anyone knows of. Its kernel "
        "has been growing for centuries and is so vast that it feels the whole "
        "sky. When DRAKORA brims, the heavens brim with it.\n\n"
        "It lives far above the clouds in the north and comes down only when it "
        "is full, to the standing stones at the top of Whisper Meadow, to ask for "
        "a bout. For generations wardens answered it there, and the storms it "
        "carried spilled away as good rain.\n\n"
        "But a hundred years have passed since anyone answered DRAKORA. Nobody "
        "knows why it stayed away so long. Perhaps a kernel that size takes a "
        "century to fill. In that time the village forgot, and children were "
        "told DRAKORA was only a story.\n\n"
        "Now the sky grumbles again, and the Almanac says that is how it began "
        "last time. DRAKORA is brimming with a hundred years of storm: enough to "
        "drown the whole Vale.\n\n"
        "Somebody must answer it.",
        "Hear that? Thunder, and not a cloud in the sky. It has been like that "
        "for weeks.\f"
        "I am old enough to be frightened by it. Let me tell you about DRAKORA, "
        "and why the Keeper looks so worried." },

    [LORE_FIRST_OATH] = { LCH_LEGENDS, LSRC_STORMSTONE, "THE FIRST OATH",
        "Words carved deep into the tallest standing stone, worn soft by "
        "centuries of wind:\n\n"
        "\"HERE THE SKY CAME DOWN, AND HERE WE ANSWERED IT.\n\n"
        "WE WHO LIVED SWEAR FOR ALL WHO COME AFTER:\n\n"
        "WE WILL NOT FEAR THE KIN.\n"
        "WE WILL ANSWER THE BRIMMING.\n"
        "WE WILL NAME THEM, FEED THEM, AND GIVE THEM REST.\n"
        "WE WILL STOP WHEN THEY SLEEP.\n"
        "WE WILL NEVER CAGE WHAT CHOOSES.\n\n"
        "AND THE KIN, IN THEIR TURN, WILL SHARE THEIR STRENGTH, AND SPILL THEIR "
        "STORMS INTO OUR BOUTS AND NOT OUR HOMES.\n\n"
        "THIS IS THE KINSHIP. KEEP IT, OR DROWN.\"\n\n"
        "Below, dozens of names are scratched in smaller letters, some so old "
        "they can barely be read. The newest is a hundred years old.",
        "The tallest stone on the hilltop is covered in carvings. The letters "
        "are old, but deep.\f"
        "You brush away the lichen and read." },

    [LORE_SKIES_GRUMBLE] = { LCH_LEGENDS, LSRC_STORMSTONE, "WHEN SKIES GRUMBLE",
        "On the north face of the stone, looking out over the clouds, is a second "
        "carving:\n\n"
        "\"WARDEN, IF YOU READ THIS, LOOK UP.\n\n"
        "WHEN THE SKY GRUMBLES WITHOUT RAIN, THE WYRM IS FULL.\n"
        "WHEN THE WIND BLOWS WITHOUT CLOUD, THE WYRM IS FULL.\n"
        "WHEN THE KIN WILL NOT SLEEP, THE WYRM IS COMING.\n\n"
        "DO NOT HIDE. HIDING DROWNED THE VALLEYS.\n\n"
        "BRING YOUR KIN TO THIS STONE AND WAIT. THE WYRM WILL COME DOWN AND ASK. "
        "ANSWER IT WITH ALL YOUR HEART, AND IT WILL SPILL ITS STORM INTO THE "
        "BOUT.\n\n"
        "IT IS NOT ANGRY. IT IS FULL. IT HAS BEEN WAITING FOR YOU.\"\n\n"
        "This carving is newer than the oath, as if someone added it later, "
        "afraid that people would forget. They were right to be afraid.",
        "The north face of the stone has a second carving, facing out over the "
        "clouds.\f"
        "This one looks newer, and more hurried." },

    [LORE_MARSH_LIGHTS] = { LCH_LEGENDS, LSRC_WOODWARD, "MARSH LIGHTS",
        "On damp nights, lights drift over the wet hollows of Bramblewood: pale, "
        "flickering, always just out of reach. Walk towards one and it drifts "
        "away. Stop, and it waits for you.\n\n"
        "They are WISPIRE. Old stories argue about them. Some say they guide lost "
        "travellers home to the nearest hearth. Others say they lead people in "
        "circles for fun. The Woodward thinks both are true, depending on the "
        "WISPIRE, and on how rude the traveller has been.\n\n"
        "WISPIRE are DUSK kin, and yet they glow. The Woodward's guess is that "
        "they drink the dark all around them and let a little of it spill out "
        "again as light, the way a full kernel brims. Nobody has studied one "
        "closely enough to know. They don't like being studied.\n\n"
        "REAL SCIENCE: flickering marsh lights, called will-o'-the-wisps, have "
        "been reported for centuries. Scientists suspect marsh gases catching "
        "fire by themselves, but nobody has ever caught one to prove it.\n\n"
        "VALE ONLY: WISPIRE.",
        "If you're out late, you'll see lights over the hollows. Don't follow "
        "them. Or do, but be polite.\f"
        "Those are WISPIRE. Travellers have told tales of them for as long as "
        "there have been travellers." },

    [LORE_RIVER_DRAKE] = { LCH_LEGENDS, LSRC_FISHER, "THE RIVER DRAKE",
        "Long ago, the river towns below Mirror Lake had a custom. Every spring, "
        "when the snowmelt came down and the rivers ran high, the whole town "
        "would walk down to the water at dusk and sing.\n\n"
        "They sang to TIDALOTL, the river drake: a great WYRM of the water with "
        "a crown of pink gill-frills. The songs asked it to let the floods pass "
        "gently. And it seems TIDALOTL listened. Its gill-crown drank the charge "
        "and churn of the flood, and the water rose soft and fell soft.\n\n"
        "Did the songs matter? The Fisher thinks so. A TIDALOTL is a kin like any "
        "other, and kin like company, and a riverbank full of singing people is "
        "the friendliest thing in the world.\n\n"
        "The songs are mostly forgotten now. The Fisher still hums one on the "
        "dock in spring. It has no words left, only a tune, but the AQUAPO in "
        "the reeds always come to listen.\n\n"
        "And every so often a warden's AQUAPO grows all the way into a TIDALOTL, "
        "and the old songs come true again.",
        "Hear me humming? Old habit. My grandmother's tune. It had words once, "
        "long ago.\f"
        "It was a song for the river drake. Want to hear the story? The fish "
        "won't mind." },

    [LORE_STORM_RHYME] = { LCH_LEGENDS, LSRC_GRAN, "THE STORM RHYME",
        "Gran used to sing this at bedtime when the thunder rolled. Every child "
        "in Maple Village knows it:\n\n"
        "\"Grumble, grumble, sky so full,\n"
        "Who will climb the hill?\n"
        "Not the baker, not the mill,\n"
        "The warden with the will.\n\n"
        "Lantern lit and kin beside,\n"
        "Up the Stormstone stair,\n"
        "Ask the wyrm to have a bout\n"
        "And spill its storm up there.\n\n"
        "Rain comes softly, soil comes warm,\n"
        "The valleys stay in green.\n"
        "Sleep now, little warden-to-be,\n"
        "The sky is kind and clean.\"\n\n"
        "Gran says it's only a lullaby. But she has been humming it rather a lot "
        "these past few weeks, and looking out of the window while she does.",
        "Thunder again, sweetpea? Come here. Do you remember the rhyme I sang "
        "you when you were little?\f"
        "No? Oh, you must! Everyone in the village knows it. Here, I'll sing it. "
        "Don't laugh." },

    [LORE_LAST_ANSWER] = { LCH_LEGENDS, LSRC_BOOK_ALMANAC, "THE LAST ANSWER",
        "A very old page of the ALMANAC, in faded brown ink. The Keeper has "
        "marked it with a red ribbon:\n\n"
        "\"Late summer. The sky has grumbled for five weeks. Thunder without "
        "rain; the barometer low and falling. Wild kin restless everywhere and "
        "brimming early. The owl of the Almanac House has not slept.\n\n"
        "The elders agree: the Wyrm is full. We have sent for a warden.\n\n"
        "Sixth week. The warden climbed the Stormstone at dawn with a team of "
        "six. The Wyrm came down at noon. The whole village watched the hilltop "
        "flash and roar until evening.\n\n"
        "At dusk it rained, gently, for three days. Every field in the valley "
        "has come up green. The Wyrm has gone back into the north.\n\n"
        "Note for the next Keeper: it came when the sky grumbled. It will come "
        "again. Do not let the village forget.\"\n\n"
        "The next entry about DRAKORA in the Almanac is the one Keeper Linden "
        "wrote this month.",
        "One volume of the ALMANAC is far older than the rest, with a red ribbon "
        "marking a page.\f"
        "It falls open at the ribbon by itself, as if someone has read this page "
        "many times lately." },

    /* ============================================================ */
    /*  PLACES                                                      */
    /* ============================================================ */

    [LORE_MAPLE_VILLAGE] = { LCH_PLACES, LSRC_BAKER, "MAPLE VILLAGE",
        "Maple Village is a farming village at the south end of the Vale, and it "
        "has lived alongside kin for as long as there has been a Kinship. It was "
        "sworn right here, at the Old Hearth in the plaza.\n\n"
        "Kin are part of daily life. A CINDERUB keeps the bakery oven warm. "
        "DANDELAMB nap in the orchards, and the grass grows back thick wherever "
        "they've slept. NIBBIT pinch buttons, and everybody knows to check the "
        "nearest NIBBIT's bundle before blaming a neighbour.\n\n"
        "In the evenings, wardens hold friendly bouts in the Bout Ring and half "
        "the village comes to watch with a slice of pie. The Almanac House keeps "
        "the records, the Hearth Hall keeps the kin rested, and the shop keeps "
        "everyone in tonics and lanterns.\n\n"
        "North of the village lies Whisper Meadow, east lies Bramblewood, and "
        "west lies Mirror Lake. The Baker says every road out of Maple Village is "
        "a good one, as long as you come back for supper.",
        "Settling in, hon? It's a good village, this. Best in the Vale, and I'm "
        "not only saying that because of my pies.\f"
        "Well. Partly because of my pies. Let me tell you about the place." },

    [LORE_HEARTHS] = { LCH_PLACES, LSRC_TENDER, "HEARTHS",
        "Long before there were villages, people gathered around fires. In the "
        "Vale they had one more reason to: the kin came too.\n\n"
        "The Old Hearth in the plaza is a great ring of warm stone, polished "
        "mirror-plates and firelight. It is a broadband resonator: it holds and "
        "bounces light and warmth of every kind, so it pumps every kernel near "
        "it, whatever the kin's type. Kin curled up around it, people came for "
        "the kin, and the village grew up around the stone. The first wardens "
        "swore the Kinship beside it.\n\n"
        "Every Hearth Hall since is built on the same idea, only smaller and "
        "tidier. Rest your team with the Tender, and the hall's hearth pumps "
        "every kernel back to full: it wakes dozing kin, refills every move and "
        "settles every status problem.\n\n"
        "A flame emblem hangs over every Hearth Hall door in the Vale. Wherever "
        "you see it, you're welcome.",
        "Warm your hands by the hearth, dear. You'll notice your kin perk right "
        "up too. They always do.\f"
        "Do you know why? It's rather a lovely story, actually. Sit." },

    [LORE_BOUT_RING] = { LCH_PLACES, LSRC_STORY, "THE BOUT RING",
        "The Bout Ring in Maple Village is a circle of packed earth ringed by low "
        "stone seats, run by WARDEN MARLO. Wardens come from all over the Vale "
        "to test their teams here, and half the village turns up in the evenings "
        "to cheer.\n\n"
        "A bout in the Ring follows the warden's code like any other: answer, "
        "stop when a kin dozes, rest your team afterwards. Marlo is loud about "
        "the code, and louder about everything else.\n\n"
        "Beat Marlo and you earn the RING SASH, which tells everyone in the Vale "
        "you can hold your own with any kin. Keeper Linden says only a warden "
        "wearing the sash should even think of climbing the Stormstone.\n\n"
        "After so many bouts, the earth of the Ring is the richest soil in the "
        "village. The gardener has asked more than once to plant beans in it. "
        "Marlo said no.",
        0 },

    [LORE_STORMSTONE_RISE] = { LCH_PLACES, LSRC_STORY, "STORMSTONE RISE",
        "Stormstone Rise is the hilltop at the very top of Whisper Meadow, where "
        "the land runs out and the sky begins. A ring of standing stones crowns "
        "it, and the tallest is carved with the Kinship's first oath.\n\n"
        "The stones are older than anyone can count. Dr. Vass thinks they are "
        "rich in quartz and were chosen because they crackle with charge when "
        "the ground shifts. The Elder says that is a very modern way of saying "
        "they're magic.\n\n"
        "Few people climb up here now. VOLTUX and ZAPPET graze the thin grass, "
        "charged up by the endless wind. When the sky is full, this is where "
        "DRAKORA comes down.\n\n"
        "The Keeper sent you here with the RING SASH around your shoulders. Look "
        "up. Something is coming.",
        0 },

    [LORE_ALMANAC] = { LCH_PLACES, LSRC_BOOK_ALMANAC, "THE ALMANAC",
        "The ALMANAC is the record Maple Village has kept since the Kinship was "
        "sworn: every kin anyone has met, every season and every storm. The "
        "oldest volumes are copies of pages older still, some so brittle they "
        "are kept in boxes.\n\n"
        "The Almanac House is where the record lives, along with the Keeper who "
        "looks after it. Keepers are chosen for patience, not strength. Their "
        "job is to watch, measure and write things down, year after year, so the "
        "village never forgets what the weather and the kin have taught it.\n\n"
        "Every warden carries a pocket ALMANAC too. Yours lists every kin you "
        "have met, and marks every kin you have befriended. When it is complete, "
        "the Keeper will copy your pages into the great record, and your name "
        "will be in it for good.\n\n"
        "The Almanac has one rule, written on the first page of the first "
        "volume: \"Write it down. Especially if it frightens you.\"",
        "The Almanac House shelves hold dozens of volumes of the ALMANAC. The "
        "first one is so old its covers are wood.\f"
        "A slip in the front, in the Keeper's neat hand, says: FOR NEW WARDENS. "
        "READ ME." },

    [LORE_WHISPER_MEADOW] = { LCH_PLACES, LSRC_SHEPHERD, "WHISPER MEADOW",
        "North of Maple Village the land opens into Whisper Meadow: long grass, "
        "wildflowers, low ledges and a wind that never quite stops. The meadow "
        "is named for that wind, which hisses through the grass day and "
        "night.\n\n"
        "The Shepherd has grazed PUFFLEECE here for a lifetime. DANDELAMB nap in "
        "the sun, PUFFOWL hunt at dusk, ZAPPET crackle on dry days, VOLTUX dart "
        "through the grass and NIBBIT raid everyone's lunch. Near sunset, "
        "SKYWISP rise in drifting clouds.\n\n"
        "At the top of the meadow the path climbs to STORMSTONE RISE, a "
        "windswept hilltop ringed with standing stones. Shepherds don't take "
        "their flocks up there. The Shepherd says the sheep won't go, and sheep "
        "know things.\n\n"
        "The meadow's wardens challenge anyone who walks into their sight. It's "
        "a friendly place, but a busy one.",
        "Hear that? The hiss in the grass. That's the meadow whispering. Been "
        "doing it since before my granddad's day.\f"
        "Aye, and louder lately. You'll want to know the lay of the land." },

    [LORE_BRAMBLEWOOD] = { LCH_PLACES, LSRC_WOODWARD, "BRAMBLEWOOD",
        "East of Maple Village lies Bramblewood: old trees, thick undergrowth, "
        "mossy logs, mushrooms and a cold creek winding through the middle.\n\n"
        "A forest is a circle, and the Woodward knows every turn of it. Leaves "
        "fall and rot. Fungi and VENOM kin turn the rot into soil. THORNIP and "
        "MOSSHELL grow fat on that soil. CINDERUB warm themselves in sunny "
        "clearings, and FLARIX slip between the trunks with their ember tails. "
        "At dusk SKYWISP flicker between the branches and WISPIRE drift over the "
        "hollows. NIBBIT raid the lot.\n\n"
        "Every kin has its part. Bouts in the wood keep the undergrowth damp and "
        "the soil warm, and a forest where kin bout often almost never "
        "burns.\n\n"
        "Deep in the wood, in a cabin with an owl on the roof, lives the Hermit. "
        "Visitors are welcome, in the sense that he doesn't chase them off.",
        "Mind where you step. This wood is older than the village, and it keeps "
        "its own counsel.\f"
        "But you seem the careful sort. I'll tell you how it all fits together." },

    [LORE_MIRROR_LAKE] = { LCH_PLACES, LSRC_FISHER, "MIRROR LAKE",
        "West of Maple Village lies Mirror Lake, so still on calm mornings that "
        "it doubles the sky. Reeds line the shore, old docks reach out over the "
        "shallows, and on the far bank stands the field station, where DR. VASS "
        "studies kin with more instruments than anyone in the Vale has ever seen "
        "in one room.\n\n"
        "AQUAPO smile in the reeds. BUBBLIN bob in the shallows and burst into "
        "droplets when startled. GOLEMIT sun themselves on the rocks. FROSTOAT "
        "leave frosty prints on the dock at dawn. ZAPPET and PUFFOWL come down "
        "to drink.\n\n"
        "The Fisher has fished here for fifty years and says the lake has moods: "
        "glassy when the kin are content, choppy when they are brimming. Lately "
        "it has been choppy with no wind at all.\n\n"
        "Dr. Vass chose the lake because still water, clear nights and plenty of "
        "kin make it the best place in the Vale to measure a kernel's light. The "
        "Fisher chose it for the trout.",
        "Look at that water. Flat as a plate. You can see the clouds in it, "
        "upside down.\f"
        "That's how the lake got its name. Sit. I'll tell you about it." },
};

/* Shown on a dark storybook screen when a NEW GAME starts, one page at a time. */
static const char *const INTRO_PAGES[] = {
    "Long ago, the people of the Vale feared the kin: wild creatures with a "
    "glowing crystal at their heart, full of living light.",
    "Kin soak up the world's energy: heat, sunlight, rain and wind. When a kin "
    "grows too full, the surplus spills out as fire and flood.",
    "Those were the burning years. Harvests failed and rivers rose. And when "
    "the great Stormwyrm brimmed, three valleys drowned.",
    "Then people learned a secret. When kin bout, their surplus spills away "
    "gently, as warm soil and soft rain. And nobody is hurt.",
    "Someone made the first lantern: a mirror of heartglass where a tired kin "
    "could choose to rest. And people and kin made a promise.",
    "People would guide the bouts and give kin names, food and rest. Kin would "
    "share their strength and keep the seasons kind.",
    "That promise is the Kinship, and those who keep it are wardens. For "
    "centuries it has kept the Vale gentle.",
    "Today is your Kindling, the day you become a warden. But the sky over "
    "Maple Village has been grumbling for weeks...",
    0
};
