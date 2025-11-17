.data
    .align 2
newline: .asciiz "\n"


.text
    .globl main

# === COMPISCRIPT PROGRAM ===

sumar:
# Prologo minimo (leaf function)

addu $t0, $a0, $a1
move $v0, $t0

# Epilogo minimo
jr $ra


main:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

li $a0, 5
li $a1, 3
jal sumar
move $t0, $v0
move $t1, $t0
move $a0, $t1
li $v0, 1
syscall
li $v0, 4
la $a0, newline
syscall

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
li $v0, 10  # syscall exit
    syscall

# === END OF PROGRAM ===