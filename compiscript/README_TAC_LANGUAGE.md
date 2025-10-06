# Lenguaje Intermedio TAC (Three Address Code) - Compiscript

## Introducción

Este documento describe el diseño e implementación del lenguaje intermedio TAC (Three Address Code) para el compilador de Compiscript. El código de tres direcciones es una representación intermedia que facilita la optimización y generación de código objeto, manteniendo una estructura simple y sistemática.

## Principios de Diseño

### 1. **Modelo de Memoria**
- **Frame Pointer (fp)**: Apunta al registro de activación actual
- **Global Array (G)**: Almacena variables globales
- **Parámetros**: Se almacenan en índices negativos del frame pointer
- **Variables Locales**: Se almacenan en índices positivos del frame pointer

### 2. **Convenciones de Direccionamiento**
- `fp[k]` donde k ≥ 0: Variables locales
- `fp[-k]` donde k > 0: Parámetros de función
- `G[k]`: Variables globales
- `fp[-1]`: Referencia a `this` en métodos de clase

### 3. **Gestión de Objetos y Campos**
- Los objetos se referencian por su dirección base
- Los campos se acceden mediante offset: `objeto[offset]`
- El offset se calcula basado en el orden de declaración y tamaño de tipos

## Estructura del Código TAC

### Formato General
```
FUNCTION nombre:
    // Código de tres direcciones
    RETURN valor
END FUNCTION nombre
```

### Tipos de Instrucciones

1. **Asignación**: `destino := expresión`
2. **Operaciones binarias**: `t := operando1 op operando2`
3. **Saltos condicionales**: `IF condición > 0 GOTO etiqueta`
4. **Saltos incondicionales**: `GOTO etiqueta`
5. **Llamadas a función**: 
   - `PARAM argumento`
   - `CALL función,num_params`
   - `t := R` (obtener valor de retorno)
6. **Retorno**: `RETURN valor`

## Ejemplos Detallados

### 1. Atributos y Métodos en Clases

#### Programa 1: Acceso a Campos
```compiscript
class Punto {
  var x: integer;
  var y: integer;

  function sum(): integer {
    return x + y;
  }
}

function main(): void {
  let p: Punto;
  // (suponemos p válido)
  let s: integer;
  s = p.x + p.y;
}
```

**Código Intermedio:**
```tac
FUNCTION sum:           ; this en fp[-1]
t0 := fp[-1][0] + fp[-1][4]   ; x en offset 0, y en 4
RETURN t0
END FUNCTION sum

FUNCTION main:
t0 := fp[0][0] + fp[0][4]     ; p.x + p.y  (p en fp[0])
fp[4] := t0                   ; s
END FUNCTION main
```

**Explicación:**
- En el método `sum`, `this` se encuentra en `fp[-1]`
- Los campos `x` e `y` tienen offsets 0 y 4 respectivamente
- En `main`, el objeto `p` está en `fp[0]` y la variable `s` en `fp[4]`

#### Programa 2: Llamada a Método con Parámetro
```compiscript
class Caja {
  var v: integer;
  function setv(a: integer): void { v = a; }
}

function main(): void {
  let c: Caja;
  // c válido
  c.setv(10);
}
```

**Código Intermedio:**
```tac
FUNCTION setv:                 ; this=fp[-1], a=fp[-2]
fp[-1][0] := fp[-2]            ; v (offset 0) = a
RETURN 0
END FUNCTION setv

FUNCTION main:
PARAM fp[0]                    ; this
PARAM 10
CALL setv,2
t0 := R
END FUNCTION main
```

**Explicación:**
- Los parámetros se pasan en orden: primero `this`, luego los argumentos
- En `setv`: `this` está en `fp[-1]`, parámetro `a` en `fp[-2]`
- La llamada incluye 2 parámetros (this + argumento)

#### Programa 3: Método con Retorno
```compiscript
class Acum {
  var acc: integer;
  function add(a: integer): integer {
    acc = acc + a;
    return acc;
  }
}

function main(): void {
  let a: Acum; let r: integer;
  // a válido
  r = a.add(5);
}
```

**Código Intermedio:**
```tac
FUNCTION add:                         ; this=fp[-1], a=fp[-2]
t0 := fp[-1][0] + fp[-2]              ; acc + a
fp[-1][0] := t0
RETURN t0
END FUNCTION add

FUNCTION main:
PARAM fp[0]                           ; this = a
PARAM 5
CALL add,2
t0 := R
fp[4] := t0                           ; r
END FUNCTION main
```

**Explicación:**
- El método modifica el campo del objeto y retorna el valor
- El valor de retorno se captura con `t0 := R`

### 2. Estructuras de Control

#### Programa 1: If Simple
```compiscript
function main(): void {
  let x: integer; let y: integer;
  if (x < y) x = y;
}
```

**Código Intermedio:**
```tac
FUNCTION main:
t0 := fp[0] < fp[4]
IF t0 > 0 GOTO IF_TRUE_0
GOTO IF_END_0
IF_TRUE_0:
fp[0] := fp[4]
IF_END_0:
END FUNCTION main
```

**Explicación:**
- Las condiciones se evalúan a 0 (falso) o 1 (verdadero)
- Si la condición es verdadera (> 0), se ejecuta el bloque

#### Programa 2: If-Else
```compiscript
function main(): void {
  let a: integer; let b: integer; let m: integer;
  if (a < b) m = a; else m = b;
}
```

**Código Intermedio:**
```tac
FUNCTION main:
t0 := fp[0] < fp[4]
IF t0 > 0 GOTO IF_TRUE_0
GOTO IF_FALSE_0
IF_TRUE_0:
fp[8] := fp[0]
GOTO IF_END_0
IF_FALSE_0:
fp[8] := fp[4]
IF_END_0:
END FUNCTION main
```

**Explicación:**
- Se generan tres etiquetas: `IF_TRUE_k`, `IF_FALSE_k`, `IF_END_k`
- Después del bloque then se salta al final para evitar ejecutar el else

#### Programa 3: While Loop
```compiscript
function main(): void {
  let i: integer;
  i = 0;
  while (i <= 3) { i = i + 1; }
}
```

**Código Intermedio:**
```tac
FUNCTION main:
fp[0] := 0
STARTWHILE_0:
t0 := fp[0] <= 3
IF t0 > 0 GOTO LABEL_TRUE_0
GOTO ENDWHILE_0
LABEL_TRUE_0:
t1 := fp[0] + 1
fp[0] := t1
GOTO STARTWHILE_0
ENDWHILE_0:
END FUNCTION main
```

**Explicación:**
- Se genera un bucle con `STARTWHILE_k` como punto de entrada
- La condición se evalúa en cada iteración
- Al final del cuerpo se regresa al inicio del bucle

### 3. Llamadas a Métodos de Objetos

#### Programa 1: Método Simple
```compiscript
class C { function id(a: integer): integer { return a; } }
function main(): void { let c: C; let r: integer; r = c.id(7); }
```

**Código Intermedio:**
```tac
FUNCTION id:               ; this=fp[-1], a=fp[-2]
RETURN fp[-2]
END FUNCTION id

FUNCTION main:
PARAM fp[0]                ; this=c
PARAM 7
CALL id,2
t0 := R
fp[4] := t0                ; r
END FUNCTION main
```

#### Programa 2: Método con Múltiples Parámetros
```compiscript
class Math { function sum(a: integer, b: integer): integer { return a + b; } }
function main(): void { let m: Math; let x: integer; x = m.sum(2,3); }
```

**Código Intermedio:**
```tac
FUNCTION sum:                      ; this=fp[-1], a=fp[-2], b=fp[-3]
t0 := fp[-2] + fp[-3]
RETURN t0
END FUNCTION sum

FUNCTION main:
PARAM fp[0]                        ; this
PARAM 2
PARAM 3
CALL sum,3
t0 := R
fp[4] := t0
END FUNCTION main
```

**Explicación:**
- Los parámetros se apilan en orden: this, luego argumentos en orden
- Cada parámetro adicional incrementa el índice negativo

#### Programa 3: Método que Modifica Estado
```compiscript
class P { var x: integer; function inc(): integer { x = x + 1; return x; } }
function main(): void { let p: P; let v: integer; v = p.inc(); }
```

**Código Intermedio:**
```tac
FUNCTION inc:                      ; this=fp[-1]
t0 := fp[-1][0] + 1
fp[-1][0] := t0
RETURN t0
END FUNCTION inc

FUNCTION main:
PARAM fp[0]                        ; this=p
CALL inc,1
t0 := R
fp[4] := t0                        ; v
END FUNCTION main
```

### 4. Ámbitos (Scoping) y Shadowing

#### Programa 1: Shadowing Global
```compiscript
var a: integer;
function main(): void {
  let a: integer;   // sombrea a la global
  a = 1;            // usa la local
}
```

**Código Intermedio:**
```tac
FUNCTION main:
fp[0] := 1
END FUNCTION main
```

**Explicación:**
- La variable local `a` en `fp[0]` oculta la global `G[0]`
- Solo se genera código para la asignación a la variable local

#### Programa 2: Variables con Nombres Distintos
```compiscript
var g: integer;
function main(): void {
  let g_local: integer;
  g = 10;
  g_local = g + 1;
}
```

**Código Intermedio:**
```tac
FUNCTION main:
G[0] := 10
t0 := G[0] + 1
fp[0] := t0
END FUNCTION main
```

**Explicación:**
- `g` se refiere a la variable global `G[0]`
- `g_local` es una variable local en `fp[0]`

### 5. Expresiones Aritméticas

#### Programa 1: Precedencia de Operadores
```compiscript
var a: integer;
function main(): void {
  let b: integer; let c: integer; let d: integer;
  a = b + c * d;
}
```

**Código Intermedio:**
```tac
FUNCTION main:
t0 := fp[4] * fp[8]
t1 := fp[0] + t0
G[0] := t1
END FUNCTION main
```

**Explicación:**
- La multiplicación se evalúa primero debido a la precedencia
- Se usan temporales para almacenar resultados intermedios

#### Programa 2: Expresiones con Paréntesis
```compiscript
function main(): void {
  let x: integer; let y: integer; let z: integer;
  z = (x - y) * (x + y);
}
```

**Código Intermedio:**
```tac
FUNCTION main:
t0 := fp[0] - fp[4]
t1 := fp[0] + fp[4]
t2 := t0 * t1
fp[8] := t2
END FUNCTION main
```

**Explicación:**
- Los paréntesis fuerzan la evaluación de subexpresiones
- Cada subexpresión se almacena en un temporal

#### Programa 3: División con Expresión Compleja
```compiscript
function main(): void {
  let a: integer; let b: integer; let r: integer;
  r = a / (b + 1);
}
```

**Código Intermedio:**
```tac
FUNCTION main:
t0 := fp[4] + 1
t1 := fp[0] / t0
fp[8] := t1
END FUNCTION main
```

### 6. Expresiones Booleanas

#### Programa 1: Operador Relacional
```compiscript
function main(): void {
  let x: integer; let y: integer;
  if (x == y) x = 0;
}
```

**Código Intermedio:**
```tac
FUNCTION main:
t0 := fp[0] == fp[4]
IF t0 > 0 GOTO IF_TRUE_0
GOTO IF_END_0
IF_TRUE_0:
fp[0] := 0
IF_END_0:
END FUNCTION main
```

#### Programa 2: Operadores Lógicos con Corto Circuito
```compiscript
function main(): void {
  let x: integer; let y: integer;
  if (x < 100 || (x > 200 && x != y)) x = 0;
}
```

**Código Intermedio:**
```tac
FUNCTION main:
t0 := fp[0] < 100
IF t0 > 0 GOTO IF_TRUE_0
GOTO OR_CONT_0
OR_CONT_0:
t1 := fp[0] > 200
IF t1 > 0 GOTO AND_CONT_0
GOTO IF_END_0
AND_CONT_0:
t2 := fp[0] != fp[4]
IF t2 > 0 GOTO IF_TRUE_0
GOTO IF_END_0
IF_TRUE_0:
fp[0] := 0
IF_END_0:
END FUNCTION main
```

**Explicación:**
- **OR (||)**: Si el primer operando es verdadero, se salta al bloque true
- **AND (&&)**: Si el primer operando es falso, se salta al final
- Se generan etiquetas intermedias para manejar el corto circuito

#### Programa 3: Operador de Negación
```compiscript
function main(): void {
  let a: integer; let b: integer;
  if (!(a <= b)) a = b;
}
```

**Código Intermedio:**
```tac
FUNCTION main:
t0 := fp[0] <= fp[4]
IF t0 > 0 GOTO IF_FALSE_0   ; !(a<=b) → true si no saltamos
GOTO IF_TRUE_0
IF_FALSE_0:
GOTO IF_END_0
IF_TRUE_0:
fp[0] := fp[4]
IF_END_0:
END FUNCTION main
```

**Explicación:**
- La negación invierte la lógica de salto
- Si `a <= b` es verdadero, saltamos a `IF_FALSE_0` (no ejecutar el bloque)
- Si `a <= b` es falso, ejecutamos el bloque en `IF_TRUE_0`

## Decisiones de Diseño Importantes

### 1. **Gestión de Temporales**
- Se generan automáticamente con el patrón `t0, t1, t2, ...`
- Cada expresión compleja usa un nuevo temporal
- Los temporales se reutilizan entre instrucciones

### 2. **Etiquetas Únicas**
- Cada estructura de control usa un ID único
- Formato: `TIPO_ID` (ej: `IF_TRUE_0`, `WHILE_START_1`)
- Evita conflictos en estructuras anidadas

### 3. **Convención de Parámetros**
- En métodos de instancia: primer parámetro siempre es `this`
- Parámetros se evalúan de izquierda a derecha
- Se almacenan en orden inverso en el stack (fp[-1], fp[-2], ...)

### 4. **Corto Circuito en Expresiones Booleanas**
- `||`: Si el primer operando es verdadero, no evalúa el segundo
- `&&`: Si el primer operando es falso, no evalúa el segundo
- Mejora eficiencia y maneja casos como división por cero

### 5. **Gestión de Objetos**
- Los objetos se tratan como referencias/punteros
- Los campos se acceden por offset calculado en tiempo de compilación
- No se genera código para inicialización de objetos (se asume válido)

## Limitaciones y Supuestos

1. **Objetos Válidos**: Se asume que los objetos están correctamente inicializados
2. **Sin Garbage Collection**: No se genera código para manejo de memoria
3. **Tipos Simples**: Solo se manejan `integer` y `boolean`
4. **Sin Herencia**: Las clases son independientes
5. **Stack Ilimitado**: No se verifica overflow del stack

## Conclusión

Este diseño de lenguaje intermedio TAC proporciona una representación clara y sistemática del código Compiscript, facilitando tanto la comprensión como la posterior generación de código objeto. La estructura uniforme y las convenciones consistentes permiten una implementación robusta y mantenible del compilador.