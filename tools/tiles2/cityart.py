"""City art: clock tower, electric street lamps, tesla beacon, bikes, cafe
tables, stone arch bridge, tram track, planter trees, kiosks."""

import math

from core import Img, hash32, rnd
from paint import stamp, scatter, clump_crown


def clock_tower(stone, roof, face, gold, out, w=48, h=96):
    img = Img(w, h)
    cx = w / 2
    top = 28
    for y in range(top, h - 2):
        for x in range(8, w - 8):
            row = (y - top) // 4
            c = stone[2]
            if (y - top) % 4 == 3 or (x + (row % 2) * 4) % 8 == 0:
                c = stone[1]
            if x < 10:
                c = stone[3]
            if x > w - 11:
                c = stone[0]
            img.set(x, y, c)
    # roof: steep pyramid
    for y in range(4, top):
        half = 3 + (y - 4) * 0.72
        for x in range(int(cx - half), int(cx + half)):
            img.set(x, y, roof[3] if x < cx - 2 else (roof[2] if x < cx + 2 else roof[1]))
        if y % 4 == 3:
            img.hline(int(cx - half), int(cx + half) - 1, y, roof[0])
    img.hline(int(cx - 20), int(cx + 19), top, roof[0])
    img.rect(cx - 1, 0, cx, 4, gold[1])
    # clock face
    img.ellipse(cx, top + 14, 9, 9, gold[0])
    img.ellipse(cx, top + 14, 7.6, 7.6, face[1])
    img.ellipse(cx - 1.5, top + 12.5, 4, 4, face[2])
    for a in range(0, 360, 30):
        img.set(int(cx + math.cos(math.radians(a)) * 6.2), int(top + 14 + math.sin(math.radians(a)) * 6.2), face[0])
    img.line(int(cx), top + 14, int(cx), top + 9, face[0])
    img.line(int(cx), top + 14, int(cx) + 4, top + 15, face[0])
    # arched door and windows
    img.rect(cx - 5, h - 18, cx + 4, h - 3, stone[0])
    img.ellipse(cx - 0.5, h - 18, 5, 3, stone[0])
    for wy in (top + 30, top + 46):
        img.rect(cx - 3, wy, cx + 2, wy + 8, stone[0])
        img.rect(cx - 2, wy + 1, cx + 1, wy + 7, face[0])
    return img.outline(out)


def electric_lamp(metal, glow, out, frame=0, h=32):
    img = Img(16, h)
    img.rect(7, 8, 8, h - 3, metal[1])
    img.vline(7, 8, h - 3, metal[2])
    img.rect(5, h - 3, 10, h - 2, metal[0])
    img.line(8, 7, 12, 4, metal[1])
    img.line(7, 7, 3, 4, metal[1])
    for x0 in (1, 11):
        img.rect(x0, 2, x0 + 3, 5, metal[0])
        img.rect(x0 + 1, 3, x0 + 2, 5, glow[1 + frame % 2] if len(glow) > 2 else glow[1])
    img.rect(6, 0, 9, 2, metal[1])
    return img.outline(out)


def tesla_beacon(metal, coil, spark, out, frame, h=48):
    """Tesla coil beacon (1x3) with an animated spark crown."""
    img = Img(16, h)
    img.rect(6, 20, 9, h - 3, metal[1])
    img.vline(6, 20, h - 3, metal[2])
    img.rect(3, h - 4, 12, h - 2, metal[0])
    for y in range(12, 22):
        img.hline(5, 10, y, coil[1] if y % 2 else coil[2])
    img.ellipse(8, 9, 5, 3.5, metal[1])
    img.ellipse(7, 8, 3, 2, metal[2])
    arcs = [((3, 6), (1, 2), (0, 4)), ((12, 5), (14, 2), (15, 6)), ((8, 5), (6, 1), (9, 0))]
    for i, pts in enumerate(arcs):
        if (i + frame) % 2 == 0:
            for a, b in zip(pts, pts[1:]):
                img.line(a[0], a[1], b[0], b[1], spark[1] if i % 2 else spark[0])
    return img.outline(out)


def parked_bike(frame_c, tyre, out):
    img = Img(32, 16)
    for cx in (7, 24):
        img.ellipse(cx, 10, 5, 5, tyre)
        img.ellipse(cx, 10, 3.6, 3.6, None)
        img.set(cx, 10, frame_c[1])
    img.line(7, 10, 13, 5, frame_c[1])
    img.line(13, 5, 22, 5, frame_c[1])
    img.line(22, 5, 24, 10, frame_c[1])
    img.line(13, 5, 16, 10, frame_c[1])
    img.line(16, 10, 7, 10, frame_c[0])
    img.rect(11, 3, 14, 3, frame_c[0])
    img.line(22, 5, 21, 2, frame_c[1])
    img.hline(19, 23, 2, frame_c[0])
    return img.outline(out)


def cafe_table(cloth, metal, parasol, out):
    img = Img(32, 32)
    for y in range(2, 12):
        half = 3 + (y - 2) * 1.3
        for x in range(int(16 - half), int(16 + half)):
            img.set(x, y, parasol[2] if ((x - 16) // 3) % 2 else parasol[1])
    img.hline(2, 29, 12, parasol[0])
    img.vline(16, 12, 22, metal[1])
    img.ellipse(16, 23, 8, 3, cloth[1])
    img.ellipse(15, 22.5, 6, 2, cloth[2])
    img.vline(16, 25, 29, metal[0])
    for x in (4, 27):
        img.rect(x, 22, x + 2, 28, metal[1])
        img.hline(x - 1, x + 3, 22, metal[2])
    return img.outline(out)


def arch_bridge(stone, rail, out, w=48, h=48):
    """Stone arch bridge over a canal, north-south deck (3x3, floor)."""
    img = Img(w, h)
    for y in range(h):
        for x in range(6, w - 6):
            c = stone[2] if (x + (y // 4) * 4) % 8 else stone[1]
            if y % 4 == 3:
                c = stone[1]
            img.set(x, y, c)
    for y in range(h):
        img.rect(3, y, 6, y, rail[1])
        img.rect(w - 7, y, w - 4, y, rail[0])
        if y % 8 == 0:
            img.rect(2, y, 7, y + 1, rail[2])
            img.rect(w - 8, y, w - 3, y + 1, rail[1])
    return img.outline(out)


def tram_track(road, metal, out):
    """Tram rails set into the road, as a 64x16 strip: [E-W][N-S][cross][stop]."""
    img = Img(64, 16)
    img.paste(road, 0, 0)
    img.paste(road, 16, 0)
    img.paste(road, 32, 0)
    img.paste(road, 48, 0)
    for ox in (0, 32, 48):
        for ry in (4, 11):
            img.hline(ox, ox + 15, ry, metal[2])
            img.hline(ox, ox + 15, ry + 1, metal[0])
    for ox in (16, 32):
        for rx in (4, 11):
            img.vline(ox + rx, 0, 15, metal[2])
            img.vline(ox + rx + 1, 0, 15, metal[0])
    img.rect(48 + 12, 2, 48 + 14, 13, metal[1])
    return img


def planter_tree(leaf, bark, box, out, grate=None):
    """Street tree in a square planter (1x2)."""
    img = Img(16, 32)
    img.rect(1, 24, 14, 30, box[1])
    img.hline(1, 14, 24, box[2])
    img.hline(1, 14, 30, box[0])
    img.rect(3, 25, 12, 26, box[0])
    img.rect(7, 14, 8, 25, bark[1])
    img.vline(7, 14, 25, bark[2])
    cl = [(8, 8, 6.5), (4, 11, 4), (12, 11, 4), (8, 4, 4.5), (8, 13, 4.5)]
    crown = clump_crown(16, 32, cl, leaf, None, speck=True, gdark=0.4)
    img.paste(crown, 0, 0)
    return img.outline(out)


def kiosk(wall, roof, glass, sign, out, w=32, h=48):
    img = Img(w, h)
    for y in range(14, h - 2):
        for x in range(3, w - 3):
            img.set(x, y, wall[1] if x > 4 else wall[2])
    img.rect(6, 20, w - 7, 30, glass[1])
    img.set(w - 9, 22, glass[2])
    img.rect(3, 31, w - 4, 33, wall[0])
    for y in range(2, 14):
        half = 6 + (y - 2) * 0.9
        img.hline(int(w / 2 - half), int(w / 2 + half), y, roof[2] if y % 3 else roof[1])
    img.hline(1, w - 2, 13, roof[0])
    img.rect(8, 15, w - 9, 18, sign)
    return img.outline(out)
