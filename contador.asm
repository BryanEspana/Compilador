.data
    .align 2
newline: .asciiz "\n"


.text
    .globl main

# === COMPISCRIPT PROGRAM ===

main:
# Prologo minimo (leaf function)

li $t0, 0
STARTWHILE_0:
slti $t1, $t0, 5
bne $t1, $zero, LABEL_TRUE_0
j ENDWHILE_0
LABEL_TRUE_0:
move $a0, $t0
li $v0, 1
syscall
li $v0, 4
la $a0, newline
syscall
addi $t2, $t0, 1
move $t0, $t2
j STARTWHILE_0
ENDWHILE_0:

# Epilogo minimo
li $v0, 10  # syscall exit
    syscall

# === END OF PROGRAM ===