# ---------------------------------------------------------------
# GBA build for WILDKIN -- The Brimming Storm.
#
#   make        build game.gba
#   make run    build and open in mGBA
#   make test   host-side unit tests (rules, battles, maps, menus)
#   make art    regenerate the art headers from tools/gen_*.py
#               (and src/music_data.h from tools/music/*.py)
#   make songs  render every song to build/music/*.wav (host synth)
#   make audio  build the headless audio recorder (needs libmgba)
#   make maps   render every map to build/maps/*.png
#   make shot   build the headless screenshot harness (needs libmgba)
#   make clean  remove build artifacts
#
# Uses the bare-metal ARM toolchain from Homebrew (arm-none-eabi-gcc)
# plus the crt0/link script in this repo. gbafix (from `cargo install
# gbafix`) repairs the cartridge header after linking.
# ---------------------------------------------------------------

.DEFAULT_GOAL := all

TARGET   := game
ROMTITLE := WILDKIN

BUILD    := build
SOURCES  := src/main.c src/mem.c
CRT0_SRC := src/crt0.S

CC       := arm-none-eabi-gcc
OBJCOPY  := arm-none-eabi-objcopy
GBAFIX   := $(shell command -v gbafix)
HOSTCC   ?= cc
MGBA_PREFIX ?= /opt/homebrew

# The GBA's ARM7TDMI: ARMv4T. Thumb + interwork calls is the usual setup.
ARCH     := -mcpu=arm7tdmi -mthumb -mthumb-interwork
CFLAGS   := -g -O2 -Wall -Wextra -Wno-missing-field-initializers $(ARCH) -fomit-frame-pointer -ffreestanding -DGBA
ASFLAGS  := -g -mcpu=arm7tdmi -marm
# (IWRAM holds ARM code copied from ROM -- the music mixer -- so its segment is RWX by design)
LDFLAGS  := $(ARCH) -nostartfiles -T gba.ld -Wl,-Map,$(BUILD)/$(TARGET).map -Wl,--no-warn-rwx-segments

OBJS     := $(SOURCES:%.c=$(BUILD)/%.o)
OBJS     += $(BUILD)/src/crt0.o

# Generated art headers and the scripts that write them.
ART      := src/gfx_ui.h src/gfx_monsters.h src/gfx_field.h src/gfx_battle.h src/species_data.h \
            src/gfx_travel.h src/gfx_craft.h src/gfx_fusion.h src/gfx_rune.h src/gfx_keepers.h

.PHONY: save-layout
save-layout:
	python3 tools/gen_save_layout.py

$(BUILD)/src/main.o: save-layout

all: $(TARGET).gba

run: $(TARGET).gba
	mgba $(TARGET).gba

# Host-side unit tests: tools/test_field.c and tools/test_game.c include
# src/main.c (hardware registers become plain memory on the host), so the
# rules, battles, maps and every menu screen are exercised frame by frame.
# test_game.c also runs a tiered round-robin balance simulation.
test: save-layout
	@mkdir -p $(BUILD)
	$(HOSTCC) -std=c11 -Wall -Wextra -Wno-missing-field-initializers -Wno-unused-function -o $(BUILD)/test_field tools/test_field.c
	$(BUILD)/test_field
	$(HOSTCC) -std=c11 -Wall -Wextra -Wno-missing-field-initializers -Wno-unused-function -o $(BUILD)/test_game tools/test_game.c
	$(BUILD)/test_game
	@for t in tools/tests/test_*.c; do \
		n=$$(basename $$t .c); \
		$(HOSTCC) -std=c11 -Wall -Wextra -Wno-missing-field-initializers -Wno-unused-function -o $(BUILD)/$$n $$t || exit 1; \
		$(BUILD)/$$n || exit 1; \
	done

art:
	python3 tools/gen_ui_gfx.py
	python3 tools/gen_species.py
	python3 tools/gen_monsters.py
	python3 tools/gen_field_gfx.py
	python3 tools/gen_battle_gfx.py
	python3 tools/gen_travel_gfx.py
	python3 tools/gen_craft_gfx.py
	python3 tools/gen_fusion_gfx.py
	python3 tools/gen_rune_gfx.py
	python3 tools/gen_keeper_gfx.py
	python3 tools/gen_music.py

maps:
	python3 tools/render_maps.py build/maps

# build/shot game.gba script.txt [save.sav] -- scripted inputs + PNG shots
shot:
	@mkdir -p $(BUILD)
	$(HOSTCC) -O2 -I$(MGBA_PREFIX)/include -o $(BUILD)/shot tools/shot.c -L$(MGBA_PREFIX)/lib -lmgba -lz

# build/render_music [-s SECONDS] [SONG...] -- the game's synth on the host
songs:
	@mkdir -p $(BUILD)/music
	$(HOSTCC) -std=c11 -O2 -Wall -Wextra -Wno-missing-field-initializers -Wno-unused-function -o $(BUILD)/render_music tools/render_music.c -lm
	$(BUILD)/render_music -o $(BUILD)/music

# build/record_audio game.gba script.txt [save.sav] -- the ROM's audio to WAV
audio:
	@mkdir -p $(BUILD)
	$(HOSTCC) -O2 -I$(MGBA_PREFIX)/include -o $(BUILD)/record_audio tools/record_audio.c -L$(MGBA_PREFIX)/lib -lmgba -lz

clean:
	rm -fr $(BUILD) $(TARGET).elf $(TARGET).gba

# elf -> raw binary ROM, then fix the cartridge header (logo + checksum).
$(TARGET).gba: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@
	-$(GBAFIX) $@ -t"$(ROMTITLE)" -cDGST -m01
	python3 tools/check_rom.py $@

$(TARGET).elf: $(OBJS) gba.ld
	$(CC) $(LDFLAGS) $(OBJS) -o $@ -nostdlib -lgcc

$(BUILD)/src/main.o: $(ART) src/music_data.h $(wildcard src/*.h) $(wildcard src/game/*.c) $(wildcard src/game/*.h) \
                    $(wildcard src/game/world/*.h src/game/world/*.inc src/game/world/*.c src/game/world/*/* src/game/world/*/biomes/*)

$(BUILD)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.o: %.S
	@mkdir -p $(dir $@)
	$(CC) $(ASFLAGS) -c $< -o $@

.PHONY: all run test art maps shot songs audio clean
