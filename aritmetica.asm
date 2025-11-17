.data
    .align 2
newline: .asciiz "\n"


.text
    .globl main

# === COMPISCRIPT PROGRAM ===

main:
# Prologo minimo (leaf function)

li $t0, 10
li $t1, 4
mult $t0, $t1
mflo $t2
move $t3, $t2
div $t0, $t1
mflo $t4
move $t5, $t4
move $a0, $t3
li $v0, 1
syscall
li $v0, 4
la $a0, newline
syscall
move $a0, $t5
li $v0, 1
syscall
li $v0, 4
la $a0, newline
syscall

# Epilogo minimo
li $v0, 10  # syscall exit
    syscall

# === END OF PROGRAM ===