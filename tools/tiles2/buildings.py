"""Buildings: parametric houses in the GBA-era 3/4 view (roof front face,
walls, windows, doors, foundation). One call draws a whole building as a
transparent object; styles come from role dictionaries so every area can
build its own architecture from the same routine.

Style dict keys (roles):
  out           building outline
  roof          [dark, dk, base, lt, hi] roof ramp
  wall          [dark, base, lt] wall ramp
  trim          [dark, base, lt] wood trim / beams / door frame
  glass         [dark, base, glint]
  door          [dark, base, lt] door leaf (defaults to trim)
  found         [dark, base, lt] foundation stones (defaults to wall)
  accent        optional role for signs / emblems
"""

import math

from core import Img, hash32, rnd
from paint import stamp


def _roof_shingles(img, x0, y0, x1, y1, R, style='shingle', ridge=True, out=None, slant=True):
    """Fill a roof face with rows of shingles lit from the top."""
    H = y1 - y0 + 1
    for y in range(y0, y1 + 1):
        ry = y - y0
        row = ry // 4
        k = ry % 4
        # vertical light: upper rows catch more sun
        sh = 1 if ry < H * 0.3 else (0 if ry < H * 0.72 else -1)
        idx = lambda i: R[max(0, min(4, i + sh))]
        dark, dk, base, lt, hi = R[0], idx(1), idx(2), idx(3), idx(4)
        if sh < 0:
            dark = R[0]
        for x in range(x0, x1 + 1):
            if style == 'shingle':
                c = hi if k == 0 else (lt if k == 1 else (base if k == 2 else dk))
                tab = (x + (row % 2) * 4) % 8
                if tab == 0 and k in (1, 2):
                    c = dk
            elif style == 'tile':          # curved clay tiles in columns
                col = x % 4
                c = lt if col == 1 else (base if col in (0, 2) else dk)
                if k == 3:
                    c = dk if col != 1 else base
                if k == 0 and col == 1:
                    c = hi
            elif style == 'thatch':
                n = hash32(x % 16, (y // 2) % 8, 7) % 5
                c = [dk, base, base, lt, hi][n] if k != 3 else (dk if (x + row) % 2 else base)
            elif style == 'slate':
                tab = (x + (row % 2) * 4) % 8
                c = lt if k == 0 else base
                if k == 3 or tab == 0:
                    c = dk
            elif style == 'snow':          # snow-laden: white with blue shade
                c = hi if k < 2 else lt
                if k == 3 and (x + row * 3) % 7 < 3:
                    c = base
            else:
                c = base
            # darken toward the eave
            if ry > H - 3:
                c = dk if ry == H - 2 else dark
            img.set(x, y, c)
    if ridge:
        img.hline(x0, x1, y0, hi)


def _window(img, x, y, w, h, st, shutters=None, box=None):
    """Window with frame, glass (dark top-left, glint), sill."""
    trim = st['trim']
    gl = st['glass']
    img.rect(x, y, x + w - 1, y + h - 1, trim[1])
    img.rect(x + 1, y + 1, x + w - 2, y + h - 2, gl[1])
    img.hline(x + 1, x + w - 2, y + 1, gl[0])
    img.vline(x + 1, y + 1, y + h - 2, gl[0])
    # glint diagonal
    for i in range(min(w, h) - 3):
        if x + 2 + i < x + w - 1 and y + h - 3 - i > y + 1:
            pass
    img.set(x + w - 3, y + 2, gl[2])
    img.set(x + w - 4, y + 3, gl[2])
    img.set(x + w - 3, y + 3, gl[2])
    # mullions
    if w >= 8:
        img.vline(x + w // 2, y + 1, y + h - 2, trim[1])
    if h >= 8:
        img.hline(x + 1, x + w - 2, y + h // 2, trim[1])
    img.hline(x - 1, x + w, y + h, trim[2])       # sill
    img.hline(x, x + w - 1, y + h + 1, trim[0])
    if shutters:
        img.rect(x - 3, y, x - 2, y + h - 1, shutters[1])
        img.rect(x + w + 1, y + 1 - 1, x + w + 2, y + h - 1, shutters[0])
    if box:
        img.rect(x - 1, y + h + 1, x + w, y + h + 3, box[0])
        for i in range(x - 1, x + w + 1, 2):
            img.set(i, y + h, box[1] if (i // 2) % 2 else box[2])
            img.set(i + 1, y + h + 1, box[2])


def _door(img, x, y, w, h, st, arch=True, glass=True):
    d = st.get('door', st['trim'])
    trim = st['trim']
    img.rect(x - 1, y - 1, x + w, y + h - 1, trim[0])
    img.rect(x, y, x + w - 1, y + h - 1, d[1])
    img.vline(x, y, y + h - 1, d[2])
    img.vline(x + w - 1, y, y + h - 1, d[0])
    for yy in range(y + 2, y + h - 1, 3):
        img.hline(x + 1, x + w - 2, yy, d[0] if (yy - y) % 6 == 2 else d[1])
    if arch:
        img.set(x, y, trim[0])
        img.set(x + w - 1, y, trim[0])
    if glass and h >= 12:
        gl = st['glass']
        img.rect(x + 2, y + 2, x + w - 3, y + 4, gl[1])
        img.set(x + w - 3, y + 2, gl[2])
    img.set(x + w - 3, y + h // 2 + 1, st['glass'][2] if 'knob' not in st else st['knob'])
    # step
    img.hline(x - 1, x + w, y + h, trim[2])
    img.hline(x - 2, x + w + 1, y + h + 1, trim[1])


def house(w, h, st, roof_h=None, roof_style='shingle', door_at=None, windows=None,
          chimney=None, shutters=None, flower_box=None, sign=None, awning=None, gable=False,
          siding='plaster', beams=False, emblem=None, door_w=10, storeys=1):
    """A building w x h px (multiples of 16). Returns an Img.

    door_at: x centre of the door (px) or None for no door.
    windows: list of (x, y) top-left positions (relative to the wall top)
             or 'auto'.
    chimney: x of a chimney or None. sign: (x, y, w, h) plate on the wall.
    awning: (x0, x1, [dark, base, lt]) striped canopy over the door.
    emblem: callable(img, x, y) that draws a symbol centred at x, y."""
    img = Img(w, h)
    out = st['out']
    R = st['roof']
    Wl = st['wall']
    trim = st['trim']
    found = st.get('found', Wl)
    rh = roof_h or int(h * 0.52)
    fy = h - 3                                  # foundation top
    wall_top = rh
    # ---- walls ------------------------------------------------------------
    for y in range(wall_top, fy):
        for x in range(2, w - 2):
            if siding == 'plank':
                c = Wl[2] if (y - wall_top) % 4 == 0 else Wl[1]
                if (y - wall_top) % 4 == 3:
                    c = Wl[0]
            elif siding == 'brick':
                row = (y - wall_top) // 3
                k = (y - wall_top) % 3
                c = Wl[1]
                if k == 2 or (x + (row % 2) * 4) % 8 == 0:
                    c = Wl[0]
                elif k == 0 and (x * 3 + row) % 5 == 0:
                    c = Wl[2]
            elif siding == 'stone':
                row = (y - wall_top) // 4
                k = (y - wall_top) % 4
                off = (row % 2) * 4
                c = Wl[1]
                if k == 3 or (x + off) % 8 == 0:
                    c = Wl[0]
                elif k == 0:
                    c = Wl[2]
            elif siding == 'log':
                k = (y - wall_top) % 5
                c = [Wl[2], Wl[1], Wl[1], Wl[1], Wl[0]][k]
            else:                                # plaster
                c = Wl[1]
                if hash32(x % 16, y % 16, 3) % 23 == 0:
                    c = Wl[2]
            img.set(x, y, c)
    # shadow under the eave
    img.hline(2, w - 3, wall_top, Wl[0])
    img.hline(2, w - 3, wall_top + 1, Wl[0])
    # corner posts / beams
    if beams or siding in ('plaster',):
        for x in (2, 3):
            img.vline(x, wall_top, fy - 1, trim[2] if x == 2 else trim[1])
        for x in (w - 4, w - 3):
            img.vline(x, wall_top, fy - 1, trim[1] if x == w - 4 else trim[0])
    if beams:
        img.hline(2, w - 3, wall_top + 2, trim[1])
        mid = (wall_top + fy) // 2
        if storeys > 1:
            img.hline(2, w - 3, mid, trim[1])
            img.hline(2, w - 3, mid + 1, trim[0])
    # foundation
    for y in range(fy, h - 1):
        for x in range(2, w - 2):
            c = found[1] if (x + (y - fy) * 4) % 8 else found[0]
            if y == fy:
                c = found[2] if x % 8 else found[0]
            img.set(x, y, c)
    # ---- roof ------------------------------------------------------------------
    if gable:
        # front gable: a triangle of wall framed by two thick roof slopes
        cx = w / 2
        th = 6
        for y in range(0, rh + 1):
            half = (y + 1.5) * (w / 2) / (rh - 1)
            for x in range(0, w):
                dx = abs(x + 0.5 - cx)
                if dx > half:
                    continue
                edge = half - dx
                if edge < th:
                    left = x < cx
                    k = (3 if edge > 1.5 else 4) if left else (1 if edge > 1.5 else 2)
                    if edge < 1.0:
                        k = 0
                    row = int(edge + y) % 4
                    c = R[k] if row else R[max(0, k - 1)]
                    img.set(x, y, c)
                else:
                    if siding == 'plank':
                        c = Wl[2] if y % 4 == 0 else (Wl[0] if y % 4 == 3 else Wl[1])
                    else:
                        c = Wl[1]
                    if edge < th + 1.2:
                        c = Wl[0]
                    img.set(x, y, c)
        # gable vent
        vx, vy = int(cx) - 3, max(th + 2, rh // 2)
        img.rect(vx, vy, vx + 5, vy + 4, trim[0])
        img.rect(vx + 1, vy + 1, vx + 4, vy + 3, st['glass'][1])
        img.set(vx + 3, vy + 1, st['glass'][2])
        img.hline(0, w - 1, rh, R[0])
        img.hline(0, w - 1, rh - 1, R[1])
    else:
        inset = 3
        for y in range(0, rh):
            t = y / max(1, rh - 1)
            ins = int(round(inset * (1 - t)))
            xl, xr = ins, w - 1 - ins
            _roof_shingles(img, xl, y, xr, y, R, roof_style, ridge=False)
            # side facets of a hip roof: darker, lit on the left
            for x in range(xl, min(xl + 3, xr)):
                if y < rh - 2:
                    img.set(x, y, R[3] if x == xl else img.get(x, y))
        _roof_shingles(img, inset, 1, w - 1 - inset, rh - 1, R, roof_style, ridge=False)
        img.hline(inset, w - 1 - inset, 0, R[1])
        img.hline(inset, w - 1 - inset, 1, R[4])
        for y in range(0, rh):
            t = y / max(1, rh - 1)
            ins = int(round(inset * (1 - t)))
            for x in range(ins, inset + 1):
                if y < rh - 2:
                    img.set(x, y, R[3] if (x + y) % 3 else R[2])
                    img.set(w - 1 - x, y, R[1] if (x + y) % 3 else R[0])
        img.hline(0, w - 1, rh - 1, R[0])
        img.hline(0, w - 1, rh - 2, R[1])
    if chimney is not None:
        cx = chimney
        ch = st.get('chimney', found)
        for y in range(1, 9):
            for x in range(cx, cx + 6):
                c = ch[1]
                if y % 3 == 0 or (x - cx + (y // 3) * 3) % 6 == 0:
                    c = ch[0]
                img.set(x, y, c)
        img.vline(cx, 1, 8, ch[2])
        img.rect(cx - 1, 0, cx + 6, 1, ch[2])
        img.hline(cx - 1, cx + 6, 1, ch[0])
        img.hline(cx, cx + 5, 9, R[0])
    # ---- windows & door -----------------------------------------------------------
    wall_h = fy - wall_top
    if windows == 'auto':
        windows = []
        n = max(1, (w - 16) // 22)
        slots = [int((i + 0.5) * w / (n + 1)) for i in range(n + 1)]
        for sx in slots:
            if door_at is None or abs(sx - door_at) > door_w + 2:
                windows.append((sx - 6, 4))
        if storeys > 1:
            windows += [(sx - 6, 4 + wall_h // 2) for sx in slots
                        if door_at is None or abs(sx - door_at) > door_w + 2]
    for (wx, wy) in (windows or []):
        ww, wh = st.get('window', (12, 10))
        _window(img, wx, wall_top + wy, ww, wh, st, shutters=shutters, box=flower_box)
    if awning:
        ax0, ax1, A = awning
        ay = wall_top + 2
        for x in range(ax0, ax1 + 1):
            stripe = ((x - ax0) // 3) % 2
            for y in range(ay, ay + 4):
                img.set(x, y, A[2] if stripe else A[1])
            img.set(x, ay + 4, A[0] if (x - ax0) % 3 != 1 else None)
            img.set(x, ay - 1, A[0])
        img.hline(ax0, ax1, ay + 3, A[0])
    if door_at is not None:
        dh = min(16, wall_h - 1)
        _door(img, int(door_at - door_w / 2), fy - dh, door_w, dh, st)
    if sign:
        sx, sy, sw, sh = sign
        img.rect(sx, wall_top + sy, sx + sw - 1, wall_top + sy + sh - 1, trim[0])
        img.rect(sx + 1, wall_top + sy + 1, sx + sw - 2, wall_top + sy + sh - 2, st.get('sign', trim[2]))
    if emblem:
        emblem(img, w // 2, max(3, rh // 2))
    return img.outline(out)


def door_cell(w, h, door_at, fy=None):
    """(col, row) of the cell containing the door of a house(w, h, door_at)."""
    return (int(door_at // 16), h // 16 - 1)


# ---------------------------------------------------------------------------
# emblems
# ---------------------------------------------------------------------------

def flame_emblem(hot, mid, dark, plate=None, plate_dk=None):
    """Hearth Hall flame on a round plate."""
    def draw(img, x, y):
        if plate:
            img.ellipse(x, y + 0.5, 5.5, 5.5, plate_dk)
            img.ellipse(x - 0.3, y + 0.2, 4.6, 4.6, plate)
        stamp(img, x - 3, y - 4, '''
        ...d...
        ..dm...
        ..dmd..
        .dmhmd.
        .dmhhmd
        .dmhhmd
        ..dmmd.
        ''', {'d': dark, 'm': mid, 'h': hot})
    return draw


def text_plate(ink):
    def draw(img, x, y):
        for i in range(-4, 5, 2):
            img.set(x + i, y, ink)
    return draw
