/* items/craft.inc -- CRAFT owner: crafted lanterns, dishes, drinks and materials.
 * ITEM_DEF(id, "NAME" (<= 14 chars), pocket, kind, param, price (0 = not sold), icon, "desc") */
ITEM_DEF(ITEM_DUSK_LANTERN, "DUSK LANTERN", POCKET_LANTERNS, IK_LANTERN, 16, 0, ICON_LANTERN,
         "Smoked heartglass. Much better at night and in dark places.")
ITEM_DEF(ITEM_TIDE_LANTERN, "TIDE LANTERN", POCKET_LANTERNS, IK_LANTERN, 16, 0, ICON_PRISM_LANTERN,
         "Sealed against water. Much better on kin met on water.")
ITEM_DEF(ITEM_HEAVY_LANTERN, "HEAVY LANTERN", POCKET_LANTERNS, IK_LANTERN, 16, 0, ICON_STAR_LANTERN,
         "Thick iron-bound glass. Much better on big, heavy kin.")
ITEM_DEF(ITEM_QUICK_LANTERN, "QUICK LANTERN", POCKET_LANTERNS, IK_LANTERN, 16, 0, ICON_LANTERN,
         "Pre-tuned heartglass. Much better on the first turn of a bout.")
ITEM_DEF(ITEM_BONE_LANTERN, "BONE LANTERN", POCKET_LANTERNS, IK_LANTERN, 16, 0, ICON_LANTERN,
         "Frosted with bone meal. Much better on HOLLOW kin.")
ITEM_DEF(ITEM_BERRY_TART, "BERRY TART", POCKET_FOOD, IK_FOOD, 0, 0, ICON_HONEY_DROP,
         "A sweet tart. Your team gets more XP for the next few bouts.")
ITEM_DEF(ITEM_HONEY_BUN, "HONEY BUN", POCKET_FOOD, IK_FOOD, 1, 0, ICON_HONEY_DROP,
         "Soft and golden. Your team heals a little after each bout for a while.")
ITEM_DEF(ITEM_VEGGIE_STEW, "VEGGIE STEW", POCKET_FOOD, IK_FOOD, 2, 0, ICON_HONEY_DROP,
         "Hearty stew. Raises your team's DEFENSE and WILL for the next bouts.")
ITEM_DEF(ITEM_CHILI_POT, "CHILI POT", POCKET_FOOD, IK_FOOD, 3, 0, ICON_HONEY_DROP,
         "Fiery chili. Raises your team's ATTACK and FOCUS for the next bouts.")
ITEM_DEF(ITEM_PUMPKIN_PIE, "PUMPKIN PIE", POCKET_FOOD, IK_FOOD, 4, 0, ICON_HONEY_DROP,
         "Spiced pie. Wild kin are easier to befriend for a while.")
ITEM_DEF(ITEM_MOONCAKE, "MOONCAKE", POCKET_FOOD, IK_FOOD, 5, 0, ICON_HONEY_DROP,
         "A festival cake. Rare kin show themselves more often for a while.")
ITEM_DEF(ITEM_TRUFFLE_RICE, "TRUFFLE RICE", POCKET_FOOD, IK_FOOD, 6, 0, ICON_HONEY_DROP,
         "Rich and earthy. Lots more XP for the next few bouts.")
ITEM_DEF(ITEM_CAMP_SKEWER, "CAMP SKEWER", POCKET_FOOD, IK_FOOD, 7, 0, ICON_HONEY_DROP,
         "Grilled on a campfire. Raises your team's SPEED for the next bouts.")
ITEM_DEF(ITEM_SUN_SALAD, "SUN SALAD", POCKET_FOOD, IK_FOOD, 8, 0, ICON_HONEY_DROP,
         "Crisp greens. Heals your whole team by half.")
ITEM_DEF(ITEM_KERNEL_CANDY, "KERNEL CANDY", POCKET_FOOD, IK_FOOD, 9, 0, ICON_SUNSEED,
         "Crystallised honey and mote dust. One kin grows a level.")
ITEM_DEF(ITEM_BERRY_JUICE, "BERRY JUICE", POCKET_FOOD, IK_FOOD, 10, 0, ICON_GLOW_TONIC,
         "Fresh pressed. Restores 40 HP to one kin.")
ITEM_DEF(ITEM_APPLE_PRESS, "APPLE PRESS", POCKET_FOOD, IK_FOOD, 11, 0, ICON_BRIGHT_TONIC,
         "Cloudy apple juice. Restores 80 HP to one kin.")
ITEM_DEF(ITEM_PEACH_NECTAR, "PEACH NECTAR", POCKET_FOOD, IK_FOOD, 12, 0, ICON_RADIANT_TONIC,
         "Thick peach nectar. Fully restores one kin and its moves.")
ITEM_DEF(ITEM_GLOW_HONEY, "GLOW HONEY", POCKET_MATERIALS, IK_MATERIAL, 0, 120, ICON_HONEY_DROP,
         "Honey from glow-bees. Faintly luminous. Used in cooking and brewing.")
ITEM_DEF(ITEM_HEARTGLASS_SAND, "HEART SAND", POCKET_MATERIALS, IK_MATERIAL, 0, 80, ICON_SUNSEED,
         "Fine crystal sand for making heartglass lanterns.")
ITEM_DEF(ITEM_IRON_ORE, "IRON ORE", POCKET_MATERIALS, IK_MATERIAL, 0, 100, ICON_GUARD_COIL,
         "Rust-red ore. Forged into lantern frames and tools.")
ITEM_DEF(ITEM_COAL, "COAL", POCKET_MATERIALS, IK_MATERIAL, 0, 40, ICON_DUSK_SHARD,
         "Keeps a forge roaring.")
ITEM_DEF(ITEM_BONE_MEAL, "BONE MEAL", POCKET_MATERIALS, IK_MATERIAL, 0, 60, ICON_SUNSEED,
         "Ground bone. Good for soil and for frosting lanterns.")
ITEM_DEF(ITEM_SILK_THREAD, "SILK THREAD", POCKET_MATERIALS, IK_MATERIAL, 0, 90, ICON_TUNING_FORK,
         "Strong spider silk.")
ITEM_DEF(ITEM_SALT, "SALT", POCKET_MATERIALS, IK_MATERIAL, 0, 30, ICON_FROST_SHARD,
         "Sea salt from Port Brine. Every cook needs it.")
ITEM_DEF(ITEM_MINT_LEAF, "MINT LEAF", POCKET_MATERIALS, IK_MATERIAL, 0, 40, ICON_BLOOM_SHARD,
         "A cool, sharp herb for brews and teas.")
ITEM_DEF(ITEM_GLOWCAP, "GLOWCAP", POCKET_MATERIALS, IK_MATERIAL, 0, 70, ICON_BLOOM_SHARD,
         "A mushroom that glows in the dark. Brewers love it.")
ITEM_DEF(ITEM_STARDUST_CHIP, "STARDUST CHIP", POCKET_MATERIALS, IK_MATERIAL, 0, 300, ICON_STAR_LANTERN,
         "A flake of fallen star.")
ITEM_DEF(ITEM_OLD_COIN, "OLD COIN", POCKET_MATERIALS, IK_MATERIAL, 0, 500, ICON_AMP_COIL,
         "An ancient coin. Collectors pay well for it.")
ITEM_DEF(ITEM_COOKBOOK, "COOKBOOK", POCKET_MATERIALS, IK_FOOD, 20, 3000, ICON_RECIPE_BOOK,
         "A well-thumbed cookbook. Read it to learn PUMPKIN PIE, PEACH NECTAR and TRUFFLE RICE.")
ITEM_DEF(ITEM_BREW_NOTES, "BREW NOTES", POCKET_MATERIALS, IK_FOOD, 21, 3500, ICON_RECIPE_BOOK,
         "A brewer's stained notes. Read them to learn REVIVAL BREW and LURE INCENSE.")
ITEM_DEF(ITEM_FORGE_MANUAL, "FORGE MANUAL", POCKET_MATERIALS, IK_FOOD, 22, 3500, ICON_RECIPE_BOOK,
         "A smith's manual. Read it to learn QUICK LANTERN, TUNING FORK and HUSH BELL.")
