# Regional weather and festival visual handoff

Field-only visuals now use the existing `farm_draw()` hook: an 8x8 procedural tile strip in OBJ tiles 532–538, the existing emote palette (bank 15), and at most 16 weather plus 6 festival sprites, stopping when the OAM queue reaches 104 entries, leaving 24 for later draws. Tile art is uploaded on map load and after returning from other screens (battle FX overwrite this range); it does not claim new OBJ palette colours or save bytes. `field_tint()` applies an outdoor-only palette treatment, refreshing each night band, weather change, and during aurora/heat animation.

- FOG: pale palette haze and slow low-lying wisps. This is a colour treatment and particles, **not** hardware BG blending or a reduced kin sight radius.
- SNOW: snowfall on every `MF_SNOW` outdoor map, thicker during a regional snow front. Daytime AURORA reverts to that baseline.
- AURORA: night-only palette cycle and high drifting sky streamers in the north front. Map geometry has no dedicated sky layer.
- HEAT: warm palette pulse and wavering heat marks on the volcanic front; **no scanline BG distortion**.
- ASH: extra falling flakes and subdued palette when the ash front is active. The existing grim-world ash renderer remains untouched; its normal ash still falls on `MF_ASH` maps.
- STORM/RAIN: existing storm and rain paths remain unchanged; the farm still checks only global `gtime.weather` for watering.
- Festivals: Kindling ember glow in Maple, Millrace streamers at Brookmill, night-only Lantern glow in Duskmere, Frost Fair flurries by Frosthollow's host, and night-only Starfall streaks over the Rise. These are ambient visuals by the existing hosts, **not** new festival decor, races, or map patches.

`tools/tests/test_weather_visuals.c` forces weather fronts and all five dates, checks field tint and actual OAM sprites, night/day gating, the `MF_SNOW` baseline, OAM/tile bounds, and global rain isolation. It is picked up by the existing `make test` test-file loop. Renderer animation and visual polish still warrant an on-device mGBA pass; the host test verifies render commands, not their physical display quality.
