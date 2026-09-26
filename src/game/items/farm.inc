/* items/farm.inc -- FARM owner: seeds, saplings, fertilisers, crops and farm gear.
 * ITEM_DEF(id, "NAME" (<= 14 chars), pocket, kind, param, price (0 = not sold), icon, "desc") */
ITEM_DEF(ITEM_SEED_GLOWBERRY, "GLOW SEED", POCKET_FARM, IK_PLANT, 0, 40, ICON_SEED_GLOWBERRY,
         "Grows into a glowberry bush in 3 days. Regrows.")
ITEM_DEF(ITEM_SEED_EMBERBERRY, "EMBER SEED", POCKET_FARM, IK_PLANT, 1, 60, ICON_SEED_EMBERBERRY,
         "Grows into an emberberry bush in 4 days. Regrows.")
ITEM_DEF(ITEM_SEED_TIDEBERRY, "TIDE SEED", POCKET_FARM, IK_PLANT, 2, 60, ICON_SEED_TIDEBERRY,
         "Grows into a tideberry bush in 4 days. Regrows.")
ITEM_DEF(ITEM_SEED_RADISH, "RADISH SEED", POCKET_FARM, IK_PLANT, 3, 20, ICON_SEED_RADISH,
         "Radishes are ready in 2 days.")
ITEM_DEF(ITEM_SEED_CARROT, "CARROT SEED", POCKET_FARM, IK_PLANT, 4, 30, ICON_SEED_CARROT,
         "Carrots are ready in 3 days.")
ITEM_DEF(ITEM_SEED_POTATO, "POTATO SEED", POCKET_FARM, IK_PLANT, 5, 40, ICON_SEED_POTATO,
         "Potatoes are ready in 4 days.")
ITEM_DEF(ITEM_SEED_PUMPKIN, "PUMPKIN SEED", POCKET_FARM, IK_PLANT, 6, 100, ICON_SEED_PUMPKIN,
         "Pumpkins take 7 days but sell well.")
ITEM_DEF(ITEM_SEED_CHILI, "CHILI SEED", POCKET_FARM, IK_PLANT, 7, 60, ICON_SEED_CHILI,
         "Chilies are ready in 4 days. Regrows.")
ITEM_DEF(ITEM_SEED_TOMATO, "TOMATO SEED", POCKET_FARM, IK_PLANT, 8, 50, ICON_SEED_TOMATO,
         "Tomatoes are ready in 5 days. Regrows.")
ITEM_DEF(ITEM_SEED_CORN, "CORN SEED", POCKET_FARM, IK_PLANT, 9, 80, ICON_SEED_CORN,
         "Corn takes 6 days. Regrows.")
ITEM_DEF(ITEM_SEED_SUNFLOWER, "SUNNY SEED", POCKET_FARM, IK_PLANT, 10, 60, ICON_SEED_SUNFLOWER,
         "Sunflowers bloom in 5 days.")
ITEM_DEF(ITEM_SEED_MOTEBLOOM, "MOTE SEED", POCKET_FARM, IK_PLANT, 11, 300, ICON_SEED_MOTEBLOOM,
         "A rare flower that gathers motes. Blooms in 8 days.")
ITEM_DEF(ITEM_SAPLING_APPLE, "APPLE SAPLING", POCKET_FARM, IK_PLANT, 12, 1000, ICON_SAPLING,
         "An apple tree. Fruits every 3 days once grown (12 days).")
ITEM_DEF(ITEM_SAPLING_PEACH, "PEACH SAPLING", POCKET_FARM, IK_PLANT, 13, 1200, ICON_SAPLING,
         "A peach tree. Fruits every 3 days once grown (12 days).")
ITEM_DEF(ITEM_FERTILIZER, "FERTILIZER", POCKET_FARM, IK_FERTILIZER, 0, 50, ICON_FERTILIZER,
         "Basic fertiliser. Crops grow a little faster.")
ITEM_DEF(ITEM_RICH_COMPOST, "RICH COMPOST", POCKET_FARM, IK_FERTILIZER, 1, 120, ICON_RICH_COMPOST,
         "Dark compost. Crops are more often top quality.")
ITEM_DEF(ITEM_GROW_MULCH, "GROW MULCH", POCKET_FARM, IK_FERTILIZER, 2, 150, ICON_GROW_MULCH,
         "Keeps soil damp. Watered soil stays watered for 2 days.")
ITEM_DEF(ITEM_CROP_GLOWBERRY, "GLOWBERRY", POCKET_FARM, IK_CROP, 0, 0, ICON_CROP_GLOWBERRY,
         "A berry that glows softly. Sweet.")
ITEM_DEF(ITEM_CROP_EMBERBERRY, "EMBERBERRY", POCKET_FARM, IK_CROP, 1, 0, ICON_CROP_EMBERBERRY,
         "A warm, peppery berry.")
ITEM_DEF(ITEM_CROP_TIDEBERRY, "TIDEBERRY", POCKET_FARM, IK_CROP, 2, 0, ICON_CROP_TIDEBERRY,
         "A juicy berry that tastes of rain.")
ITEM_DEF(ITEM_CROP_RADISH, "RADISH", POCKET_FARM, IK_CROP, 3, 0, ICON_CROP_RADISH,
         "Crunchy and a little peppery.")
ITEM_DEF(ITEM_CROP_CARROT, "CARROT", POCKET_FARM, IK_CROP, 4, 0, ICON_CROP_CARROT,
         "Sweet and orange.")
ITEM_DEF(ITEM_CROP_POTATO, "POTATO", POCKET_FARM, IK_CROP, 5, 0, ICON_CROP_POTATO,
         "A good, honest potato.")
ITEM_DEF(ITEM_CROP_PUMPKIN, "PUMPKIN", POCKET_FARM, IK_CROP, 6, 0, ICON_CROP_PUMPKIN,
         "A big orange pumpkin.")
ITEM_DEF(ITEM_CROP_CHILI, "CHILI", POCKET_FARM, IK_CROP, 7, 0, ICON_CROP_CHILI,
         "Hot, hot, hot.")
ITEM_DEF(ITEM_CROP_TOMATO, "TOMATO", POCKET_FARM, IK_CROP, 8, 0, ICON_CROP_TOMATO,
         "Ripe and red.")
ITEM_DEF(ITEM_CROP_CORN, "CORN", POCKET_FARM, IK_CROP, 9, 0, ICON_CROP_CORN,
         "A golden ear of corn.")
ITEM_DEF(ITEM_CROP_SUNFLOWER, "SUNFLOWER", POCKET_FARM, IK_CROP, 10, 0, ICON_CROP_SUNFLOWER,
         "A bright sunflower head, full of seeds.")
ITEM_DEF(ITEM_CROP_MOTEBLOOM, "MOTEBLOOM", POCKET_FARM, IK_CROP, 11, 0, ICON_CROP_MOTEBLOOM,
         "A flower full of loose motes.")
ITEM_DEF(ITEM_CROP_APPLE, "APPLE", POCKET_FARM, IK_CROP, 12, 0, ICON_CROP_APPLE,
         "A crisp apple.")
ITEM_DEF(ITEM_CROP_PEACH, "PEACH", POCKET_FARM, IK_CROP, 13, 0, ICON_CROP_PEACH,
         "A soft, fragrant peach.")
ITEM_DEF(ITEM_SPRINKLER, "SPRINKLER", POCKET_FARM, IK_PLACE, 0, 800, ICON_SPRINKLER,
         "Place it on your farm. Waters the 8 plots around it every morning.")
ITEM_DEF(ITEM_FRUIT_JAM, "FRUIT JAM", POCKET_FARM, IK_CROP, 14, 0, ICON_FRUIT_JAM,
         "Berries or fruit cooked down in the PRESERVES JAR. Sells well.")
ITEM_DEF(ITEM_PICKLES, "PICKLES", POCKET_FARM, IK_CROP, 15, 0, ICON_PICKLES,
         "Vegetables kept in brine in the PRESERVES JAR. Crunchy.")
ITEM_DEF(ITEM_DRIED_CHILI, "DRIED CHILI", POCKET_FARM, IK_CROP, 16, 0, ICON_DRIED_CHILI,
         "Chilies dried on the rack. Hotter than fresh.")
ITEM_DEF(ITEM_DRIED_FRUIT, "DRIED FRUIT", POCKET_FARM, IK_CROP, 17, 0, ICON_DRIED_FRUIT,
         "Apple or peach rings dried in the sun. Chewy and sweet.")
ITEM_DEF(ITEM_SUN_SEEDS, "SUN SEEDS", POCKET_FARM, IK_CROP, 18, 0, ICON_SUN_SEEDS,
         "Toasted sunflower seeds from the drying rack. A kin favourite.")
