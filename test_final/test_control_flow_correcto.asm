.data
    .align 2
newline:     .asciiz "\n"
str_par:     .asciiz " es par\n"
str_impar:   .asciiz " es impar\n"
log_buffer:  .space 256      # Buffer para el log

.text
    .globl main

# ========================================
# Función toString(x: integer): string
# Convierte un número a string (versión simplificada)
# Parámetros: $a0 = número entero
# Retorna: $v0 = puntero a string (simplificado: retorna el número)
# ========================================
toString:
    # Por simplicidad, solo retornamos el número mismo
    # En una implementación real, convertiríamos a ASCII
    move $v0, $a0
    jr $ra

# ========================================
# Función printString(x: string): string
# Imprime un string y lo retorna
# Parámetros: $a0 = puntero a string
# Retorna: $v0 = el mismo string
# ========================================
printString:
    # Guardar argumento para retornar
    move $t0, $a0
    
    # Imprimir el string (syscall 4)
    li $v0, 4
    syscall
    
    # Retornar el string
    move $v0, $t0
    jr $ra

# ========================================
# Programa Principal
# ========================================
main:
    # Prólogo
    addi $sp, $sp, -20
    sw $ra, 16($sp)
    sw $s0, 12($sp)     # log (no se usa realmente)
    sw $s1, 8($sp)      # i
    sw $s2, 4($sp)      # temp
    sw $s3, 0($sp)      # temp
    
    # Inicializar variables
    # let log: string = "";  (no se usa en SPIM)
    # let i: integer = 1;
    li $s1, 1           # i = 1
    
# ========================================
# while (i <= 12)
# ========================================
while_start:
    # Condición: i <= 12
    li $t0, 12
    sgt $t1, $s1, $t0   # $t1 = (i > 12)
    bne $t1, $zero, while_end   # Si i > 12, salir del loop
    
    # ========================================
    # Cuerpo del while: if ((i % 2) == 0)
    # ========================================
    
    # Calcular i % 2
    li $t0, 2
    div $s1, $t0        # i / 2
    mfhi $t1            # $t1 = i % 2
    
    # Comparar: (i % 2) == 0
    bne $t1, $zero, else_branch
    
    # ========================================
    # Branch: if - es par
    # ========================================
if_branch:
    # Imprimir el número
    move $a0, $s1
    li $v0, 1           # syscall print_int
    syscall
    
    # Imprimir " es par\n"
    la $a0, str_par
    li $v0, 4           # syscall print_string
    syscall
    
    j if_end
    
    # ========================================
    # Branch: else - es impar
    # ========================================
else_branch:
    # Imprimir el número
    move $a0, $s1
    li $v0, 1           # syscall print_int
    syscall
    
    # Imprimir " es impar\n"
    la $a0, str_impar
    li $v0, 4           # syscall print_string
    syscall

if_end:
    # i = i + 1
    addi $s1, $s1, 1
    
    # Volver al inicio del while
    j while_start

# ========================================
# Fin del while
# ========================================
while_end:
    # printString(log) - ya se imprimió todo durante el loop
    
    # Epílogo
    lw $ra, 16($sp)
    lw $s0, 12($sp)
    lw $s1, 8($sp)
    lw $s2, 4($sp)
    lw $s3, 0($sp)
    addi $sp, $sp, 20
    
    # Salir del programa
    li $v0, 10          # syscall exit
    syscall
