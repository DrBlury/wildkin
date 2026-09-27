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

## Later: towns on the height layer
Port Brine and Gull Isle were rebuilt with elevation (and the Current Hall / Drowned Bell moved to
their own `tide` tileset to free scene tiles for props): see docs/handoff/towns_west.md.

## Routes West — REGION-WEST plan 04 (branch `plan-routes-west`)

- Six **append-only map IDs**: `MAP_HERON_FEN` (64x40), `MAP_REEDWICK` (40x36;
  expanded four rows so both west cells y31–32 exist), `MAP_REED_HEARTH`,
  `MAP_REED_SHOP`, `MAP_REED_TUNNEL` (20x12, `MF_DARK`) and `MAP_FEN_HERMIT`.
  Mirror Lake's sole change is its W link to `MAP_HERON_FEN`; Saltwind E now
  points to Reedwick and keeps its y31–32 opening. Fen's E opening y31–32
  and W opening y19–20 connect the route in both directions.
- **G2** is `HERON_FEN_PATCHES`: invert `FLAG_FEN_RIVETS` makes x28–31,
  y19–20 deep impassable tidepools and lowers their elevation. Once Volt
  crest is held, a carpenter sets the flag and E3 replaces the pair with a
  thank-you NPC. The lake-side teaser and exit remain open. West of the gap
  are a rookery, two reed-cutters side by side, a fisher and a night wisp
  chaser; the east side has a Lv18 warden. The other island's crossing has
  a raised bridge over the reed channel. `ZONE_FEN_REEDS` Lv17–21 includes
  MUDDLE and BLINKET by night; water has BUBBLIN, JELLUME and LURELING.
- **Reedwick** has a Hearth, shop, two Lv20–21 wardens, season-once
  `REEDS FOR THE ROOF` (five TIDEBERRIES from West's berry ids 10–19,
  300c), Nell's BERRY JUICE stock, two lore sources, and a reserved empty
  (12,10) for the Vale Courier owner. Light unlocks the dark reed tunnel's
  DUSK SHARD; Surf accesses the fen hermit's SLIPSTREAM tutor (two SALT,
  first healthy kin with a free move slot) and Reedwick's isolated wreck
  (two GLOW LANTERNS). There is **no `ITEM_IGNITER`** in the current item
  registry; no shared item id was added.
- Saltwind wild slots are Lv19–23; its wardens Lv20–23. A non-pumice boulder
  seals its cliff cache (three TIDE LANTERNS). The Current Hall wardens are
  Lv23–26, MAREN Lv25–28 and still grants `FLAG_TIDE_CREST` and SURF.
  The Drowned Bell entrance inside the cave is sealed by a post-game patch
  until `FLAG_OSSUREX_ANSWERED`; its exterior sign remains visible.
- **LINKS contract:** Port Brine N `link[LINK_N] = MAP_GREYWATER_FJORD`, water
  cells **x20–21, y0** only. A narrow water channel runs west behind the
  Current Hall to the existing coastal water. The LINKS owner must put a
  reciprocal `MAP_GREYWATER_FJORD` south link, with x20–21 surf-only landing;
  no new ID or map was registered in West for this external map. The buoy
  and sign say SURF ONLY. The existing south ferry/Sea Route is unchanged.
- Event hooks: open rookery and foggy reed beds for plan 09's migration and
  fog front; saltwind bluff lighthouse for storm lighting; three fish-market
  stall spaces in Brine stay owned by the existing fish market.

**Known gaps against the route checklist:** The two reed-cutters are adjacent
wardens with matching dialogue, not a simultaneous double-bout: the current
battle API exposes only single-opponent trainer-team starts. The two Fen
"hidden" satchels are placed under roots/reeds but use ordinary ground
satchel records, so their examine-only visibility is not enforced; the
current satchel record has no hidden flag. These mechanics require a shared
engine/battle API and are not claimed as complete here. The dark reed tunnel
uses the existing `MF_DARK` visibility behavior rather than blocking entry;
the first visit is possible without LIGHT but navigation is dark.

**Integration/testing:** E1 save IDs are present at baseline `ca6a672`.
E3 (`PERSON_IF`, `NpcDef.when`) and E5 (`MapPatch`, `MapDef.patches` plus
reapply-on-flag) are concurrent, and the E8 `MAP_GREYWATER_FJORD` ID is not
in this branch. Do not compile this branch alone; compile and run
`tools/tests/test_west.c`, `test_field`, `test_elevation`, `test_puzzles`,
`test_progression` and ROM screenshots after integrating those owners.
No post-change ROM screenshots are attached because the concurrent APIs and
fjord ID are absent here. Independently validated map dimensions, boardwalk
closed/open foot geometry, both Reedwick edge cells, the sealed Bell throat,
and the x20–21 Surf-connected fjord mouth; Python tile modules syntax-check.
