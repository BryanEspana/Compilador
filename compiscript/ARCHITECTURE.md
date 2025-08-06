# 🏗️ Arquitectura del Compilador Compiscript

## 📋 Resumen General

Este documento describe la arquitectura del compilador Compiscript, implementado como parte del proyecto de análisis semántico. El compilador está construido usando ANTLR para el análisis sintáctico y Python para la implementación del análisis semántico.

## 🧩 Componentes Principales

### 1. **Analizador Léxico y Sintáctico (ANTLR)**
- **Archivo**: `Compiscript.g4`
- **Generados**: `CompiscriptLexer.py`, `CompiscriptParser.py`, `CompiscriptListener.py`
- **Función**: Convierte el código fuente en un árbol sintáctico abstracto (AST)

### 2. **Tabla de Símbolos** (`SymbolTable.py`)
- **Clases principales**:
  - `SymbolTable`: Gestiona todos los ámbitos y símbolos
  - `Scope`: Representa un ámbito específico (global, función, clase, bloque)
  - `Symbol`: Representa un símbolo básico (variable, constante)
  - `FunctionSymbol`: Representa funciones con parámetros y tipo de retorno
  - `ClassSymbol`: Representa clases con métodos y atributos

**Características**:
- Manejo jerárquico de ámbitos
- Resolución de nombres con búsqueda en ámbitos padre
- Detección de redeclaraciones
- Soporte para funciones anidadas y closures

### 3. **Analizador Semántico** (`SemanticAnalyzer.py`)
- **Patrón**: ANTLR Listener
- **Función**: Recorre el AST y valida reglas semánticas
- **Validaciones implementadas**:
  - Declaración y uso de variables
  - Verificación de tipos en asignaciones
  - Validación de funciones y parámetros
  - Control de flujo (break/continue en loops, return en funciones)
  - Manejo de clases y herencia
  - Verificación de constantes

### 4. **Evaluador de Expresiones** (`ExpressionEvaluator.py`)
- **Función**: Evalúa expresiones y verifica compatibilidad de tipos
- **Capacidades**:
  - Evaluación de operadores aritméticos, lógicos y de comparación
  - Verificación de tipos en operaciones
  - Manejo de precedencia de operadores
  - Validación de llamadas a funciones y acceso a propiedades

### 5. **Driver Principal** (`Driver.py`)
- **Función**: Punto de entrada del compilador
- **Proceso**:
  1. Análisis léxico y sintáctico
  2. Construcción del AST
  3. Análisis semántico
  4. Reporte de errores

### 6. **Sistema de Testing** (`TestRunner.py`)
- **Función**: Ejecuta batería de pruebas automatizadas
- **Casos de prueba**:
  - `test_success.cps`: Código válido que debe pasar
  - `test_errors.cps`: Código inválido que debe fallar

## 🔄 Flujo de Compilación

```
Código Fuente (.cps)
        ↓
   Análisis Léxico (CompiscriptLexer)
        ↓
   Análisis Sintáctico (CompiscriptParser)
        ↓
   Árbol Sintáctico Abstracto (AST)
        ↓
   Análisis Semántico (SemanticAnalyzer + ExpressionEvaluator)
        ↓
   Tabla de Símbolos + Lista de Errores
        ↓
   Reporte de Resultados
```

## 🎯 Validaciones Semánticas Implementadas

### ✅ Sistema de Tipos
- Verificación de tipos en operaciones aritméticas (`+`, `-`, `*`, `/`, `%`)
- Verificación de tipos en operaciones lógicas (`&&`, `||`, `!`)
- Compatibilidad de tipos en comparaciones (`==`, `!=`, `<`, `<=`, `>`, `>=`)
- Verificación de tipos en asignaciones
- Inicialización obligatoria de constantes

### ✅ Manejo de Ámbito
- Resolución de nombres según ámbito local/global
- Error por uso de variables no declaradas
- Prohibición de redeclaración en el mismo ámbito
- Control de acceso en bloques anidados
- Entornos separados para funciones, clases y bloques

### ✅ Funciones y Procedimientos
- Validación de número y tipo de argumentos
- Validación de tipo de retorno
- Soporte para recursión
- Detección de múltiples declaraciones

### ✅ Control de Flujo
- Condiciones booleanas en `if`, `while`, `do-while`, `for`
- Validación de `break` y `continue` solo en bucles
- Validación de `return` solo en funciones

### ✅ Clases y Objetos
- Validación de herencia
- Verificación de constructores
- Manejo básico de `this`

### ✅ Generales
- Detección de código después de `return`, `break`
- Verificación de expresiones semánticamente válidas
- Validación de declaraciones duplicadas

## 📊 Métricas de Implementación

### Cobertura de Validaciones
- **Implementadas**: ~80% de las reglas requeridas
- **Funcionales**: Sistema de tipos, ámbitos, funciones, control de flujo
- **En desarrollo**: Manejo completo de objetos y arrays

### Rendimiento de Tests
- **Tests ejecutados**: 3
- **Tests pasando**: 2 (66.7%)
- **Errores detectados**: 29 errores semánticos en casos de prueba

## 🛠️ Tecnologías Utilizadas

- **ANTLR 4.13.1**: Generación de lexer y parser
- **Python 3.x**: Implementación del análisis semántico
- **Patrón Visitor/Listener**: Recorrido del AST
- **Programación Orientada a Objetos**: Diseño modular

## 🔧 Configuración y Uso

### Requisitos
```bash
pip install antlr4-python3-runtime==4.13.0
```

### Generación del Parser
```bash
java -jar antlr-4.13.1-complete.jar -Dlanguage=Python3 Compiscript.g4
```

### Compilación
```bash
python Driver.py programa.cps
```

### Testing
```bash
python TestRunner.py                    # Todos los tests
python TestRunner.py archivo.cps        # Test específico
```

## 🚀 Extensiones Futuras

1. **Completar validaciones de objetos**: Mejorar manejo de clases y métodos
2. **Optimización de tipos**: Inferencia de tipos más sofisticada
3. **Generación de código**: Extensión a fases posteriores del compilador
4. **IDE mejorado**: Interfaz gráfica más completa
5. **Debugging**: Información de depuración en errores

## 👥 Contribuciones

Este compilador fue desarrollado como proyecto académico para el curso de Compiladores, implementando las especificaciones del lenguaje Compiscript con enfoque en análisis semántico robusto y manejo de errores.
