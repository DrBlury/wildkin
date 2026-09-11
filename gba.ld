/*
 * GBA cartridge link script.
 *
 * Code and constants live in ROM at 0x08000000. Writable data lands in
 * the 32 KiB IWRAM; the load address (LMA) stays in ROM and crt0 copies
 * it over at boot. .bss is zeroed by crt0.
 */

OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(_start)

MEMORY
{
    rom   (rx)  : ORIGIN = 0x08000000, LENGTH = 32M
    iwram (rwx) : ORIGIN = 0x03000000, LENGTH = 32K
    ewram (rwx) : ORIGIN = 0x02000000, LENGTH = 256K
}

SECTIONS
{
    .text : {
        KEEP(*(.crt0))
        *(.text*)
        *(.glue_7)
        *(.glue_7t)
    } > rom

    .rodata : {
        *(.rodata*)
        . = ALIGN(4);
    } > rom

    __data_lma = ALIGN(4);

    .data : AT (__data_lma) {
        __data_start = .;
        *(.data*)
        . = ALIGN(4);
        __data_end = .;
    } > iwram

    .bss (NOLOAD) : {
        __bss_start = .;
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        __bss_end = .;
    } > iwram

    /DISCARD/ : {
        *(.ARM.exidx*)
        *(.ARM.attributes)
        *(.comment)
        *(.note*)
    }
}
