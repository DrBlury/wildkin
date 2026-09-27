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


# ---------------------------------------------------------------------------
# more helpers for the remaining scenes
# ---------------------------------------------------------------------------

def _glow(S, cx, cy, rings, only=None, ymin=0, ymax=TY, sy=1.0, airy=False):
    """Concentric dithered halo. rings: [(radius, colour), ...] from the
    inside out; a pixel takes the first ring it falls in, with a checker
    dither over the outer pixel of each ring. Only pixels whose colour is in
    `only` (if given) are replaced. airy: the outermost ring is only a
    checker dither."""
    rmax = rings[-1][0]
    for y in range(max(ymin, int(cy - rmax / sy) - 1), min(ymax, int(cy + rmax / sy) + 2)):
        row = S[y]
        for x in range(max(0, int(cx - rmax) - 1), min(SW, int(cx + rmax) + 2)):
            if only is not None and row[x] not in only:
                continue
            d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * sy)
            for i, (r, c) in enumerate(rings):
                if d <= r and i == len(rings) - 1 and airy and (x + y) % 2:
                    break
                if d <= r:
                    if d > r - 1.2 and (x + y) % 2 and i + 1 < len(rings):
                        c = rings[i + 1][1]
                    elif d > r - 1.2 and (x + y) % 2 and i + 1 == len(rings):
                        c = None
                    if c is not None:
                        row[x] = c
                    break


def _wavy_bands(S, edges, cols, seam=None, lip=None, amp=1.5, period=32):
    """Ground bands whose edges undulate with a 32 px period (so tiles still
    repeat): band i spans edges[i]..edges[i+1] and takes cols[i % len]. An
    optional dark seam runs along each edge with a lit lip just above it."""
    for x in range(SW):
        e = [edges[0]] + [edges[i] + amp * (0.5 + i / len(edges)) *
                          math.sin((x + i * 13) * 2 * math.pi / period) for i in range(1, len(edges))]
        for y in range(edges[0], min(TY, edges[-1])):
            i = max(k for k in range(len(e) - 1) if e[k] <= y + 0.5) if y + 0.5 >= e[0] else 0
            c = cols[i % len(cols)]
            if i > 0 and seam is not None and y + 0.5 - e[i] < 1.0:
                c = seam
            elif lip is not None and i + 1 < len(e) and 0 < e[i + 1] - (y + 0.5) < 1.0 and (x // 3) % 3:
                c = lip
            S[y][x] = c


def _ring_base(g, S, base, rim, dark, fill, hi, edge=None, lip=None):
    """A raised plate: dark 1px outline, lit back-left lip, shaded front
    face (the plate's thickness shown below the ellipse)."""
    cx, cy, rx, ry = base
    face = 3

    def fn(x, y, d, r, dx, dy, old):
        if d < 0:
            # thickness of the plate under the front half, then its outline
            below = g.ell_dist(x, y - face, base)
            if below >= 0 and dy > 0:
                return rim if below < 1.0 or y >= cy + ry + face - 1 else (edge or dark)
            if edge is not None and below > -1.0 and dy > 0.2:
                return rim
            return None
        if d < 1.0:
            return rim
        if dy < 0 and d < 2.6 and dx < 0.5:
            return lip or hi
        if dy > 0.3 and d < 2.4:
            return dark
        return fill
    _disc(g, S, base, fn, pad=face + 2)


# ---------------------------------------------------------------------------
# 3. SEA ROUTE: open water from a raft, far island, rolling swells
# ---------------------------------------------------------------------------

def paint_sea(g):
    C = g.C
    K = {
        "sky0": C(96, 160, 232), "sky1": C(136, 192, 244), "sky2": C(184, 220, 248),
        "cl": C(248, 248, 248), "cl_s": C(204, 222, 240),
        "is0": C(56, 96, 96), "is1": C(88, 136, 112), "is2": C(128, 176, 120), "isd": C(216, 200, 150),
        "w0": C(24, 64, 136), "w1": C(40, 96, 176), "w2": C(64, 136, 208), "w3": C(120, 188, 236),
        "w4": C(224, 244, 252),
        "sd0": C(168, 140, 96), "sd1": C(208, 180, 128), "sd2": C(236, 216, 168),
        "wd0": C(72, 44, 32), "wd1": C(120, 80, 48), "wd2": C(168, 120, 72), "wd3": C(208, 164, 104),
        "rope": C(224, 204, 150),
    }
    S = g.new_scene(g.PLAIN)
    HOR = 32
    _bands(S, 0, HOR, [9, 21], [K["sky0"], K["sky1"], K["sky2"]])
    _puffs(S, [(118, 10, 22), (212, 5, 16)], K["cl"], K["cl_s"], HOR - 4)
    _streak(S, 176, 22, 34, 1.4, K["cl"], K["cl_s"])
    _streak(S, 60, 26, 20, 1.2, K["cl"])

    # a far island on the left: rocky hump, beach and two palms
    for x in range(0, 96):
        top = HOR - 1 - max(0.0, 9.5 - abs(x - 38) * 0.26) - 1.6 * math.sin(x * 0.4) * (abs(x - 38) < 26)
        top = min(top, HOR - 1)
        for y in range(int(top), HOR):
            if y >= HOR - 2:
                c = K["isd"] if 8 < x < 80 else K["is0"]
            elif y < top + 1:
                c = K["is2"]
            elif (x + (y // 2)) % 9 < 5 and x < 44:
                c = K["is1"]
            else:
                c = K["is0"] if x > 40 or (x + y) % 3 == 0 else K["is1"]
            _put(S, x, y, c)
    for (px, py, lean) in ((30, 18, -1), (50, 20, 1)):
        for k in range(8):
            _put(S, px + (lean * k) // 4, py + k, K["wd1"])
        for (dx, dy) in ((-3, 1), (-2, 0), (-1, 0), (0, -1), (1, 0), (2, 0), (3, 1), (-4, 2), (4, 2),
                         (0, 0), (-1, 1), (1, 1)):
            _put(S, px + dx, py + dy, K["is0"] if dy > 0 and abs(dx) > 1 else K["is2"])
    # a distant sail on the right horizon
    for y in range(HOR - 6, HOR - 1):
        for x in range(222, 222 + (y - (HOR - 6)) // 2 + 2):
            _put(S, x, y, K["cl"] if x < 224 else K["cl_s"])
    _rect(S, 219, HOR - 1, 227, HOR, K["wd0"])

    # rolling swells: crest rows spaced in perspective, each crest a sine
    # with a 32 px period so the water tiles repeat
    crests = [HOR, 34, 37, 41, 46, 52, 59, 67, 76, 86, 97, 109, 122]
    amp = [0.4, 0.6, 0.8, 1.0, 1.3, 1.6, 2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.0]
    for x in range(SW):
        cy = [crests[k] + amp[k] * math.sin((x + k * 11) * math.pi / 16) for k in range(len(crests))]
        cy[0] = HOR
        for y in range(HOR, TY):
            k = max(i for i in range(len(cy) - 1) if cy[i] <= y + 0.5) if y + 0.5 >= cy[0] else 0
            h = cy[k + 1] - cy[k]
            t = (y + 0.5 - cy[k]) / h
            far = k < 3
            if k > 0 and t < 1.0 / h + 0.02:
                peak = math.sin((x + k * 11) * math.pi / 16) < -0.55
                c = K["w4"] if peak and k > 3 else K["w3"]
            elif t < 0.34:
                c = K["w1"] if far else K["w2"]
            elif t < 0.8:
                c = K["w0"] if far else K["w1"]
            else:
                c = K["w0"]
                if t < 0.88 and (x + y) % 2 and not far:
                    c = K["w1"]
            S[y][x] = c
    _rect(S, 0, HOR, SW, HOR + 1, K["w3"])                     # horizon shimmer
    for x in range(SW):
        if x % 5 in (1, 3):
            _put(S, x, HOR + 1, K["w1"])
    # glints on the lit faces
    grng = g.Rng(41)
    for y in range(HOR + 4, TY - 2, 4):
        x0 = grng.rand(0, 31)
        ln = 1 + (y - HOR) // 16
        for x in _grid32(x0):
            for k in range(ln):
                if 0 <= x + k < SW and S[y][x + k] == K["w2"]:
                    _put(S, x + k, y, K["w4"] if k < ln - 1 or ln == 1 else K["w3"])

    # enemy: a sandbar breaking the surface, ringed with surf
    def bar(x, y, d, r, dx, dy, old):
        if d < 0:
            if d > -2.2 and (x + y) % 2 == 0:
                return K["w4"]
            if d > -1.1:
                return K["w3"]
            if d > -3.5 and dy > 0.2:
                return K["w0"] if (x + y) % 2 else None
            return None
        if d < 1.0:
            return K["w4"] if (x // 2) % 2 else K["w3"]
        if d < 2.2:
            return K["sd0"]
        if dy < 0 and r > 0.7 and dx < 0.5:
            return K["sd2"]
        if dy > 0.2 and r > 0.66:
            return K["sd0"]
        return K["sd1"] if (x * 3 + y * 7) % 23 else K["sd2"]
    _disc(g, S, g.ENEMY_BASE, bar, pad=4)
    for (x, y) in ((160, 67), (188, 72), (174, 64)):
        _put(S, x, y, K["sd0"])
        _put(S, x + 1, y, K["sd0"])

    # ally: a log raft lashed with rope, floating in its own ripple
    cx, cy, rx, ry = g.ALLY_BASE
    LOG = 4

    def raft(x, y, d, r, dx, dy, old):
        if d < 0:
            if d > -2.0 and (x + y) % 2 == 0:
                return K["w4"]
            if d > -1.0:
                return K["w3"]
            return None
        if d < 1.0:
            return K["wd0"]
        ly = (y - (cy - ry)) % LOG
        rope = abs(abs(x + 0.5 - cx) - 30) < 1.5
        if rope:
            return K["rope"] if ly != LOG - 1 else K["wd1"]
        if d < 3.0:                                          # sawn log ends
            return K["wd3"] if ly in (0, 1) else K["wd2"]
        if ly == LOG - 1:
            return K["wd0"]
        if ly == 0:
            return K["wd3"] if dx < 0.4 else K["wd2"]
        grain = (x * 5 + (y - ly) * 17) % 29 < 3
        return K["wd1"] if grain or ly == LOG - 2 else K["wd2"]
    _disc(g, S, g.ALLY_BASE, raft, pad=3)
    return S


# ---------------------------------------------------------------------------
# 4. FROSTPINE PASS: snowfield under a pale sky, snowy pines and far peaks
# ---------------------------------------------------------------------------

def paint_snow(g):
    C = g.C
    K = {
        "sky0": C(144, 164, 216), "sky1": C(176, 192, 232), "sky2": C(208, 218, 244), "sky3": C(232, 236, 250),
        "mt0": C(104, 120, 172), "mt1": C(136, 152, 200), "mt2": C(200, 212, 240), "mt3": C(248, 250, 255),
        "pn0": C(24, 52, 64), "pn1": C(40, 80, 80), "pn2": C(64, 108, 96),
        "sn0": C(136, 160, 208), "sn1": C(176, 196, 232), "sn2": C(208, 222, 246), "sn3": C(240, 246, 255),
        "b_rim": C(112, 136, 188), "wood": C(96, 72, 64),
    }
    S = g.new_scene(g.PLAIN)
    HOR = 38
    _bands(S, 0, HOR, [7, 15, 24], [K["sky0"], K["sky1"], K["sky2"], K["sky3"]])
    _streak(S, 70, 8, 40, 1.5, K["sky3"], K["sky2"])
    _streak(S, 196, 12, 30, 1.3, K["sky3"], K["sky2"])

    # far peaks, snow-capped, lit from the left
    peaks = [(-10, 18, 30), (34, 9, 34), (88, 16, 28), (132, 6, 38), (196, 13, 32), (246, 10, 30)]
    for x in range(SW):
        best = None
        for (px, py, w) in peaks:
            top = py + abs(x + 0.5 - px) * (26.0 / w)
            if best is None or top < best[0]:
                best = (top, px, py)
        top, px, py = best
        for y in range(max(0, int(top)), HOR):
            left = x + 0.5 < px
            depth = y - py
            snowline = 9 + int(2 * math.sin(x * 0.9))
            if depth < snowline:
                c = K["mt3"] if left else K["mt2"]
            else:
                c = K["mt1"] if left else K["mt0"]
                if depth < snowline + 3 and (x + y) % 3 == 0:
                    c = K["mt2"]
            if y < top + 1 and not left:
                c = K["mt2"]
            _put(S, x, y, c)
    # low mist band hiding the peaks' feet
    for y in range(28, HOR):
        for x in range(SW):
            if y > 31 or (y > 29 and (x + y) % 2 == 0):
                S[y][x] = K["sky3"] if y < 34 else K["sn2"]

    # snowy pines along the horizon, big clumps at the edges
    def pine(px, base_y, h):
        w = h * 0.36
        for y in range(base_y - h, base_y + 1):
            t = (y - (base_y - h)) / h
            tier = (y - (base_y - h)) % max(3, h // 4)
            half = w * t * (0.75 + 0.25 * (tier / max(3, h // 4))) + 0.5
            for x in range(int(px - half), int(math.ceil(px + half))):
                rel = (x + 0.5 - px) / max(1.0, half)
                if tier == 0 and rel < 0.6:
                    c = K["sn3"] if rel < 0 else K["sn2"]           # snow on each tier
                elif tier == 1 and rel < -0.2:
                    c = K["sn2"]
                elif rel < -0.35:
                    c = K["pn2"]
                elif rel < 0.4:
                    c = K["pn1"]
                else:
                    c = K["pn0"]
                _put(S, x, y, c)
        _put(S, px, base_y - h - 1, K["sn3"])
        _put(S, px, base_y + 1, K["wood"])
        _put(S, px - 1, base_y + 1, K["wood"])
    trees = [(4, 46, 34), (18, 44, 26), (-4, 50, 38), (30, 41, 16), (44, 40, 12), (100, 39, 9), (112, 40, 11),
             (124, 39, 8), (212, 40, 12), (226, 44, 26), (238, 47, 32)]
    for x0 in range(52, 96, 7):
        trees.append((x0, 39, 6 + (x0 * 7) % 4))

    # the snowfield: soft bands with a scalloped drift edge
    g.perspective_bands(S, HOR + 1, [HOR + 1, 44, 49, 55, 62, 70, 80, 92, TY], (K["sn2"], K["sn3"]),
                        saw=(0, 0, 1, 1, 1, 1, 0, 0), seam=K["sn1"])
    for y in range(HOR - 1, HOR + 2):
        for x in range(SW):
            S[y][x] = K["sn1"] if y == HOR - 1 and x % 4 == 0 else K["sn2"]
    # pines stand on the field, each with a blue shadow falling right
    for (px, by, h) in sorted(trees, key=lambda t: t[1]):
        for y in range(by, by + 2 + h // 12):
            for x in range(px - 2, px + h // 3 + 3):
                if (x + y) % 2 == 0 or y == by:
                    _put(S, x, y, K["sn1"])
        pine(px, by - 1, h - 1)
    # drifts: shaded hollows with a lit lip, on a 32 px grid
    drng = g.Rng(64)
    for y0 in range(HOR + 8, TY - 3, 7):
        depth = (y0 - HOR) / (TY - HOR)
        x0 = drng.rand(0, 31)
        w = 5 + int(depth * 9)
        for x in _grid32(x0):
            for k in range(w):
                bump = int(1.5 * math.sin(k / w * math.pi))
                _put(S, x + k, y0 - bump, K["sn3"])
                if 0 < k < w - 1:
                    _put(S, x + k, y0 - bump + 1, K["sn1"])
                    if depth > 0.4 and 1 < k < w - 2:
                        _put(S, x + k, y0 - bump + 2, K["sn1"] if (x + k) % 2 else K["sn2"])
    # sparkles
    for y in range(HOR + 5, TY, 6):
        x0 = (y * 13) % 32
        for x in _grid32(x0):
            if 0 <= x < SW and S[y][x] == K["sn2"]:
                _put(S, x, y, K["sn3"])

    # rocks poking out of the snow, capped white
    for (rx0, ry0, w, h) in ((112, 60, 9, 5), (20, 80, 14, 7), (218, 84, 12, 6), (130, 96, 7, 4)):
        for y in range(ry0 - h, ry0 + 1):
            for x in range(rx0, rx0 + w):
                u = (x + 0.5 - rx0) / w * 2 - 1
                v = (ry0 + 0.5 - y) / h
                if u * u + v * v > 1.0:
                    continue
                if v > 0.55 - 0.2 * math.sin(x * 1.3):
                    c = K["sn3"] if u < 0.2 else K["sn2"]
                else:
                    c = K["mt1"] if u < -0.3 else K["mt0"] if u < 0.5 else K["b_rim"]
                _put(S, x, y, c)
        for x in range(rx0 + 1, rx0 + w + 3):
            _put(S, x, ry0 + 1, K["sn1"])
    # a few flakes drifting down
    for y in range(2, 30, 5):
        x0 = (y * 19) % 32
        for x in _grid32(x0):
            if 0 <= x < SW and S[y][x] in (K["sky0"], K["sky1"], K["sky2"]):
                _put(S, x, y, K["sn3"])
    pal = {"rim": K["b_rim"], "dark": K["sn1"], "fill": K["sn2"], "hi": K["sn3"], "edge": K["sn1"]}
    g.soft_base(S, g.ENEMY_BASE, pal, seed=21)
    g.soft_base(S, g.ALLY_BASE, pal, seed=22)
    return S


# ---------------------------------------------------------------------------
# 5. GLIMMER CAVERNS: stalactites, glowing crystals and fungi, rocky floor
# ---------------------------------------------------------------------------

def paint_cave(g):
    C = g.C
    K = {
        "r0": C(16, 12, 28), "r1": C(32, 26, 48), "r2": C(52, 44, 72), "r3": C(78, 68, 100), "r4": C(112, 100, 136),
        "cr0": C(40, 88, 160), "cr1": C(72, 160, 224), "cr2": C(160, 232, 248), "cr3": C(236, 252, 255),
        "fu0": C(112, 48, 144), "fu1": C(192, 96, 216), "fu2": C(248, 184, 244),
        "gw": C(48, 64, 112), "gw2": C(72, 104, 152),
    }
    # one 14-colour ramp for the whole cave: the floor reuses the rock
    # colours and the pooled light reuses the wall glow, so every tile
    # (wall, crystals, fungi, floor) shares a single palette bank
    K.update({"f0": K["r0"], "f1": K["r1"], "f2": K["r2"], "f3": K["r3"],
              "fg1": K["gw"], "fg2": K["gw2"], "fp1": K["fu0"], "fp2": K["fu0"]})
    S = g.new_scene(g.PLAIN)
    FLOOR = 44
    # back wall: wavy strata, darker toward the ceiling
    for y in range(FLOOR):
        for x in range(SW):
            v = (y + 3.0 * math.sin(x * math.pi / 32 + y * 0.2) + 2 * math.sin(x * math.pi / 16)) / 8.0
            band = int(v) % 3
            base = 0 if y < 10 else 1 if y < 24 else 2
            lv = base + (1 if band == 0 else 0)
            f = v - int(v)
            if f < 0.13 and y > 6:
                lv = max(0, lv - 1)                  # dark crack between strata
            elif f < 0.26 and y > 6 and band == 0:
                lv = min(4, lv + 1)                  # lit lip of the stratum
            S[y][x] = [K["r0"], K["r1"], K["r2"], K["r3"], K["r4"]][min(lv, 3)]

    # stalactites hanging from the ceiling
    def spike(px, top, h, w, up=False):
        for k in range(h):
            y = top + k if not up else top - k
            half = w * (1 - k / h) / 2 + 0.3
            for x in range(int(px - half), int(math.ceil(px + half))):
                rel = (x + 0.5 - (px - half)) / (2 * half)
                c = K["r4"] if rel < 0.25 else K["r3"] if rel < 0.55 else K["r1"] if rel < 0.85 else K["r0"]
                _put(S, x, y, c)
    for (px, h, w) in ((12, 22, 9), (26, 12, 5), (46, 18, 7), (70, 9, 4), (92, 16, 7), (108, 8, 4), (124, 14, 6),
                       (148, 7, 4), (164, 10, 5), (200, 8, 4), (218, 20, 8), (232, 13, 6)):
        spike(px, 0, h, w)
        _put(S, px, h, K["cr2"] if px % 3 == 0 else K["r2"])        # a drip

    # glowing crystal clusters: faceted shards, lit face / shadow face
    blue_ramp = (K["cr0"], K["cr1"], K["cr2"], K["cr3"])
    pink_ramp = (K["fu0"], K["fu1"], K["fu2"], K["cr3"])

    def shard(bx, by, h, w, lean, ramp=blue_ramp):
        for k in range(h):
            y = by - k
            t = k / h
            half = w / 2 * (1 - max(0.0, t - 0.55) / 0.45) if t > 0.55 else w / 2
            cxk = bx + lean * k
            for x in range(int(cxk - half), int(math.ceil(cxk + half))):
                rel = (x + 0.5 - (cxk - half)) / max(0.5, 2 * half)
                if rel < 0.18 or (t > 0.8 and rel < 0.5):
                    c = ramp[3]
                elif rel < 0.5:
                    c = ramp[2]
                elif rel < 0.82:
                    c = ramp[1]
                else:
                    c = ramp[0]
                if x == int(cxk - half) or x == int(math.ceil(cxk + half)) - 1:
                    c = ramp[0] if rel > 0.5 else c
                _put(S, int(x), y, c)

    def cluster(cx, by, s, halo=True, ramp=blue_ramp):
        if halo:
            _glow(S, cx, by - 7 * s, [(6 * s, K["gw2"]), (12 * s, K["gw"]), (18 * s, K["gw"])],
                  only={K["r0"], K["r1"], K["r2"], K["r3"]}, ymax=by + 2, airy=True)
        for (dx, h, w, lean) in ((-9, 7, 3, -0.45), (9, 8, 3, 0.4), (-5, 14, 4, -0.22), (5, 12, 4, 0.28),
                                 (0, 21, 5, 0.0), (-13, 4, 2, -0.6), (13, 5, 2, 0.6)):
            shard(cx + dx * s, by, int(h * s), max(2, int(w * s)), lean, ramp)
    cluster(24, FLOOR + 3, 1.35)
    cluster(118, 36, 0.75, ramp=pink_ramp)
    cluster(80, 30, 0.45, halo=False)
    cluster(226, FLOOR + 4, 1.0)

    # floor edge and the rocky floor
    for x in range(SW):
        e = FLOOR + int(1.2 * math.sin(x * math.pi / 16))
        for y in range(e - 2, e + 1):
            if S[y][x] not in (K["cr0"], K["cr1"], K["cr2"], K["cr3"]):
                S[y][x] = K["r0"] if y == e else K["r3"] if y == e - 2 else K["r2"]
    _wavy_bands(S, [FLOOR + 1, 48, 53, 59, 66, 74, 84, 96, TY + 4], (K["f1"], K["f2"]),
                seam=K["f0"], lip=K["f3"], amp=2.0)
    for y in range(FLOOR + 1, FLOOR + 3):
        for x in range(SW):
            S[y][x] = K["f0"] if y == FLOOR + 1 else K["f1"]
    # pebbles and cracks on a 32 px grid
    prng = g.Rng(90)
    for y0 in range(FLOOR + 7, TY - 2, 6):
        depth = (y0 - FLOOR) / (TY - FLOOR)
        x0 = prng.rand(0, 31)
        big = depth > 0.45
        for x in _grid32(x0):
            pts = [(0, 0, "f3"), (1, 0, "f2"), (0, 1, "f2"), (1, 1, "f0"), (2, 1, "f0")]
            if big:
                pts = [(1, -1, "f3"), (2, -1, "f3"), (0, 0, "f3"), (1, 0, "f2"), (2, 0, "f2"), (3, 0, "f1"),
                       (0, 1, "f2"), (1, 1, "f1"), (2, 1, "f1"), (3, 1, "f0"), (1, 2, "f0"), (2, 2, "f0")]
            for (dx, dy, c) in pts:
                _put(S, x + dx, y0 + dy, K[c])
        x1 = (x0 + 13) % 32
        for x in _grid32(x1):
            for k in range(3 + int(depth * 4)):
                _put(S, x + k, y0 + 3 + (k // 2) % 2, K["f0"])
    # crystal light pooled on the floor
    blue = {K["f1"]: K["fg1"], K["f2"]: K["fg2"], K["f0"]: K["f1"], K["f3"]: K["cr2"]}
    blue_s = {K["f1"]: K["fg1"], K["f2"]: K["fg1"], K["f3"]: K["fg2"]}
    _tint(S, 24, FLOOR + 5, 30, 6, blue, blue_s, ymin=FLOOR + 1)
    _tint(S, 228, FLOOR + 7, 26, 6, blue, blue_s, ymin=FLOOR + 1)

    # stalagmites at the edges of the floor
    for (px, by, h, w) in ((6, 66, 20, 9), (232, 70, 24, 10), (120, 52, 9, 5)):
        spike(px, by, h, w, up=True)
        _rect(S, px - w // 2 - 1, by, px + w // 2 + 2, by + 1, K["f0"])

    # glowing fungi: little caps with light spots
    def shroom(x, y, s):
        cap = int(3 * s)
        for dy in range(-cap, 1):
            for dx in range(-cap - 1, cap + 2):
                if (dx / (cap + 1.5)) ** 2 + ((dy + 0.5) / (cap + 0.5)) ** 2 <= 1.0:
                    c = K["fu2"] if (dx < 0 and dy < -cap // 2) else K["fu1"] if dy < 0 else K["fu0"]
                    _put(S, x + dx, y - int(3 * s) + dy, c)
        for k in range(int(3 * s)):
            _put(S, x, y - k, K["fu2"] if k < 1 else K["cr2"])
    pink = {K["f1"]: K["fp1"], K["f2"]: K["fp2"], K["f0"]: K["f1"]}
    for (x, y, s, halo) in ((14, 104, 1.4, True), (24, 108, 1.0, False), (6, 96, 0.8, False),
                            (130, 84, 1.0, True), (138, 86, 0.7, False), (220, 100, 1.3, True), (230, 104, 0.9, False),
                            (104, 58, 0.7, True)):
        if halo:
            _tint(S, x, y - 1, 14 * s, 4 * s, pink, {K["f1"]: K["fp1"], K["f2"]: K["fp1"]}, ymin=FLOOR + 1)
        shroom(x, y, s)

    _ring_base(g, S, g.ENEMY_BASE, K["r0"], K["r2"], K["r3"], K["r4"], edge=K["r1"])
    _ring_base(g, S, g.ALLY_BASE, K["r0"], K["r2"], K["r3"], K["r4"], edge=K["r1"])
    return S


# ---------------------------------------------------------------------------
# 6. GRAVEWOOD: a haunted moor, dead trees, headstones, fog, a sickly moon
# ---------------------------------------------------------------------------

def paint_grim(g):
    C = g.C
    K = {
        "k0": C(36, 36, 56), "k1": C(56, 60, 76), "k2": C(84, 96, 96), "k3": C(120, 136, 116), "k4": C(160, 176, 140),
        "mo0": C(184, 204, 144), "mo1": C(224, 236, 184), "mo2": C(248, 252, 224),
        "si0": C(20, 20, 32), "si1": C(40, 38, 54), "si2": C(62, 60, 76),
        "hs0": C(60, 62, 78), "hs1": C(98, 100, 112), "hs2": C(140, 142, 150),
        "fg0": C(110, 124, 118), "fg1": C(150, 164, 150),
        "gd0": C(34, 32, 42), "gd1": C(58, 52, 60), "gd2": C(78, 70, 76), "gd3": C(108, 98, 92),
        "b_dark": C(72, 56, 52), "b_fill": C(92, 74, 64), "b_hi": C(124, 104, 88),
        "wisp": C(168, 232, 184),
    }
    S = g.new_scene(g.PLAIN)
    HOR = 36
    _bands(S, 0, HOR, [6, 14, 22, 29], [K["k0"], K["k1"], K["k2"], K["k3"], K["k4"]])
    # the moon and its halo, top left
    MX, MY = 42, 13
    _glow(S, MX, MY, [(14, K["k3"]), (20, K["k2"])], only={K["k0"], K["k1"], K["k2"]})
    for y in range(MY - 9, MY + 10):
        for x in range(MX - 9, MX + 10):
            d = math.hypot(x + 0.5 - MX, y + 0.5 - MY)
            if d <= 8.6:
                lit = math.hypot(x + 0.5 - MX + 2.5, y + 0.5 - MY + 2.5) < 6.5
                c = K["mo2"] if lit and d < 7 else K["mo1"] if d < 7.6 else K["mo0"]
                for (qx, qy, qr) in ((MX + 2, MY - 3, 1.6), (MX - 3, MY + 2, 2.2), (MX + 4, MY + 3, 1.2)):
                    if math.hypot(x + 0.5 - qx, y + 0.5 - qy) < qr:
                        c = K["mo0"]
                _put(S, x, y, c)
    # thin clouds crossing the moon
    _streak(S, 36, 16, 22, 1.1, K["k1"])
    _streak(S, 150, 8, 40, 1.4, K["k1"], K["k0"])
    _streak(S, 210, 18, 30, 1.2, K["k2"], K["k1"])

    # far moor: low silhouette hills with a ruined chapel
    for x in range(SW):
        top = HOR - 5 + 2.2 * math.sin(x * 0.03 + 2.0) + 1.1 * math.sin(x * 0.13)
        for y in range(int(top), HOR + 1):
            _put(S, x, y, K["si2"] if y < top + 1 else K["si1"])
    CX = 96
    _rect(S, CX, 22, CX + 12, 33, K["si1"])
    for y in range(12, 22):
        half = (y - 12) * 0.35
        for x in range(int(CX + 3 - half), int(math.ceil(CX + 4 + half))):
            _put(S, x, y, K["si1"])
    for y in range(8, 12):
        _put(S, CX + 3, y, K["si1"])
    _rect(S, CX + 2, 9, CX + 6, 10, K["si1"])
    _rect(S, CX + 12, 26, CX + 22, 33, K["si1"])
    _put(S, CX + 3, 24, K["wisp"])
    _put(S, CX + 3, 25, K["wisp"])
    _put(S, CX + 16, 28, K["mo0"])

    # moor ground
    g.perspective_bands(S, HOR + 1, [HOR + 1, 41, 46, 52, 59, 67, 77, 89, 102, TY], (K["gd1"], K["gd2"]),
                        saw=(0, 1, 2, 1, 0, 2, 1, 0), seam=K["gd0"])
    for x in range(SW):
        _put(S, x, HOR + 1, K["gd0"] if x % 3 else K["si1"])
    # dead grass tufts on a 32 px grid
    trng = g.Rng(66)
    for y0 in range(HOR + 5, TY - 1, 5):
        depth = (y0 - HOR) / (TY - HOR)
        x0 = trng.rand(0, 31)
        for x in _grid32(x0):
            pts = [(0, 0), (1, -1), (2, 0)] if depth < 0.5 else [(0, 0), (1, -1), (1, -2), (2, 0), (3, -1), (4, 0)]
            for (dx, dy) in pts:
                _put(S, x + dx, y0 + dy, K["gd3"] if dy < 0 else K["gd0"])

    # headstones: far row small, a few big ones in front
    def stone(x0, by, w, h, kind):
        for y in range(by - h, by + 1):
            for x in range(x0, x0 + w):
                rel = (x - x0) / max(1, w - 1)
                if kind == "round" and y < by - h + w // 2:
                    if math.hypot(x + 0.5 - (x0 + w / 2), (y + 0.5 - (by - h + w / 2))) > w / 2:
                        continue
                if kind == "cross":
                    arm = by - h + max(2, h // 4)
                    if not (abs(x + 0.5 - (x0 + w / 2)) < max(1, w / 6) or arm <= y < arm + max(1, h // 6)):
                        continue
                c = K["hs2"] if rel < 0.25 else K["hs1"] if rel < 0.75 else K["hs0"]
                if y == by:
                    c = K["gd0"]
                _put(S, x, y, c)
        if kind != "cross" and h > 8:                    # a crack
            for k in range(3):
                _put(S, x0 + w // 2 + (k % 2), by - h + 4 + k, K["hs0"])
    for (x0, by, w, h, kind) in ((64, 39, 3, 5, "round"), (72, 40, 3, 4, "round"), (80, 39, 5, 7, "cross"),
                                 (118, 40, 3, 4, "round"), (126, 39, 4, 6, "cross"), (134, 40, 3, 4, "round"),
                                 (206, 40, 3, 5, "round"), (214, 39, 5, 7, "cross")):
        stone(x0, by, w, h, kind)
    for (x0, by, w, h, kind) in ((110, 70, 8, 14, "round"), (124, 74, 10, 16, "cross"),
                                 (214, 98, 10, 17, "round"), (226, 94, 11, 20, "cross"), (0, 90, 9, 16, "round")):
        stone(x0, by, w, h, kind)
        for x in range(x0 + 1, x0 + w + 3):                   # moon shadow falls right
            _put(S, x, by + 1, K["gd0"])

    # dead trees: gnarled trunk and bare branching limbs
    def limb(x, y, ang, ln, th):
        for i in range(int(ln)):
            px = x + math.cos(ang) * i
            py = y - math.sin(ang) * i
            t = max(1, int(th * (1 - i / ln)) + 1)
            for k in range(t):
                _put(S, int(px) + k, int(py), K["si0"] if k else K["si2"] if th > 1.5 else K["si1"])
        ex, ey = x + math.cos(ang) * ln, y - math.sin(ang) * ln
        if ln > 5:
            limb(ex, ey, ang + 0.55, ln * 0.62, th * 0.6)
            limb(ex, ey, ang - 0.5, ln * 0.55, th * 0.6)
    for (tx, by, h, th, lean) in ((14, 64, 42, 7, 0.1), (230, 58, 36, 6, -0.15)):
        for y in range(by - h, by + 1):
            t = (by - y) / h
            w = int(th * (1.3 - 0.5 * t)) + (3 if y > by - 3 else 0)
            x0 = int(tx + lean * (by - y) - w / 2)
            for x in range(x0, x0 + w):
                _put(S, x, y, K["si2"] if x == x0 else K["si0"] if x >= x0 + w - 1 else K["si1"])
        top_x = tx + lean * h
        limb(top_x, by - h, 1.9, 14, 3)
        limb(top_x, by - h, 0.9, 16, 3)
        limb(tx + lean * h * 0.55, by - h * 0.55, 0.35 if lean > 0 else 2.8, 20, 3)
        limb(tx + lean * h * 0.35, by - h * 0.35, 2.7 if lean > 0 else 0.5, 13, 2.5)
        for k in (-3, -1, 2, 4):                                   # roots
            for i in range(4):
                _put(S, int(tx + k * (1 + i * 0.6)), by - 1 + i // 2, K["si0"])

    # low fog banks: dithered wisps on a 32 px grid
    ground = {K["gd0"], K["gd1"], K["gd2"], K["gd3"], K["si1"], K["si2"], K["k3"], K["k4"]}
    for (y0, amp, th, col, core) in ((HOR - 4, 1.2, 10, K["fg0"], K["fg1"]),):
        for x in range(SW):
            c0 = y0 + amp * math.sin(x * math.pi / 16) + 0.8 * math.sin(x * math.pi / 8 + 1)
            for y in range(int(c0) - 1, int(c0) + th + 1):
                if not (0 <= y < TY) or S[y][x] not in ground:
                    continue
                t = (y + 0.5 - c0) / th                 # 0 at the top of the bank, 1 at the bottom
                if 0.2 < t < 0.75:
                    S[y][x] = core if (x + y) % 2 == 0 else col
                elif -0.2 < t < 1.0 and (x + y) % 2 == 0 and (t > 0 or x % 4 == 0):
                    S[y][x] = col
    # will-o'-wisps
    for (x, y) in ((58, 50), (200, 30), (140, 88)):
        for (dx, dy, c) in ((0, 0, "wisp"), (1, 0, "mo2"), (0, 1, "wisp"), (1, 1, "wisp"), (-1, 0, "fg1"),
                            (2, 1, "fg1"), (0, -1, "fg1"), (1, 2, "fg1")):
            _put(S, x + dx, y + dy, K[c])

    pal = {"rim": K["gd0"], "dark": K["b_dark"], "fill": K["b_fill"], "hi": K["b_hi"], "edge": K["gd0"]}
    g.soft_base(S, g.ENEMY_BASE, pal, seed=31)
    g.soft_base(S, g.ALLY_BASE, pal, seed=32)
    return S


# ---------------------------------------------------------------------------
# 7. LANTERN CRYPT: vaulted bone niches, candle sconces, flagstone floor
# ---------------------------------------------------------------------------

def paint_crypt(g):
    C = g.C
    K = {
        "w0": C(24, 20, 32), "w1": C(44, 40, 56), "w2": C(68, 62, 80), "w3": C(96, 88, 104), "w4": C(132, 122, 132),
        "b0": C(136, 124, 100), "b1": C(196, 184, 148), "b2": C(236, 228, 200),
        "fl0": C(224, 112, 40), "fl1": C(248, 196, 88), "fl2": C(255, 248, 208),
        "gw0": C(92, 72, 72), "gw1": C(132, 100, 80),
        "gh0": C(80, 144, 112), "gh1": C(160, 224, 176),
    }
    S = g.new_scene(g.PLAIN)
    FLOOR = 42
    # back wall of dressed stone: 6 px courses, blocks staggered, 32 px repeat
    for y in range(FLOOR):
        course, ly = divmod(y, 6)
        for x in range(SW):
            lx = (x + (8 if course % 2 else 0)) % 16
            if ly == 5 or lx == 15:
                c = K["w0"]
            elif ly == 0 or lx == 0:
                c = K["w3"]
            elif lx == 14 or ly == 4:
                c = K["w1"]
            else:
                c = K["w2"]
                if (x * 7 + course * 5) % 32 < 2 and ly == 2:
                    c = K["w1"]
            S[y][x] = c
    # darker vault ceiling
    for y in range(0, 6):
        for x in range(SW):
            if y < 3 or (x + y) % 2:
                S[y][x] = K["w0"] if y < 2 else K["w1"] if S[y][x] != K["w0"] else K["w0"]

    # four arched niches (64 px apart) packed with bones and skulls
    def niche(cx):
        x0, x1, top, bot = cx - 18, cx + 18, 8, FLOOR - 4
        spring = top + 12
        for y in range(top - 2, bot + 2):
            for x in range(x0 - 2, x1 + 2):
                if y < spring:
                    d = math.hypot(x + 0.5 - cx, (y + 0.5 - spring) * 1.5)
                    inside = d < 18
                    frame = d < 20.5
                else:
                    inside = x0 <= x < x1 and y < bot
                    frame = x0 - 2 <= x < x1 + 2 and y < bot + 2
                if inside:
                    _put(S, x, y, K["w0"])
                elif frame:
                    lit = x < cx and (y < spring or x < x0)
                    if y >= bot:
                        c = K["w4"] if y == bot else K["w1"]
                    else:
                        c = K["w4"] if lit else K["w1"]
                    # voussoir joints on the arch
                    if y < spring and int(math.degrees(math.atan2(spring - y, x + 0.5 - cx))) % 22 < 3:
                        c = K["w0"]
                    _put(S, x, y, c)
        # shelves of skulls (top) and stacked long bones (bottom)
        for sy in (spring - 4, spring + 5, spring + 14):
            if sy + 5 > bot:
                continue
            _rect(S, x0 + 1, sy + 5, x1 - 1, sy + 6, K["w3"])
            _rect(S, x0 + 1, sy + 6, x1 - 1, sy + 7, K["w1"])
            skulls = sy < spring + 8
            for bx in range(x0 + 3, x1 - 4, 6 if skulls else 1):
                if skulls:
                    if sy < spring and abs(bx + 2 - cx) > 12 - (spring - sy):
                        continue
                    sk = [".bbb.", "bBBBb", "BkBkB", "bBBBb", ".b.b."]
                    for dy, line in enumerate(sk):
                        for dx, ch in enumerate(line):
                            c = {"b": K["b0"], "B": K["b1"], "k": K["w0"]}.get(ch)
                            if ch == "B" and dx < 2 and dy < 2:
                                c = K["b2"]
                            if c:
                                _put(S, bx + dx, sy + dy, c)
                else:
                    ly = (bx * 3) % 5
                    for dy in range(5):
                        c = K["b1"] if dy == ly or dy == (ly + 2) % 5 else K["b0"] if dy != 4 else K["w0"]
                        if bx % 7 == 0 and dy in (ly, (ly + 2) % 5):
                            c = K["b2"]
                        _put(S, bx, sy + dy, c)
    for cx in (24, 88, 152, 216):
        niche(cx)

    # iron sconces on the piers between the niches, with candle flames
    def sconce(x, y):
        _glow(S, x + 0.5, y - 1, [(5, K["gw1"]), (10, K["gw0"]), (14, K["gw0"])],
              only={K["w1"], K["w2"], K["w3"], K["w4"]}, airy=True)
        for (dx, dy, c) in ((0, 0, "fl1"), (0, -1, "fl2"), (0, -2, "fl1"), (1, -1, "fl0"), (-1, -1, "fl0"),
                            (0, -3, "fl0"), (0, 1, "b2"), (0, 2, "b1"), (-1, 3, "w0"), (0, 3, "w0"), (1, 3, "w0"),
                            (-2, 3, "w0"), (2, 3, "w0"), (-2, 2, "w0"), (2, 2, "w0"), (0, 4, "w0"), (0, 5, "w0")):
            _put(S, x + dx, y + dy, K[c])
    for x in (56, 120, 184):
        sconce(x, 20)
    # candle clusters on the floor ledge at the wall's foot
    for (x, h) in ((6, 5), (9, 3), (12, 4), (116, 3), (120, 5), (124, 4), (228, 4), (232, 6), (235, 3)):
        top = FLOOR - h
        for y in range(top, FLOOR):
            _put(S, x, y, K["b2"] if y == top else K["b1"])
            _put(S, x + 1, y, K["b0"])
        _put(S, x, top - 1, K["fl1"])
        _put(S, x, top - 2, K["fl2"] if h > 3 else K["fl1"])
        _put(S, x + 1, top - 1, K["fl0"])

    # flagstone floor in perspective
    F = {"j": K["w0"], "d": K["w1"], "m": K["w2"], "l": K["w3"]}

    def flag(i, ly, h, lx, k, n):
        if ly == 0 or lx < k:
            return F["j"]
        if ly == 1 or lx < 2 * k:
            return F["l"]
        if lx > 16 - k or ly == h - 1:
            return F["d"]
        return F["d"] if (n * 5 + i * 3) % 7 == 0 else F["m"]
    _slabs(S, FLOOR, [FLOOR, 44, 47, 51, 56, 62, 69, 78, 88, 100, TY + 8], 16.0, flag, vy=-160.0)
    for x in range(SW):
        S[FLOOR][x] = K["w4"] if x % 7 else K["w3"]
        S[FLOOR + 1][x] = K["w0"]
    # candle glow pooled on the floor
    warm = {K["w2"]: K["gw1"], K["w3"]: K["b0"], K["w1"]: K["gw0"]}
    warm_s = {K["w2"]: K["gw0"], K["w3"]: K["gw1"]}
    for (cx, cy) in ((10, FLOOR + 4), (121, FLOOR + 4), (232, FLOOR + 4)):
        _tint(S, cx, cy, 22, 5, warm, warm_s, ymin=FLOOR + 2)
    # scattered bones on the floor
    for (x, y, ln) in ((104, 58, 6), (20, 80, 7), (222, 92, 8), (128, 100, 5)):
        for k in range(ln):
            _put(S, x + k, y + k // 3, K["b1"] if k else K["b2"])
            _put(S, x + k, y + 1 + k // 3, K["w0"])
        _put(S, x - 1, y - 1, K["b2"])
        _put(S, x + ln, y + ln // 3 - 1, K["b1"])

    # bases: carved seals of the old wards, glowing faintly green
    def seal(x, y, d, r, dx, dy, old):
        if d < 0:
            return K["w0"] if (d > -1.2 and dy > 0.2) else None
        if d < 1.0:
            return K["w0"]
        if d < 2.4:
            return K["w4"] if dx + dy * 1.6 < -0.2 else K["w1"]
        if d < 3.2:
            return K["w0"]
        cx, cy, rx, ry = cur[0]
        rr = g.ell_r(x, y, (cx, cy, rx - 3, ry - 3))
        ang = math.atan2((y + 0.5 - cy) / ry, (x + 0.5 - cx) / rx)
        if 0.78 < rr < 0.88:
            return K["gh1"] if int((ang + math.pi) / (2 * math.pi) * 24) % 3 else K["gh0"]
        if 0.4 < rr < 0.47:
            return K["gh0"]
        if rr < 0.78 and abs(math.sin(ang * 3)) < 0.08 and rr > 0.47:
            return K["gh0"]
        return K["w3"] if dy < -0.35 and rr > 0.9 else K["w2"]
    for base in (g.ENEMY_BASE, g.ALLY_BASE):
        cur = [base]
        _disc(g, S, base, seal)
    return S


# ---------------------------------------------------------------------------
# 8. CINDER ROAD: a smoking cone, lava flows, ash sky, basalt ground
# ---------------------------------------------------------------------------

def paint_volcano(g):
    C = g.C
    K = {
        "a0": C(36, 18, 28), "a1": C(64, 28, 36), "a2": C(108, 44, 40), "a3": C(164, 68, 44), "a4": C(216, 116, 60),
        "ac0": C(68, 48, 56), "ac1": C(108, 80, 80),
        "v0": C(24, 16, 24), "v1": C(48, 32, 40), "v2": C(76, 52, 60), "v3": C(108, 76, 80),
        "l0": C(168, 36, 24), "l1": C(232, 96, 32), "l2": C(252, 180, 64), "l3": C(255, 240, 168),
        "g0": C(22, 18, 26), "g1": C(40, 34, 42), "g2": C(60, 50, 58), "g3": C(92, 78, 84),
        "gg1": C(104, 48, 40), "gg2": C(148, 72, 48),
    }
    S = g.new_scene(g.PLAIN)
    HOR = 38
    _bands(S, 0, HOR, [5, 12, 20, 28], [K["a0"], K["a1"], K["a2"], K["a3"], K["a4"]])
    # rolling ash clouds across the upper sky
    for (cx, cy, w, h) in ((150, 6, 60, 3.2), (40, 3, 40, 2.4), (230, 12, 30, 2.2), (110, 15, 26, 1.6)):
        for y in range(max(0, int(cy - h) - 1), int(cy + h) + 2):
            for x in range(max(0, int(cx - w)), min(SW, int(cx + w) + 1)):
                d = math.hypot((x + 0.5 - cx) / w, (y + 0.5 - cy) / h) + 0.12 * math.sin(x * 0.4)
                if d <= 1.0:
                    S[y][x] = K["ac1"] if y > cy + 0.5 else K["ac0"]
                elif d < 1.15 and (x + y) % 2:
                    S[y][x] = K["ac0"]

    # the volcano: a tall cone on the left, lit flank, glowing crater
    PX, PY = 64, 15
    for x in range(0, 176):
        slope = abs(x + 0.5 - PX)
        top = PY + max(0.0, slope - 7) * 0.5 + 1.0 * math.sin(x * 0.5) * (slope > 9)
        if slope < 7:
            top = PY + (1 if slope < 5 else 0)
        top = min(top, 30 + 3 * math.sin(x * 0.11) + max(0.0, x - 120) * 0.3)   # foothills
        for y in range(int(top), HOR + 1):
            left = x + 0.5 < PX - 2
            ridge = int((x - PX) * (0.9 if left else -0.9) + y * 1.4) % 12 < 2 and y > top + 2
            if y < top + 1:
                c = K["a4"] if slope < 7 else K["v3"] if left else K["v2"]
            elif ridge:
                c = K["v0"] if not left else K["v1"]
            else:
                c = K["v2"] if left and (x + y) % 6 else K["v1"]
                if not left and (x + y) % 3 == 0:
                    c = K["v0"]
                if y > HOR - 4:
                    c = K["v1"] if (x + y) % 2 else K["v0"]
            S[y][x] = c
    # glow above the crater, then a billowing ash plume lit from below
    _glow(S, PX, PY - 1, [(5, K["l2"]), (10, K["a4"]), (16, K["a3"]), (24, K["a3"])],
          only={K["a0"], K["a1"], K["a2"]}, airy=True)
    for i in range(18, -1, -1):
        cx = PX - i * 2.3 + 2.0 * math.sin(i * 0.6)
        cy = PY - 2 - i * 0.62 - 3 * math.sin(min(i, 9) / 9 * math.pi / 2)
        r = 2.6 + i * 0.3
        for y in range(max(0, int(cy - r)), min(PY, int(cy + r) + 1)):
            for x in range(int(cx - r), int(cx + r) + 1):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                d = math.hypot(dx, dy)
                if d > r or not (0 <= x < SW):
                    continue
                if dy > r * 0.45 and i < 7:
                    c = K["a4"] if i < 3 and dy > r * 0.7 else K["a3"]
                elif dx + dy < -r * 0.5:
                    c = K["ac1"] if d > r * 0.6 else K["a2"]
                elif dx - dy > r * 0.6:
                    c = K["ac0"]
                else:
                    c = K["ac1"] if (x + y) % 2 and d > r - 1.2 else K["ac0"] if dy < 0 else K["ac1"]
                S[y][x] = c
    _rect(S, PX - 5, PY, PX + 6, PY + 2, K["l1"])
    _rect(S, PX - 3, PY, PX + 4, PY + 1, K["l3"])
    # lava rivulets meandering down the flanks
    for (x0, drift, ln) in ((PX - 3, -0.75, 27), (PX + 3, 0.8, 25), (PX, -0.1, 14)):
        x = float(x0)
        for k in range(ln):
            y = PY + 2 + k
            x += drift + 0.9 * math.sin(k * 0.45 + x0)
            core = k < ln * 0.6
            _put(S, int(x) - 1, y, K["l1"] if core else K["l0"])
            _put(S, int(x), y, K["l3"] if core and k % 5 == 0 else K["l2"] if core else K["l1"])
            _put(S, int(x) + 1, y, K["l1"] if core else K["l0"])
    # a far second cone on the right edge
    for x in range(200, SW):
        top = 24 + abs(x - 226) * 0.7
        for y in range(int(top), HOR + 1):
            _put(S, x, y, K["v2"] if y < top + 1 else K["v1"] if x < 226 else K["v0"])
    _rect(S, 223, 24, 229, 25, K["l1"])

    # basalt ground: cracked plates, lava seeping through the joints
    _wavy_bands(S, [HOR + 1, 43, 48, 54, 61, 69, 79, 91, 104, TY + 4], (K["g1"], K["g2"]),
                seam=K["g0"], lip=K["g3"], amp=1.6)
    for x in range(SW):
        S[HOR][x] = K["v0"]
        S[HOR + 1][x] = K["gg1"] if x % 5 == 2 else K["g0"]
    # a lava channel winding across the middle distance
    for x in range(SW):
        c0 = 50 + 2.2 * math.sin(x * math.pi / 32) + 0.8 * math.sin(x * math.pi / 8)
        w = 2.0
        for y in range(int(c0) - 2, int(c0 + w) + 3):
            t = y + 0.5 - c0
            if 0 <= t < w:
                c = K["l3"] if t < 0.8 and x % 6 < 3 else K["l2"] if t < 1.4 else K["l1"]
            elif -1.5 <= t < 0:
                c = K["g0"] if t < -1 else K["l0"]
            elif w <= t < w + 1.2:
                c = K["l0"]
            elif w + 1.2 <= t < w + 2.2 and (x + y) % 2:
                c = K["gg2"]
            else:
                continue
            _put(S, x, y, c)
    # glowing cracks on a 32 px grid
    crng = g.Rng(77)
    for y0 in range(HOR + 18, TY - 2, 9):
        depth = (y0 - HOR) / (TY - HOR)
        x0 = crng.rand(0, 31)
        ln = 4 + int(depth * 8)
        for x in _grid32(x0):
            for k in range(ln):
                yy = y0 + int(1.5 * math.sin(k * 0.9))
                _put(S, x + k, yy, K["l1"] if 1 < k < ln - 2 else K["l0"])
                if 1 < k < ln - 2 and k % 3 == 0:
                    _put(S, x + k, yy + 1, K["gg1"])
    # embers drifting up
    for y in range(4, HOR - 2, 5):
        x0 = (y * 23) % 32
        for x in _grid32(x0):
            if 0 <= x < SW and S[y][x] in (K["a0"], K["a1"], K["a2"]):
                _put(S, x, y, K["l2"] if y % 2 else K["l1"])

    # bases: cooled basalt plates with a molten seam around the rim
    def plate(x, y, d, r, dx, dy, old):
        if d < 0:
            if d > -1.2:
                return K["l0"] if dy > -0.2 else K["g0"]
            if d > -2.4 and dy > 0.3 and (x + y) % 2:
                return K["gg1"]
            return None
        if d < 1.0:
            return K["l1"] if (x // 3) % 4 else K["l2"]
        if d < 2.0:
            return K["g0"]
        if dy < 0 and d < 3.6 and dx < 0.4:
            return K["g3"]
        if dy > 0.3 and d < 3.4:
            return K["g1"]
        # a few cracks across the plate, one still glowing
        saw = abs(((dx * 4.0) % 2.0) - 1.0)
        crack = abs(dy - 0.25 * saw - 0.02) < 0.07 and abs(dx) < 0.5
        crack2 = abs(dx - 0.25 - 0.12 * math.sin(dy * 6)) < 0.03 and dy < 0.1
        if crack:
            return K["l1"] if abs(dx) < 0.4 else K["l0"]
        if crack2:
            return K["g0"]
        return K["g3"] if (x * 7 + y * 13) % 37 == 0 else K["g2"]
    for base in (g.ENEMY_BASE, g.ALLY_BASE):
        _disc(g, S, base, plate, pad=3)
    return S


# ---------------------------------------------------------------------------
# 9. DREAMSPIRE: pastel dream sky, floating isles, stars, checkered floor
# ---------------------------------------------------------------------------

def paint_dream(g):
    C = g.C
    K = {
        "d0": C(104, 96, 192), "d1": C(152, 120, 208), "d2": C(200, 144, 216), "d3": C(240, 176, 208),
        "d4": C(252, 212, 200),
        "st": C(255, 248, 216), "st2": C(200, 188, 244), "moon": C(255, 240, 184), "moon_s": C(232, 200, 168),
        "i0": C(88, 64, 120), "i1": C(128, 96, 152), "i2": C(112, 200, 176), "i3": C(176, 236, 196),
        "c0": C(232, 212, 244), "c1": C(255, 252, 255),
        "p0": C(196, 164, 228), "p1": C(244, 204, 228), "p2": C(164, 132, 204), "p3": C(255, 234, 244),
    }
    S = g.new_scene(g.PLAIN)
    HOR = 40
    _bands(S, 0, HOR, [6, 14, 23, 32], [K["d0"], K["d1"], K["d2"], K["d3"], K["d4"]])
    # stars: twinkles and dots, denser high up
    srng = g.Rng(303)
    for y in range(1, 26, 3):
        for _ in range(2 if y < 14 else 1):
            x0 = srng.rand(0, 31)
            big = srng.rand(0, 3) == 0
            for x in _grid32(x0):
                if big:
                    for (dx, dy, c) in ((0, 0, "st"), (1, 0, "st2"), (-1, 0, "st2"), (0, 1, "st2"), (0, -1, "st2")):
                        _put(S, x + dx, y + dy, K[c])
                else:
                    _put(S, x, y, K["st"] if y < 12 else K["st2"])
    # crescent moon, top left
    MX, MY = 30, 11
    for y in range(MY - 9, MY + 10):
        for x in range(MX - 9, MX + 10):
            d = math.hypot(x + 0.5 - MX, y + 0.5 - MY)
            e = math.hypot(x + 0.5 - MX - 4, y + 0.5 - MY + 3)
            if d <= 8.5 and e > 7.0:
                _put(S, x, y, K["moon"] if e > 8.2 or d < 7 else K["moon_s"])
    # floating islands: grassy tops, rocky undersides trailing roots
    def isle(cx, top, w, depth):
        for y in range(top - 2, top + depth + 1):
            for x in range(int(cx - w - 1), int(cx + w + 2)):
                dx = (x + 0.5 - cx) / w
                if y < top + 1:                                   # grassy cap
                    if dx * dx + ((y + 0.5 - top) / 2.2) ** 2 > 1.0:
                        continue
                    c = K["i3"] if dx < 0.1 and y < top else K["i2"]
                else:
                    t = (y - top) / depth
                    half = (1 - t) ** 0.8
                    if abs(dx) > half:
                        continue
                    if y == top + 1:
                        c = K["i2"] if (x % 3) else K["i1"]
                    else:
                        c = K["i1"] if dx < -0.2 * half else K["i0"]
                        if int(x * 0.5 + y) % 5 == 0:
                            c = K["i0"]
                _put(S, x, y, c)
        for k in range(-2, 3):                                 # dangling roots
            rx = int(cx + k * w * 0.3)
            for y in range(top + 2, top + depth + 3 + (k % 2) * 3):
                if abs(rx + 0.5 - cx) / w < max(0.0, 1 - (y - top) / depth) ** 0.8 + 0.05:
                    continue
                _put(S, rx, y, K["i1"])
    isle(84, 16, 20, 14)
    isle(20, 30, 11, 7)
    isle(222, 7, 13, 8)
    isle(124, 30, 6, 5)
    # a tiny spire on the big isle
    for y in range(4, 16):
        half = (y - 4) * 0.22
        for x in range(int(90 - half), int(math.ceil(91 + half))):
            _put(S, x, y, K["c1"] if x < 90.5 else K["p2"])
    _put(S, 90, 3, K["st"])
    _put(S, 90, 10, K["d0"])

    # soft cloud bank on the horizon, 32 px repeat
    for x in range(SW):
        u = (x % 32) / 32.0
        h = 4 + 2.5 * abs(math.sin(u * math.pi)) + 1.5 * abs(math.sin(u * 3 * math.pi))
        for y in range(int(HOR - h), HOR + 3):
            top = y < HOR - h + 1.5
            S[y][x] = K["c1"] if top or (y < HOR - h + 3 and (x % 32) < 16) else K["c0"]

    # checkered dream floor converging on the horizon
    def check(i, ly, h, lx, k, n):
        if lx < k and i > 1:
            return K["p2"]
        c = K["p0"] if (n + i) % 2 else K["p1"]
        if ly == 0 and i > 1:
            return K["p2"]
        if ly == 1 and c == K["p1"]:
            return K["p3"]
        return c
    _slabs(S, HOR + 3, [HOR + 3, 45, 48, 52, 57, 63, 70, 79, 90, 104, TY + 16], 24.0, check, vy=-60.0,
           stagger=0.0)
    for x in range(SW):
        S[HOR + 3][x] = K["c0"] if x % 3 else K["c1"]
    # stardust sparkles on the floor
    for y in range(HOR + 8, TY, 7):
        x0 = (y * 11) % 32
        for x in _grid32(x0):
            for (dx, dy) in ((0, 0), (1, 0), (-1, 0), (0, -1), (0, 1)):
                if (dx, dy) == (0, 0) or y > 70:
                    _put(S, x + dx, y + dy, K["st"] if (dx, dy) == (0, 0) else K["p3"])

    # bases: plump clouds
    def cloud(x, y, d, r, dx, dy, old):
        ang = math.atan2(dy, dx * 0.6)
        dd = d - 3.0 * (1 - abs(math.sin(ang * 5)))          # scalloped puffs
        if dd < 0:
            if dd > -1.2 and dy > 0.3 and d > -1:
                return K["p2"]                              # soft shadow on the floor
            return None
        if dd < 1.0:
            return K["st2"] if dy < 0 else K["p2"]
        # each puff lit from the top-left
        lobe = ang * 5 / math.pi % 1.0
        if dy > 0.35 and dd < 3.0:
            return K["st2"]
        if dy < 0.1 and lobe < 0.35 and dd < 3.5:
            return K["c1"]
        if dx + dy < -0.35:
            return K["c1"]
        return K["c0"]
    for base in (g.ENEMY_BASE, g.ALLY_BASE):
        _disc(g, S, base, cloud, pad=4)
    return S


# ---------------------------------------------------------------------------
# 10. WILLOW ACRE: sunny farmland, red barn and silo, fence, crop rows
# ---------------------------------------------------------------------------

def paint_farm(g):
    C = g.C
    K = {
        "sky0": C(112, 176, 240), "sky1": C(152, 204, 248), "sky2": C(196, 228, 252),
        "cl": C(248, 248, 248), "cl_s": C(208, 224, 240),
        "h0": C(96, 160, 96), "h1": C(128, 184, 104), "t0": C(48, 104, 64), "t1": C(80, 140, 72),
        "br0": C(136, 40, 40), "br1": C(192, 64, 56), "rf": C(80, 56, 64), "rf1": C(112, 80, 84),
        "wt": C(244, 240, 224), "dk": C(48, 32, 40),
        "si0": C(136, 140, 152), "si1": C(188, 192, 200),
        "fe0": C(120, 84, 56), "fe1": C(188, 144, 96),
        "s0": C(96, 64, 44), "s1": C(132, 92, 60), "s2": C(168, 124, 80),
        "cr0": C(64, 128, 56), "cr1": C(112, 176, 72), "wh0": C(200, 160, 72), "wh1": C(240, 208, 112),
        "g0": C(88, 152, 64), "g1": C(116, 176, 80), "g2": C(140, 196, 96), "g3": C(180, 224, 128),
    }
    # shared shades keep the scene to 24 colours so the barn, field, fence
    # and pasture tiles all find a bank
    K.update({"rf1": K["br0"], "rf": K["dk"], "si1": K["cl_s"], "s2": K["fe1"], "t0": K["cr0"], "t1": K["g0"]})
    S = g.new_scene(g.PLAIN)
    HOR = 32
    _bands(S, 0, HOR, [9, 20], [K["sky0"], K["sky1"], K["sky2"]])
    _puffs(S, [(130, 8, 24), (206, 12, 18), (60, 5, 16)], K["cl"], K["cl_s"], HOR - 6)
    # rolling hills with hedgerow trees
    for x in range(SW):
        top = 22 + 2.5 * math.sin(x * 0.028 + 0.3) + 1.5 * math.sin(x * 0.09 + 2)
        for y in range(int(top), HOR + 1):
            S[y][x] = K["h1"] if y < top + 1 or (y < top + 3 and (x + y) % 3 == 0) else K["h0"]
    for tx in range(100, 236, 13):
        if 120 < tx < 150:
            continue
        top = int(22 + 2.5 * math.sin(tx * 0.028 + 0.3) + 1.5 * math.sin(tx * 0.09 + 2))
        r = 4 + tx % 3
        for y in range(top - r - 2, top + 2):
            for x in range(tx - r, tx + r + 1):
                d = math.hypot(x + 0.5 - tx, (y + 0.5 - (top - r + 1)) * 1.15)
                if d <= r:
                    _put(S, x, y, K["t1"] if (x + 0.5 - tx) + (y + 0.5 - (top - r + 1)) < -1 else K["t0"])

    # the barn: gambrel roof, red boards, white trim and X doors
    BX0, BX1, EAVE, GROUND = 6, 54, 16, 40
    mid = (BX0 + BX1) / 2
    for y in range(2, EAVE + 1):
        t = (y - 2) / (EAVE - 2)
        half = (BX1 - BX0) / 2 * (0.35 + 0.5 * t if t < 0.45 else 0.575 + 0.5 * (t - 0.45))
        half = min(half + 2, (BX1 - BX0) / 2 + 2)
        for x in range(int(mid - half), int(math.ceil(mid + half))):
            edge = x < mid - half + 1 or x >= mid + half - 1
            c = K["wt"] if edge and x < mid else K["dk"] if edge else (K["rf1"] if x < mid else K["rf"])
            if (y - 2) % 3 == 2 and not edge:
                c = K["rf"] if x < mid else K["dk"]
            _put(S, x, y, c)
    for y in range(EAVE + 1, GROUND):
        for x in range(BX0, BX1):
            c = K["br1"] if (x - BX0) % 4 else K["br0"]
            if x >= BX1 - 3:
                c = K["br0"]
            _put(S, x, y, c)
    # hayloft window and the big doors
    _rect(S, int(mid) - 4, EAVE + 3, int(mid) + 4, EAVE + 9, K["wt"])
    _rect(S, int(mid) - 3, EAVE + 4, int(mid) + 3, EAVE + 8, K["dk"])
    _rect(S, int(mid) - 3, EAVE + 4, int(mid), EAVE + 6, K["wh1"])        # hay
    DX0, DX1, DT = int(mid) - 10, int(mid) + 10, 27
    _rect(S, DX0, DT, DX1, GROUND, K["wt"])
    for y in range(DT + 1, GROUND):
        for x in range(DX0 + 1, DX1 - 1):
            if x == int(mid):
                c = K["wt"]
            else:
                side = x < mid
                lx = (x - (DX0 + 1)) if side else (x - int(mid) - 1)
                wdt = int(mid) - DX0 - 1
                u = lx / max(1, wdt - 1)
                v = (y - DT - 1) / max(1, GROUND - DT - 2)
                c = K["wt"] if abs(u - v) < 0.12 or abs(u + v - 1) < 0.12 else K["br0"]
            _put(S, x, y, c)
    for y in range(EAVE + 1, GROUND):
        _put(S, BX0, y, K["wt"])
        _put(S, BX1 - 1, y, K["wt"])
    # silo
    for y in range(6, GROUND):
        for x in range(56, 68):
            rel = (x - 56) / 11
            if y < 11:
                if math.hypot(x + 0.5 - 62, (y + 0.5 - 11) * 1.2) > 6.2:
                    continue
                c = K["si1"] if rel < 0.4 else K["si0"]
            else:
                c = K["si1"] if rel < 0.35 else K["si0"] if rel < 0.85 else K["dk"]
                if (y - 11) % 6 == 0:
                    c = K["si0"] if rel < 0.85 else K["dk"]
            _put(S, x, y, c)
    # a small windmill on the far right
    WX, WY = 214, 14
    for y in range(WY, HOR):
        half = 1.5 + (y - WY) * 0.15
        for x in range(int(WX - half), int(math.ceil(WX + half))):
            _put(S, x, y, K["wt"] if x < WX else K["si0"])
    for k in range(-7, 8):
        for (dx, dy) in ((k, k), (k, -k)):
            if k:
                _put(S, WX + dx, WY + dy, K["fe0"] if abs(k) < 3 else K["wt"])
    _put(S, WX, WY, K["dk"])

    # crop field behind the fence: rows converging on the horizon
    FIELD0, FIELD1 = 34, 48
    VX, VY = 132.0, -40.0
    for y in range(FIELD0, FIELD1):
        k = (FIELD0 - VY) / (y + 0.5 - VY)
        for x in range(SW):
            if y < GROUND and (BX0 <= x < BX1 or 56 <= x < 68):
                continue
            u = ((x + 0.5 - VX) * k) % 10.0
            wheat = x > 150
            if u < 3.0:
                c = K["s0"] if u < 1.2 else K["s1"]
            elif u < 5.0:
                c = K["wh1"] if wheat else K["cr1"]
            else:
                c = K["wh0"] if wheat else K["cr0"]
            if y == FIELD0 and u >= 3.0:
                c = K["wh1"] if wheat else K["cr1"]
            S[y][x] = c
    for x in range(SW):
        if S[HOR][x] in (K["h0"], K["h1"]):
            S[HOR][x] = K["h0"]
    # the fence: posts every 16 px, two rails
    FY = 48
    for x in range(SW):
        for (ry, c) in ((FY - 5, "fe1"), (FY - 4, "fe0"), (FY - 1, "fe1"), (FY, "fe0")):
            _put(S, x, ry, K[c])
        if x % 16 in (6, 7, 8):
            for y in range(FY - 8, FY + 3):
                _put(S, x, y, K["fe1"] if x % 16 == 6 else K["fe0"] if x % 16 == 7 else K["dk"])
            _put(S, x, FY - 9, K["fe1"] if x % 16 < 8 else K["fe0"])

    # pasture in front
    g.perspective_bands(S, FY + 1, [FY + 1, 53, 59, 66, 74, 84, 96, TY], (K["g1"], K["g2"]), seam=K["g0"])
    for x in range(SW):
        S[FY + 1][x] = K["g0"]
        S[FY + 2][x] = K["g0"] if x % 2 else K["g1"]
    trng = g.Rng(88)
    for y0 in range(FY + 6, TY - 1, 5):
        depth = (y0 - FY) / (TY - FY)
        x0 = trng.rand(0, 31)
        for x in _grid32(x0):
            pts = [(0, 0, "g0"), (1, -1, "g0"), (2, 0, "g0")]
            if depth > 0.4:
                pts += [(1, -2, "g3"), (3, -1, "g0"), (4, 0, "g0")]
            for (dx, dy, c) in pts:
                _put(S, x + dx, y0 + dy, K[c])
            if (y0 // 5) % 3 == 0:                                  # a daisy
                fx = x + 17
                for (dx, dy, c) in ((0, 0, "wh1"), (-1, 0, "wt"), (1, 0, "wt"), (0, -1, "wt"), (0, 1, "wt")):
                    _put(S, fx + dx, y0 + dy - 3, K[c])

    # enemy on a patch of short grass, ally on freshly tilled soil
    pal = {"rim": K["g0"], "dark": K["g1"], "fill": K["g2"], "hi": K["g3"], "edge": K["g0"]}
    g.soft_base(S, g.ENEMY_BASE, pal, seed=41)

    def tilled(x, y, d, r, dx, dy, old):
        if d < 0:
            return K["g0"] if (d > -1.2 and dy > 0.25) else None
        if d < 1.0 + max(0.0, dy):
            return K["s0"]
        if dy < 0 and r > 0.84 and dx < 0.5:
            return K["s2"]
        f = (y - int(g.ALLY_BASE[1] - g.ALLY_BASE[3])) % 4             # furrows
        if f == 0:
            return K["s2"] if dx < 0.3 else K["s1"]
        if f == 3:
            return K["s0"]
        return K["s1"]
    _disc(g, S, g.ALLY_BASE, tilled)
    return S


# ---------------------------------------------------------------------------
# 11. THE LAIR: a ruined sanctum on a peak, a blazing aura behind the dais
# ---------------------------------------------------------------------------

def paint_lair(g):
    C = g.C
    K = {
        "k0": C(20, 12, 40), "k1": C(40, 20, 72), "k2": C(72, 32, 108), "k3": C(120, 56, 140),
        "gl0": C(176, 92, 164), "gl1": C(232, 152, 168), "gl2": C(252, 212, 176), "gl3": C(255, 248, 228),
        "s0": C(28, 24, 48), "s1": C(56, 48, 84), "s2": C(92, 80, 120), "s3": C(136, 124, 160), "s4": C(188, 176, 204),
        "r0": C(176, 120, 48), "r1": C(240, 196, 88), "r2": C(255, 240, 176),
        "f0": C(36, 28, 56), "f1": C(64, 54, 88), "f2": C(88, 76, 112), "f3": C(120, 106, 140),
    }
    S = g.new_scene(g.PLAIN)
    HOR = 42
    _bands(S, 0, HOR, [8, 18, 30], [K["k0"], K["k1"], K["k2"], K["k3"]])
    # the aura: a huge sun-like halo behind the enemy's dais, with rays
    AX, AY = 176, 30
    for y in range(0, HOR):
        for x in range(96, SW):
            dx, dy = x + 0.5 - AX, y + 0.5 - AY
            d = math.hypot(dx, dy)
            if d > 70:
                continue
            ang = math.atan2(dy, dx)
            ray = math.cos(ang * 9) > 0.55
            lvl = 4.2 - d / 12.0 + (0.9 if ray else 0.0)
            j = 0.35 if (x + y) % 2 else -0.15
            i = int(lvl + j)
            if i <= 0:
                continue
            cur = S[y][x]
            order = [K["k0"], K["k1"], K["k2"], K["k3"], K["gl0"], K["gl1"], K["gl2"], K["gl3"]]
            base_i = order.index(cur) if cur in order else 0
            S[y][x] = order[min(len(order) - 1, max(base_i, i + 2))]
    for y in range(AY - 11, AY + 12):
        for x in range(AX - 11, AX + 12):
            d = math.hypot(x + 0.5 - AX, y + 0.5 - AY)
            if d <= 10.5:
                _put(S, x, y, K["gl3"] if d < 8.5 or (x + y) % 2 else K["gl2"])
    # stars in the dark corners
    for y in range(2, 26, 4):
        x0 = (y * 13) % 32
        for x in _grid32(x0):
            if 0 <= x < SW and S[y][x] in (K["k0"], K["k1"]):
                _put(S, x, y, K["s4"] if y % 3 else K["gl1"])

    # distant peaks silhouetted against the glow
    for x in range(SW):
        top = HOR - 8 + 4 * math.sin(x * 0.045 + 1.0) + 2 * math.sin(x * 0.13) - (6 if 150 < x < 200 else 0) * \
            math.sin(max(0.0, min(1.0, (x - 150) / 50)) * math.pi)
        for y in range(int(top), HOR + 1):
            _put(S, x, y, K["s2"] if y < top + 1 and (AX - x) * 0.3 > -6 else K["s1"])

    # broken colonnade: fluted pillars, lit left, some snapped off
    def pillar(x0, w, top, snapped):
        bot = HOR + 4
        for y in range(top, bot):
            for x in range(x0, x0 + w):
                rel = (x - x0) / (w - 1)
                flute = (x - x0) % 3 == 2 and 0 < x - x0 < w - 1
                c = K["s4"] if rel < 0.2 else K["s3"] if rel < 0.55 else K["s2"] if rel < 0.85 else K["s1"]
                if flute:
                    c = K["s2"] if rel < 0.55 else K["s1"]
                if x > AX - 60 and rel > 0.85:
                    c = K["gl0"]                                        # rim light from the aura
                _put(S, x, y, c)
        if snapped:
            for x in range(x0, x0 + w):
                jag = (x * 5) % 4
                for y in range(top, top + jag):
                    _put(S, x, y, S[top - 1][x] if top > 0 else K["k0"])
                _put(S, x, top + jag, K["s4"] if x < x0 + w // 2 else K["s3"])
        else:
            _rect(S, x0 - 2, top - 3, x0 + w + 2, top, K["s3"])
            _rect(S, x0 - 2, top - 3, x0 + w + 2, top - 2, K["s4"])
            _rect(S, x0 - 1, top - 5, x0 + w + 1, top - 3, K["s2"])
            _rect(S, x0 - 1, top, x0 + w + 1, top + 1, K["s1"])
        _rect(S, x0 - 2, bot - 3, x0 + w + 2, bot, K["s2"])
        _rect(S, x0 - 2, bot - 3, x0 + w + 2, bot - 2, K["s3"])
    for (x0, w, top, snapped) in ((4, 12, 6, False), (32, 10, 18, True), (84, 10, 12, False), (116, 9, 28, True),
                                  (222, 12, 4, False)):
        pillar(x0, w, top, snapped)
    # a lintel still bridging the first pair
    _rect(S, 0, 1, 40, 5, K["s2"])
    _rect(S, 0, 1, 40, 2, K["s4"])
    _rect(S, 0, 5, 40, 6, K["s0"])
    for x in range(36, 42):
        for y in range(1, 6):
            if x - 36 > y - 1:
                S[y][x] = S[0][x]

    # ancient floor: great slabs with rune-lit joints
    def slab(i, ly, h, lx, k, n):
        if ly == 0 or lx < k:
            return K["f0"]
        if ly == 1 or lx < 2 * k:
            return K["f3"]
        if lx > 20 - k or ly == h - 1:
            return K["f1"]
        return K["f2"]
    _slabs(S, HOR + 2, [HOR + 2, 46, 50, 55, 61, 68, 77, 88, 101, TY + 12], 20.0, slab, vy=-200.0)
    for x in range(SW):
        S[HOR + 2][x] = K["s3"]
        S[HOR + 3][x] = K["f0"]
    # the aura's light spilling across the floor
    warm = {K["f2"]: K["gl0"], K["f3"]: K["gl1"], K["f1"]: K["f2"]}
    warm_s = {K["f2"]: K["f3"], K["f1"]: K["f2"]}
    _tint(S, AX, HOR + 12, 64, 9, warm, warm_s, ymin=HOR + 4)
    # glowing runes set into a few slabs, 32 px repeat
    for (y0, x0) in ((60, 10), (96, 22)):
        for x in _grid32(x0):
            if 40 < x + 2 < 110 or x < -4:
                continue
            for (dx, dy) in ((0, 0), (1, 0), (2, 0), (1, -1), (1, 1), (0, 2), (2, 2)):
                _put(S, x + dx, y0 + dy, K["r1"] if (dx, dy) != (1, 0) else K["r2"])

    # bases: the enemy's raised dais with a blazing rune ring; the ally's
    # worn rune circle on the floor
    def dais(x, y, d, r, dx, dy, old):
        if d < 0:
            below = g.ell_dist(x, y - 5, cur[0])
            if below >= 0 and dy > 0:
                step = (y - (cur[0][1])) % 3
                if below < 1.0 or y >= cur[0][1] + cur[0][3] + 4:
                    return K["s0"]
                return K["s3"] if step == 0 and dx < 0.3 else K["s1"] if dx > 0.5 else K["s2"]
            return None
        if d < 1.0:
            return K["s4"] if dy < 0 else K["s1"]
        if d < 2.5:
            return K["r1"] if (int((math.atan2(dy, dx) + math.pi) * 6) % 3) else K["r2"]
        if d < 3.4:
            return K["r0"]
        if dy < -0.3 and d < 5:
            return K["s4"]
        cx, cy, rx, ry = cur[0]
        rr = g.ell_r(x, y, (cx, cy, rx - 4, ry - 4))
        ang = math.atan2(dy, dx)
        if 0.66 < rr < 0.74:                                    # engraved inner ring with glyphs
            return K["r0"] if int((ang + math.pi) / (2 * math.pi) * 16) % 2 else K["s1"]
        if rr < 0.3:
            return K["s4"] if dx + dy < -0.1 else K["s3"]
        if rr < 0.36:
            return K["s1"]
        return K["s3"] if dy > 0.25 or (x + y) % 11 else K["s2"]
    cur = [g.ENEMY_BASE]
    _disc(g, S, g.ENEMY_BASE, dais, pad=7)

    def circle(x, y, d, r, dx, dy, old):
        if d < 0:
            return K["f0"] if (d > -1.2 and dy > 0.2) else None
        if d < 1.0:
            return K["f0"]
        if d < 2.2:
            return K["r1"] if dx + dy * 1.6 < 0.2 else K["r0"]
        if d < 3.2:
            return K["f0"]
        if 0.6 < r < 0.66:
            return K["r0"]
        if dy < -0.2 and r > 0.8:
            return K["f3"]
        return K["f2"]
    _disc(g, S, g.ALLY_BASE, circle)
    return S


def scenes(g):
    """(key, painter) pairs in BSCENE_* order after the original five."""
    return [
        ("city", lambda: paint_city(g)),
        ("coast", lambda: paint_coast(g)),
        ("sea", lambda: paint_sea(g)),
        ("snow", lambda: paint_snow(g)),
        ("cave", lambda: paint_cave(g)),
        ("grim", lambda: paint_grim(g)),
        ("crypt", lambda: paint_crypt(g)),
        ("volcano", lambda: paint_volcano(g)),
        ("dream", lambda: paint_dream(g)),
        ("farm", lambda: paint_farm(g)),
        ("lair", lambda: paint_lair(g)),
    ]
