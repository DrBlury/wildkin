"""Named, hand-authored biome strokes; x/y coordinates are zero based.

These are intentionally individual scene beats, not a procedural shape generator.
The guarded JSON records the exact inspected old/new rows assembled from them.
"""
# The following hand-placed banks interrupt previously straight walks. Their
# exact old/new cells (including the earlier texture strokes) are pinned in
# guarded_spans.json; only those cells may change collision in apply.py.
BANKS = {
    'east/BROOK_TRAIL': (2, 18, 20, 23, 'pine bank above the millrace'),
    'west/SALTWIND': (4, 20, 10, 13, 'dune-side pines steering toward the shore'),
    'north/FROSTPINE': (27, 28, 19, 20, 'snow-pine switchback below bridge'),
    'far/MOONVEIL': (20, 21, 24, 25, 'moon grove beside central lane'),
}

STROKES = {
    # Brook: upstream curved footpath, millrace bank and a wooded approach.
    'east/BROOK_TRAIL': [(4, 20, '...'), (5, 22, '...'), (6, 24, '...'),
                         (7, 27, '...'), (8, 29, '...'), (9, 30, '...'),
                         (10, 29, '...'), (11, 27, '...'), (12, 24, '...')],
    'east/BROOKMILL': [(3, 10, ',,,'), (4, 11, ',,,'), (5, 12, ',,,'),
                       (20, 15, '==='), (21, 16, '==='), (22, 17, '===')],
    # Fen: two banks frame the old boardwalk; reed craft yard is approached on decking.
    'west/HERON_FEN': [(8, 35, '==='), (9, 37, '==='), (10, 39, '==='),
                       (11, 40, '==='), (12, 39, '==='), (13, 37, '==='),
                       (14, 35, '===')],
    'west/REEDWICK': [(8, 23, '==='), (9, 24, '==='), (10, 25, '==='),
                      (11, 26, '==='), (12, 25, '==='), (13, 24, '===')],
    # Coast: a dune wash, scalloped beach, salt-work and sheltered salvage garden.
    'west/SALTWIND': [(5, 25, '...'), (6, 27, '...'), (7, 29, '...'),
                      (8, 30, '...'), (9, 29, '...')],
    'west/PORT_BRINE': [(24, 20, 'sss'), (25, 21, 'sss'), (26, 20, 'sss')],
    'west/GULL_ISLE': [(15, 16, '==='), (16, 17, '==='), (17, 18, '==='),
                       (18, 19, '==='), (19, 20, '===')],
    # North: staggered pine switchbacks and the sawmill log-yard apron.
    'north/FROSTPINE': [(32, 29, '==='), (33, 28, '==='), (34, 27, '==='),
                        (35, 26, '===')],
    'north/TIMBERLINE': [(14, 24, '==='), (15, 24, '==='), (16, 24, '==='),
                         (17, 25, '==='), (18, 26, '==='), (19, 27, '===')],
    'north/FROSTHOLLOW': [(30, 26, '==='), (31, 27, '==='), (33, 30, '===')],
    # Far: cooled shelf detour, forge apron, rail siding, moonlit gathering circuit.
    'far/EMBER_TUNNEL': [(9, 9, '___'), (15, 9, ':::')],
    'far/CALDERA': [(3, 4, 'yyy'), (3, 8, 'yyy')],
    'far/CINDERMOOR': [(10, 27, '==='), (11, 29, '==='), (12, 31, '===')],
    'far/RAILHEAD': [(22, 13, '==='), (23, 15, '==='), (24, 17, '==='),
                     (25, 19, '===')],
    'far/MOONVEIL': [(20, 16, 'fff'), (21, 18, 'fff'), (22, 20, 'fff'),
                     (23, 22, 'fff'), (24, 20, 'fff')],
    'far/DREAMSPIRE': [(24, 25, 'fff'), (25, 26, 'fff'), (26, 25, 'fff')],
    # Grim: erosion channel, root pocket and lantern memorial paving.
    'grim/HOLLOW_DOWNS': [(9, 44, 'ddd'), (10, 43, 'ddd'), (11, 42, 'ddd')],
    'grim/GRAVEWOOD': [(5, 5, 'ggg'), (6, 8, 'ggg'), (7, 11, 'ggg')],
    'grim/DUSKMERE': [(28, 18, 'ddd'), (29, 19, 'ddd'), (30, 20, 'ddd')],
}
