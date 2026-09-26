"""Battle backgrounds for the expansion areas, painted with the helpers of
tools/gen_battle_gfx.py (which also paints the original five scenes).

    scenes(g) -> [(key, painter), ...]   # g = the gen_battle_gfx module

The order continues BSCENE_* after MEADOW, FOREST, LAKE, RING, STORM:
CITY, COAST, SEA, SNOW, CAVE, GRIM, CRYPT, VOLCANO, DREAM, FARM, LAIR.
Every painter returns a 240x160 image of (r, g, b) 5-bit tuples.

Same rules as the original scenes: only rows 0..111 are painted (the text
box covers the rest with the plain colour), the horizon sits around y 24..44,
light comes from the top-left, ground detail repeats on a 32 px grid where it
can, and the two kin stand on bases at ENEMY_BASE / ALLY_BASE. Each scene
keeps its colours grouped by region (sky, backdrop, ground, bases) so every
8x8 tile fits one of the four 15-colour banks that pack_scene hands out.
"""

import math

SW, TY = 240, 112           # screen width, first row of the text box


# ---------------------------------------------------------------------------
# small drawing helpers
# ---------------------------------------------------------------------------

def _put(S, x, y, c):
    if 0 <= x < SW and 0 <= y < TY:
        S[y][x] = c


def _rect(S, x0, y0, x1, y1, c):
    """Fill [x0, x1) x [y0, y1), clipped to the painted area."""
    for y in range(max(0, y0), min(TY, y1)):
        row = S[y]
        for x in range(max(0, x0), min(SW, x1)):
            row[x] = c


def _bands(S, y0, y1, edges, cols):
    """Horizontal colour bands; band i ends at row edges[i], which is split
    between the two bands by the meadow sky's stepped pattern."""
    for y in range(y0, min(TY, y1)):
        row = S[y]
        for x in range(SW):
            j = (x // 2 + x // 7) % 2
            i = 0
            for e in edges:
                if y > e or (y == e and not j):
                    i += 1
            row[x] = cols[i]


def _puffs(S, clouds, lit, shade, ymax):
    """Soft three-puff clouds (the meadow's), clipped above ymax."""
    for (cx, cy, w) in clouds:
        puffs = [(cx - w * 0.35, cy + 2, w * 0.28), (cx, cy, w * 0.38), (cx + w * 0.38, cy + 2.5, w * 0.26)]
        for y in range(max(0, int(cy - w * 0.3) - 1), min(ymax, int(cy + 5))):
            for x in range(int(cx - w), int(cx + w) + 1):
                if not (0 <= x < SW):
                    continue
                inside = [p for p in puffs
                          if math.hypot((x + 0.5 - p[0]) / p[2], (y + 0.5 - p[1]) / (p[2] * 0.62)) <= 1.0]
                if inside and y <= cy + 4:
                    lt = any(math.hypot((x + 0.5 - p[0] + 1.5) / p[2], (y + 0.5 - p[1] + 1.5) / (p[2] * 0.62)) <= 0.95
                             for p in inside)
                    S[y][x] = lit if lt and y < cy + 3 else shade


def _streak(S, cx, cy, w, h, col, under=None):
    """Long thin cloud (the lake's)."""
    for y in range(max(0, int(cy - h) - 1), min(TY, int(cy + h) + 2)):
        for x in range(max(0, int(cx - w)), min(SW, int(cx + w) + 1)):
            if math.hypot((x + 0.5 - cx) / w, (y + 0.5 - cy) / h) <= 1.0:
                S[y][x] = col if (under is None or y < cy) else under


def _slabs(S, top, rows, unit, pick, vx=120.0, vy=-230.0, stagger=0.5):
    """Perspective paving (the ring's): joints converge on (vx, vy).
    pick(i, ly, h, lx, k, n) -> colour, where i = course index, ly/h = row
    inside the course / course height, lx = position inside the slab in
    far-edge units (0..unit), k = far-edge units per screen pixel and n =
    the slab's index along the course."""
    for i in range(len(rows) - 1):
        y0, y1 = rows[i], rows[i + 1]
        off = unit * stagger if i % 2 else 0.0
        for y in range(y0, min(TY, y1)):
            k = (top - vy) / (y + 0.5 - vy)
            row = S[y]
            for x in range(SW):
                u = (x + 0.5 - vx) * k - off
                row[x] = pick(i, y - y0, y1 - y0, u % unit, k, int(math.floor(u / unit)))


def _disc(g, S, base, fn, pad=3):
    """Run fn(x, y, d, r, dx, dy, old) over a base ellipse (d = pixels inside
    the edge, r = normalised radius, dx/dy = normalised offsets); a returned
    colour replaces the pixel."""
    cx, cy, rx, ry = base
    for y in range(max(0, int(cy - ry - pad)), min(TY, int(cy + ry + pad + 1))):
        for x in range(max(0, int(cx - rx - pad)), min(SW, int(cx + rx + pad + 1))):
            d = g.ell_dist(x, y, base)
            r = g.ell_r(x, y, base)
            c = fn(x, y, d, r, (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry, S[y][x])
            if c is not None:
                S[y][x] = c


def _grid32(x0):
    """x positions of a detail repeated every 32 px across the screen."""
    return range(x0 - 32, SW + 32, 32)


def _tint(S, cx, cy, rx, ry, mapping, soft=None, ymin=0, ymax=TY):
    """Recolour pixels inside an ellipse through `mapping` (a glow pool); an
    optional softer mapping is dithered over the outer ring."""
    for y in range(max(ymin, int(cy - ry) - 1), min(ymax, int(cy + ry) + 2)):
        row = S[y]
        for x in range(max(0, int(cx - rx) - 1), min(SW, int(cx + rx) + 2)):
            d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
            if d <= 0.62:
                row[x] = mapping.get(row[x], row[x])
            elif d <= 1.0 and (x + y) % 2 == 0:
                row[x] = (soft or mapping).get(row[x], row[x])


# ---------------------------------------------------------------------------
# 1. LUMEN CITY at golden dusk: lamp-lit townhouses over a cobbled plaza
# ---------------------------------------------------------------------------

def paint_city(g):
    C = g.C
    K = {
        "s0": C(72, 56, 120), "s1": C(128, 80, 144), "s2": C(200, 108, 128), "s3": C(240, 156, 104),
        "s4": C(248, 204, 136),
        "far": C(144, 88, 136), "far_l": C(184, 116, 140),
        "dk": C(40, 28, 48), "iron": C(96, 72, 104),
        "rf0": C(84, 56, 88), "rf1": C(124, 76, 108),
        "br0": C(128, 60, 64), "br1": C(172, 84, 76),
        "pl0": C(176, 132, 124), "pl1": C(220, 176, 148),
        "te0": C(64, 96, 112), "te1": C(92, 132, 140),
        "win0": C(248, 188, 80), "win1": C(255, 240, 176), "unlit": C(60, 52, 92),
        "awn": C(208, 72, 64),
        "j": C(88, 64, 80), "c1": C(124, 96, 104), "c2": C(156, 124, 120), "c3": C(188, 152, 132),
        "w1": C(212, 160, 120), "w2": C(240, 200, 144),
        "brass0": C(160, 108, 56), "brass1": C(232, 180, 88),
    }
    S = g.new_scene(g.PLAIN)
    rng = g.Rng(2024)
    FLOOR = 40          # plaza starts on a tile row: houses above, paving below
    SHOP = 28
    _bands(S, 0, FLOOR, [4, 9, 14, 19], [K["s0"], K["s1"], K["s2"], K["s3"], K["s4"]])

    # distant hazy towers peeking between the roofs
    for (x0, x1, top, kind) in ((84, 92, 2, "spire"), (140, 162, 8, "dome"), (182, 188, 1, "mast"),
                                (104, 116, 6, "block"), (58, 70, 5, "block")):
        w = x1 - x0
        body = top + (w // 2 if kind == "dome" else 8 if kind == "spire" else 5 if kind == "mast" else 0)
        for y in range(top, 24):
            for x in range(x0, x1):
                if y < body:
                    if kind == "dome":
                        if math.hypot((x + 0.5 - (x0 + x1) / 2) / (w / 2), (y + 0.5 - body) / (w / 2)) > 1.0:
                            continue
                    elif kind == "spire":
                        if abs(x + 0.5 - (x0 + x1) / 2) > (y - top + 1) * (w / 2) / (body - top):
                            continue
                    elif abs(x + 0.5 - (x0 + x1) / 2) > 1.0:
                        continue
                lit = x == x0 or (kind == "dome" and y < body and x - x0 < w * 0.3)
                _put(S, x, y, K["far_l"] if lit else K["far"])
        if kind == "mast":            # the Resonance Works' heartglass beacon
            cx = (x0 + x1) // 2
            for (dx, dy, c) in ((0, -1, "win0"), (-1, 0, "win0"), (0, 0, "win1"), (1, 0, "win0"), (0, 1, "win0")):
                _put(S, cx + dx, top + 2 + dy, K[c])
        for y in range(body + 2, 24, 4):
            for x in range(x0 + 2, x1 - 1, 3):
                if (x * 7 + y * 3) % 5 < 2:
                    _put(S, x, y, K["win0"])

    # townhouses and shopfronts. House edges sit on the 8px tile grid and
    # eaves on tile rows, so sky tiles and facade tiles never mix.
    tones = (("br0", "br1"), ("pl0", "pl1"), ("te0", "te1"))
    plan = [(16, 1, 16, 1), (32, 0, 16, 0), (40, 1, 16, 2), (24, 2, 24, 0), (32, 0, 16, 0),
            (32, 2, 24, 1), (32, 1, 24, 0), (24, 0, 16, 2), (32, 2, 16, 0)]
    x = -8
    for (w, st, eave, roof) in plan:
        x0, x1 = x, x + w
        x = x1
        dk_, lt_ = K[tones[st][0]], K[tones[st][1]]
        # roof (always above the eave row, clipped to the house)
        if roof == 0:                                          # steep gable
            h = min(eave, int(w * 0.36))
            peak = (x0 + x1) / 2
            top = eave - h
            for y in range(top, eave):
                half = (y + 1 - top) * (w / 2) / h
                for xx in range(x0, x1):
                    dd = abs(xx + 0.5 - peak)
                    if dd > half:
                        continue
                    left = xx + 0.5 < peak
                    if half - dd < 1.0:
                        c = K["s4"] if left else K["dk"]      # sunlit / shaded verge
                    elif (y - top) % 3 == 2:
                        c = K["rf0"] if left else K["dk"]     # tile courses
                    else:
                        c = K["rf1"] if left else K["rf0"]
                    _put(S, xx, y, c)
            if h >= 6:                                         # chimney
                cxm = int(x0 + w * 0.72)
                for y in range(top + 1, top + h // 2 + 1):
                    for xx in range(cxm, cxm + 3):
                        _put(S, xx, y, K["dk"] if y == top + 1 else (K["rf1"] if xx == cxm else K["rf0"]))
        elif roof == 1:                                        # flat top with a cornice
            _rect(S, x0, eave - 3, x1, eave, K["rf0"])
            _rect(S, x0, eave - 3, x1, eave - 2, K["s4"])
            _rect(S, x0 + w - 1, eave - 3, x1, eave, K["dk"])
            for xx in range(x0 + 3, x1 - 3, 4):                # little balustrade
                _put(S, xx, eave - 4, K["rf0"])
                _put(S, xx, eave - 5, K["rf0"])
            _rect(S, x0 + 1, eave - 6, x1 - 1, eave - 5, K["rf1"])
        else:                                                  # mansard with a lit dormer
            hgt = min(eave, 7)
            for y in range(eave - hgt, eave):
                ins = (eave - y) * 0.5
                for xx in range(x0, x1):
                    if xx + 0.5 < x0 + ins or xx + 0.5 > x1 - ins:
                        continue
                    if y == eave - hgt:
                        c = K["s4"]
                    else:
                        c = K["rf1"] if xx < x0 + w * 0.45 else K["rf0"]
                        if (eave - y) % 2 == 0:
                            c = K["rf0"] if c == K["rf1"] else K["dk"]
                    _put(S, xx, y, c)
            dx0 = (x0 + x1) // 2 - 2
            _rect(S, dx0 - 1, eave - hgt + 2, dx0 + 5, eave, K["dk"])
            _rect(S, dx0, eave - hgt + 3, dx0 + 4, eave, K["win0"])
            _put(S, dx0, eave - hgt + 3, K["win1"])
            _put(S, dx0 + 1, eave - hgt + 3, K["win1"])
        # facade
        for y in range(eave, FLOOR - 2):
            for xx in range(x0, x1):
                _put(S, xx, y, dk_ if (xx >= x1 - 2 or y == eave) else lt_)
        # upper windows
        n = max(1, (w - 4) // 8)
        span = (w - 2) / n
        for wy in range(eave + 3, SHOP - 7, 9):
            for i in range(n):
                wx = int(x0 + span * (i + 0.5)) - 2
                lit = rng.rand(0, 9) < 6
                for dy in range(6):
                    for dx in range(4):
                        if dy == 0 or dy == 3:
                            c = K["dk"]
                        elif lit:
                            c = K["win1"] if (dx + dy < 4 and dy < 3) else K["win0"]
                        else:
                            c = K["unlit"]
                        _put(S, wx + dx, wy + dy, c)
                for dx in range(-1, 5):
                    _put(S, wx + dx, wy + 6, K["s4"] if dx < 4 else dk_)
        # ground floor: awning, shop window and door (or an arched lit doorway)
        if st != 2:
            for y in range(SHOP - 1, SHOP + 2):
                for xx in range(x0 + 1, x1 - 1):
                    c = K["awn"] if ((xx - x0) // 3) % 2 else K["pl1"]
                    if y == SHOP + 1 and xx % 2:
                        c = K["dk"]
                    _put(S, xx, y, c)
            _rect(S, x0 + 1, SHOP + 2, x1 - 1, SHOP + 3, K["dk"])
            sx1 = x0 + int(w * 0.58)
            _rect(S, x0 + 2, SHOP + 4, sx1, FLOOR - 3, K["dk"])
            for y in range(SHOP + 5, FLOOR - 4):
                for xx in range(x0 + 3, sx1 - 1):
                    _put(S, xx, y, K["win1"] if (xx - x0 + (y - SHOP)) % 7 == 0 else K["win0"])
            _rect(S, x1 - 9, SHOP + 4, x1 - 4, FLOOR - 2, K["dk"])
            _rect(S, x1 - 8, SHOP + 5, x1 - 5, SHOP + 7, K["win0"])
        else:
            dxm = (x0 + x1) // 2
            for y in range(SHOP, FLOOR - 2):
                for xx in range(dxm - 4, dxm + 4):
                    if y < SHOP + 4 and math.hypot(xx + 0.5 - dxm, (y + 0.5 - (SHOP + 4)) * 1.3) > 4.2:
                        continue
                    inner = abs(xx + 0.5 - dxm) < 3 and y > SHOP
                    _put(S, xx, y, K["unlit"] if inner and y > SHOP + 4 else K["win0"] if inner else K["dk"])
        _rect(S, x0, FLOOR - 2, x1, FLOOR, K["dk"])

    # cobbled plaza: small setts converging on a point above the screen
    UNIT = 8.0

    def cobble(i, ly, h, lx, k, n):
        if ly == 0 or lx < k:
            return K["j"]
        if ly == 1 or lx < 2 * k:
            return K["c3"]
        if lx > UNIT - k or ly == h - 1:
            return K["c1"]
        v = (n * 7 + i * 13 + (n * i) % 5) % 9          # a few darker / paler setts
        return K["c1"] if v == 0 else K["c3"] if v == 4 else K["c2"]
    _slabs(S, FLOOR, [FLOOR, 43, 45, 48, 51, 55, 59, 64, 70, 77, 85, 94, 103, TY], UNIT, cobble, vy=-90.0)
    _rect(S, 0, FLOOR, SW, FLOOR + 1, K["c3"])                  # kerb
    _rect(S, 0, FLOOR + 1, SW, FLOOR + 2, K["c1"])
    _rect(S, 0, FLOOR + 2, SW, FLOOR + 3, K["j"])
    for y in range(FLOOR + 3, FLOOR + 7):                      # shade under the houses
        for x in range(SW):
            if S[y][x] in (K["c2"], K["c3"]) and (y < FLOOR + 5 or (x + y) % 2):
                S[y][x] = K["c1"]

    # iron lamp posts with glowing heartglass lanterns
    for (L, foot) in ((12, 54), (118, 52), (228, 54)):
        top = 10
        _tint(S, L + 1, foot + 1, 22, 5, {K["c2"]: K["w1"], K["c3"]: K["w2"], K["c1"]: K["c2"]},
              {K["c2"]: K["w1"], K["c1"]: K["c2"]}, ymin=FLOOR + 3)
        for y in range(max(0, top - 8), top + 12):
            for xx in range(max(0, L - 9), min(SW, L + 11)):
                d = math.hypot(xx + 0.5 - (L + 1), (y + 0.5 - (top + 3)) * 1.15)
                if 3.6 < d < 7.5 and (xx + y) % 2 == 0 and S[y][xx] not in (K["win0"], K["win1"]):
                    S[y][xx] = K["win0"] if d < 5.6 else K["s4"]
        for y in range(top + 7, foot):
            _put(S, L, y, K["iron"])
            _put(S, L + 1, y, K["dk"])
        for y in range(foot - 5, foot - 1):
            _put(S, L - 1, y, K["iron"])
            _put(S, L + 2, y, K["dk"])
        _rect(S, L - 2, foot - 1, L + 4, foot + 1, K["dk"])
        _put(S, L - 2, foot - 1, K["iron"])
        cage = ["..dd..", ".dddd.", "dhwwhd", "dwWWwd", "dhwwhd", ".dddd.", "..dd.."]
        for dy, line in enumerate(cage):
            for dx, ch in enumerate(line):
                c = {"d": K["dk"], "h": K["win0"], "w": K["win0"], "W": K["win1"]}.get(ch)
                if c is not None:
                    _put(S, L - 2 + dx, top + dy, c)
        _put(S, L, top - 1, K["dk"])
        _put(S, L + 1, top - 1, K["dk"])

    # bases: round plaza medallions, a brass ring around a compass-rose inlay
    def medallion(x, y, d, r, dx, dy, old):
        if d < 0:
            return K["j"] if (d > -1.2 and dy > 0.3) else None
        if d < 1.0:
            return K["j"]
        if d < 2.6:
            return K["brass1"] if dx + dy * 1.6 < -0.25 else K["brass0"]
        if d < 3.4:
            return K["j"]
        if dy < 0 and r > 0.8 and dx < 0.5:
            return K["w2"]
        if dy > 0.25 and r > 0.72:
            return K["c3"]
        cx, cy, rx, ry = inner[0]
        if -0.6 < g.ell_dist(x, y, (cx, cy, rx * 0.56, ry * 0.56)) < 0.6:
            return K["brass0"]
        return K["w1"]
    for base in (g.ENEMY_BASE, g.ALLY_BASE):
        inner = [base]
        _disc(g, S, base, medallion)
    return S


# ---------------------------------------------------------------------------
# 2. PORT BRINE: lighthouse headland, harbour, sparkling sea, sandy beach
# ---------------------------------------------------------------------------

def paint_coast(g):
    C = g.C
    K = {
        "sky0": C(120, 184, 248), "sky1": C(160, 208, 248), "sky2": C(200, 228, 248),
        "cl": C(248, 248, 248), "cl_s": C(208, 224, 240),
        "rk0": C(88, 80, 96), "rk1": C(136, 124, 124), "rk2": C(176, 164, 152),
        "gr0": C(72, 136, 80), "gr1": C(120, 184, 96),
        "red": C(208, 64, 56), "lamp": C(255, 232, 120),
        "wd0": C(104, 68, 48), "wd1": C(160, 112, 72),
        "w0": C(40, 96, 168), "w1": C(56, 128, 200), "w2": C(88, 168, 224), "w3": C(200, 236, 252),
        "wet0": C(184, 156, 108), "wet1": C(208, 180, 128), "s1": C(232, 208, 152), "s2": C(244, 228, 184),
        "shell": C(240, 160, 152), "star": C(232, 120, 72), "b_rim": C(160, 128, 92),
    }
    S = g.new_scene(g.PLAIN)
    HOR = 32
    _bands(S, 0, HOR, [10, 21], [K["sky0"], K["sky1"], K["sky2"]])
    _puffs(S, [(92, 9, 26), (226, 6, 18)], K["cl"], K["cl_s"], HOR)
    _streak(S, 40, 24, 30, 1.6, K["cl"], K["cl_s"])
    _streak(S, 170, 27, 22, 1.3, K["cl"])

    # sea: darker toward the horizon, glints on a 32px grid
    SHORE = 56
    _bands(S, HOR, SHORE, [35, 44], [K["w0"], K["w1"], K["w2"]])
    srng = g.Rng(21)
    for y in range(HOR + 2, SHORE - 2, 3):
        x0 = srng.rand(0, 31)
        ln = 2 + (y - HOR) // 7
        for x in _grid32(x0):
            for k in range(ln):
                _put(S, x + k, y, K["w3"] if k < ln - 1 else K["w2"])

    # distant sails on the horizon
    for (bx, h) in ((104, 7), (126, 5)):
        for y in range(HOR - h - 1, HOR - 1):
            t = (y - (HOR - h - 1)) / h
            for x in range(bx + 1, bx + 2 + int(t * h * 0.7)):
                _put(S, x, y, K["cl"] if x < bx + 1 + t * h * 0.45 else K["cl_s"])
            _put(S, bx, y, K["wd0"])
        _rect(S, bx - 3, HOR - 1, bx + 5, HOR, K["wd0"])
        _rect(S, bx - 2, HOR, bx + 4, HOR + 1, K["w1"])

    # the lighthouse headland on the left
    def cliff_top(x):
        return 15 + max(0.0, x - 30) * 0.42 + 1.2 * math.sin(x * 0.7) * (x > 30)
    for x in range(0, 78):
        top = int(cliff_top(x))
        foot = HOR + 3 + (1 if x % 5 == 0 else 0)
        for y in range(top, foot):
            if y < top + 1:
                c = K["gr1"]
            elif y < top + 3 and (x + y) % 4:
                c = K["gr0"]
            else:
                band = (y + (x // 6) % 3) % 5
                c = K["rk0"] if band == 0 else K["rk2"] if (band == 1 and x % 7 < 4) else K["rk1"]
            _put(S, x, y, c)
        if top < foot:
            _put(S, x, foot, K["cl"] if x % 3 else K["w3"])        # surf at the foot
    # tower: red and white bands, lit from the left
    LX, LB = 20, 16
    for y in range(4, LB):
        half = 2.5 + (y - 4) * 0.12
        red = ((y - 4) // 3) % 2 == 1
        for x in range(int(LX - half), int(math.ceil(LX + half))):
            rel = (x + 0.5 - (LX - half)) / (2 * half)
            if red:
                c = K["red"] if rel < 0.7 else K["rk0"]
            else:
                c = K["cl"] if rel < 0.7 else K["cl_s"]
            _put(S, x, y, c)
    _rect(S, LX - 4, 3, LX + 4, 4, K["rk0"])                   # gallery
    _rect(S, LX - 2, 1, LX + 2, 3, K["lamp"])                  # lamp room
    _put(S, LX - 2, 1, K["cl"])
    _rect(S, LX - 2, 0, LX + 2, 1, K["red"])
    for y in range(0, 10):                                     # the lamp's glow
        for x in range(LX - 9, LX + 9):
            d = math.hypot(x + 0.5 - LX, (y + 0.5 - 2) * 1.2)
            if 3.0 < d < 6.5 and (x + y) % 2 == 0 and S[y][x] in (K["sky0"], K["sky1"]):
                S[y][x] = K["lamp"] if d < 4.6 else K["sky2"]
    _rect(S, LX + 5, 12, LX + 11, 16, K["cl"])                 # keeper's cottage
    _rect(S, LX + 9, 12, LX + 11, 16, K["cl_s"])
    for x in range(LX + 4, LX + 12):
        _put(S, x, 11, K["red"])
    _put(S, LX + 6, 13, K["rk0"])

    # the harbour town and pier on the right
    for x in range(200, SW):
        top = 27 - int((x - 200) * 0.1)
        for y in range(top, HOR + 1):
            _put(S, x, y, K["gr0"] if y == top else K["rk1"] if y < HOR - 1 else K["rk0"])
    for (hx, hw, hh) in ((208, 6, 5), (216, 7, 7), (225, 6, 4), (232, 8, 6)):
        base_y = 27 - int((hx - 200) * 0.1)
        _rect(S, hx, base_y - hh, hx + hw, base_y + 1, K["cl"])
        _rect(S, hx + hw - 2, base_y - hh, hx + hw, base_y + 1, K["cl_s"])
        for x in range(hx - 1, hx + hw + 1):
            _put(S, x, base_y - hh - 1, K["red"])
        for x in range(hx, hx + hw):
            if x % 3 == 1:
                _put(S, x, base_y - hh + 2, K["rk0"])
    for x in range(206, SW):                                   # jetty
        _put(S, x, 37, K["wd1"])
        _put(S, x, 38, K["wd0"])
        if x % 6 == 0:
            for y in range(39, 43):
                _put(S, x, y, K["wd0"])
            _put(S, x, 43, K["w3"])
    for y in range(28, 37):                                    # moored boat's mast and sail
        _put(S, 214, y, K["wd0"])
        for x in range(215, 215 + (y - 28) // 2 + 1):
            _put(S, x, y, K["cl"] if x < 217 else K["cl_s"])
    _rect(S, 210, 36, 220, 37, K["red"])

    # surf line, wet sand, dry sand
    for x in range(SW):
        e = SHORE + int(round(1.5 * math.sin(x * math.pi / 16)))
        for y in range(SHORE - 3, TY):
            if y < e - 2:
                continue
            if y == e - 2:
                c = K["w3"] if x % 2 else S[y][x]
            elif y == e - 1:
                c = K["cl"]
            elif y < e + 2:
                c = K["wet0"]
            elif y < e + 5:
                c = K["wet1"]
            elif y == e + 5 and (x % 8) in (1, 2, 5):
                c = K["wet1"]
            else:
                c = K["s1"]
            S[y][x] = c
    # ripples in the sand on a 32px grid, bigger when nearer
    rrng = g.Rng(33)
    for y0 in range(SHORE + 10, TY - 1, 5):
        depth = (y0 - SHORE) / (TY - SHORE)
        for _ in range(2):
            x0 = rrng.rand(0, 31)
            ln = 3 + int(depth * 6)
            for x in _grid32(x0):
                for k in range(ln):
                    _put(S, x + k, y0, K["s2"])
                    if 0 < k < ln - 1:
                        _put(S, x + k, y0 + 1, K["wet1"])
    # shells, a starfish, pebbles and driftwood
    for (x, y, kind) in ((24, 70, "shell"), (122, 64, "star"), (218, 96, "shell"), (134, 90, "pebble"),
                         (10, 100, "pebble"), (226, 66, "pebble"), (110, 104, "shell"), (60, 64, "shell")):
        if kind == "shell":
            for (dx, dy, c) in ((0, 0, "shell"), (1, -1, "shell"), (2, -1, "cl"), (3, 0, "shell"),
                                (1, 0, "cl"), (2, 0, "shell"), (1, 1, "wet0"), (2, 1, "wet0")):
                _put(S, x + dx, y + dy, K[c])
        elif kind == "star":
            for (dx, dy) in ((0, 0), (-1, 0), (1, 0), (0, -1), (-2, 1), (2, 1), (-1, 2), (1, 2), (0, 1)):
                _put(S, x + dx, y + dy, K["star"])
            _put(S, x, y, K["s2"])
        else:
            for (dx, dy, c) in ((0, 0, "rk2"), (1, 0, "rk1"), (0, 1, "rk1"), (1, 1, "rk0"), (2, 1, "rk0")):
                _put(S, x + dx, y + dy, K[c])
    for (x0, y0, ln) in ((96, 76, 14), (6, 84, 11)):
        for k in range(ln):
            yy = y0 + (1 if k > ln * 0.6 else 0)
            _put(S, x0 + k, yy, K["wd1"])
            _put(S, x0 + k, yy + 1, K["wd0"])
            _put(S, x0 + k, yy + 2, K["wet1"])
        _put(S, x0 + 3, y0 - 1, K["wd1"])
        _put(S, x0 + 2, y0 - 2, K["wd1"])
        _put(S, x0 + ln - 1, y0 - 1 + (1 if ln * 0.6 < ln - 1 else 0), K["wd0"])

    pal = {"rim": K["b_rim"], "dark": K["wet0"], "fill": K["wet1"], "hi": K["s2"], "edge": K["wet0"]}
    g.soft_base(S, g.ENEMY_BASE, pal, seed=11)
    g.soft_base(S, g.ALLY_BASE, pal, seed=12)
    return S


def scenes(g):
    """(key, painter) pairs in BSCENE_* order after the original five."""
    return [
        ("city", lambda: paint_city(g)),
        ("coast", lambda: paint_coast(g)),
    ]
