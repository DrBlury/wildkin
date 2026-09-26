/* items/core.inc -- battle/UI owner: supplies usable in bouts and the new growth shards.
 * ITEM_DEF(id, "NAME" (<= 14 chars), pocket, kind, param, price (0 = not sold), icon, "desc") */
ITEM_DEF(ITEM_VIGOR_DRAUGHT, "VIGOR DRAUGHT", POCKET_SUPPLIES, IK_HEAL_CURE, 50, 0, ICON_GLOW_TONIC,
         "A brewed draught. Restores 50 HP and cures any status problem.")
ITEM_DEF(ITEM_CLARITY_BREW, "CLARITY BREW", POCKET_SUPPLIES, IK_TEA_ALL, 0, 0, ICON_HONEY_DROP,
         "Clears a kin's modes completely. Restores every move's uses.")
ITEM_DEF(ITEM_REVIVAL_BREW, "REVIVAL BREW", POCKET_SUPPLIES, IK_REVIVE, 0, 0, ICON_IGNITER,
         "Re-seeds a collapsed field in one go. Wakes a dozing kin with full HP.")
ITEM_DEF(ITEM_SWIFT_COIL, "SWIFT COIL", POCKET_SUPPLIES, IK_XSTAT, STAT_SPE, 550, ICON_AMP_COIL,
         "Tunes a kin's pump for speed. Sharply raises SPEED for the bout.")
ITEM_DEF(ITEM_FOCUS_COIL, "FOCUS COIL", POCKET_SUPPLIES, IK_XSTAT, STAT_SPA, 550, ICON_AMP_COIL,
         "Sharpens a kin's field. Sharply raises FOCUS for the bout.")
ITEM_DEF(ITEM_WILL_COIL, "WILL COIL", POCKET_SUPPLIES, IK_XSTAT, STAT_SPD, 550, ICON_GUARD_COIL,
         "Steadies a kin's field. Sharply raises WILL for the bout.")
ITEM_DEF(ITEM_LURE_INCENSE, "LURE INCENSE", POCKET_SUPPLIES, IK_LURE, 20, 900, ICON_HUSH_BELL,
         "Sweet smoke that brimming rare kin find hard to resist. Lasts 200 steps.")
ITEM_DEF(ITEM_WAYSTONE, "WAYSTONE", POCKET_SUPPLIES, IK_WAYSTONE, 0, 400, ICON_SPARK_SHARD,
         "A twin crystal tuned to hearths. Takes you back to the last Hearth Hall.")
ITEM_DEF(ITEM_HOLLOW_SHARD, "HOLLOW SHARD", POCKET_SHARDS, IK_SHARD, 0, 2500, ICON_DUSK_SHARD,
         "A seed crystal of bone-white quartz. Some kin grow when they touch it.")
ITEM_DEF(ITEM_RELIC_SHARD, "RELIC SHARD", POCKET_SHARDS, IK_SHARD, 0, 2500, ICON_SPARK_SHARD,
         "A seed crystal worn smooth by a century of hands. Some kin grow at its touch.")
ITEM_DEF(ITEM_METAL_SHARD, "METAL SHARD", POCKET_SHARDS, IK_SHARD, 0, 2500, ICON_FROST_SHARD,
         "A seed crystal of lodestone. Some kin grow when they touch it.")
ITEM_DEF(ITEM_ASTRAL_SHARD, "ASTRAL SHARD", POCKET_SHARDS, IK_SHARD, 0, 3000, ICON_BLOOM_SHARD,
         "A seed crystal that fell from the sky. Some kin grow when they touch it.")
