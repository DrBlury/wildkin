"""Remaining props so every old decor kind has a second-generation
counterpart (see tools/tiles2/legacy.py): outdoor odds and ends, mine
gear, coast and snow specials, study and workshop furniture, fusion
machines, civic buildings and entrances."""

import math

from core import Img, G, hash32, rnd
from paint import stamp, scatter, clump_crown
from interiorart import box
from props import rock, crate, barrel


# ---------------------------------------------------------------------------
# outdoor
# ---------------------------------------------------------------------------

def crate_stack(wood, out):
    img = Img(16, 32)
    img.paste(crate(wood, out, 16, 16), 0, 16)
    top = crate(wood, out, 14, 14)
    img.paste(top, 1, 3)
    return img


def stone_lantern(stone, glow, out, h=32):
    img = Img(16, h)
    img.rect(6, 16, 9, h - 4, stone[1])
    img.vline(6, 16, h - 4, stone[2])
    img.rect(3, h - 4, 12, h - 2, stone[0])
    img.hline(3, 12, h - 4, stone[2])
    img.rect(3, 13, 12, 15, stone[1])
    img.rect(4, 7, 11, 12, stone[1])
    img.rect(6, 8, 9, 11, glow[0])
    img.rect(7, 9, 8, 10, glow[1])
    for y in range(2, 7):
        half = 2 + (y - 2) * 1.3
        img.hline(int(8 - half), int(7 + half), y, stone[2] if y < 5 else stone[1])
    img.set(7, 1, stone[2])
    return img.outline(out)


def flag(pole, cloth, out, frame=0, h=32):
    img = Img(16, h)
    img.vline(3, 1, h - 2, pole[1])
    img.vline(4, 1, h - 2, pole[0])
    img.set(3, 0, pole[2])
    for x in range(5, 15):
        wave = int(round(math.sin((x + frame * 2) / 2.5)))
        for y in range(3, 11):
            img.set(x, y + wave, cloth[1] if y < 7 else cloth[0])
        img.set(x, 3 + wave, cloth[2])
    img.rect(2, h - 3, 5, h - 2, pole[0])
    return img.outline(out)


def picnic_table(wood, out):
    img = Img(32, 32)
    box(img, 3, 8, 28, 20, 3, wood, wood)
    for y in (4, 23):
        img.rect(4, y, 27, y + 2, wood[1])
        img.hline(4, 27, y, wood[2])
    for x in (6, 24):
        img.rect(x, 20, x + 1, 27, wood[0])
    return img.outline(out)


def wheelbarrow(wood, metal, out, load=None):
    img = Img(16, 16)
    for y in range(4, 11):
        inset = (y - 4) // 2
        img.hline(3 + inset, 13 - inset // 2, y, wood[1])
    img.hline(3, 13, 4, wood[2])
    img.line(3, 6, 0, 9, wood[0])
    img.line(3, 8, 0, 11, wood[0])
    img.ellipse(11, 12.5, 2.5, 2.5, metal[0])
    img.set(11, 12, metal[1])
    img.rect(5, 11, 6, 14, wood[0])
    if load:
        img.ellipse(8, 4, 4, 1.8, load[1])
        img.set(7, 3, load[2])
    return img.outline(out)


def shrine(wood, roof, stone, offering, out, w=32, h=32):
    img = Img(w, h)
    img.rect(3, h - 6, w - 4, h - 2, stone[1])
    img.hline(3, w - 4, h - 6, stone[2])
    for x in (6, w - 8):
        img.rect(x, 12, x + 1, h - 6, wood[1])
        img.vline(x, 12, h - 6, wood[2])
    img.rect(9, 16, w - 10, h - 7, wood[0])
    img.rect(12, h - 12, w - 13, h - 8, offering)
    for y in range(3, 12):
        half = 8 + (y - 3) * 0.9
        img.hline(int(w / 2 - half), int(w / 2 + half), y, roof[2] if y < 8 else roof[1])
    img.hline(2, w - 3, 11, roof[0])
    img.hline(int(w / 2) - 5, int(w / 2) + 4, 3, roof[2])
    return img.outline(out)


def telescope(metal, wood, out):
    img = Img(16, 32)
    img.line(3, 30, 8, 14, wood[1])
    img.line(13, 30, 8, 14, wood[1])
    img.line(8, 30, 8, 14, wood[0])
    for t in range(12):
        x = 3 + t
        y = 14 - int(t * 0.8)
        img.rect(x, y - 1, x, y + 1, metal[1] if t % 4 else metal[2])
    img.rect(14, 3, 15, 5, metal[2])
    return img.outline(out)


def rain_gauge(metal, glass, water, out):
    img = Img(16, 16)
    img.rect(6, 2, 9, 12, glass)
    img.rect(6, 8, 9, 12, water)
    img.vline(6, 2, 12, metal[1])
    img.rect(4, 13, 11, 14, metal[0])
    for y in (4, 6, 8, 10):
        img.set(9, y, metal[0])
    return img.outline(out)


def ore_pile(R, ore, out):
    img = rock(32, 16, R, out, 3, parts=[(10, 11, 8, 4), (21, 11, 8, 4), (15, 8, 7, 4)])
    for (x, y) in scatter(28, 10, 8, 4, margin=3, min_dist=4):
        if img.get(x + 2, y + 3) not in (None, out):
            img.set(x + 2, y + 3, ore[1])
            img.set(x + 3, y + 3, ore[0])
    return img


def headframe(wood, metal, out, w=48, h=64):
    """Mine headframe: a timber tower with a pulley wheel (3x4)."""
    img = Img(w, h)
    for (x0, x1) in ((6, 16), (w - 7, w - 17)):
        img.line(x0, h - 2, x1, 10, wood[1])
        img.line(x0 + 1, h - 2, x1 + 1, 10, wood[2])
    for y in range(18, h - 4, 10):
        img.line(10, y, w - 11, y, wood[0])
        img.line(10, y, w - 11, y + 10, wood[0])
    img.rect(14, 8, w - 15, 12, wood[1])
    img.hline(14, w - 15, 8, wood[2])
    img.ellipse(w / 2, 6, 6, 6, metal[0])
    img.ellipse(w / 2, 6, 4.5, 4.5, None)
    for a in range(0, 360, 45):
        img.line(int(w / 2), 6, int(w / 2 + math.cos(math.radians(a)) * 5), int(6 + math.sin(math.radians(a)) * 5),
                 metal[1])
    img.vline(int(w / 2), 12, h - 6, metal[0])
    return img.outline(out)


def mine_mouth(R, beam, void, out, w=48, h=32):
    """Adit entrance in a rock face: timber-framed dark opening (3x2)."""
    import terrain as T
    tex = T.lump_texture(R, 48, 32, 2, rx=5.5, ry=4, sx=8, sy=6)
    img = Img(w, h)
    for y in range(h):
        for x in range(w):
            if abs(x + 0.5 - w / 2) < w / 2 - 1 - max(0, 6 - y):
                img.p[y][x] = tex.p[y][x]
    img.rect(w / 2 - 9, 8, w / 2 + 8, h - 1, void)
    img.rect(w / 2 - 11, 8, w / 2 - 9, h - 1, beam[1])
    img.rect(w / 2 + 8, 8, w / 2 + 10, h - 1, beam[0])
    img.rect(w / 2 - 12, 5, w / 2 + 11, 8, beam[1])
    img.hline(int(w / 2) - 12, int(w / 2) + 11, 5, beam[2])
    return img.outline(out)


def stag_altar(stone, antler, out, w=32, h=32):
    img = Img(w, h)
    box(img, 4, 14, w - 5, h - 2, 7, stone, stone)
    for side in (-1, 1):
        cx = w / 2 + side * 3
        img.line(int(cx), 14, int(cx + side * 6), 4, antler[1])
        img.line(int(cx + side * 3), 9, int(cx + side * 8), 8, antler[1])
        img.line(int(cx + side * 5), 6, int(cx + side * 4), 1, antler[2])
    img.ellipse(w / 2, 13, 3, 2, antler[0])
    return img.outline(out)


def old_hearth(stone, ash, out, w=32, h=32):
    """Ruined stone hearth from an abandoned homestead (2x2)."""
    img = Img(w, h)
    for (x, y, rx, ry) in ((6, 22, 4, 3), (12, 25, 4, 3), (20, 25, 4, 3), (26, 22, 4, 3), (8, 16, 3.5, 3),
                           (24, 16, 3.5, 3), (10, 9, 3.2, 3), (22, 10, 3.2, 3)):
        img.ellipse(x, y, rx, ry, stone[1])
        img.ellipse(x - 0.8, y - 0.8, rx - 1.4, ry - 1.2, stone[2])
    img.ellipse(16, 18, 5, 3.5, ash[0])
    img.ellipse(16, 18, 3.5, 2, ash[1])
    return img.outline(out)


def small_flowers(petals, stem):
    """Transparent sprinkle of tiny flowers (decor, walkable)."""
    img = Img(16, 16)
    for i, (x, y) in enumerate(((3, 4), (10, 3), (6, 9), (12, 11), (2, 12))):
        p = petals[i % len(petals)]
        img.set(x, y, p)
        img.set(x + 1, y, p)
        img.set(x, y + 1, p)
        img.set(x + 1, y + 1, petals[(i + 1) % len(petals)])
        img.set(x, y + 2, stem)
    return img


def fallen_leaves(colors):
    img = Img(16, 16)
    for i, (x, y) in enumerate(scatter(13, 13, 7, 3, margin=1, min_dist=3.5)):
        c = colors[i % len(colors)]
        img.set(x, y, c)
        img.set(x + 1, y, c)
        img.set(x + 1, y + 1, colors[(i + 1) % len(colors)])
    return img


def river_foam(W, frame):
    img = Img(16, 16)
    for i in range(6):
        x = (i * 5 + frame * 3) % 16
        y = (i * 7 + frame) % 16
        img.set(x, y, W[1])
        img.set(x + 1, y, W[0])
    return img


# ---------------------------------------------------------------------------
# farm, coast, snow, cave, volcanic, dream specials
# ---------------------------------------------------------------------------

def preserves(glass, fills, lid, out):
    img = Img(16, 16)
    for i, x in enumerate((2, 7, 12)):
        f = fills[i % len(fills)]
        img.rect(x - 1, 7, x + 2, 13, glass)
        img.rect(x - 1, 9, x + 2, 13, f)
        img.rect(x - 1, 5, x + 2, 6, lid)
    return img.outline(out)


def cider_press(wood, metal, out):
    img = Img(32, 32)
    box(img, 4, 18, 27, 29, 6, wood, wood)
    img.rect(8, 8, 23, 18, wood[1])
    for x in range(9, 23, 3):
        img.vline(x, 9, 17, wood[0])
    img.vline(16, 1, 8, metal[1])
    img.hline(10, 22, 2, metal[1])
    img.hline(10, 22, 1, metal[2])
    return img.outline(out)


def drying_rack(wood, hang, out):
    img = Img(32, 32)
    for x in (3, 27):
        img.rect(x, 4, x + 1, 30, wood[1])
    for y in (6, 14):
        img.hline(3, 28, y, wood[1])
        for x in range(6, 26, 4):
            img.rect(x, y + 1, x + 1, y + 5, hang[(x // 4) % len(hang)])
    return img.outline(out)


def lifebuoy(red, white, out):
    img = Img(16, 16)
    img.ellipse(8, 8, 6, 6, white)
    img.ellipse(8, 8, 3, 3, None)
    for (x, y) in ((8, 2), (8, 13), (2, 8), (13, 8)):
        img.rect(x - 1, y - 1, x + 1, y + 1, red)
    return img.outline(out)


def salt_heap(salt, out):
    img = Img(32, 16)
    img.ellipse(16, 12, 14, 5, salt[1])
    img.ellipse(13, 10, 9, 4, salt[2])
    img.ellipse(18, 7, 6, 3, salt[2])
    img.set(12, 7, salt[2])
    img.hline(4, 28, 15, salt[0])
    return img.outline(out)


def bell_buoy(red, metal, out, frame):
    img = Img(16, 32)
    bob = frame % 2
    img.ellipse(8, 26 + bob, 6, 4, red[1])
    img.ellipse(7, 25 + bob, 4, 2.5, red[2])
    for x in (4, 11):
        img.line(x, 23 + bob, 8, 10 + bob, metal[1])
    img.ellipse(8, 17 + bob, 3, 3, metal[2])
    img.rect(6, 17 + bob, 10, 19 + bob, metal[1])
    img.set(8, 20 + bob, metal[0])
    return img.outline(out)


def crab_shell(shell, out):
    img = Img(16, 16)
    img.ellipse(8, 10, 5, 3.5, shell[1])
    img.ellipse(7, 9, 3, 2, shell[2])
    for x in (3, 5, 11, 13):
        img.set(x, 13, shell[0])
    img.line(3, 8, 1, 6, shell[1])
    img.line(13, 8, 15, 6, shell[1])
    return img.outline(out)


HERON = '''
......oo..
.....ohlo.
.....olldo
....ool...
...oll....
...olo....
..olllo...
.ollllmo..
ollllmmmo.
olllmmmmdo
.ollmmmmdo
..oommmdo.
....odo...
....odo...
....odo...
...oodoo..
'''


def heron_statue(stone, out, plinth):
    img = Img(16, 32)
    img.rect(2, 24, 13, 30, plinth[1])
    img.hline(2, 13, 24, plinth[2])
    img.hline(2, 13, 30, plinth[0])
    body = G(HERON, {'o': out, 'd': stone[0], 'm': stone[1], 'l': stone[2], 'h': stone[3]})
    img.paste(body, 3, 24 - body.h)
    return img.outline(out)


def ferry_boat(hull, deck, cabin, out, w=64, h=48):
    img = Img(w, h)
    for y in range(26, 44):
        inset = (y - 26) * 0.5
        for x in range(int(3 + inset), int(w - 3 - inset * 0.6)):
            img.set(x, y, hull[1] if y < 36 else hull[0])
    img.hline(3, w - 4, 26, hull[2])
    img.rect(6, 22, w - 8, 26, deck[1])
    img.hline(6, w - 8, 22, deck[2])
    img.rect(18, 8, 44, 22, cabin[1])
    img.hline(18, 44, 8, cabin[2])
    for x in range(21, 43, 6):
        img.rect(x, 12, x + 3, 16, hull[0])
    img.rect(30, 1, 34, 8, hull[1])
    img.hline(30, 34, 1, hull[2])
    return img.outline(out)


def ice_blocks(I, out):
    img = Img(16, 16)
    box(img, 1, 6, 8, 14, 4, I[1:], I)
    box(img, 7, 3, 14, 12, 4, I[1:], I)
    img.set(9, 5, I[-1])
    return img.outline(out)


WOLF = '''
..o.......o.......
.oho.....olo......
.ohlo...ollo......
.ohllooolllo......
..olllllllmo......
..ohlodllodmo.....
..ollllllllmo.....
...oolllllmo......
....ollllmmo......
....olllllmmoo....
...ollhllllmmmo...
...olhllllllmmmo..
...ollllllllmmmdo.
..olllllllllmmmdo.
..olllllllllmmmmdo
..ollllooolllmmmdo
..olllo...ollmmdo.
...ooo.....oooooo.
'''


def wolf_statue(stone, out, plinth):
    img = Img(32, 48)
    img.rect(3, 35, 28, 45, plinth[1])
    img.hline(3, 28, 35, plinth[2])
    img.hline(3, 28, 45, plinth[0])
    body = G(WOLF, {'o': out, 'd': stone[0], 'm': stone[1], 'l': stone[2], 'h': stone[3]})
    img.paste(body, 7, 35 - body.h + 1)
    return img.outline(out)


def ice_statue(I, out, plinth):
    img = wolf_statue(I, out, plinth)
    return img


def rime_pillar(I, stone, out, h=48):
    img = Img(16, h)
    for y in range(4, h - 3):
        for x in range(4, 12):
            u = (x - 4) / 7
            img.set(x, y, stone[2] if u < 0.3 else (stone[1] if u < 0.8 else stone[0]))
    for y in range(4, h - 3, 3):
        img.set(4 + (y % 5), y, I[2])
        img.set(11, y + 1, I[1])
    img.rect(2, 1, 13, 4, I[2])
    img.hline(2, 13, 1, I[3])
    img.rect(2, h - 4, 13, h - 2, stone[0])
    return img.outline(out)


def sky_arch(stone, I, out, w=48, h=48):
    img = Img(w, h)
    for x in (4, w - 10):
        img.rect(x, 12, x + 5, h - 2, stone[1])
        img.vline(x, 12, h - 2, stone[2])
    for y in range(0, 14):
        for x in range(4, w - 4):
            d = math.hypot((x - w / 2) / (w / 2 - 4), (y - 14) / 13)
            if 0.7 < d <= 1.0:
                img.set(x, y, stone[2] if y < 6 else stone[1])
    for x in range(8, w - 8, 5):
        img.set(x, 2 + abs(x - w // 2) // 5, I[3])
    return img.outline(out)


def ski_rack(wood, skis, out):
    img = Img(16, 32)
    img.rect(1, 12, 14, 13, wood[1])
    img.rect(1, 24, 14, 25, wood[1])
    for x in (1, 14):
        img.vline(x, 10, 30, wood[0])
    for i, x in enumerate((3, 6, 9, 12)):
        img.vline(x, 4 + (i % 2) * 2, 29, skis[i % len(skis)])
        img.set(x, 3 + (i % 2) * 2, skis[i % len(skis)])
    return img.outline(out)


def wash_bucket(wood, water, out):
    img = Img(16, 16)
    img.ellipse(8, 10, 5.5, 4.5, wood[1])
    img.ellipse(8, 8, 5.5, 2.4, wood[2])
    img.ellipse(8, 8.3, 4.3, 1.5, water)
    img.hline(3, 13, 11, wood[0])
    return img.outline(out)


def light_shaft(L, w=16, h=32):
    """Moonbeam through a ceiling crack: dithered pale column (top layer)."""
    img = Img(w, h)
    for y in range(h):
        x0 = 4 + y // 8
        for x in range(x0, x0 + 7):
            if (x + y) % 2 == 0:
                img.set(x, y, L[1] if 1 < x - x0 < 5 else L[0])
    return img


def moth_dais(stone, glow, out):
    img = Img(32, 32)
    img.ellipse(16, 20, 13, 8, stone[0])
    img.ellipse(16, 19, 12, 7, stone[1])
    img.ellipse(16, 18, 9, 5, stone[2])
    for (x, y) in ((10, 17), (22, 17), (16, 15), (16, 21)):
        img.set(x, y, glow[1])
    img.ellipse(16, 18, 2.5, 1.6, glow[0])
    return img.outline(out)


def fungal_shelf(cap, stem, out):
    img = Img(16, 16)
    for (y, x0, x1) in ((4, 2, 9), (8, 6, 14), (12, 1, 8)):
        img.rect(x0, y, x1, y + 1, cap[1])
        img.hline(x0 + 1, x1 - 1, y - 1, cap[2])
        img.hline(x0, x1, y + 2, cap[0])
    img.vline(1, 2, 15, stem)
    return img.outline(out)


def furnace(brick, fire, metal, out, frame=0):
    img = Img(32, 32)
    for y in range(8, 30):
        for x in range(3, 29):
            row = y // 3
            c = brick[1]
            if y % 3 == 2 or (x + (row % 2) * 2) % 4 == 0:
                c = brick[0]
            img.set(x, y, c)
    img.rect(10, 16, 21, 28, metal[0])
    img.ellipse(15.5, 16, 6, 3, metal[0])
    for x in range(11, 21):
        hh = 4 + ((x + frame) % 3) * 2
        img.vline(x, 28 - hh, 27, fire[1] if x % 2 else fire[2])
    img.rect(12, 0, 19, 8, brick[1])
    img.hline(11, 20, 0, metal[1])
    return img.outline(out)


def tool_rack(wood, metal, out):
    img = Img(32, 32)
    img.rect(2, 4, 29, 6, wood[1])
    for x in (3, 28):
        img.vline(x, 4, 30, wood[0])
    tools = [(7, 'hammer'), (13, 'tongs'), (19, 'saw'), (24, 'shovel')]
    for (x, k) in tools:
        img.vline(x, 7, 26, wood[2])
        if k == 'hammer':
            img.rect(x - 2, 7, x + 2, 9, metal[1])
        elif k == 'tongs':
            img.line(x, 20, x - 2, 27, metal[1])
            img.line(x, 20, x + 2, 27, metal[1])
        elif k == 'saw':
            img.rect(x, 12, x + 3, 22, metal[2])
        else:
            img.rect(x - 2, 22, x + 2, 28, metal[1])
    return img.outline(out)


def big_bell(metal, frame_c, out):
    img = Img(32, 48)
    for x in (3, 28):
        img.rect(x, 4, x + 1, 46, frame_c[1])
    img.rect(2, 3, 29, 5, frame_c[1])
    img.hline(2, 29, 3, frame_c[2])
    for y in range(8, 32):
        t = (y - 8) / 24
        half = 4 + t ** 1.5 * 9
        for x in range(int(16 - half), int(16 + half)):
            u = (x + 0.5 - (16 - half)) / (2 * half)
            img.set(x, y, metal[3] if u < 0.2 else (metal[2] if u < 0.5 else (metal[1] if u < 0.85 else metal[0])))
    img.hline(3, 28, 32, metal[0])
    img.ellipse(16, 34, 2, 2, metal[1])
    return img.outline(out)


def book_pile(books, out):
    img = Img(16, 16)
    y = 13
    for i, b in enumerate(books[:4]):
        w = 10 - i
        x = 3 + (i % 2)
        img.rect(x, y - 2, x + w, y, b[1])
        img.hline(x, x + w, y - 2, b[2])
        img.vline(x + w, y - 2, y, b[0])
        y -= 3
    return img.outline(out)


def reading_desk(wood, paper, lamp, out):
    img = Img(32, 32)
    box(img, 2, 10, 29, 24, 5, wood, wood)
    for x in (4, 26):
        img.rect(x, 24, x + 1, 29, wood[0])
    img.rect(8, 11, 17, 16, paper[1])
    img.vline(12, 11, 16, paper[0])
    img.rect(21, 5, 25, 11, lamp[1])
    img.hline(20, 26, 5, lamp[2])
    img.vline(23, 11, 14, wood[0])
    return img.outline(out)


def petals(colors):
    img = Img(16, 16)
    for i, (x, y) in enumerate(scatter(14, 14, 9, 7, margin=1, min_dist=3)):
        img.set(x, y, colors[i % len(colors)])
        if i % 3 == 0:
            img.set(x + 1, y, colors[(i + 1) % len(colors)])
    return img


def root_bridge(wood, moss, out, w=48, h=32):
    img = Img(w, h)
    for k, y0 in enumerate((8, 13, 18)):
        for x in range(w):
            y = y0 + int(2 * math.sin(x / (w - 1) * math.pi + k))
            img.rect(x, y, x, y + 3, wood[1] if (x + k) % 5 else wood[0])
            img.set(x, y, wood[2])
    for x in range(2, w - 2, 6):
        img.set(x, 8 + int(2 * math.sin(x / (w - 1) * math.pi)), moss)
    return img.outline(out)


# ---------------------------------------------------------------------------
# interior furniture
# ---------------------------------------------------------------------------

def cooktop(metal, fire, out, frame=0):
    img = Img(16, 16)
    box(img, 1, 3, 14, 14, 5, metal, metal)
    for x in (5, 10):
        img.ellipse(x, 6, 2.2, 1.4, metal[0])
        img.set(x, 6, fire[frame % 2])
    return img.outline(out)


def cauldron(metal, brew, fire, out, frame=0):
    img = Img(16, 16)
    img.ellipse(8, 9, 6.5, 5, metal[1])
    img.ellipse(7, 8.5, 4.5, 3.5, metal[2])
    img.ellipse(8, 6, 6, 2, metal[0])
    img.ellipse(8, 6, 5, 1.4, brew[0])
    img.set(6 + frame % 3, 5, brew[1])
    img.set(10 - frame % 2, 6, brew[1])
    img.hline(5, 11, 15, fire)
    return img.outline(out)


def anvil_in(metal, block, out):
    from fireart import anvil
    return anvil(metal, block, out)


def fusion_machine(kind, metal, glow, glass, out, frame=0):
    """The four fusion lab devices (extractor, mixer, loom, tanks), 2x2."""
    img = Img(32, 32)
    box(img, 2, 10, 29, 30, 10, metal, metal)
    if kind == 'extractor':
        img.rect(8, 1, 23, 12, glass[1])
        img.ellipse(15.5, 7, 5, 4, glow[frame % 2])
        img.rect(6, 0, 25, 1, metal[2])
    elif kind == 'mixer':
        for i, x in enumerate((7, 16, 24)):
            img.rect(x - 2, 2, x + 2, 11, glass[1])
            img.rect(x - 2, 6 + (i + frame) % 3, x + 2, 11, glow[i % 2])
    elif kind == 'loom':
        for x in range(5, 27, 3):
            img.vline(x, 2, 11, glow[(x // 3 + frame) % 2])
        img.hline(4, 27, 2, metal[2])
    else:
        for x in (8, 22):
            img.ellipse(x, 6, 5, 5, glass[1])
            img.ellipse(x, 7 + frame % 2, 3.5, 3, glow[0])
    img.rect(10, 20, 21, 24, metal[0])
    img.set(12 + frame % 6, 22, glow[1])
    return img.outline(out)


def pylon(metal, glow, out, frame=0, h=32):
    img = Img(16, h)
    img.rect(6, 6, 9, h - 3, metal[1])
    img.vline(6, 6, h - 3, metal[2])
    for y in range(8, h - 4, 4):
        img.hline(4, 11, y, metal[0])
    img.rect(3, h - 3, 12, h - 2, metal[0])
    img.ellipse(7.5, 4, 3.5, 3, glow[frame % 2])
    img.set(6, 3, glow[1])
    return img.outline(out)


def coil(metal, copper, glow, out, frame=0, h=32):
    img = Img(16, h)
    for y in range(8, h - 4):
        img.hline(4, 11, y, copper[1] if y % 2 else copper[2])
    img.rect(3, h - 4, 12, h - 2, metal[1])
    img.ellipse(7.5, 5, 4.5, 3, metal[2])
    if frame % 2:
        img.line(2, 2, 5, 5, glow)
        img.line(13, 1, 10, 5, glow)
    return img.outline(out)


def vat(metal, fluid, out, frame=0):
    img = Img(16, 32)
    img.rect(2, 6, 13, 29, metal[1])
    img.rect(4, 8, 11, 26, fluid[0])
    img.rect(4, 12 + frame % 2, 11, 26, fluid[1])
    img.set(6, 18 - frame % 3, fluid[2])
    img.hline(2, 13, 6, metal[2])
    img.hline(2, 13, 29, metal[0])
    return img.outline(out)


def dynamo(metal, copper, out, frame=0):
    img = Img(32, 16)
    box(img, 2, 3, 29, 14, 4, metal, metal)
    img.ellipse(10, 7, 5, 3.5, copper[1])
    img.line(10, 7, 10 + int(4 * math.cos(frame)), 7 + int(3 * math.sin(frame)), copper[0])
    img.rect(18, 5, 26, 9, copper[2])
    return img.outline(out)


def bike_display(frame_c, tyre, stand, out):
    from cityart import parked_bike
    img = Img(32, 32)
    box(img, 1, 20, 30, 30, 4, stand, stand)
    img.paste(parked_bike(frame_c, tyre, out), 0, 8)
    return img


def gears(metal, out):
    img = Img(16, 16)
    for (cx, cy, r) in ((6, 7, 4.5), (11, 11, 3.2)):
        for a in range(0, 360, 30):
            x = cx + math.cos(math.radians(a)) * (r + 1)
            y = cy + math.sin(math.radians(a)) * (r + 1)
            img.set(int(x), int(y), metal[1])
        img.ellipse(cx, cy, r, r, metal[1])
        img.ellipse(cx - 0.6, cy - 0.6, r - 1.5, r - 1.5, metal[2])
        img.ellipse(cx, cy, 1.2, 1.2, metal[0])
    return img.outline(out)


def file_cabinet(metal, out):
    img = Img(16, 32)
    box(img, 2, 4, 13, 30, 22, metal, metal)
    for y in (12, 18, 24):
        img.hline(3, 12, y, metal[0])
        img.rect(6, y - 3, 9, y - 3, metal[2])
    return img.outline(out)


def wall_banner(cloth, rod, emblem, out):
    from dungeonart import banner
    return banner(cloth, rod, emblem, out)


def work_board(wood, paper, pin, out):
    img = Img(32, 16)
    img.rect(1, 1, 30, 13, wood[1])
    img.rect(2, 2, 29, 12, wood[0])
    for i, x in enumerate(range(4, 27, 6)):
        img.rect(x, 3 + i % 2, x + 4, 9 + i % 2, paper[1])
        img.set(x + 2, 3 + i % 2, pin)
        img.hline(x + 1, x + 3, 6 + i % 2, paper[0])
    return img.outline(out)


def chest(wood, metal, out):
    img = Img(16, 16)
    box(img, 2, 4, 13, 14, 6, wood, wood)
    img.hline(2, 13, 8, metal[1])
    img.rect(7, 7, 8, 10, metal[2])
    return img.outline(out)


def radio(wood, cloth, dial, out):
    img = Img(16, 16)
    box(img, 2, 3, 13, 14, 9, wood, wood)
    img.rect(4, 7, 8, 12, cloth)
    img.ellipse(11, 9, 1.6, 1.6, dial)
    img.ellipse(11, 12, 1, 1, dial)
    return img.outline(out)


def desk(wood, paper, out):
    img = Img(32, 16)
    box(img, 1, 1, 30, 14, 6, wood, wood)
    img.rect(4, 2, 12, 6, paper)
    img.rect(20, 9, 28, 13, wood[0])
    return img.outline(out)


def tea_set(china, tea, out):
    img = Img(16, 16)
    img.ellipse(6, 9, 3.5, 3, china[1])
    img.ellipse(5.5, 8.5, 2, 1.6, china[2])
    img.line(9, 8, 11, 6, china[1])
    img.rect(5, 5, 7, 6, china[1])
    for x in (11, 13):
        img.rect(x - 1, 11, x, 13, china[1])
        img.set(x - 1, 11, tea)
    return img.outline(out)


def cushion(cloth, out):
    img = Img(16, 16)
    img.rect(3, 6, 12, 13, cloth[1])
    img.hline(3, 12, 6, cloth[2])
    img.vline(3, 6, 13, cloth[2])
    img.set(7, 9, cloth[0])
    img.set(8, 10, cloth[0])
    return img.outline(out)


def kin_basket(wicker, blanket, out):
    img = Img(16, 16)
    img.ellipse(8, 10, 7, 4.5, wicker[1])
    for x in range(2, 15, 2):
        img.vline(x, 7, 13, wicker[0])
    img.ellipse(8, 8.5, 5.5, 2.5, blanket[1])
    img.ellipse(7, 8, 3, 1.2, blanket[2])
    return img.outline(out)


def small_bookshelf(wood, books, out):
    from interiorart import bookshelf
    img = bookshelf(wood, books, out, w=16, h=32)
    return img


def toy_box(wood, toys, out):
    img = Img(16, 16)
    box(img, 2, 5, 13, 14, 6, wood, wood)
    img.ellipse(6, 5, 2, 2, toys[0])
    img.rect(9, 3, 11, 5, toys[1])
    return img.outline(out)


def coat_rack(wood, coats, out):
    img = Img(16, 32)
    img.vline(8, 3, 29, wood[1])
    img.rect(5, 29, 11, 30, wood[0])
    img.hline(4, 12, 4, wood[2])
    img.rect(3, 6, 6, 16, coats[0])
    img.rect(10, 6, 12, 13, coats[1])
    return img.outline(out)


def cactus_pot(pot, green, out):
    img = Img(16, 16)
    img.rect(5, 10, 10, 14, pot[1])
    img.hline(4, 11, 10, pot[2])
    img.rect(7, 3, 9, 10, green[1])
    img.vline(7, 3, 10, green[2])
    img.rect(4, 5, 5, 8, green[1])
    img.rect(10, 4, 11, 7, green[1])
    return img.outline(out)


PLUSH = '''
.o.....o.
oho...olo
olhooolmo
.ollllmo.
olldlldmo
ollllllmo
.ollllmo.
olllllmmo
.oo.oo.o.
'''


def kin_plush(fur, out):
    img = Img(16, 16)
    body = G(PLUSH, {'o': out, 'd': fur[0], 'm': fur[1], 'l': fur[2], 'h': fur[3]})
    img.paste(body, 3, 5)
    return img


def brick_oven(brick, fire, out, frame=0):
    img = Img(32, 32)
    img.ellipse(16, 16, 14, 12, brick[1])
    for y in range(4, 28, 3):
        for x in range(2, 30):
            if img.get(x, y) and (x + (y // 3) * 2) % 5 == 0:
                img.set(x, y, brick[0])
    img.rect(2, 16, 29, 29, brick[1])
    img.rect(10, 16, 21, 26, brick[0])
    img.ellipse(15.5, 16, 6, 3, brick[0])
    for x in range(11, 21):
        img.vline(x, 26 - 2 - (x + frame) % 3, 25, fire[(x + frame) % 2])
    return img.outline(out)


def lantern_rack(wood, glow, out):
    img = Img(32, 16)
    img.hline(1, 30, 3, wood[1])
    for x in (1, 30):
        img.vline(x, 3, 15, wood[0])
    for x in range(5, 28, 7):
        img.rect(x, 5, x + 3, 10, wood[0])
        img.rect(x + 1, 6, x + 2, 9, glow)
    return img.outline(out)


def bread_display(wood, bread, out):
    img = Img(32, 16)
    box(img, 1, 5, 30, 14, 4, wood, wood)
    for x in range(3, 28, 5):
        img.ellipse(x + 2, 6, 2.5, 1.8, bread[1])
        img.set(x + 1, 5, bread[2])
    return img.outline(out)


def microscope(metal, out):
    img = Img(16, 16)
    img.rect(4, 13, 11, 14, metal[0])
    img.line(6, 12, 9, 3, metal[1])
    img.rect(8, 2, 10, 4, metal[2])
    img.hline(5, 10, 9, metal[1])
    return img.outline(out)


def telegraph(wood, metal, out):
    img = Img(16, 16)
    box(img, 2, 7, 13, 14, 3, wood, wood)
    img.rect(5, 4, 10, 7, metal[1])
    img.set(7, 3, metal[2])
    img.line(10, 5, 13, 3, metal[0])
    return img.outline(out)


def chalkboard(wood, board, chalk, out):
    img = Img(32, 16)
    img.rect(1, 1, 30, 13, wood[1])
    img.rect(2, 2, 29, 12, board)
    for x in range(4, 27, 2):
        if (x // 2) % 3:
            img.set(x, 5, chalk)
    img.line(5, 9, 12, 7, chalk)
    img.line(16, 9, 26, 9, chalk)
    return img.outline(out)


def poster(paper, ink, out, kind='map'):
    img = Img(16, 16)
    img.rect(2, 2, 13, 13, paper[1])
    img.hline(2, 13, 2, paper[2])
    if kind == 'map':
        img.line(4, 10, 8, 5, ink[0])
        img.line(8, 5, 12, 9, ink[0])
        img.ellipse(6, 8, 1.5, 1.2, ink[1])
    elif kind == 'calendar':
        img.rect(2, 2, 13, 4, ink[1])
        for y in range(6, 13, 2):
            for x in range(3, 13, 2):
                img.set(x, y, ink[0])
    return img.outline(out)


def pennant(cloth, stick, out):
    img = Img(16, 16)
    img.vline(2, 2, 13, stick)
    for x in range(3, 14):
        span = int((14 - x) * 0.4)
        img.vline(x, 7 - span, 7 + span, cloth[1] if x % 3 else cloth[2])
    return img.outline(out)


def ship_wheel(wood, out):
    img = Img(16, 16)
    img.ellipse(8, 8, 5, 5, wood[1])
    img.ellipse(8, 8, 3.5, 3.5, None)
    for a in range(0, 360, 45):
        img.line(8, 8, int(8 + math.cos(math.radians(a)) * 7), int(8 + math.sin(math.radians(a)) * 7), wood[2])
    img.ellipse(8, 8, 1.3, 1.3, wood[0])
    return img.outline(out)


def fish_trophy(wood, fish, out):
    img = Img(16, 16)
    img.rect(2, 4, 13, 12, wood[1])
    img.ellipse(7, 8, 4, 2, fish[1])
    img.set(5, 7, fish[2])
    img.line(11, 8, 13, 6, fish[1])
    img.line(11, 8, 13, 10, fish[1])
    return img.outline(out)


def ship_bottle(glass, ship, out):
    img = Img(16, 16)
    img.rect(2, 7, 12, 12, glass)
    img.rect(12, 8, 14, 11, glass)
    img.rect(4, 10, 9, 11, ship[0])
    img.vline(7, 7, 10, ship[0])
    img.rect(5, 8, 6, 9, ship[1])
    return img.outline(out)


def net_wall(rope, float_c, out):
    img = Img(32, 16)
    for y in range(2, 14):
        for x in range(2, 30):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                img.set(x, y, rope)
    for x in (6, 16, 26):
        img.ellipse(x, 3, 1.6, 1.6, float_c)
    return img


def script_pedestal(stone, paper, glow, out):
    img = Img(16, 32)
    img.rect(5, 14, 10, 29, stone[1])
    img.vline(5, 14, 29, stone[2])
    img.rect(3, 29, 12, 30, stone[0])
    img.rect(2, 10, 13, 14, stone[2])
    img.rect(4, 7, 11, 11, paper[1])
    img.vline(7, 7, 11, paper[0])
    img.set(9, 5, glow)
    img.set(6, 4, glow)
    return img.outline(out)


# ---------------------------------------------------------------------------
# entrances
# ---------------------------------------------------------------------------

def cave_mouth(R, void, out, w=48, h=48):
    """A cave opening in a rock outcrop (3x3; enter at the bottom middle)."""
    import terrain as T
    tex = T.lump_texture(R, 48, 48, 4, rx=6, ry=4.5, sx=8.5, sy=6.5)
    img = Img(w, h)
    for y in range(h):
        for x in range(w):
            hump = 6 + 5 * math.cos((x - w / 2) / (w / 2) * math.pi / 2)
            if y > h - hump * 4.5 and abs(x + 0.5 - w / 2) < w / 2 - 1:
                img.p[y][x] = tex.p[y][x]
    img.ellipse(w / 2, h - 6, 9, 12, void)
    img.rect(w / 2 - 9, h - 8, w / 2 + 8, h - 1, void)
    return img.outline(out)


def tunnel_arch(brick, void, out, w=48, h=48):
    img = Img(w, h)
    for y in range(8, h):
        for x in range(2, w - 2):
            row = y // 4
            c = brick[1]
            if y % 4 == 3 or (x + (row % 2) * 4) % 8 == 0:
                c = brick[0]
            if y < 10:
                c = brick[2]
            img.set(x, y, c)
    img.ellipse(w / 2, h - 12, 12, 12, void)
    img.rect(w / 2 - 12, h - 12, w / 2 + 11, h - 1, void)
    for a in range(180, 361, 12):
        x = w / 2 + math.cos(math.radians(a)) * 14
        y = h - 12 + math.sin(math.radians(a)) * 14
        img.rect(int(x) - 1, int(y) - 1, int(x) + 1, int(y) + 1, brick[2])
    return img.outline(out)


def bone_gate(bone, void, out, w=48, h=48):
    img = Img(w, h)
    img.rect(w / 2 - 10, 14, w / 2 + 9, h - 1, void)
    for side in (-1, 1):
        x = int(w / 2 + side * 14)
        for y in range(10, h - 1, 5):
            img.ellipse(x, y + 2, 4, 2.4, bone[1])
            img.ellipse(x - 1, y + 1.5, 2.4, 1.2, bone[2])
    for x in range(int(w / 2 - 16), int(w / 2 + 16), 6):
        img.ellipse(x + 3, 9, 3.2, 3, bone[1])
        img.set(x + 2, 9, bone[0])
        img.set(x + 4, 9, bone[0])
    return img.outline(out)


def crack(R, void, out):
    """A narrow fissure in a wall face you can squeeze through (1x2)."""
    img = Img(16, 32)
    for y in range(2, 31):
        half = 1.5 + 2 * math.sin(y / 31 * math.pi)
        cx = 8 + int(1.5 * math.sin(y / 5.0))
        for x in range(int(cx - half), int(cx + half) + 1):
            img.set(x, y, void)
        img.set(int(cx - half) - 1, y, R[0])
        img.set(int(cx + half) + 1, y, R[2])
    return img
