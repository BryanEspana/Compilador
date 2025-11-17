.data
    .align 2
newline: .asciiz "\n"


.text
    .globl main

# === COMPISCRIPT PROGRAM ===

main:
# Prologo minimo (leaf function)

li $t0, 8
li $t1, 3
addu $t2, $t0, $t1
move $t3, $t2
move $a0, $t3
li $v0, 1
syscall
li $v0, 4
la $a0, newline
syscall

# Epilogo minimo
li $v0, 10  # syscall exit
    syscall

# === END OF PROGRAM ===