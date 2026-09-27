/* Saga interfaces are visible to earlier regional scripts in the unified build. */
enum { PROJ_COPPERLINE_TRAM, PROJ_CINDER_BRIDGE, PROJ_TIMBERLINE_LIFT,
       PROJ_REEDWICK_FERRY, PROJ_MAPLE_MARKET, SAGA_PROJECT_COUNT };
#define SAGA_TRAM PROJ_COPPERLINE_TRAM
#define SAGA_BRIDGE PROJ_CINDER_BRIDGE
#define SAGA_LIFT PROJ_TIMBERLINE_LIFT
#define SAGA_FERRY PROJ_REEDWICK_FERRY
#define SAGA_MARKET PROJ_MAPLE_MARKET
static void saga_project_offer(int proj);
static int saga_project_state(int proj);
static void saga_note(int id, int solved);
enum {
#define SAGA_NOTE(ID, MAP, X, Y, ABILITY, SOLVED) NOTE_##ID,
#include "notes.inc"
#undef SAGA_NOTE
    NOTE_COUNT
};

/* Saga quest text and marker maps. All stage arrays include stage zero. */
#define SAGA_STAGE(NAME, ...) static const char *const saga_##NAME##_goals[] = { 0, __VA_ARGS__ }
#define SAGA_MAPS(NAME, ...) static const u8 saga_##NAME##_maps[] = { MAP_NONE, __VA_ARGS__ }
SAGA_STAGE(tram, "Bring Holt 5 IRON ORE and 3000c in Brookmill.", "The tram is being built. Return after dawn.");
SAGA_MAPS(tram, MAP_BROOKMILL, MAP_BROOKMILL);
SAGA_STAGE(bridge, "Bring Greta 4 IRON ORE, 2 COAL and 4000c.", "Greta is building the Cinder bridge. Return after dawn.");
SAGA_MAPS(bridge, MAP_RAILHEAD, MAP_RAILHEAD);
SAGA_STAGE(lift, "Bring Astrid 6 TIMBER and 2500c.", "The Timberline lift is being built. Return after dawn.");
SAGA_MAPS(lift, MAP_TIMBERLINE, MAP_TIMBERLINE);
SAGA_STAGE(ferry, "Bring Elspeth 4 TIMBER, 2 SALT and 2000c.", "The Reedwick punt is being built. Return after dawn.");
SAGA_MAPS(ferry, MAP_REEDWICK, MAP_REEDWICK);
SAGA_STAGE(market, "Bring Linden 5 FLOUR, 5 HONEY and 6000c.", "The Maple market is being built. Return after dawn.");
SAGA_MAPS(market, MAP_TOWN, MAP_TOWN);
SAGA_STAGE(courier,
    "Take Elspeth's parcel to Brookmill's miller.", "Bring the miller's reply to Elspeth.",
    "Take Elspeth's wire to the Lumen clerk.", "Bring the clerk's reply to Elspeth.",
    "Carry the post to Greta at Railhead.", "Bring Greta's answer to Elspeth.",
    "Deliver the next parcel to Astrid in Timberline.", "Bring Astrid's reply to Elspeth.",
    "Take the sealed letter to Captain Audra.", "Bring Audra's answer to Sister Maud.",
    "Meet Elspeth's brother at Pilgrim Rest.", "Bring the brother's letter to Reedwick.");
SAGA_MAPS(courier, MAP_BROOKMILL_MILL, MAP_REEDWICK, MAP_LUMEN, MAP_REEDWICK,
    MAP_RAILHEAD, MAP_REEDWICK, MAP_TIMBERLINE, MAP_REEDWICK,
    MAP_ACCORD_GATE, MAP_WAYCHAPEL, MAP_PILGRIM_REST, MAP_REEDWICK);
SAGA_STAGE(almanac, "Survey the East and report in Maple.", "Survey the West and report in Maple.",
    "Survey the Forge and report in Maple.", "Survey the North and report in Maple.",
    "Survey the March and report in Maple.", "Survey the Dream and report in Maple.");
SAGA_MAPS(almanac, MAP_TOWN, MAP_TOWN, MAP_TOWN, MAP_TOWN, MAP_TOWN, MAP_TOWN);
SAGA_STAGE(legend, "Seek the old pilgrims' verses.", "Return to the book after healing the March.");
SAGA_MAPS(legend, MAP_PILGRIM_REST, MAP_PILGRIM_REST);
SAGA_STAGE(ring, "Find the widow's ring in Heron Fen.", "A RACCOIN carried it to Maple at night.", "Return the ring to Reedwick.");
SAGA_MAPS(ring, MAP_HERON_FEN, MAP_TOWN, MAP_REEDWICK);
SAGA_STAGE(lamp, "Find the lost lamp in Copperline Mine.", "Take the lamp to Cindermoor's forge.", "Return to the miner for a reward.");
SAGA_MAPS(lamp, MAP_COPPER_MINE, MAP_CINDERMOOR, MAP_COPPER_MINE);
SAGA_STAGE(chalk, "Bring BONE MEAL and SALT to the chalk cutter.", "Return to the Chalk Horse to see the restored figure.");
SAGA_MAPS(chalk, MAP_HOLLOW_DOWNS, MAP_HOLLOW_DOWNS);
SAGA_STAGE(ida, "Read the star cairn in the Foothills.", "Bring the reading back to Ida.");
SAGA_MAPS(ida, MAP_FOOTHILLS, MAP_FROSTHOLLOW);
SAGA_STAGE(notes, "Ask the route guides about hidden places and return with new abilities.");
SAGA_MAPS(notes, MAP_TOWN);
#undef SAGA_STAGE
#undef SAGA_MAPS
