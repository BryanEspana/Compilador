# Three-Address Code (TAC) Tests

Este directorio contiene todos los tests relacionados con la generación y parsing de Three-Address Code (TAC) para el compilador Compiscript.

## 📁 Estructura de Archivos

```
tests/tac/
├── __init__.py              # Paquete Python
├── README.md                # Este archivo
├── run_tac_tests.py         # Script principal para ejecutar todos los tests
├── test_tac_basic.py        # Tests para generación básica de TAC
└── test_tac_parser.py       # Tests para parsing de TAC
```

## 🧪 Tests Disponibles

### 1. **test_tac_basic.py** - Generación de TAC
Tests para validar la generación correcta de instrucciones TAC:

- **Operaciones Aritméticas**: `+`, `-`, `*`, `/`, `%`, `neg`
- **Operaciones de Comparación**: `==`, `!=`, `<`, `<=`, `>`, `>=`
- **Operaciones Lógicas**: `&&`, `||`, `!`
- **Control de Flujo**: `if_false`, `if_true`, `goto`, `label`
- **Funciones**: `call`, `return`, `param`
- **Arrays**: `array_access`, `array_assign`
- **Objetos**: `object_access`, `object_assign`, `new_object`
- **Strings**: `concat`
- **I/O**: `print`, `read`
- **Expresiones Complejas**: Precedencia de operadores
- **Variables Temporales**: Generación automática
- **Etiquetas**: Generación automática

### 2. **test_tac_parser.py** - Parsing de TAC
Tests para validar el parsing correcto de instrucciones TAC:

- **Operaciones Básicas**: Parsing de operaciones aritméticas
- **Control de Flujo**: Parsing de `if`, `goto`, `label`
- **Funciones**: Parsing de `call`, `return`, `param`
- **Arrays**: Parsing de acceso y asignación de arrays
- **Objetos**: Parsing de acceso y asignación de propiedades
- **Comentarios**: Parsing de comentarios `//`
- **Manejo de Errores**: Detección de instrucciones inválidas
- **Expresiones Complejas**: Parsing de expresiones anidadas

## 🚀 Cómo Ejecutar los Tests

### Ejecutar Todos los Tests
```bash
cd compiscript/program/tests/tac
python run_tac_tests.py
```

### Ejecutar Tests Específicos
```bash
# Solo tests de generación
python test_tac_basic.py

# Solo tests de parsing
python test_tac_parser.py
```

## 📊 Resultados Esperados

Los tests deben mostrar:
- ✅ **Generación de TAC**: 12 categorías de tests
- ✅ **Parsing de TAC**: 8 categorías de tests
- ✅ **Sin errores**: Todos los tests pasan exitosamente

## 🔧 Estructura de TAC

### Instrucciones Soportadas

```tac
// Asignación
result = value

// Operaciones aritméticas
result = arg1 + arg2
result = arg1 - arg2
result = arg1 * arg2
result = arg1 / arg2
result = arg1 % arg2
result = -arg1

// Operaciones de comparación
result = arg1 == arg2
result = arg1 != arg2
result = arg1 < arg2
result = arg1 <= arg2
result = arg1 > arg2
result = arg1 >= arg2

// Operaciones lógicas
result = arg1 && arg2
result = arg1 || arg2
result = !arg1

// Control de flujo
label:
goto label
if_false condition goto label
if_true condition goto label

// Funciones
param value
call function_name, num_params
return [value]

// Arrays
result = array[index]
array[index] = value

// Objetos
result = object.property
object.property = value
result = new ClassName

// Strings
result = str1 + str2

// I/O
print value
read variable
```

## 🎯 Próximos Pasos

1. **Integración con Analizador Semántico**: Conectar TAC con el AST
2. **Optimizaciones**: Implementar optimizaciones básicas de TAC
3. **Generación de Código**: Convertir TAC a código assembler
4. **Tests de Integración**: Tests end-to-end con código Compiscript

## 📝 Notas de Desarrollo

- Los tests están organizados por funcionalidad
- Cada test es independiente y puede ejecutarse por separado
- Los tests incluyen validación de errores y casos edge
- La estructura permite fácil extensión para nuevas funcionalidades
