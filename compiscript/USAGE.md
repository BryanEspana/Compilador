# 📖 Guía de Uso - Compilador Compiscript

## 🚀 Inicio Rápido

### Prerrequisitos
- Python 3.x instalado
- Java (para generar archivos ANTLR)

### Instalación
1. **Instalar dependencias:**
   ```bash
   pip install antlr4-python3-runtime==4.13.0
   ```

2. **Generar archivos del parser:**
   ```bash
   cd program
   java -jar ../antlr-4.13.1-complete.jar -Dlanguage=Python3 Compiscript.g4
   ```

## 💻 Formas de Uso

### 1. Compilador de Línea de Comandos

**Compilar un archivo:**
```bash
python Driver.py programa.cps
```

**Ejemplo de salida exitosa:**
```
Compiling: programa.cps
==================================================
[OK] Syntax analysis completed successfully
[INFO] Starting semantic analysis...
[OK] Semantic analysis completed successfully
[INFO] Symbol Table:
=== SYMBOL TABLE ===
...
```

**Ejemplo de salida con errores:**
```
Compiling: programa.cps
==================================================
[OK] Syntax analysis completed successfully
[INFO] Starting semantic analysis...
[ERROR] Semantic analysis failed:
=== SEMANTIC ERRORS ===
ERROR: Line 5:10 - Variable 'x' already declared in current scope
ERROR: Line 8:15 - Cannot assign string to integer variable
=====================
```

### 2. IDE Gráfico

**Ejecutar el IDE:**
```bash
python CompiscriptIDE.py
```

**Características del IDE:**
- ✅ Editor de código con numeración de líneas
- ✅ Resaltado básico de sintaxis
- ✅ Compilación integrada (F5)
- ✅ Gestión de archivos (Nuevo, Abrir, Guardar)
- ✅ Panel de salida con errores coloreados
- ✅ Código de ejemplo precargado

### 3. Sistema de Testing

**Ejecutar todos los tests:**
```bash
python TestRunner.py
```

**Ejecutar un test específico:**
```bash
python TestRunner.py tests/test_success.cps
python TestRunner.py tests/test_errors.cps
```

## 📝 Sintaxis del Lenguaje Compiscript

### Declaración de Variables
```cps
// Variables con tipo explícito
let edad: integer = 25;
let nombre: string = "Juan";
let activo: boolean = true;

// Variables con inferencia de tipo
let contador = 0;
let mensaje = "Hola mundo";

// Constantes (obligatorio inicializar)
const PI: integer = 314;
const MAX_SIZE: integer = 100;
```

### Funciones
```cps
// Función con parámetros y tipo de retorno
function suma(a: integer, b: integer): integer {
    return a + b;
}

// Función sin tipo de retorno (void)
function saludar(nombre: string) {
    print("Hola " + nombre);
}

// Llamada a función
let resultado: integer = suma(5, 3);
saludar("María");
```

### Arrays
```cps
// Arrays unidimensionales
let numeros: integer[] = [1, 2, 3, 4, 5];
let palabras: string[] = ["hola", "mundo"];

// Arrays multidimensionales
let matriz: integer[][] = [[1, 2], [3, 4]];

// Acceso a elementos
let primero: integer = numeros[0];
let elemento: integer = matriz[0][1];
```

### Control de Flujo
```cps
// Condicionales
if (edad >= 18) {
    print("Mayor de edad");
} else {
    print("Menor de edad");
}

// Bucles
while (contador < 10) {
    contador = contador + 1;
}

do {
    print("Al menos una vez");
} while (false);

for (let i: integer = 0; i < 5; i = i + 1) {
    print("Iteración: " + i);
}

foreach (numero in numeros) {
    print("Número: " + numero);
}

// Switch
switch (edad) {
    case 18:
        print("Recién mayor de edad");
    case 21:
        print("Puede beber");
    default:
        print("Otra edad");
}
```

### Clases y Objetos
```cps
// Definición de clase
class Persona {
    let nombre: string;
    let edad: integer;
    
    function constructor(nombre: string, edad: integer) {
        this.nombre = nombre;
        this.edad = edad;
    }
    
    function saludar(): string {
        return "Hola, soy " + this.nombre;
    }
}

// Herencia
class Estudiante : Persona {
    let carrera: string;
    
    function constructor(nombre: string, edad: integer, carrera: string) {
        this.nombre = nombre;
        this.edad = edad;
        this.carrera = carrera;
    }
    
    function estudiar() {
        print(this.nombre + " está estudiando " + this.carrera);
    }
}

// Instanciación
let persona: Persona = new Persona("Ana", 25);
let estudiante: Estudiante = new Estudiante("Luis", 20, "Ingeniería");

// Uso de métodos
print(persona.saludar());
estudiante.estudiar();
```

### Manejo de Errores
```cps
try {
    let riesgoso: integer = numeros[100]; // Índice fuera de rango
} catch (error) {
    print("Error capturado: " + error);
}
```

## ⚠️ Errores Semánticos Comunes

### 1. Errores de Tipos
```cps
// ❌ Error: Asignación de tipo incompatible
let numero: integer = "texto";

// ❌ Error: Operación aritmética con tipos incompatibles
let resultado: integer = 5 + "hola";

// ✅ Correcto: Concatenación de strings
let mensaje: string = "Número: " + 5;
```

### 2. Errores de Ámbito
```cps
// ❌ Error: Variable no declarada
print(variableNoDeclarada);

// ❌ Error: Redeclaración en el mismo ámbito
let x: integer = 5;
let x: string = "texto"; // Error

// ❌ Error: Uso antes de inicialización
let y: integer;
print(y); // Error
```

### 3. Errores de Control de Flujo
```cps
// ❌ Error: Condición no booleana
if (5) { // Error: debe ser boolean
    print("Esto no funciona");
}

// ❌ Error: break fuera de bucle
break; // Error: debe estar en un bucle

// ❌ Error: return fuera de función
return 5; // Error: debe estar en una función
```

### 4. Errores de Funciones
```cps
// ❌ Error: Número incorrecto de argumentos
function test(a: integer, b: string) { }
test(5); // Error: falta un argumento

// ❌ Error: Tipo de retorno incorrecto
function getNumber(): integer {
    return "no es un número"; // Error
}

// ❌ Error: Función sin return
function calculate(x: integer): integer {
    print("Calculando...");
    // Error: falta return
}
```

## 🧪 Casos de Prueba

### Archivo de Prueba Exitoso (`tests/test_success.cps`)
Contiene código válido que debe compilar sin errores:
- Declaraciones de variables y constantes correctas
- Funciones con tipos apropiados
- Control de flujo con condiciones booleanas
- Clases con herencia válida

### Archivo de Prueba con Errores (`tests/test_errors.cps`)
Contiene 25+ errores semánticos diferentes para validar:
- Errores de tipos
- Errores de ámbito
- Errores de control de flujo
- Errores de funciones y clases

## 📊 Interpretación de Resultados

### Compilación Exitosa
```
[OK] Syntax analysis completed successfully
[INFO] Starting semantic analysis...
[OK] Semantic analysis completed successfully
```

### Compilación con Errores
```
[ERROR] Semantic analysis failed:
=== SEMANTIC ERRORS ===
ERROR: Line 5:10 - Variable 'count' already declared in current scope
ERROR: Line 8:15 - Cannot assign string to integer variable
ERROR: Line 12:4 - If condition must be boolean, got integer
=====================
```

**Formato de errores:**
- `Line X:Y` - Número de línea y columna
- Descripción clara del error semántico
- Sugerencias implícitas para corrección

## 🔧 Solución de Problemas

### Error: "Module not found"
```bash
pip install antlr4-python3-runtime==4.13.0
```

### Error: "CompiscriptLexer not found"
```bash
java -jar ../antlr-4.13.1-complete.jar -Dlanguage=Python3 Compiscript.g4
```

### Error de codificación Unicode (Windows)
El compilador maneja automáticamente caracteres Unicode, pero si hay problemas, asegúrate de que los archivos estén guardados en UTF-8.

## 📈 Métricas de Validación

El compilador actual detecta:
- ✅ **26 tipos de errores semánticos** diferentes
- ✅ **Validación de tipos** en operaciones y asignaciones
- ✅ **Manejo de ámbitos** con resolución correcta de nombres
- ✅ **Validación de funciones** con parámetros y tipos de retorno
- ✅ **Control de flujo** con verificación de condiciones
- ✅ **Clases y herencia** básica

**Tasa de éxito en tests:** 66.7% (2/3 tests pasan correctamente)

## 🎯 Próximos Pasos

Para mejorar el compilador:
1. Completar validación de objetos y métodos
2. Mejorar inferencia de tipos
3. Agregar más validaciones de arrays
4. Implementar optimizaciones semánticas
5. Agregar generación de código intermedio
