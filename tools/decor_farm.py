#!/usr/bin/env python3
"""Farm decor catalog (owner: FARM, docs/EXPANSION.md 7.2 and 10.1).

Outdoor kinds live in the 'farm' tileset and use its bank 3 (the village
prop colours: outline, stone, wood, yellow, orange, red, water, leaves).
Interior kinds (the farmhouse) use the interior tileset's textile bank.
Everything is drawn on transparency. farm.c gives the working ones their
behaviour (shipping bin, processors, work board, storage chest); the
examine= lines are what other maps (and the asset viewer) say.
"""

from pixelart import Decor
from decor_outdoor import SG, OL
from decor_indoor import IL

F = ['farm']
I = ['interior']

SHIPPING_BIN = SG('''
................................
................................
..OOOOOOOOOOOOOOOOOOOOOOOOOOOO..
.OAAAAAAAAAAAAAAAAAAAAAAAAAAAAO.
.OABBBBBBBBBBBBBBBBBBBBBBBBBBKO.
.OKKKKKKKKKKKKKKOOKKKKKKKKKKKKO.
.OOOOOOOOOOOOOOOyyOOOOOOOOOOOOO.
.OlmOABBBBBBBBBOyoOBBBBBBBBBKOmO
.OlmOABBBBBBBBBBOOBBBBBBBBBBKOmO
.OlmOAKKKKKKKKKKKKKKKKKKKKKKKOmO
.OlmOABBBBBBBBBBBBBBBBBBBBBBKOmO
.OlmOABBBBBBBBBBBBBBBBBBBBBBKOdO
.OlmOAKKKKKKKKKKKKKKKKKKKKKKKOdO
.OlmOABBBBBBBBBBBBBBBBBBBBBBKOdO
.OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
..OKKO....................OKKO..
''', OL, w=32)

PRESERVES_JAR = SG('''
................
....OOOOOOOO....
...OAAAAAAABO...
...OKKKKKKKKO...
....OwwwwwwO....
...OwuuuuuuUO...
..OwurrrrrrrUO..
..OwrrorrrrrUO..
..OuwwwwwwwwUO..
..OurwKKKKwrUO..
..OurwwwwwwrUO..
..OurrrrrrrrUO..
..OuroorrrrrUO..
...OUrrrrrrUO...
....OOOOOOOO....
................
''', OL)

PRESS = SG('''
................
................
.......OO.......
......OllO......
..OOOOOlmOOOOO..
..OAAAAlmBBBBO..
..OOOOOlmOOOOO..
......OlmO......
......OlmO......
......OlmO......
......OldO......
....OOOlmOOO....
...OlllllmmdO...
...OOOOOOOOOO...
..OAABBBBBBBKO..
..OAKKKKKKKKKO..
.OmmmmmmmmmmmdO.
.OAABBBBBBBBBKO.
.OAABBBBBBBBBKO.
.OAABBBBBBBBBKO.
.OmmmmmmmmmmmdO.
.OAABBBBBBBBBKO.
.OAABBBBBBBBBKO.
.OAABBBBBBBBBKO.
.OmmmmmmmmmmmdO.
.OAABBBBBBBBBKO.
.OAABBBBBBBBBKO.
..OOOOOrrOOOOO..
....OrrorrO.....
.....OOOOO......
................
................
''', OL)

DRIER = SG('''
................................
..OOOOOOOOOOOOOOOOOOOOOOOOOOOO..
..OAAAAAAAAAAAAAAAAAAAAAAAAAAO..
..OKKKKKKKKKKKKKKKKKKKKKKKKKKO..
..OOOOOOOOOOOOOOOOOOOOOOOOOOOO..
..OAOryrOoyoOrrOyyOoyOryrOooKO..
..OAOOOOOOOOOOOOOOOOOOOOOOOOKO..
..OAKmKmKmKmKmKmKmKmKmKmKmKmKO..
..OAOoyoOryrOyOrrOoyoOryrOyoKO..
..OAOOOOOOOOOOOOOOOOOOOOOOOOKO..
..OAKmKmKmKmKmKmKmKmKmKmKmKmKO..
..OAOOOOOOOOOOOOOOOOOOOOOOOOKO..
..OAO......................OKO..
..OAO......................OKO..
..OKO......................OKO..
..OOO......................OOO..
''', OL, w=32)

FOR_SALE = SG('''
................
.OOOOOOOOOOOOOO.
OrrrrrrrrrrrrrrO
OrwwrwrwwrwwrrrO
OrwrrwrwrrwrrrrO
OrwwrwrwwrwwrrrO
OrrrrrrrrrrrrrrO
OrwrwwrwrrwwrrrO
OrwrwrrwrrwrrrrO
OrwrwwrwwrwwrrrO
OrrrrrrrrrrrrrrO
.OOOOOOABOOOOOO.
......OABKO.....
......OABKO.....
......OABKO.....
......OOOOO.....
''', OL)

FARM_GATE = SG('''
................
................
................
.OOOO.OO.OO.OO..
.OABOOAOOAOOAOO.
.OABOOAOOAOOAOO.
.OABOAAAAAAAAAAA
.OABOBBBBBBBBBBB
.OABOOAOKAOOAOOO
.OABOOAOOKOOAOO.
.OABOOAOOAKOAOO.
.OABOAAAAAAKAAAA
.OABOKKKKKKKKKKK
.OABOOAOOAOOAOOO
.OABOOBOOBOOBOO.
.OOOOOOOOOOOOOO.
''', OL)

WORK_BOARD = SG('''
................................
.OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
.OAAAAAAAAAAAAAAAAAAAAAAAAAAAAO.
.OABBBBBBBBBBBBBBBBBBBBBBBBBBKO.
.OABOOOOOOOBBBBBBBOOOOOOOOBBBKO.
.OABOZRZZZOBBOOOOOOOZUZZZOBBBKO.
.OABOZZZZZOBBOZZZZZOZZZZZOBBBKO.
.OABOZGgZZOBBOZYZZZOZOOZZOBBBKO.
.OABOZgGZZOBBOZZZZZOZZZZZOBBBKO.
.OABOZOOOZOBBOZOOZZOZOOOZOBBBKO.
.OABOZZZZZOBBOZZZZZOOOOOOOBBBKO.
.OABOOOOOOOBBOZOOOZOBBBBBBBBBKO.
.OABBBBBBBBBBOZZZZZOBBBBBBBBBKO.
.OABBBBBBBBBBOOOOOOOBBBOOOOOBKO.
.OABBOOOOOOOBBBBBBBBBBBOZRZOBKO.
.OABBOZUZZZOBBBBBBBBBBBOZZZOBKO.
.OABBOZZZZZOBBOOOOOOOBBOZOZOBKO.
.OABBOZGgZZOBBOZYZZZOBBOZZZOBKO.
.OABBOZZZZZOBBOZZZZZOBBOOOOOBKO.
.OABBOZOOOZOBBOZZOOZOBBBBBBBBKO.
.OABBOZZZZZOBBOZZZZZOBBBBBBBBKO.
.OABBOOOOOOOBBOZOOOZOBBBBBBBBKO.
.OABBBBBBBBBBBOZZZZZOBBBBBBBBKO.
.OABBBBBBBBBBBOOOOOOOBBBBBBBBKO.
.OKKKKKKKKKKKKKKKKKKKKKKKKKKKKO.
.OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
................................
................................
................................
................................
................................
................................
''', IL, w=32)

FARM_CHEST = SG('''
................
................
..OOOOOOOOOOOO..
.OAAAAAAAAAAAAO.
.OABBBBBBBBBBKO.
.OYBBBBBBBBBBYO.
.OyKKKKKKKKKKyO.
.OOOOOOYYOOOOOO.
.OYAAAAYyAAAAYO.
.OyBBBBOOBBBBYO.
.OyBBBBBBBBBBYO.
.OyBBBBBBBBBByO.
.OyKKKKKKKKKKyO.
.OOOOOOOOOOOOOO.
..OO........OO..
................
''', IL)

FARM_DECOR = [
    Decor('SHIPPING_BIN', F, SHIPPING_BIN, doc='farm shipping bin: produce put in is paid for next morning',
          examine='A sturdy shipping bin. The lid says: PAID EACH MORNING.'),
    Decor('PRESERVES_JAR', F, PRESERVES_JAR, doc='preserves jar: fruit becomes jam',
          examine='A big preserves jar. Fruit goes in, jam comes out.'),
    Decor('PRESS', F, PRESS, top='X/.', doc='fruit press 1x2; screw handle over people',
          examine='A fruit press. Turn the screw and juice runs out of the spout.'),
    Decor('DRIER', F, DRIER, doc='drying rack for chilies, fruit and seeds',
          examine='A drying rack with slatted trays. The sun does the rest.'),
    Decor('FOR_SALE', F, FOR_SALE, doc='FOR SALE sign on a post (WILLOW ACRE before you buy it)',
          examine='FOR SALE: WILLOW ACRE. See REEVE at the LAND OFFICE.'),
    Decor('FARM_GATE', F, FARM_GATE, doc='field gate (matches the farm fence)',
          examine='The field gate is locked.'),
    Decor('WORK_BOARD', I, WORK_BOARD, solid='XX/XX', doc='farm work board on the back wall (2x2)',
          examine='A cork board for the farm jobs.'),
    Decor('FARM_CHEST', I, FARM_CHEST, doc='farmhouse storage chest',
          examine='A big wooden storage chest.'),
]
