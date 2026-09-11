#!/usr/bin/env python3
"""Sanity-check a .gba ROM header.

Verifies the complement checksum (bytes 0xA0-0xBD) and that the entry
point starts with an ARM branch instruction. Exits non-zero on failure.
"""

import sys

HEADER_COMPLEMENT_OFFSET = 0xBD
HEADER_SUM_START = 0xA0
HEADER_SUM_END = 0xBD  # exclusive of the checksum byte itself


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <rom.gba>", file=sys.stderr)
        return 2

    with open(sys.argv[1], "rb") as f:
        rom = f.read()

    if len(rom) < 0xC0:
        print("FAIL: ROM smaller than the 192-byte cartridge header")
        return 1

    entry = int.from_bytes(rom[0:4], "little")
    if (entry & 0xFF000000) != 0xEA000000:
        print(f"FAIL: entry point word {entry:#010x} is not an ARM branch")
        return 1

    total = sum(rom[HEADER_SUM_START:HEADER_SUM_END]) + 0x19
    expected = (-total) & 0xFF
    stored = rom[HEADER_COMPLEMENT_OFFSET]
    if stored != expected:
        print(f"FAIL: header checksum {stored:#04x} != expected {expected:#04x} "
              "(run gbafix to repair)")
        return 1

    title = rom[0xA0:0xAC].decode("ascii", "replace").strip("\0 ")
    code = rom[0xAC:0xB0].decode("ascii", "replace")
    print(f"OK: {sys.argv[1]} ({len(rom)} bytes), title={title!r}, code={code!r}, "
          "header checksum valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
