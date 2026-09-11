# ---------------------------------------------------------------
# GBA starter build.
#
#   make        build game.gba
#   make run    build and open in mGBA
#   make clean  remove build artifacts
#
# Uses the bare-metal ARM toolchain from Homebrew (arm-none-eabi-gcc)
# plus the crt0/link script in this repo. gbafix (from `cargo install
# gbafix`) repairs the cartridge header after linking.
# ---------------------------------------------------------------

TARGET   := game
ROMTITLE := STARTER

BUILD    := build
SOURCES  := $(wildcard src/*.c)
CRT0_SRC := src/crt0.S

CC       := arm-none-eabi-gcc
OBJCOPY  := arm-none-eabi-objcopy
GBAFIX   := $(shell command -v gbafix)

# The GBA's ARM7TDMI: ARMv4T. Thumb + interwork calls is the usual setup.
ARCH     := -mcpu=arm7tdmi -mthumb -mthumb-interwork
CFLAGS   := -g -O2 -Wall -Wextra $(ARCH) -fomit-frame-pointer
ASFLAGS  := -g -mcpu=arm7tdmi -marm
LDFLAGS  := $(ARCH) -nostartfiles -T gba.ld -Wl,-Map,$(BUILD)/$(TARGET).map

OBJS     := $(SOURCES:%.c=$(BUILD)/%.o)
OBJS     += $(BUILD)/src/crt0.o

all: $(TARGET).gba

run: $(TARGET).gba
	mgba $(TARGET).gba

clean:
	rm -fr $(BUILD) $(TARGET).elf $(TARGET).gba

# elf -> raw binary ROM, then fix the cartridge header (logo + checksum).
$(TARGET).gba: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@
	-$(GBAFIX) $@ -t"$(ROMTITLE)" -cDGST -m01
	python3 tools/check_rom.py $@

$(TARGET).elf: $(OBJS) gba.ld
	$(CC) $(LDFLAGS) $(OBJS) -o $@ -nostdlib -lgcc

$(BUILD)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.o: %.S
	@mkdir -p $(dir $@)
	$(CC) $(ASFLAGS) -c $< -o $@

.PHONY: all run clean
