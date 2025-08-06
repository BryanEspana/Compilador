
# 🧪 Compiscript

## 📋 Descripción General

Este lenguaje se encuentra basado en Typescript, por lo que representa un subset del mismo, con algunas diferencias.

---

## 🧰 Instrucciones de Configuración

1. **Construir y Ejecutar el Contenedor Docker:** Desde el directorio raíz, ejecuta el siguiente comando para construir la imagen y lanzar un contenedor interactivo:

   ```bash
   docker build --rm . -t csp-image && docker run --rm -ti -v "$(pwd)/program":/program csp-image
   ```
2. **Entender el Entorno**

   - El directorio `program` se monta dentro del contenedor.
   - Este contiene la **gramática de ANTLR de Compiscript y una versión en BNF**, un archivo `Driver.py` (punto de entrada principal) y un archivo `program.cps` (entrada de prueba con la extensión de archivos de Compiscript).
3. **Generar Archivos de Lexer y Parser:** Dentro del contenedor, compila la gramática ANTLR a Python con:

   ```bash
   antlr -Dlanguage=Python3 Compiscript.g4
   ```
4. **Ejecutar el Analizador**
   Usa el driver para analizar el archivo de prueba:

   ```bash
   python3 Driver.py program.cps
   ```

   - ✅ Si el archivo es sintácticamente correcto, **no se mostrará ningún resultado**.
   - ❌ Si existen errores, ANTLR los mostrará en la consola.

---

## 🧩 Características del Lenguaje

Compiscript soporta los siguientes conceptos fundamentales:

### ✅ Tipos de Datos

```cps
let a: integer = 10;
let b: string = "hola";
let c: boolean = true;
let d = null;
```

### ✅ Literales

```cps
123          // integer
"texto"      // string
true, false  // boolean
null         // nulo
```

### ✅ Expresiones Aritméticas y Lógicas

```cps
let x = 5 + 3 * 2;
let y = !(x < 10 || x > 20);
```

### ✅ Precedencia y Agrupamiento

```cps
let z = (1 + 2) * 3;
```

### ✅ Declaración y Asignación de Variables

```cps
let nombre: string;
nombre = "Compiscript";
```

### ✅ Constantes (`const`)

```cps
const PI: integer = 314;
```

### ✅ Funciones y Parámetros

```cps
function saludar(nombre: string): string {
  return "Hola " + nombre;
}
```

### ✅ Expresiones de Llamada

```cps
let mensaje = saludar("Mundo");
```

### ✅ Acceso a Propiedades (`.`)

```cps
print(dog.nombre);
```

### ✅ Acceso a Elementos de Arreglo (`[]`)

```cps
let lista = [1, 2, 3];
print(lista[0]);
```

### ✅ Arreglos

```cps
let notas: integer[] = [90, 85, 100];
let matriz: integer[][] = [[1, 2], [3, 4]];
```

### ✅ Funciones como Closures

```cps
function crearContador(): integer {
  function siguiente(): integer {
    return 1;
  }
  return siguiente();
}
```

### ✅ Clases y Constructores

```cps
class Animal {
  let nombre: string;

  function constructor(nombre: string) {
    this.nombre = nombre;
  }

  function hablar(): string {
    return this.nombre + " hace ruido.";
  }
}
```

### ✅ Herencia

```cps
class Perro : Animal {
  function hablar(): string {
    return this.nombre + " ladra.";
  }
}
```

### ✅ `this`

```cps
this.nombre = "Firulais";
```

### ✅ Instanciación con `new`

```cps
let perro: Perro = new Perro("Toby");
```

### ✅ Bloques y Ámbitos

```cps
{
  let x = 42;
  print(x);
}
```

### ✅ Control de Flujo

#### `if` / `else`

```cps
if (x > 10) {
  print("Mayor a 10");
} else {
  print("Menor o igual");
}
```

#### `while`

```cps
while (x < 5) {
  x = x + 1;
}
```

#### `do-while`

```cps
do {
  x = x - 1;
} while (x > 0);
```

#### `for`

```cps
for (let i: integer = 0; i < 3; i = i + 1) {
  print(i);
}
```

#### `foreach`

```cps
foreach (item in lista) {
  print(item);
}
```

#### `break` / `continue`

```cps
foreach (n in notas) {
  if (n < 60) continue;
  if (n == 100) break;
  print(n);
}
```

### ✅ `switch / case`

```cps
switch (x) {
  case 1:
    print("uno");
  case 2:
    print("dos");
  default:
    print("otro");
}
```

### ✅ `try / catch`

```cps
try {
  let peligro = lista[100];
} catch (err) {
  print("Error atrapado: " + err);
}
```

### ✅ `return`

```cps
function suma(a: integer, b: integer): integer {
  return a + b;
}
```

### ✅ Recursión

```cps
function factorial(n: integer): integer {
  if (n <= 1) return 1;
  return n * factorial(n - 1);
}
```

---

## 🖥️ IDE de Compiscript

### **Ejecutar el IDE**

Para usar el entorno de desarrollo integrado (IDE) de Compiscript:

```bash
# Navegar al directorio del programa
cd program

# Ejecutar el IDE
python CompiscriptIDE.py
```

### **Características del IDE**

- **Editor de código** con resaltado de sintaxis
- **Compilación en tiempo real** (F5)
- **Detección de errores semánticos** automática
- **Funciones de archivo**: Nuevo, Abrir, Guardar (Ctrl+N, Ctrl+O, Ctrl+S)
- **Panel de salida** para mostrar resultados de compilación
- **Código de ejemplo** precargado

### **Uso del IDE**

1. **Escribir código** en el editor principal
2. **Presionar F5** para compilar
3. **Revisar errores** en el panel de salida
4. **Corregir errores** y volver a compilar

### **Ejemplo de uso en el IDE**

```cps
// Ejemplo de código que puedes escribir en el IDE
const PI: integer = 314;

function calcularArea(radio: integer): integer {
  return PI * radio * radio / 100;
}

let area: integer = calcularArea(5);
print("El área es: " + area);
```

---

## 🧪 Pruebas y Validación

### **Ejecutar las Pruebas**

Para ejecutar la batería completa de pruebas:

```bash
# Ejecutar todas las pruebas
python TestRunner.py

# Ejecutar una prueba específica
python TestRunner.py tests/test_success.cps
```

### **Estado de las Pruebas**

- ✅ **Tests de casos exitosos**: Pasan correctamente
- ✅ **Tests de casos fallidos**: Detectan errores apropiadamente  
- ✅ **Tests de integración**: Funcionan correctamente
- ✅ **Tasa de éxito**: 100%

### **Características Validadas**

- ✅ **Sistema de tipos** completo y funcional
- ✅ **Manejo de ámbitos** y tabla de símbolos
- ✅ **Validación semántica** robusta
- ✅ **Llamadas a métodos** de clase
- ✅ **Operaciones aritméticas** con compatibilidad de tipos
- ✅ **Control de flujo** con validación de condiciones
- ✅ **Estructuras de datos** (arrays, clases)

---

## 📦 Extensión de Archivo

Todos los archivos fuente de Compiscript deben usar la extensión:

```bash
program.cps
```
