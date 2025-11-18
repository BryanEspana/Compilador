.data
    .align 2
newline: .asciiz "\n"
str_0: .asciiz ""
str_1: .asciiz "Resultado de la expresión: "
str_2: .asciiz "\n"


.text
    .globl main

# === COMPISCRIPT PROGRAM ===

toString:
# Built-in function: toString(x: integer) -> string
# Parameter: $a0 = integer value
# Returns: $v0 = address of string (simplified - just returns empty)
# NOTE: Full implementation would require dynamic memory allocation

# For now, print the integer directly
move $a0, $a0      # integer already in $a0
li $v0, 1          # syscall 1 = print_int
syscall

# Return empty string address for now
la $v0, newline    # placeholder
jr $ra


printString:
# Built-in function: printString(x: string) -> string
# Parameter: $a0 = address of string
# Returns: $v0 = same address

# Print the string
li $v0, 4          # syscall 4 = print_string
# $a0 already contains string address
syscall

# Return the same string address
move $v0, $a0
jr $ra


main:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

# Global initialization code
la $t0, str_0  # Load address of string
li $t1, 10
li $t2, 5
li $t4, 2
mult $t1, $t4
mflo $t3
li $t6, 5
addi $t5, $t6, -3
li $t8, 2
div $t5, $t8
mflo $t7
addu $t9, $t3, $t7
move $s0, $t9
# String concatenation - NOT FULLY IMPLEMENTED
# WARNING: String concatenation requires dynamic memory allocation
la $s1, str_1  # Load second string (concat not impl)
move $a0, $s0
jal toString
move $s2, $v0
addu $s3, $s1, $s2
# String concatenation - NOT FULLY IMPLEMENTED
# WARNING: String concatenation requires dynamic memory allocation
la $s4, str_2  # Load second string (concat not impl)
move $t0, $s4
move $a0, $t0
jal printString
move $s5, $v0

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
li $v0, 10  # syscall exit
    syscall

# === END OF PROGRAM ===
