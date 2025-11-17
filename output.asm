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


printInteger:
# Prologo minimo (leaf function)

move $v0, $a0

# Epilogo minimo
jr $ra


printString:
# Prologo minimo (leaf function)

move $v0, $a0

# Epilogo minimo
jr $ra


fibonacci:
# Prologo minimo (leaf function)

li $t2, 1
slt $t1, $t2, $a0
xori $t1, $t1, 1
bne $t1, $zero, IF_TRUE_0
j IF_FALSE_0
IF_TRUE_0:
move $v0, $a0
IF_FALSE_0:
li $t3, 0
li $t4, 0
addu $t5, $t3, $t4
move $t6, $t5
move $v0, $t5

# Epilogo minimo
jr $ra


constructor:
# Prologo minimo (leaf function)

move $t7, $a1
move $t8, $a2
move $s0, $t9
li $v0, 0

# Epilogo minimo
jr $ra


saludar:
# Prologo minimo (leaf function)

addu $t1, $s1, $a0
move $v0, $t1

# Epilogo minimo
jr $ra


incrementarEdad:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

addu $t1, $a0, $a1
move $t8, $t1
move $a0, $a0
jal toString
move $t5, $v0
addu $s3, $s2, $t5
addu $s5, $s3, $s4
move $v0, $s5

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
jr $ra


constructor:
# Prologo minimo (leaf function)

move $t7, $a1
move $t8, $a2
move $s0, $t9
move $s6, $a3
li $v0, 0

# Epilogo minimo
jr $ra


estudiar:
# Prologo
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp

addu $t1, $a0, $s7
move $a0, $a0
jal toString
move $t5, $v0
addu $s3, $t1, $t5
sw $t1, -4($fp)  # Spill t0
addu $s5, $s3, $t1
move $v0, $s5

# Epilogo
lw $ra, 4($sp)
lw $fp, 0($sp)
addi $sp, $sp, 8
jr $ra


promedioNotas:
# Prologo minimo (leaf function)

sw $t3, -4($fp)  # Spill fp[0]
addu $t3, $a1, $a2
addu $t5, $t3, $a3
sw $t0, -8($fp)  # Spill ""
lw $t0, 12($fp)  # Load param 5
addu $s3, $t5, $t0
lw $t0, 16($fp)  # Load param 6
addu $s5, $s3, $t0
lw $t0, 20($fp)  # Load param 7
addu $t0, $s5, $t0
sw $t0, -12($fp)  # Spill t4
sw $t0, -16($fp)  # Spill t5
lw $t0, 6
div $t0, $t0
mflo $t0
lw $t0, -16($fp)
sw $t3, -20($fp)  # Spill t0
move $t3, $t0
lw $t0, -16($fp)
move $v0, $t0

# Epilogo minimo
jr $ra

lw $t0, -8($fp)
sw $t3, -4($fp)  # Spill fp[0]
move $t3, $t0
sw $t3, -24($fp)  # Spill G[24]
sw $t4, -28($fp)  # Spill fp[4]
move $t4, $t3
move $a0, $t4
li $a1, 15
li $a2, 4
jal newEstudiante
sw $t4, -32($fp)  # Spill G[32]
move $t4, $v0
sw $t4, -36($fp)  # Spill t6
sw $t4, -40($fp)  # Spill G[40]
sw $t5, -44($fp)  # Spill t1
move $t5, $t4
move $a0, $t5
li $a1, 15
li $a2, 4
jal newEstudiante
sw $t5, -48($fp)  # Spill G[44]
move $t5, $v0
sw $t5, -52($fp)  # Spill t7
sw $t5, -56($fp)  # Spill G[52]
sw $t6, -60($fp)  # Spill fp[8]
move $t6, $t5
move $a0, $t6
li $a1, 15
li $a2, 4
jal newEstudiante
sw $t6, -64($fp)  # Spill G[56]
move $t6, $v0
sw $t6, -68($fp)  # Spill t8
lw $t0, -40($fp)
move $a0, $t0
jal saludar
move $t0, $v0
sw $t0, -72($fp)  # Spill t9
lw $t0, -24($fp)
lw $t0, -72($fp)
sw $t6, -76($fp)  # Spill G[64]
addu $t6, $t0, $t0
sw $t6, -80($fp)  # Spill t10
sw $t7, -84($fp)  # Spill fp[-1][0]
addu $t7, $t6, $t6
sw $t7, -88($fp)  # Spill t11
lw $t0, -40($fp)
move $a0, $t0
jal estudiar
move $t0, $v0
sw $t0, -92($fp)  # Spill t12
addu $t0, $t7, $t0
sw $t0, -96($fp)  # Spill t13
addu $t0, $t0, $t6
move $t7, $t0
sw $t0, -100($fp)  # Spill t14
lw $t0, -40($fp)
move $a0, $t0
li $a1, 6
jal incrementarEdad
move $t0, $v0
sw $t0, -104($fp)  # Spill t15
addu $t0, $t7, $t0
sw $t0, -108($fp)  # Spill t16
addu $t0, $t0, $t6
move $t7, $t0
sw $t0, -112($fp)  # Spill t17
lw $t0, -56($fp)
move $a0, $t0
jal saludar
move $t0, $v0
sw $t0, -116($fp)  # Spill t18
addu $t0, $t7, $t0
sw $t0, -120($fp)  # Spill t19
addu $t0, $t0, $t6
move $t7, $t0
sw $t0, -124($fp)  # Spill t20
lw $t0, -56($fp)
move $a0, $t0
jal estudiar
move $t0, $v0
sw $t0, -128($fp)  # Spill t21
addu $t0, $t7, $t0
sw $t0, -132($fp)  # Spill t22
addu $t0, $t0, $t6
move $t7, $t0
sw $t0, -136($fp)  # Spill t23
lw $t0, -56($fp)
move $a0, $t0
li $a1, 7
jal incrementarEdad
move $t0, $v0
sw $t0, -140($fp)  # Spill t24
addu $t0, $t7, $t0
sw $t0, -144($fp)  # Spill t25
addu $t0, $t0, $t6
move $t7, $t0
sw $t0, -148($fp)  # Spill t26
lw $t0, -76($fp)
move $a0, $t0
jal saludar
move $t0, $v0
sw $t0, -152($fp)  # Spill t27
addu $t0, $t7, $t0
sw $t0, -156($fp)  # Spill t28
addu $t0, $t0, $t6
move $t7, $t0
sw $t0, -160($fp)  # Spill t29
lw $t0, -76($fp)
move $a0, $t0
jal estudiar
move $t0, $v0
sw $t0, -164($fp)  # Spill t30
addu $t0, $t7, $t0
sw $t0, -168($fp)  # Spill t31
addu $t0, $t0, $t6
move $t7, $t0
sw $t0, -172($fp)  # Spill t32
lw $t0, -76($fp)
move $a0, $t0
li $a1, 6
jal incrementarEdad
move $t0, $v0
sw $t0, -176($fp)  # Spill t33
addu $t0, $t7, $t0
sw $t0, -180($fp)  # Spill t34
addu $t0, $t0, $t6
move $t7, $t0
sw $t0, -184($fp)  # Spill t35
li $t0, 1
STARTWHILE_0:
sw $t0, -188($fp)  # Spill G[68]
sw $t0, -192($fp)  # Spill t36
li $t0, 12
slt $t0, $t0, $t0
xori $t0, $t0, 1
lw $t0, -192($fp)
bne $t0, $zero, LABEL_TRUE_0
j ENDWHILE_0
LABEL_TRUE_0:
lw $t0, -188($fp)
sw $t0, -196($fp)  # Spill t37
lw $t0, 2
div $t0, $t0
mfhi $t0
lw $t0, -196($fp)
sw $t7, -24($fp)  # Spill G[24]
li $t0, 0
sub $t0, $t0, $t0
sltiu $t7, $t0, 1
bne $t7, $zero, IF_TRUE_1
j IF_FALSE_1
IF_TRUE_1:
lw $t0, -188($fp)
move $a0, $t0
jal toString
move $t0, $v0
sw $t0, -200($fp)  # Spill t39
lw $t0, -24($fp)
lw $t0, -200($fp)
sw $t7, -204($fp)  # Spill t38
addu $t7, $t0, $t0
sw $t7, -208($fp)  # Spill t40
sw $t8, -212($fp)  # Spill fp[-1][8]
addu $t8, $t7, $t7
sw $t8, -216($fp)  # Spill t41
j IF_END_1
IF_FALSE_1:
lw $t0, -188($fp)
move $a0, $t0
jal toString
move $t0, $v0
sw $t0, -220($fp)  # Spill t42
addu $t0, $t8, $t0
sw $t0, -224($fp)  # Spill t43
sw $t8, -24($fp)  # Spill G[24]
addu $t8, $t0, $t0
sw $t8, -228($fp)  # Spill t44
IF_END_1:
sw $t0, -232($fp)  # Spill " es impar\n"
lw $t0, -188($fp)
addi $t0, $t0, 1
sw $t0, -236($fp)  # Spill t45
j STARTWHILE_0
ENDWHILE_0:
sw $t0, -188($fp)  # Spill G[68]
sw $t8, -24($fp)  # Spill G[24]
sw $t0, -240($fp)  # Spill G[76][8]
lw $t0, 2
mult $t0, $t0
mflo $t8
sw $t0, -244($fp)  # Spill t47
lw $t0, 5
addi $t0, $t0, -3
lw $t0, -244($fp)
sw $t8, -248($fp)  # Spill t46
lw $t0, 2
div $t0, $t0
mflo $t8
lw $t0, -248($fp)
sw $t8, -252($fp)  # Spill t48
addu $t8, $t0, $t8
sw $t8, -256($fp)  # Spill t49
lw $t0, -24($fp)
sw $t8, -260($fp)  # Spill G[72]
addu $t8, $t0, $t0
sw $t0, -264($fp)  # Spill "Resultado de la expresión: "
lw $t0, -260($fp)
move $a0, $t0
jal toString
move $t0, $v0
sw $t0, -268($fp)  # Spill t51
addu $t0, $t8, $t0
sw $t0, -272($fp)  # Spill t52
addu $t0, $t0, $t6
sw $t0, -276($fp)  # Spill t53
sw $t0, -24($fp)  # Spill G[24]
li $t0, 0
sw $t0, -280($fp)  # Spill G[80]
lw $t0, -40($fp)
move $a0, $t0
li $a1, 99
li $a2, 95
li $a3, 98
addi $sp, $sp, -12
li $t9, 100
sw $t9, 0($sp)
li $t9, 95
sw $t9, 4($sp)
li $t9, 94
sw $t9, 8($sp)
jal promedioNotas
addi $sp, $sp, 12
move $t0, $v0
sw $t0, -284($fp)  # Spill t54
sw $t0, -280($fp)  # Spill G[80]
lw $t0, -24($fp)
sw $t8, -288($fp)  # Spill t50
addu $t8, $t0, $t0
sw $t0, -292($fp)  # Spill "Promedio (entero): "
lw $t0, -280($fp)
move $a0, $t0
jal toString
move $t0, $v0
sw $t0, -296($fp)  # Spill t56
addu $t0, $t8, $t0
sw $t0, -300($fp)  # Spill t57
addu $t0, $t0, $t6
sw $t0, -304($fp)  # Spill t58
sw $t0, -24($fp)  # Spill G[24]
sw $t8, -308($fp)  # Spill t55
addu $t8, $t0, $t0
sw $t8, -312($fp)  # Spill t59
sw $t8, -24($fp)  # Spill G[24]
li $t8, 20
sw $t8, -316($fp)  # Spill G[84]
li $t8, 0
STARTWHILE_1:
sw $t0, -320($fp)  # Spill "Prueba: Fibonacci recursivo\n"
lw $t0, -316($fp)
slt $t0, $t0, $t8
xori $t0, $t0, 1
bne $t0, $zero, LABEL_TRUE_1
j ENDWHILE_1
LABEL_TRUE_1:
move $a0, $t8
jal fibonacci
sw $t0, -324($fp)  # Spill t60
move $t0, $v0
sw $t0, -328($fp)  # Spill t61
sw $t0, -332($fp)  # Spill G[92]
lw $t0, -24($fp)
sw $t8, -336($fp)  # Spill G[88]
addu $t8, $t0, $t0
sw $t0, -340($fp)  # Spill "Fib("
lw $t0, -336($fp)
move $a0, $t0
jal toString
move $t0, $v0
sw $t0, -344($fp)  # Spill t63
addu $t0, $t8, $t0
sw $t0, -348($fp)  # Spill t64
sw $t8, -352($fp)  # Spill t62
addu $t8, $t0, $t0
sw $t0, -356($fp)  # Spill ") = "
lw $t0, -332($fp)
move $a0, $t0
jal toString
move $t0, $v0
sw $t0, -360($fp)  # Spill t66
addu $t0, $t8, $t0
sw $t0, -364($fp)  # Spill t67
addu $t0, $t0, $t6
sw $t0, -368($fp)  # Spill t68
sw $t0, -24($fp)  # Spill G[24]
lw $t0, -336($fp)
addi $t0, $t0, 1
sw $t0, -372($fp)  # Spill t69
j STARTWHILE_1
ENDWHILE_1:
sw $t0, -336($fp)  # Spill G[88]
lw $t0, -24($fp)
move $a0, $t0
jal printString
move $t0, $v0
# === END OF PROGRAM ===

main:
    li $v0, 10  # syscall exit
    syscall