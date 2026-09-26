/* items/farm.inc -- FARM owner: seeds, saplings, fertilisers, crops and farm gear.
 * ITEM_DEF(id, "NAME" (<= 14 chars), pocket, kind, param, price (0 = not sold), icon, "desc") */
ITEM_DEF(ITEM_SEED_GLOWBERRY, "GLOW SEED", POCKET_FARM, IK_PLANT, 0, 40, ICON_SUNSEED,
         "Grows into a glowberry bush in 3 days. Regrows.")
ITEM_DEF(ITEM_SEED_EMBERBERRY, "EMBER SEED", POCKET_FARM, IK_PLANT, 1, 60, ICON_SUNSEED,
         "Grows into an emberberry bush in 4 days. Regrows.")
ITEM_DEF(ITEM_SEED_TIDEBERRY, "TIDE SEED", POCKET_FARM, IK_PLANT, 2, 60, ICON_SUNSEED,
         "Grows into a tideberry bush in 4 days. Regrows.")
ITEM_DEF(ITEM_SEED_RADISH, "RADISH SEED", POCKET_FARM, IK_PLANT, 3, 20, ICON_SUNSEED,
         "Radishes are ready in 2 days.")
ITEM_DEF(ITEM_SEED_CARROT, "CARROT SEED", POCKET_FARM, IK_PLANT, 4, 30, ICON_SUNSEED,
         "Carrots are ready in 3 days.")
ITEM_DEF(ITEM_SEED_POTATO, "POTATO SEED", POCKET_FARM, IK_PLANT, 5, 40, ICON_SUNSEED,
         "Potatoes are ready in 4 days.")
ITEM_DEF(ITEM_SEED_PUMPKIN, "PUMPKIN SEED", POCKET_FARM, IK_PLANT, 6, 100, ICON_SUNSEED,
         "Pumpkins take 7 days but sell well.")
ITEM_DEF(ITEM_SEED_CHILI, "CHILI SEED", POCKET_FARM, IK_PLANT, 7, 60, ICON_SUNSEED,
         "Chilies are ready in 4 days. Regrows.")
ITEM_DEF(ITEM_SEED_TOMATO, "TOMATO SEED", POCKET_FARM, IK_PLANT, 8, 50, ICON_SUNSEED,
         "Tomatoes are ready in 5 days. Regrows.")
ITEM_DEF(ITEM_SEED_CORN, "CORN SEED", POCKET_FARM, IK_PLANT, 9, 80, ICON_SUNSEED,
         "Corn takes 6 days. Regrows.")
ITEM_DEF(ITEM_SEED_SUNFLOWER, "SUNNY SEED", POCKET_FARM, IK_PLANT, 10, 60, ICON_SUNSEED,
         "Sunflowers bloom in 5 days.")
ITEM_DEF(ITEM_SEED_MOTEBLOOM, "MOTE SEED", POCKET_FARM, IK_PLANT, 11, 300, ICON_SUNSEED,
         "A rare flower that gathers motes. Blooms in 8 days.")
ITEM_DEF(ITEM_SAPLING_APPLE, "APPLE SAPLING", POCKET_FARM, IK_PLANT, 12, 1000, ICON_SUNSEED,
         "An apple tree. Fruits every 3 days once grown (12 days).")
ITEM_DEF(ITEM_SAPLING_PEACH, "PEACH SAPLING", POCKET_FARM, IK_PLANT, 13, 1200, ICON_SUNSEED,
         "A peach tree. Fruits every 3 days once grown (12 days).")
ITEM_DEF(ITEM_FERTILIZER, "FERTILIZER", POCKET_FARM, IK_FERTILIZER, 0, 50, ICON_SUNSEED,
         "Basic fertiliser. Crops grow a little faster.")
ITEM_DEF(ITEM_RICH_COMPOST, "RICH COMPOST", POCKET_FARM, IK_FERTILIZER, 1, 120, ICON_SUNSEED,
         "Dark compost. Crops are more often top quality.")
ITEM_DEF(ITEM_GROW_MULCH, "GROW MULCH", POCKET_FARM, IK_FERTILIZER, 2, 150, ICON_SUNSEED,
         "Keeps soil damp. Watered soil stays watered for 2 days.")
ITEM_DEF(ITEM_CROP_GLOWBERRY, "GLOWBERRY", POCKET_FARM, IK_CROP, 0, 0, ICON_BLOOM_SHARD,
         "A berry that glows softly. Sweet.")
ITEM_DEF(ITEM_CROP_EMBERBERRY, "EMBERBERRY", POCKET_FARM, IK_CROP, 1, 0, ICON_BLOOM_SHARD,
         "A warm, peppery berry.")
ITEM_DEF(ITEM_CROP_TIDEBERRY, "TIDEBERRY", POCKET_FARM, IK_CROP, 2, 0, ICON_BLOOM_SHARD,
         "A juicy berry that tastes of rain.")
ITEM_DEF(ITEM_CROP_RADISH, "RADISH", POCKET_FARM, IK_CROP, 3, 0, ICON_BLOOM_SHARD,
         "Crunchy and a little peppery.")
ITEM_DEF(ITEM_CROP_CARROT, "CARROT", POCKET_FARM, IK_CROP, 4, 0, ICON_BLOOM_SHARD,
         "Sweet and orange.")
ITEM_DEF(ITEM_CROP_POTATO, "POTATO", POCKET_FARM, IK_CROP, 5, 0, ICON_BLOOM_SHARD,
         "A good, honest potato.")
ITEM_DEF(ITEM_CROP_PUMPKIN, "PUMPKIN", POCKET_FARM, IK_CROP, 6, 0, ICON_BLOOM_SHARD,
         "A big orange pumpkin.")
ITEM_DEF(ITEM_CROP_CHILI, "CHILI", POCKET_FARM, IK_CROP, 7, 0, ICON_BLOOM_SHARD,
         "Hot, hot, hot.")
ITEM_DEF(ITEM_CROP_TOMATO, "TOMATO", POCKET_FARM, IK_CROP, 8, 0, ICON_BLOOM_SHARD,
         "Ripe and red.")
ITEM_DEF(ITEM_CROP_CORN, "CORN", POCKET_FARM, IK_CROP, 9, 0, ICON_BLOOM_SHARD,
         "A golden ear of corn.")
ITEM_DEF(ITEM_CROP_SUNFLOWER, "SUNFLOWER", POCKET_FARM, IK_CROP, 10, 0, ICON_BLOOM_SHARD,
         "A bright sunflower head, full of seeds.")
ITEM_DEF(ITEM_CROP_MOTEBLOOM, "MOTEBLOOM", POCKET_FARM, IK_CROP, 11, 0, ICON_BLOOM_SHARD,
         "A flower full of loose motes.")
ITEM_DEF(ITEM_CROP_APPLE, "APPLE", POCKET_FARM, IK_CROP, 12, 0, ICON_BLOOM_SHARD,
         "A crisp apple.")
ITEM_DEF(ITEM_CROP_PEACH, "PEACH", POCKET_FARM, IK_CROP, 13, 0, ICON_BLOOM_SHARD,
         "A soft, fragrant peach.")
ITEM_DEF(ITEM_SPRINKLER, "SPRINKLER", POCKET_FARM, IK_PLACE, 0, 0, ICON_TUNING_FORK,
         "Place it on your farm. Waters the 8 plots around it every morning.")
