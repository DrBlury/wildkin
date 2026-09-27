# Acts V–VII trainer XP handoff

Scope: isolated trainer tables only. The direct Hall-path sim in `tools/test_game.c` includes six wild bouts per accessible route, all mapped wardens once, a persistent four-kin team, and Master XP only after each arrival. It does not model survival or prove that all placed wardens are unavoidable. Baseline uses merged early-act corrections, not the older `tools/playthrough/BALANCE_HANDOFF.md` trace.

| Act | Baseline arrival / Master min | Tuned arrival / delta | Tuned zero-wild arrival | Tuned path (map mean before→after; wardens/wild) |
| --- | --- | --- | --- | --- |
| V North | 45 / 34 | 40 / +6 | 36 | Foothills 36→38 (7/6); Timberline 38→38 (2/0); Frostpine 38→39 (3/6); Frosthollow 39→39 (0/0); Rime Hall 39→40 (4/0) |
| VI Ash | 53 / 38 | 46 / +8 | 41 | Hollow Downs 42→43 (6/6); Ashen Fields 43→44 (3/6); Gravewood 44→45 (3/6); Duskmere 45→45 (0/0); Lantern Crypt 45→46 (3/0) |
| VII Dream | 59 / 42 | 51 / +9 | 46 | Mistfen 47→49 (6/6); Moonveil 49→50 (3/6); Dreamspire 50→50 (0/0); Mirror Hall 50→51 (3/0) |

The ±2 arrival assertions deliberately remain **red**. Act V already enters Foothills at mean 36 after unchanged BRONWEN (the allowed upper bound at SIGRUN). At zero wild bouts the unchanged placements and substantially trimmed trainer teams still reach 36, while the normal 12 route wild bouts raise arrival to 40. Keeping seven Foothills wardens, three Frostpine wardens, four Rime Hall wardens, and the normal wild density rules out the remaining +4 reduction with plausible team-size trims. Master teams and levels, prizes, placements, route encounter levels, paired climbers/pilgrims/twins, and satchel guards remain intact. Hollow Downs and Mistfen retain six wardens each; the normal-rate sim still confirms no extra grinding. Acts VI/VII inherit the previous Masters' XP and remain red despite mostly single-kin opposing teams. Further reduction requires changing mandatory density, wild frequency/XP assumptions, or earlier progression/XP design outside this scope; do not fake green by changing target levels.
