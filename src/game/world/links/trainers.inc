#define LINK_TR(ID, NAME, A, B, C, L, INTRO) \
    [TR_LINK_##ID] = { "WARDEN " NAME, 3, { SP_##A, SP_##B, SP_##C }, \
        { L, L + 1, L + 2 }, 2700, INTRO, "Fair bout! The trail is yours." },
LINK_TR(ASH_A, "FLINT", SCORCHION, FORTADILLO, LODEHORN, 41, "Glass from fire, strength from ash!")
LINK_TR(ASH_B, "MARA", LODEHORN, CAWDAVER, FOUNDRAKE, 42, "I study every layer of ash.")
LINK_TR(ASH_C, "KERR", REAPMANTIS, SCORCHION, FORTADILLO, 41, "A cache is worth protecting.")
LINK_TR(ASH_D, "ROWE", CAWDAVER, FORTADILLO, REAPMANTIS, 42, "The Accord sent us together.")
LINK_TR(ASH_E, "TEAL", LODEHORN, SCORCHION, CAWDAVER, 41, "Ranger one, reporting!")
LINK_TR(ASH_F, "VALE", FOUNDRAKE, REAPMANTIS, CAWDAVER, 42, "Ranger two, reporting!")
LINK_TR(STAR_A, "IDA", MOONHARE, GLACIYAK, METEORB, 42, "Read the sky, then bout!")
LINK_TR(STAR_B, "DANE", CRAGHORN, GLACIYAK, MOONHARE, 43, "The climb is its own reward.")
LINK_TR(STAR_C, "OTTO", TENGALE, CRAGHORN, METEORB, 42, "A star chart is hidden here.")
LINK_TR(STAR_D, "NELL", GLACIYAK, MOONHARE, CRAGHORN, 42, "Ski fast, bout faster!")
LINK_TR(STAR_E, "PIP", MOONHARE, WENDIGAUNT, METEORB, 43, "My partner and I race together.")
LINK_TR(STAR_F, "ALBA", METEORB, CRAGHORN, GLACIYAK, 43, "Watch the aurora turn.")
LINK_TR(FJORD_A, "HALE", TUXFLAKE, MEDUSHOCK, EMPERICE, 38, "The fjord knows my nets.")
LINK_TR(FJORD_B, "FENN", EMPERICE, TUXFLAKE, MEDUSHOCK, 39, "Ice fisher's challenge!")
LINK_TR(FJORD_C, "SAIL", MEDUSHOCK, EMPERICE, TUXFLAKE, 38, "The tide carries us.")
LINK_TR(FJORD_D, "RIME", TUXFLAKE, EMPERICE, ABYSSLURE, 39, "Cold hands, steady line.")
LINK_TR(FJORD_E, "LARS", EMPERICE, MEDUSHOCK, TUXFLAKE, 40, "Meet me on the islet.")
#undef LINK_TR

#include "biomes/trainers.inc"
