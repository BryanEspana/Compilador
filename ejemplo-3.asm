.data
    .align 2
newline: .asciiz "\n"


.text
    .globl main

# === COMPISCRIPT PROGRAM ===
main:
addi $sp, $sp, -8
sw $fp, 4($sp)
sw $ra, 0($sp)
move $fp, $sp
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
lw $ra, 0($sp)
lw $fp, 4($sp)
addi $sp, $sp, 8
jr $ra
# === END OF PROGRAM ===