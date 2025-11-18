.data
    .align 2
newline: .asciiz "\n"
str_0: .asciiz "rojo"
str_1: .asciiz "Hola, mi nombre es "
str_2: .asciiz "Ahora tengo "
str_3: .asciiz " años."
str_4: .asciiz ""
str_5: .asciiz "\n"


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

# CLASS Persona

constructor_Persona:
# Prologo minimo (leaf function)

move $t0, $a1
move $t1, $a2
la $t2, str_0  # Load address of string
li $v0, 0

# Epilogo minimo
jr $ra


saludar_Persona:
# Prologo minimo (leaf function)

# String concatenation - NOT FULLY IMPLEMENTED
# WARNING: String concatenation requires dynamic memory allocation
la $t3, str_1  # Load first string (concat not impl)
move $v0, $t3

# Epilogo minimo
jr $ra


incrementarEdad_Persona:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

addu $t3, $a0, $a1
move $t1, $t3
move $a0, $a0
jal toString
move $t4, $v0
# String concatenation - NOT FULLY IMPLEMENTED
# WARNING: String concatenation requires dynamic memory allocation
la $t5, str_2  # Load first string (concat not impl)
# String concatenation - NOT FULLY IMPLEMENTED
# WARNING: String concatenation requires dynamic memory allocation
la $t6, str_3  # Load second string (concat not impl)
move $v0, $t6

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
jr $ra

# END CLASS Persona

main:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

# Global initialization code
la $t7, str_4  # Load address of string
move $a0, $t8
li $a1, 25
addi $sp, $sp, -4
sw $t8, 0($sp)
jal newPersona
lw $t8, 0($sp)
addi $sp, $sp, 4
move $t9, $v0
move $s0, $t9
move $a0, $s0
addi $sp, $sp, -4
sw $t8, 0($sp)
jal saludar
lw $t8, 0($sp)
addi $sp, $sp, 4
move $s1, $v0
addu $s2, $t7, $s1
# String concatenation - NOT FULLY IMPLEMENTED
# WARNING: String concatenation requires dynamic memory allocation
la $s3, str_5  # Load second string (concat not impl)
move $t7, $s3
move $a0, $s0
li $a1, 5
addi $sp, $sp, -4
sw $t8, 0($sp)
jal incrementarEdad
lw $t8, 0($sp)
addi $sp, $sp, 4
move $s4, $v0
addu $s5, $t7, $s4
# String concatenation - NOT FULLY IMPLEMENTED
# WARNING: String concatenation requires dynamic memory allocation
la $s6, str_5  # Load second string (concat not impl)
move $t7, $s6
move $a0, $t7
addi $sp, $sp, -4
sw $t8, 0($sp)
jal printString
lw $t8, 0($sp)
addi $sp, $sp, 4
move $s7, $v0

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
li $v0, 10  # syscall exit
    syscall

# === END OF PROGRAM ===
