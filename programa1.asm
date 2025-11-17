.data
    .align 2
newline: .asciiz "\n"


.text
    .globl main

# === COMPISCRIPT PROGRAM ===

toString:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

move $v0, $t0

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
jr $ra


printInteger:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

move $v0, $t1

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
jr $ra


printString:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

move $v0, $t1

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
jr $ra


fibonacci:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

lw $t3, 1
slt $t2, $t3, $t1
xori $t2, $t2, 1
bne $t2, $zero, IF_TRUE_0
j IF_FALSE_0
IF_TRUE_0:
move $v0, $t1
IF_FALSE_0:
li $t4, 0
li $t5, 0
add $t6, $t4, $t5
move $t7, $t6
move $v0, $t6

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
jr $ra

# CLASS Persona

constructor_Persona:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

move $t9, $t8
move $s1, $s0
move $s3, $s2
li $v0, 0

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
jr $ra


saludar_Persona:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

add $t2, $s4, $t9
move $v0, $t2

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
jr $ra


incrementarEdad_Persona:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

add $t2, $s1, $t8
move $s1, $t2
move $a0, $s1
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal toString
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
move $t6, $v0
add $s6, $s5, $t6
sw $t0, -4($fp)
add $t0, $s6, $s7
move $v0, $t0

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
jr $ra

# END CLASS Persona
# CLASS Estudiante

constructor_Estudiante:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

move $t9, $t8
move $s1, $s0
move $s3, $s2
sw $t0, -4($fp)
move $t0, $t0
li $v0, 0

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
jr $ra


estudiar_Estudiante:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

add $t2, $t9, $t0
move $a0, $t0
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal toString
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
move $t6, $v0
add $s6, $t2, $t6
sw $t0, -4($fp)
lw $t0, -4($fp)
add $t0, $s6, $t0
move $v0, $t0

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
jr $ra


promedioNotas_Estudiante:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

add $t2, $t8, $s0
sw $t0, -4($fp)
lw $t0, -4($fp)
add $t6, $t2, $t0
add $s6, $t6, $t0
sw $t0, -8($fp)
lw $t0, -4($fp)
add $t0, $s6, $t0
sw $t0, -12($fp)
add $t0, $t0, $t0
sw $t0, -16($fp)
lw $t0, 6
div $t0, $t0
mflo $t0
move $t4, $t0
move $v0, $t0

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
jr $ra

# END CLASS Estudiante
sw $t0, -20($fp)
lw $t0, -4($fp)
move $t0, $t0
sw $t0, -24($fp)
move $t0, $t0
move $a0, $t0
li $a1, 15
li $a2, 4
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal newEstudiante
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
sw $t0, -28($fp)
move $t0, $v0
move $t0, $t0
sw $t0, -32($fp)
move $t0, $t0
move $a0, $t0
li $a1, 15
li $a2, 4
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal newEstudiante
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
sw $t0, -36($fp)
move $t0, $v0
move $t0, $t0
sw $t0, -40($fp)
move $t0, $t0
move $a0, $t0
li $a1, 15
li $a2, 4
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal newEstudiante
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
sw $t0, -44($fp)
move $t0, $v0
move $t0, $t0
move $a0, $t0
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal saludar
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
sw $t0, -48($fp)
move $t0, $v0
lw $t0, -44($fp)
sw $t0, -52($fp)
add $t0, $t0, $t0
sw $t0, -56($fp)
add $t0, $t0, $t0
lw $t0, -44($fp)
move $t0, $t0
move $a0, $t0
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal estudiar
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
sw $t0, -60($fp)
move $t0, $v0
lw $t0, -60($fp)
sw $t0, -64($fp)
add $t0, $t0, $t0
add $t0, $t0, $t0
sw $t0, -68($fp)
lw $t0, -60($fp)
move $t0, $t0
lw $t0, -64($fp)
move $a0, $t0
li $a1, 6
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal incrementarEdad
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
sw $t0, -72($fp)
move $t0, $v0
lw $t0, -72($fp)
sw $t0, -76($fp)
add $t0, $t0, $t0
add $t0, $t0, $t0
sw $t0, -80($fp)
lw $t0, -72($fp)
move $t0, $t0
move $a0, $t0
addi $sp, $sp, -36
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal saludar
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 36
move $t0, $v0
sw $t0, -84($fp)
add $t0, $t0, $t0
add $t0, $t0, $t0
sw $t0, -88($fp)
lw $t0, -84($fp)
move $t0, $t0
lw $t0, -88($fp)
move $a0, $t0
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal estudiar
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
sw $t0, -92($fp)
move $t0, $v0
lw $t0, -92($fp)
sw $t0, -96($fp)
add $t0, $t0, $t0
add $t0, $t0, $t0
sw $t0, -100($fp)
lw $t0, -92($fp)
move $t0, $t0
lw $t0, -88($fp)
move $a0, $t0
li $a1, 7
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal incrementarEdad
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
sw $t0, -104($fp)
move $t0, $v0
lw $t0, -104($fp)
sw $t0, -108($fp)
add $t0, $t0, $t0
add $t0, $t0, $t0
sw $t0, -112($fp)
lw $t0, -104($fp)
move $t0, $t0
lw $t0, -112($fp)
move $a0, $t0
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal saludar
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
sw $t0, -116($fp)
move $t0, $v0
lw $t0, -116($fp)
sw $t0, -120($fp)
add $t0, $t0, $t0
add $t0, $t0, $t0
sw $t0, -124($fp)
lw $t0, -116($fp)
move $t0, $t0
lw $t0, -112($fp)
move $a0, $t0
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal estudiar
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
sw $t0, -128($fp)
move $t0, $v0
lw $t0, -128($fp)
sw $t0, -132($fp)
add $t0, $t0, $t0
lw $t0, -132($fp)
sw $t0, -136($fp)
add $t0, $t0, $t0
lw $t0, -128($fp)
move $t0, $t0
sw $t0, -140($fp)
lw $t0, -112($fp)
move $a0, $t0
li $a1, 6
addi $sp, $sp, -36
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal incrementarEdad
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 36
move $t0, $v0
sw $t0, -144($fp)
lw $t0, -140($fp)
add $t0, $t0, $t0
sw $t0, -148($fp)
lw $t0, -132($fp)
add $t0, $t0, $t0
sw $t0, -152($fp)
lw $t0, -140($fp)
move $t0, $t0
li $t0, 1
STARTWHILE_0:
sw $t0, -156($fp)
lw $t0, 12
slt $t0, $t0, $t0
xori $t0, $t0, 1
bne $t0, $zero, LABEL_TRUE_0
j ENDWHILE_0
LABEL_TRUE_0:
sw $t0, -160($fp)
lw $t0, 2
div $t0, $t0
mfhi $t0
sw $t0, -164($fp)
lw $t0, 0
sw $t0, -168($fp)
sub $t0, $t0, $t0
sltiu $t0, $t0, 1
bne $t0, $zero, IF_TRUE_1
j IF_FALSE_1
IF_TRUE_1:
move $a0, $t0
addi $sp, $sp, -36
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal toString
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 36
move $t0, $v0
sw $t0, -172($fp)
lw $t0, -156($fp)
add $t0, $t0, $t0
sw $t0, -176($fp)
add $t0, $t0, $t0
sw $t0, -180($fp)
lw $t0, -156($fp)
move $t0, $t0
j IF_END_1
IF_FALSE_1:
move $a0, $t0
addi $sp, $sp, -36
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal toString
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 36
move $t0, $v0
sw $t0, -184($fp)
add $t0, $t0, $t0
sw $t0, -188($fp)
add $t0, $t0, $t0
lw $t0, -184($fp)
move $t0, $t0
IF_END_1:
sw $t0, -192($fp)
addi $t0, $t0, 1
move $t0, $t0
j STARTWHILE_0
ENDWHILE_0:
sw $t0, -196($fp)
lw $t0, 2
mult $t0, $t0
mflo $t0
sw $t0, -200($fp)
addi $t0, 5, -3
sw $t0, -204($fp)
lw $t0, 2
div $t0, $t0
mflo $t0
add $t0, $t0, $t0
sw $t0, -208($fp)
move $t0, $t0
lw $t0, -192($fp)
sw $t0, -212($fp)
add $t0, $t0, $t0
move $a0, $t0
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal toString
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
sw $t0, -216($fp)
move $t0, $v0
add $t0, $t0, $t0
sw $t0, -220($fp)
lw $t0, -132($fp)
add $t0, $t0, $t0
sw $t0, -224($fp)
lw $t0, -192($fp)
move $t0, $t0
li $t0, 0
sw $t0, -228($fp)
lw $t0, -64($fp)
move $a0, $t0
li $a1, 99
li $a2, 95
li $a3, 98
addi $sp, $sp, -48
sw $t1, 44($sp)
sw $t2, 40($sp)
sw $t3, 36($sp)
sw $t4, 32($sp)
sw $t5, 28($sp)
sw $t6, 24($sp)
sw $t7, 20($sp)
sw $t8, 16($sp)
sw $t9, 12($sp)
li $t9, 100
sw $t9, 0($sp)
li $t9, 95
sw $t9, 4($sp)
li $t9, 94
sw $t9, 8($sp)
jal promedioNotas
lw $t1, 44($sp)
lw $t2, 40($sp)
lw $t3, 36($sp)
lw $t4, 32($sp)
lw $t5, 28($sp)
lw $t6, 24($sp)
lw $t7, 20($sp)
lw $t8, 16($sp)
lw $t9, 12($sp)
addi $sp, $sp, 48
move $t0, $v0
move $t0, $t0
sw $t0, -232($fp)
lw $t0, -228($fp)
sw $t0, -236($fp)
add $t0, $t0, $t0
move $a0, $t0
addi $sp, $sp, -36
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal toString
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 36
move $t0, $v0
sw $t0, -240($fp)
add $t0, $t0, $t0
lw $t0, -132($fp)
sw $t0, -244($fp)
add $t0, $t0, $t0
lw $t0, -228($fp)
move $t0, $t0
sw $t0, -248($fp)
add $t0, $t0, $t0
sw $t0, -252($fp)
lw $t0, -248($fp)
move $t0, $t0
li $t0, 20
sw $t0, -256($fp)
li $t0, 0
STARTWHILE_1:
slt $t0, $t0, $t0
xori $t0, $t0, 1
bne $t0, $zero, LABEL_TRUE_1
j ENDWHILE_1
LABEL_TRUE_1:
move $a0, $t0
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal fibonacci
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
sw $t0, -260($fp)
move $t0, $v0
move $t0, $t0
sw $t0, -264($fp)
lw $t0, -256($fp)
sw $t0, -268($fp)
add $t0, $t0, $t0
move $a0, $t0
addi $sp, $sp, -36
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal toString
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 36
move $t0, $v0
sw $t0, -272($fp)
add $t0, $t0, $t0
sw $t0, -276($fp)
add $t0, $t0, $t0
move $a0, $t0
addi $sp, $sp, -36
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal toString
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 36
move $t0, $v0
sw $t0, -280($fp)
add $t0, $t0, $t0
lw $t0, -132($fp)
sw $t0, -284($fp)
add $t0, $t0, $t0
lw $t0, -256($fp)
move $t0, $t0
sw $t0, -288($fp)
addi $t0, $t0, 1
move $t0, $t0
j STARTWHILE_1
ENDWHILE_1:
lw $t0, -288($fp)
move $a0, $t0
addi $sp, $sp, -40
sw $t0, 36($sp)
sw $t1, 32($sp)
sw $t2, 28($sp)
sw $t3, 24($sp)
sw $t4, 20($sp)
sw $t5, 16($sp)
sw $t6, 12($sp)
sw $t7, 8($sp)
sw $t8, 4($sp)
sw $t9, 0($sp)
jal printString
lw $t0, 36($sp)
lw $t1, 32($sp)
lw $t2, 28($sp)
lw $t3, 24($sp)
lw $t4, 20($sp)
lw $t5, 16($sp)
lw $t6, 12($sp)
lw $t7, 8($sp)
lw $t8, 4($sp)
lw $t9, 0($sp)
addi $sp, $sp, 40
sw $t0, -292($fp)
move $t0, $v0
# === END OF PROGRAM ===

main:
    li $v0, 10  # syscall exit
    syscall