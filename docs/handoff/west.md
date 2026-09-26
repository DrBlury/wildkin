# W-WEST handoff (Saltwind Trail, Port Brine, Current Hall, Sea Route, Gull Isle, Drowned Bell)

## Done
- **Tileset** `tools/tilesets/ts_coast.py`: 382 tiles (was 422). Hut is now 3x3,
  hall/hut wall and thatch textures repeat every 8 px, the grotto ceiling and
  Hall pool are single repeating tiles. BRIDGE_H / BRIDGE_V / ROWBOAT added to
  USES_DECOR (piers).
- **Decor** `tools/decor_west.py` (29 kinds, registered in `all_decor()`):
  pier post, bollard, lobster pots, anchor, lifebuoy, fishing boat, ferry
  boat, lighthouse (animated lamp), nets, fish stall, shells, starfish,
  seaweed, driftwood, sea rock, salt heap, bell buoy (bobbing), gull post,
  whale-rib arch, shell lamp, Hall column, crab shell; grotto: DROWNED_BELL,
  pillar, glow coral (pulsing), whale carving; interiors: ship wheel, fish
  trophy, ship in a bottle, wall net.
- **Maps** (`src/game/world/west/data.h`, legend in its header):
  SALTWIND TRAIL 50x40 (dunes, dune ledge, salt pans, cliff + ledge, beach,
  rock shelf), PORT BRINE 48x44 (Current Hall, hearth, shop, inn, harbor
  office, skipper's house, quays, lighthouse, ferry pier, south pier to the
  Sea Route), SEA ROUTE 40x48 (open water, 3 sandbar islets + rock islet),
  GULL ISLE 40x34 (hut, salt pans, cliff with sea cave, whale arch, ferry
  pier), CURRENT HALL 15x18 (current network; correct route: left channel ->
  P1 -> right channel -> P2 -> up channel -> dais; the middle channel and P2's
  down channel loop back to the start; a nook with a satchel), DROWNED BELL
  20x18 (temple, glowing pool, `OBJ(LEGEND, 11, 8, SP_NOCTHALE)`), interiors
  BRINE HEARTH HALL (MF_HEAL), BRINE SHOP, HARBOR OFFICE, GULL INN, SKIPPER'S
  HOUSE (new id MAP_BRINE_HOUSE, appended last), ODA'S HUT.
- Edge contracts kept: Saltwind E y31-32 (Mirror Lake), Saltwind W / Brine E
  y19-20, Brine S / Sea Route N x20-21 (plank pier), Sea Route S / Gull Isle N.
- Objects: OBJ_FERRY on both piers (arg = destination map), OBJ_BERRY ids
  10-13, the NOCTHALE legend.
- Zones: SALTWIND (14-19), SANDBARS (22-27), ISLE (24-30), SEA = water_zone of
  Saltwind/Brine/Sea Route/Gull Isle (KELPYRE night, weight 2).
- People: 13 wardens (Saltwind 4, Sea Route 3, Gull Isle 2, Hall 3) with 2-4
  kin, HALL MASTER MAREN (6 TIDE kin, Lv23-27, `battle_start_master`, win ->
  FLAG_TIDE_CREST, `travel_award_crest(CREST_TIDE)`, 3 TIDE LANTERNS,
  LORE_TIDE_CREST), ferrymen (500c or FERRY PASS, `travel_boat_to`), BRINE
  SHOP (`shop_open_stock`), inn (SCR_CHEF cook + innkeeper bed 100c), salt
  raker, lightkeeper, harbor master, skipper, hall guide, Oda.
- Quests: HARBOR POST (3 letters -> FERRY PASS), SALT FOR THE ISLE (3 SALT ->
  GRAND TONIC x2 + Drowned Bell/NOCTHALE lore).
- Lore: 11 entries (Saltwind, seabirds, Port Brine, tides, lighthouse, Current
  Hall, Tide Crest, Gull Isle, glowing sea, Drowned Bell, NOCTHALE); 9 signs;
  14 satchels; fly points Port Brine (30,108) and Gull Isle (22,146).
- `tools/tests/test_west.c`: tileset budget, people/character limits, edge
  openings, surf-only Sea Route, KELPYRE slot, Hall solved by the current
  rule (and the loop/dais checks), NOCTHALE reachable, ferries, berry ids,
  shop, ferry both ways, both quests, the Master bout and crest.
- Verified in the ROM with `build/shot` (warp menu): Port Brine, Saltwind,
  the Current Hall and the Drowned Bell render correctly.

## Shared files edited
- `tools/gen_field_gfx.py`: one line in `all_decor()` (decor_west).
- `tools/tests/harness.h`: `flood()` treats open water (A_WATER, not A_DEEP,
  no solid decor) as passable on maps with `MapDef.water_zone` (surf mode).
- `tools/test_game.c`: the KEEN EYE check reseeds the rng after each duel.
  It was seeded once, so it depended on how many NPCs `npcs_reset()` drew
  random numbers for, and broke when any region added people.
- Regenerated: `src/gfx_field.h`, `src/game/world/debug/*`.

## Left
- Traversal: currents, surf, ferry objects and the legend encounter are the
  traversal owner's (convention in data.h / ts_coast.py). Until then the
  Hall's currents are plain walkable floor in the ROM, and the Sea Route can
  only be crossed by the ferry script.
- Crafting station decor (COOKTOP) next to the inn's cook once decor_craft
  exists; berry patch art is the farm owner's.
- Optional polish: more Port Brine set dressing, Gull Isle second hut.
- `make` shows 6 pre-existing `-Wunused-function` warnings in party.c (UI
  owner), not from this region.
