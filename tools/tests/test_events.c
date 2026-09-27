/* Daily-event model checks; run by make test after E3/E10 and routes merge. */
#include "harness.h"
#include <string.h>

int main(void)
{
    game_init();
    fresh_game();
    CHECK(sizeof(EventState) <= 64, "event save blob is at most 64 bytes");
    int different = 0, outbreaks = 0, weather = 0, caravan = 0;
    int stable = 1, gated = 1, short_lines = 1, validated = 1;
    EventState baseline;
    for (int day = 1; day <= 1000; day++) {
        gtime.day = day;
        events.rolled_day = 0;
        events_new_day();
        baseline = events;
        events_new_day();
        stable &= !memcmp(&baseline, &events, sizeof events);
        gated &= events.caravan_map < CARAVAN_COUNT &&
                 CARAVAN_ROUTE[events.caravan_map].min_act <= events_act();
        if (events_active(EV_OUTBREAK)) {
            outbreaks++;
            gated &= OUTBREAKS[events_arg(EV_OUTBREAK)].min_act <= events_act();
        }
        if (events_active(EV_CARAVAN)) caravan++;
        if (events.front_kind > WX_RAIN) weather++;
        different += day > 1 && baseline.front_region != 0;
        for (int line = 0; line < 5; line++)
            short_lines &= strlen(events_gazette_line(line)) <= 30;
        events_validate();
        validated &= !memcmp(&baseline, &events, sizeof events);
    }
    CHECK(stable && validated, "same day and valid state never reroll");
    CHECK(gated, "no outbreak or caravan beyond current act");
    CHECK(short_lines, "all Gazette lines fit dialogue");
    CHECK(different > 0 && outbreaks > 0 && weather > 0 && caravan == 1000,
          "daily event kinds recur and move");
    gtime.day = 2;
    EventState before = events;
    before.rolled_day = 0;
    events = before;
    events_new_day();
    EventState first = events;
    events = before;
    events_new_day();
    CHECK(!memcmp(&first, &events, sizeof events), "same save seed and day reproduces the roll");
    CHECK(events_festival_for_day(1) == FEST_KINDLING &&
          events_festival_for_day(13) == FEST_MILLRACE &&
          events_festival_for_day(27) == FEST_LANTERN &&
          events_festival_for_day(35) == FEST_FROST &&
          events_festival_for_day(10) == FEST_STARFALL, "festival calendar");
    events.front_region = ER_COUNT;
    events_validate();
    CHECK(events.front_region < ER_COUNT && events.rolled_day == gtime.day, "corrupt state re-rolls");
    if (failures) printf("%d event check(s) FAILED\n", failures);
    else printf("all event checks passed\n");
    return failures ? 1 : 0;
}
