/* Stages are indexed by the actual quest stage; 255 is complete. */
#define SAGA_QUEST(ID, TITLE, GOALS, MAPS, CATEGORY) \
    [ID] = { TITLE, GOALS[1], GOALS, NDEC(GOALS), CATEGORY, MAPS }
    SAGA_QUEST(QUEST_PROJECT_TRAM, "COPPERLINE TRAM", saga_tram_goals, saga_tram_maps, QUEST_PROJECT),
    SAGA_QUEST(QUEST_PROJECT_BRIDGE, "CINDER BRIDGE", saga_bridge_goals, saga_bridge_maps, QUEST_PROJECT),
    SAGA_QUEST(QUEST_PROJECT_LIFT, "TIMBERLINE LIFT", saga_lift_goals, saga_lift_maps, QUEST_PROJECT),
    SAGA_QUEST(QUEST_PROJECT_FERRY, "REEDWICK FERRY", saga_ferry_goals, saga_ferry_maps, QUEST_PROJECT),
    SAGA_QUEST(QUEST_PROJECT_MARKET, "MAPLE MARKET", saga_market_goals, saga_market_maps, QUEST_PROJECT),
    SAGA_QUEST(QUEST_VALE_COURIER, "VALE COURIER", saga_courier_goals, saga_courier_maps, QUEST_SIDE),
    SAGA_QUEST(QUEST_ALMANAC_SURVEY, "ALMANAC SURVEY", saga_almanac_goals, saga_almanac_maps, QUEST_SIDE),
    SAGA_QUEST(QUEST_LEGEND_TRAIL, "LEGEND TRAIL", saga_legend_goals, saga_legend_maps, QUEST_SIDE),
    SAGA_QUEST(QUEST_HERONS_RING, "HERON'S RING", saga_ring_goals, saga_ring_maps, QUEST_SIDE),
    SAGA_QUEST(QUEST_MINERS_LAMP, "MINER'S LAMP", saga_lamp_goals, saga_lamp_maps, QUEST_SIDE),
    SAGA_QUEST(QUEST_CHALK_HORSE, "CHALK HORSE", saga_chalk_goals, saga_chalk_maps, QUEST_SIDE),
    SAGA_QUEST(QUEST_STARLIGHT_IDA, "IDA'S STARLIGHT", saga_ida_goals, saga_ida_maps, QUEST_SIDE),
    SAGA_QUEST(QUEST_FIELD_NOTES, "FIELD NOTES", saga_notes_goals, saga_notes_maps, QUEST_SIDE),
#undef SAGA_QUEST
