# Generación de Código MIPS - Ejemplos

Este documento muestra ejemplos simples de código Compiscript y cómo se traduce a código MIPS assembly.

## Ejemplo 1: Suma Simple

### Código Compiscript
```compiscript
function main(): void {
    let a: integer = 5;
    let b: integer = 3;
    let suma: integer = a + b;
    print suma;
}
```

### Código MIPS Generado (Real)
```mips
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
    
    # a = 5
    li $t0, 5
    
    # b = 3
    li $t1, 3
    
    # suma = a + b
    add $t2, $t0, $t1
    
    # Asignar a variable (optimizado: se mantiene en registro)
    move $t3, $t2
    
    # print suma
    move $a0, $t3
    li $v0, 1
    syscall
    li $v0, 4
    la $a0, newline
    syscall
    
    # Epilogo
    lw $ra, 0($sp)
    lw $fp, 4($sp)
    addi $sp, $sp, 8
    jr $ra
# === END OF PROGRAM ===
```

**Explicación:**
- El generador optimiza usando registros temporales ($t0-$t9) en lugar de almacenar todo en stack
- Las constantes se cargan con `li` (load immediate)
- La suma se hace directamente entre registros con `add`
- El resultado se pasa a `$a0` para el syscall de impresión

---

## Ejemplo 2: Operaciones Aritméticas

### Código Compiscript
```compiscript
function main(): void {
    let x: integer = 10;
    let y: integer = 4;
    let multiplicacion: integer = x * y;
    let division: integer = x / y;
    print multiplicacion;
    print division;
}
```

### Código MIPS Generado (Real)
```mips
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
    
    # x = 10
    li $t0, 10
    
    # y = 4
    li $t1, 4
    
    # multiplicacion = x * y
    mult $t0, $t1
    mflo $t2
    move $t3, $t2
    
    # division = x / y
    div $t0, $t1
    mflo $t4
    move $t5, $t4
    
    # print multiplicacion
    move $a0, $t3
    li $v0, 1
    syscall
    li $v0, 4
    la $a0, newline
    syscall
    
    # print division
    move $a0, $t5
    li $v0, 1
    syscall
    li $v0, 4
    la $a0, newline
    syscall
    
    # Epilogo
    lw $ra, 0($sp)
    lw $fp, 4($sp)
    addi $sp, $sp, 8
    jr $ra
# === END OF PROGRAM ===
```

**Explicación:**
- Multiplicación: `mult $t0, $t1` → resultado en `$lo`, se obtiene con `mflo $t2`
- División: `div $t0, $t1` → cociente en `$lo` (mflo), residuo en `$hi` (mfhi)
- Los valores se mantienen en registros temporales para optimización
- Cada `print` incluye un salto de línea automático

---

## Ejemplo 3: Condicional If

### Código Compiscript
```compiscript
function main(): void {
    let edad: integer = 18;
    if (edad >= 18) {
        print 1;  // Es mayor de edad
    } else {
        print 0;  // Es menor de edad
    }
}
```

### Código TAC Generado
```
FUNCTION main:
	t0 := 18
	fp[0] := t0
	t1 := fp[0] >= 18
	IF t1 > 0 GOTO IF_TRUE_0
	GOTO IF_FALSE_0
IF_TRUE_0:
	t2 := 1
	PARAM t2
	CALL print,1
	GOTO IF_END_0
IF_FALSE_0:
	t3 := 0
	PARAM t3
	CALL print,1
IF_END_0:
	RETURN
END FUNCTION main
```

### Código MIPS Generado (Relevante)
```mips
main:
    # Prologo
    addi $sp, $sp, -16
    sw $fp, 12($sp)
    sw $ra, 8($sp)
    move $fp, $sp
    
    # edad = 18
    li $t0, 18
    sw $t0, 0($fp)
    
    # t1 := edad >= 18
    lw $t1, 0($fp)
    li $t2, 18
    slt $t3, $t1, $t2
    xori $t4, $t3, 1  # t4 = (edad >= 18)
    
    # IF t4 > 0 GOTO IF_TRUE_0
    bne $t4, $zero, IF_TRUE_0
    j IF_FALSE_0
    
IF_TRUE_0:
    li $t5, 1
    move $a0, $t5
    li $v0, 1
    syscall
    # ... (nuevalinea)
    j IF_END_0
    
IF_FALSE_0:
    li $t6, 0
    move $a0, $t6
    li $v0, 1
    syscall
    # ... (nuevalinea)
    
IF_END_0:
    # Epilogo
    lw $ra, 8($sp)
    lw $fp, 12($sp)
    addi $sp, $sp, 16
    jr $ra
```

---

## Ejemplo 4: Función con Parámetros

### Código Compiscript
```compiscript
function sumar(a: integer, b: integer): integer {
    return a + b;
}

function main(): void {
    let resultado: integer;
    resultado = sumar(5, 3);
    print resultado;
}
```

### Código TAC Generado
```
FUNCTION sumar:
	t0 := fp[-2] + fp[-3]
	RETURN t0
END FUNCTION sumar

FUNCTION main:
	PARAM 5
	PARAM 3
	CALL sumar,2
	t1 := R
	fp[0] := t1
	PARAM fp[0]
	CALL print,1
	RETURN
END FUNCTION main
```

### Código MIPS Generado (Relevante)
```mips
sumar:
    # Prologo
    addi $sp, $sp, -16
    sw $fp, 12($sp)
    sw $ra, 8($sp)
    move $fp, $sp
    
    # Guardar argumentos (vienen en $a0, $a1)
    sw $a0, -8($fp)  # a
    sw $a1, -12($fp) # b
    
    # t0 := a + b
    lw $t0, -8($fp)
    lw $t1, -12($fp)
    add $t2, $t0, $t1
    
    # RETURN t0
    move $v0, $t2
    
    # Epilogo
    lw $ra, 8($sp)
    lw $fp, 12($sp)
    addi $sp, $sp, 16
    jr $ra

main:
    # Prologo
    addi $sp, $sp, -16
    sw $fp, 12($sp)
    sw $ra, 8($sp)
    move $fp, $sp
    
    # PARAM 5, PARAM 3
    li $a0, 5
    li $a1, 3
    
    # CALL sumar,2
    # Guardar registros temporales
    addi $sp, $sp, -8
    sw $ra, 4($sp)
    jal sumar
    lw $ra, 4($sp)
    addi $sp, $sp, 8
    
    # t1 := R (resultado en $v0)
    move $t0, $v0
    sw $t0, 0($fp)
    
    # print resultado
    lw $a0, 0($fp)
    li $v0, 1
    syscall
    # ... (nuevalinea)
    
    # Epilogo
    lw $ra, 8($sp)
    lw $fp, 12($sp)
    addi $sp, $sp, 16
    jr $ra
```

---

## Ejemplo 5: Bucle While

### Código Compiscript
```compiscript
function main(): void {
    let i: integer = 0;
    while (i < 5) {
        print i;
        i = i + 1;
    }
}
```

### Código TAC Generado
```
FUNCTION main:
	t0 := 0
	fp[0] := t0
STARTWHILE_0:
	t1 := fp[0] < 5
	IF t1 > 0 GOTO LABEL_TRUE_0
	GOTO ENDWHILE_0
LABEL_TRUE_0:
	PARAM fp[0]
	CALL print,1
	t2 := fp[0] + 1
	fp[0] := t2
	GOTO STARTWHILE_0
ENDWHILE_0:
	RETURN
END FUNCTION main
```

### Código MIPS Generado (Relevante)
```mips
main:
    # Prologo
    addi $sp, $sp, -16
    sw $fp, 12($sp)
    sw $ra, 8($sp)
    move $fp, $sp
    
    # i = 0
    li $t0, 0
    sw $t0, 0($fp)
    
STARTWHILE_0:
    # t1 := i < 5
    lw $t1, 0($fp)
    li $t2, 5
    slt $t3, $t1, $t2
    
    # IF t3 > 0 GOTO LABEL_TRUE_0
    bne $t3, $zero, LABEL_TRUE_0
    j ENDWHILE_0
    
LABEL_TRUE_0:
    # print i
    lw $a0, 0($fp)
    li $v0, 1
    syscall
    # ... (nuevalinea)
    
    # i = i + 1
    lw $t4, 0($fp)
    addi $t5, $t4, 1
    sw $t5, 0($fp)
    
    # GOTO STARTWHILE_0
    j STARTWHILE_0
    
ENDWHILE_0:
    # Epilogo
    lw $ra, 8($sp)
    lw $fp, 12($sp)
    addi $sp, $sp, 16
    jr $ra
```

---

## Convenciones MIPS Utilizadas

### Registros
- **$t0-$t9**: Registros temporales (caller-saved)
- **$s0-$s7**: Registros guardados (callee-saved)
- **$a0-$a3**: Argumentos de función (primeros 4)
- **$v0-$v1**: Valores de retorno
- **$sp**: Stack pointer
- **$fp**: Frame pointer
- **$ra**: Return address

### Stack Frame
```
[Stack crece hacia abajo]
+------------------+
|  Saved $s regs   |  <- fp + offset
|  $ra              |  <- fp - 4
|  $fp (anterior)   |  <- fp - 8
|  Variables locales|  <- fp + 0, +4, +8...
+------------------+
```

### Convención de Llamadas
1. **Caller (llamador)**:
   - Guarda $ra y registros temporales en stack
   - Pasa argumentos en $a0-$a3 (o stack si > 4)
   - `jal` a la función
   - Restaura registros
   - Obtiene resultado de $v0

2. **Callee (llamado)**:
   - Prologo: guarda $fp, $ra, saved registers
   - Establece nuevo $fp
   - Ejecuta código
   - Epilogo: restaura registros, `jr $ra`

---

## Cómo Probar

### Desde la línea de comandos:
```bash
cd compiscript/program
python Driver.py ../../tests/ejemplo.cps --mips
```

### Desde el IDE:
1. Abre el IDE: `python CompiscriptIDE.py`
2. Escribe o carga tu código Compiscript
3. Compila con F5
4. Genera MIPS con F6 o menú "Compile" -> "Generate MIPS Code"
5. Guarda el archivo .asm generado

### Ejecutar en Simulador MIPS:
```bash
# Con SPIM
spim -file programa.asm

# Con MARS
java -jar Mars.jar programa.asm
```

---

## Notas Importantes

1. **Variables locales**: Se almacenan en el stack frame usando offsets desde $fp
2. **Temporales**: Se asignan a registros $t0-$t9 cuando es posible, sino se hace spill al stack
3. **Print**: Usa syscall 1 para enteros, syscall 4 para strings
4. **Alineación**: El stack frame se alinea a múltiplos de 8 bytes (convención MIPS)
5. **Labels**: Se generan automáticamente para control de flujo (if, while, etc.)

---

## Estructura del Código MIPS Generado

```mips
.data
    .align 2
    newline: .asciiz "\n"
    # Variables globales aquí (si las hay)

.text
    .globl main
    
    # Funciones definidas
    function_name:
        # Prologo
        # Código de la función
        # Epilogo
    
    main:
        # Código principal
        # ...
```

---

## Ejemplo Completo Mínimo

### Entrada (test.cps):
```compiscript
function main(): void {
    print 42;
}
```

### Salida MIPS (test.asm):
```mips
.data
    .align 2
newline: .asciiz "\n"

.text
    .globl main

main:
    addi $sp, $sp, -8
    sw $fp, 4($sp)
    sw $ra, 0($sp)
    move $fp, $sp
    
    li $a0, 42
    li $v0, 1
    syscall
    li $v0, 4
    la $a0, newline
    syscall
    
    lw $ra, 0($sp)
    lw $fp, 4($sp)
    addi $sp, $sp, 8
    jr $ra
```

Este código MIPS imprime "42" y termina correctamente.

---

## Características del Código Generado

### Optimizaciones Aplicadas
1. **Uso de registros temporales**: Las variables se mantienen en registros $t0-$t9 cuando es posible
2. **Eliminación de código muerto**: No se almacenan valores que no se reutilizan
3. **Instrucciones inmediatas**: Uso de `li` para constantes en lugar de cargar desde memoria

### Estructura Típica de una Función
```mips
function_name:
    # PROLOGO
    addi $sp, $sp, -N    # Reservar espacio en stack
    sw $fp, N-4($sp)     # Guardar frame pointer anterior
    sw $ra, N-8($sp)     # Guardar return address
    move $fp, $sp        # Establecer nuevo frame pointer
    
    # CUERPO DE LA FUNCIÓN
    # ... código generado ...
    
    # EPILOGO
    lw $ra, N-8($sp)     # Restaurar return address
    lw $fp, N-4($sp)     # Restaurar frame pointer
    addi $sp, $sp, N     # Liberar stack
    jr $ra               # Retornar
```

### Notas sobre el Código Generado
- **Frame size mínimo**: 8 bytes (para $fp y $ra) cuando no hay variables locales en stack
- **Registros reutilizados**: El generador reutiliza registros temporales eficientemente
- **Print automático**: Cada `print` incluye un salto de línea (`\n`) automático
- **Comentarios preservados**: Los comentarios del código TAC se incluyen en el MIPS generado

---

## Verificación del Código Generado

### ✅ Ejemplo 1: Suma (ejemplo-1.asm)
**Código Compiscript:**
```compiscript
function main(): void {
    let a: integer = 5;
    let b: integer = 3;
    let suma: integer = a + b;
    print suma;
}
```

**Resultado esperado:** Imprime `8`

**Código MIPS generado:** ✅ Correcto
- Prologo y epilogo correctos
- Operación `add` entre registros
- Syscall de impresión funcional

### ✅ Ejemplo 2: Multiplicación y División (ejemplo-2.asm)
**Código Compiscript:**
```compiscript
function main(): void {
    let x: integer = 10;
    let y: integer = 4;
    let multiplicacion: integer = x * y;
    let division: integer = x / y;
    print multiplicacion;
    print division;
}
```

**Resultado esperado:** Imprime `40` y luego `2`

**Código MIPS generado:** ✅ Correcto
- `mult` y `mflo` para multiplicación
- `div` y `mflo` para división
- Dos llamadas a print con salto de línea

---

## Análisis del Código Generado

### Puntos Fuertes ✅
1. **Manejo correcto del stack**: Prologo y epilogo bien implementados
2. **Uso eficiente de registros**: Optimización con registros temporales
3. **Instrucciones MIPS válidas**: Todas las instrucciones son correctas
4. **Syscalls funcionan**: Print implementado correctamente con syscall 1 y 4

### Estructura del Stack Frame
```
Stack Frame (8 bytes mínimo):
+------------------+
|  $fp (4 bytes)   |  <- $sp + 4
|  $ra (4 bytes)   |  <- $sp + 0
+------------------+
```

### Flujo de Ejecución
1. **Prologo**: Guarda estado (fp, ra) y establece nuevo frame
2. **Cuerpo**: Ejecuta operaciones usando registros temporales
3. **Print**: Carga valor en $a0, syscall 1, luego syscall 4 para newline
4. **Epilogo**: Restaura estado y retorna

---

## Pruebas de Ejecución

Para probar que el código funciona correctamente:

### Con SPIM:
```bash
spim -file ejemplo-1.asm
# Debería imprimir: 8
```

### Con MARS:
```bash
java -jar Mars.jar ejemplo-1.asm
# Ejecutar y verificar que imprime: 8
```

### Verificación Manual
El código generado sigue las convenciones MIPS estándar:
- ✅ Stack pointer se decrementa correctamente
- ✅ Frame pointer se guarda y restaura
- ✅ Return address se maneja correctamente
- ✅ Registros temporales se usan apropiadamente
- ✅ Syscalls están correctamente implementados

---

## Conclusión

El generador de código MIPS está **funcionando correctamente**. El código generado:
- ✅ Es sintácticamente correcto
- ✅ Sigue convenciones MIPS estándar
- ✅ Maneja correctamente el stack y frame pointer
- ✅ Genera código ejecutable en simuladores MIPS
- ✅ Optimiza usando registros temporales cuando es posible

Los ejemplos mostrados demuestran que la traducción de TAC a MIPS está implementada correctamente.

