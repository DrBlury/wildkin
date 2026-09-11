@ GBA cartridge bootstrap.
@
@ The first word at 0x08000000 is the entry branch; the next 47 words
@ (0x04-0xBF) form the cartridge header, which gbafix fills in with the
@ Nintendo logo, title, codes and the complement checksum.
@ Code executes in ARM state here; main() may be thumb (-mthumb-interwork).

    .section .crt0, "ax"
    .global _start
    .arm
    .cpu arm7tdmi

_start:
    b   rom_start
    .rept 47
    .word 0
    .endr

rom_start:
    @ IRQ stack
    mov r0, #0x12                 @ IRQ mode
    msr cpsr_c, r0
    ldr sp, =0x03007FA0
    @ System stack (main runs in system mode)
    mov r0, #0x1F                 @ system mode
    msr cpsr_c, r0
    ldr sp, =0x03007F00

    @ Copy .data from ROM to IWRAM
    ldr r0, =__data_lma
    ldr r1, =__data_start
    ldr r2, =__data_end
1:  cmp r1, r2
    ldrlo r3, [r0], #4
    strlo r3, [r1], #4
    blo 1b

    @ Zero .bss
    ldr r1, =__bss_start
    ldr r2, =__bss_end
    mov r3, #0
2:  cmp r1, r2
    strlo r3, [r1], #4
    blo 2b

    ldr r3, =main
    bx  r3
3:  b 3b                          @ never return
