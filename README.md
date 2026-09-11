# GBA Starter — Game Boy Advance development environment

A ready-to-build Game Boy Advance (GBA) homebrew project plus the tooling to
run it. Edit `src/main.c`, then:

```sh
make        # build game.gba
make run    # build and open it in mGBA
```

## What is installed

| Tool | Where | Purpose |
| --- | --- | --- |
| mGBA (GUI) | `/Applications/mGBA.app` | Play any GBA (and GB/GBC) ROM — drag a `.gba` file onto the app |
| mGBA (CLI) | `/opt/homebrew/bin/mgba` | `mgba game.gba` from the terminal |
| arm-none-eabi-gcc / binutils / gdb | `/opt/homebrew` (brew) | Bare-metal ARM7TDMI cross-toolchain for GBA code |
| gbafix | `~/.cargo/bin/gbafix` | Writes the cartridge header (logo, title, checksum) |

The C toolchain is the Homebrew bare-metal GCC plus this repo's `src/crt0.S`
and `gba.ld` — no devkitPro install is required. The official devkitARM could
not be installed from this network (pkg.devkitpro.org is Cloudflare-blocking
it) and its system installer needs an admin password; switching to devkitARM
later only requires exporting `DEVKITPRO`/`DEVKITARM` and pointing `CC`/`GBAFIX`
at `$DEVKITARM/bin`/`$DEVKITPRO/tools/bin`.

## Project layout

```
src/main.c        starter program: mode-3 bitmap, D-pad square, A = color
src/crt0.S        cartridge bootstrap: stacks, .data copy, .bss zero, main()
gba.ld            memory map: ROM 0x08000000, IWRAM 0x03000000, EWRAM 0x02000000
Makefile          cc -> elf -> raw ROM -> gbafix -> header check
tools/check_rom.py  validates the ROM header (entry point + checksum)
build/            objects, game.elf, game.gba (generated)
```

### ROM header check

`make` runs `tools/check_rom.py` automatically; to run it standalone:

```sh
python3 tools/check_rom.py game.gba
```

Prints the cartridge title/code and verifies the complement checksum.

## Try it

1. `make run` — the starter boots in mGBA; move the square with the D-pad,
   press A to cycle colors.
2. Play real games: `open -a mGBA path/to/rom.gba`.

## Debugging

mGBA exposes a GDB stub (Tools → Start GDB server, default port 2345):

```sh
arm-none-eabi-gdb build/game.elf
(gdb) target extended-remote :2345
```

## Maintaining the tools

```sh
brew upgrade mgba arm-none-eabi-gcc arm-none-eabi-binutils arm-none-eabi-gdb
cargo install gbafix   # update gbafix
```

## Learning resources

- [Tonc](https://www.coranac.com/tonc/text/toc.htm) — the classic GBA programming tutorial
- [GBATek](https://problemkaputt.de/gbatek.htm) — complete GBA hardware reference
- [devkitPro gba-examples](https://github.com/devkitPro/gba-examples) — C examples
- [mGBA documentation](https://mgba.io/docs.html)
