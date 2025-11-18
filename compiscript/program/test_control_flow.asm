.data
    .align 2
newline: .asciiz "\n"


.text
    .globl main

# === COMPISCRIPT PROGRAM ===

toString:
# Prologo minimo (leaf function)

move $v0, $t0

# Epilogo minimo
jr $ra


printString:
# Prologo minimo (leaf function)

move $v0, $a0

# Epilogo minimo
jr $ra


main:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

# Global initialization code
move $t1, $t0
li $t2, 1
STARTWHILE_0:
li $t4, 12
slt $t3, $t4, $t2
xori $t3, $t3, 1
bne $t3, $zero, LABEL_TRUE_0
j ENDWHILE_0
LABEL_TRUE_0:
li $t6, 2
div $t2, $t6
mfhi $t5
li $t8, 0
sub $t9, $t5, $t8
sltiu $t7, $t9, 1
bne $t7, $zero, IF_TRUE_0
j IF_FALSE_0
IF_TRUE_0:
move $a0, $t2
jal toString
move $s0, $v0
addu $s1, $t1, $s0
addu $s3, $s1, $s2
move $t1, $s3
j IF_END_0
IF_FALSE_0:
move $a0, $t2
jal toString
move $s4, $v0
addu $s5, $t1, $s4
addu $s7, $s5, $s6
move $t1, $s7
IF_END_0:
sw $t1, -4($fp)  # Spill G[0]
addi $t1, $t2, 1
move $t2, $t1
j STARTWHILE_0
ENDWHILE_0:
sw $t0, -8($fp)  # Spill ""
lw $t0, -4($fp)
move $a0, $t0
jal printString
move $t0, $v0

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
li $v0, 10  # syscall exit
    syscall

# === END OF PROGRAM ===