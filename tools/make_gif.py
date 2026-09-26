#!/usr/bin/env python3
"""Turn recorded frames (PNG, from `build/shot`'s `rec` command) into an
animated GIF. Standard library only.

    python3 tools/make_gif.py OUT.gif FRAME_0000.png FRAME_0001.png ... \
        [--delay 4] [--scale 2] [--skip-same]

--delay is in hundredths of a second per frame, --scale enlarges pixels
(nearest neighbour), --skip-same drops frames identical to the previous
one (their time is added to the kept frame). GBA frames have few colours;
if a frame has more than 256, the least used are merged into the nearest.
"""

import struct
import sys
import zlib


def read_png(path):
    data = open(path, 'rb').read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', path
    pos, idat, w = 8, b'', 0
    while pos < len(data):
        n = struct.unpack('>I', data[pos:pos + 4])[0]
        t = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + n]
        if t == b'IHDR':
            w, h, depth, ctype = struct.unpack('>IIBB', body[:10])
            assert depth == 8 and ctype in (2, 6), 'only 8-bit RGB/RGBA PNGs'
            bpp = 3 if ctype == 2 else 4
        elif t == b'IDAT':
            idat += body
        pos += 12 + n
    raw = zlib.decompress(idat)
    stride = w * bpp
    rows, prev = [], bytearray(stride)
    i = 0
    for _ in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append([tuple(line[x * bpp:x * bpp + 3]) for x in range(w)])
        prev = line
    return w, h, rows


def scale_rows(rows, s):
    if s == 1:
        return rows
    out = []
    for r in rows:
        wide = [p for p in r for _ in range(s)]
        out.extend([wide] * s)
    return out


def palette_for(rows):
    counts = {}
    for r in rows:
        for p in r:
            counts[p] = counts.get(p, 0) + 1
    cols = sorted(counts, key=lambda c: -counts[c])
    keep = cols[:256]
    index = {c: i for i, c in enumerate(keep)}
    for c in cols[256:]:
        best = min(range(len(keep)), key=lambda i: sum((a - b) ** 2 for a, b in zip(c, keep[i])))
        index[c] = best
    return keep, index


def lzw(indices, min_size):
    clear, end = 1 << min_size, (1 << min_size) + 1
    out, bits, nbits = bytearray(), 0, 0
    size = min_size + 1

    def emit(code):
        nonlocal bits, nbits
        bits |= code << nbits
        nbits += size
        while nbits >= 8:
            out.append(bits & 255)
            bits >>= 8
            nbits -= 8
    table = {(i,): i for i in range(clear)}
    nxt = end + 1
    emit(clear)
    w = ()
    for k in indices:
        wk = w + (k,)
        if wk in table:
            w = wk
            continue
        emit(table[w])
        if nxt < 4096:
            table[wk] = nxt
            nxt += 1
            if nxt > (1 << size) and size < 12:
                size += 1
        else:
            emit(clear)
            table = {(i,): i for i in range(clear)}
            nxt = end + 1
            size = min_size + 1
        w = (k,)
    if w:
        emit(table[w])
    emit(end)
    if nbits:
        out.append(bits & 255)
    return bytes(out)


def sub_blocks(data):
    out = bytearray()
    for i in range(0, len(data), 255):
        chunk = data[i:i + 255]
        out.append(len(chunk))
        out += chunk
    out.append(0)
    return bytes(out)


def write_gif(path, frames, delays):
    h, w = len(frames[0]), len(frames[0][0])
    out = bytearray(b'GIF89a')
    out += struct.pack('<HHBBB', w, h, 0, 0, 0)
    out += b'\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00'   # loop forever
    for rows, delay in zip(frames, delays):
        pal, index = palette_for(rows)
        bits = max(1, (len(pal) - 1).bit_length())
        size = 1 << bits
        out += struct.pack('<BBBBHBB', 0x21, 0xf9, 4, 0, delay, 0, 0)
        out += struct.pack('<BHHHHB', 0x2c, 0, 0, w, h, 0x80 | (bits - 1))
        for i in range(size):
            out += bytes(pal[i]) if i < len(pal) else b'\x00\x00\x00'
        min_size = max(2, bits)
        out.append(min_size)
        out += sub_blocks(lzw([index[p] for r in rows for p in r], min_size))
    out.append(0x3b)
    open(path, 'wb').write(out)


def main(argv):
    delay, scale, skip = 4, 1, False
    args = []
    i = 0
    while i < len(argv):
        if argv[i] == '--delay':
            delay = int(argv[i + 1])
            i += 2
        elif argv[i] == '--scale':
            scale = int(argv[i + 1])
            i += 2
        elif argv[i] == '--skip-same':
            skip = True
            i += 1
        else:
            args.append(argv[i])
            i += 1
    out, paths = args[0], args[1:]
    frames, delays = [], []
    for p in paths:
        w, h, rows = read_png(p)
        if skip and frames and rows == frames[-1][0]:
            delays[-1] += delay
            continue
        frames.append((rows, None))
        delays.append(delay)
    write_gif(out, [scale_rows(r, scale) for (r, _) in frames], delays)
    print('wrote %s (%d frames)' % (out, len(frames)))


if __name__ == '__main__':
    main(sys.argv[1:])
