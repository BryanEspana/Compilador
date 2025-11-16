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
li $t0, 5
li $t1, 3
add $t2, $t0, $t1
move $t3, $t2
move $a0, $t3
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