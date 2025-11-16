.data
    .align 2
newline: .asciiz "\n"


.text
    .globl main

# === COMPISCRIPT PROGRAM ===

main:
# Prologo minimo (leaf function)

li $t0, 18
slti $t1, $t0, 18
xori $t1, $t1, 1
bne $t1, $zero, IF_TRUE_0
j IF_FALSE_0
IF_TRUE_0:
li $a0, 1
li $v0, 1
syscall
li $v0, 4
la $a0, newline
syscall
j IF_END_0
IF_FALSE_0:
li $a0, 0
li $v0, 1
syscall
li $v0, 4
la $a0, newline
syscall
IF_END_0:

# Epilogo minimo
li $v0, 10  # syscall exit
    syscall

# === END OF PROGRAM ===