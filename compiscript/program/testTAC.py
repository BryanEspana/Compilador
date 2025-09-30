"""
Test Suite TAC - Verificación de Código Intermedio
Ejecuta TODOS los programas del README_TAC_LANGUAGE.md para verificar
que se genere el código TAC esperado según las especificaciones.
"""

import sys
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from TACCodeGenerator import TACCodeGenerator

def test_tac_program(code: str, expected: str, test_name: str):
    """
    Prueba un programa Compiscript y compara el TAC generado con el esperado
    """
    print(f"\n{'='*80}")
    print(f"PRUEBA: {test_name}")
    print(f"{'='*80}")
    
    print("CÓDIGO FUENTE:")
    print(code.strip())
    
    try:
        # Análisis léxico y sintáctico
        input_stream = InputStream(code)
        lexer = CompiscriptLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = CompiscriptParser(stream)
        
        # Parsear el programa
        tree = parser.program()
        
        # Verificar errores de sintaxis
        if parser.getNumberOfSyntaxErrors() > 0:
            print(f"\nERROR: {parser.getNumberOfSyntaxErrors()} errores de sintaxis")
            return False
        
        # Generar TAC
        tac_generator = TACCodeGenerator(emit_params=True)
        walker = ParseTreeWalker()
        walker.walk(tac_generator, tree)
        
        # Obtener código TAC generado
        generated_tac = tac_generator.get_tac_code()
        
        print(f"\nCÓDIGO TAC GENERADO:")
        print("-" * 40)
        if generated_tac.strip():
            for i, line in enumerate(generated_tac.split('\n'), 1):
                if line.strip():
                    print(f"{i:3d}: {line}")
        else:
            print("(Sin código TAC generado)")
        
        print(f"\nCÓDIGO TAC ESPERADO:")
        print("-" * 40)
        for i, line in enumerate(expected.strip().split('\n'), 1):
            if line.strip():
                print(f"{i:3d}: {line}")
        
        # Comparar resultado (simplificado - solo líneas funcionales)
        generated_lines = [line.strip() for line in generated_tac.split('\n') 
                          if line.strip() and not line.strip().startswith('//')]
        expected_lines = [line.strip() for line in expected.strip().split('\n') 
                         if line.strip()]
        
        # Filtrar líneas del programa wrapper
        functional_generated = []
        in_function = False
        for line in generated_lines:
            if line.startswith('FUNCTION'):
                in_function = True
                functional_generated.append(line)
            elif line.startswith('END FUNCTION'):
                functional_generated.append(line)
                in_function = False
            elif in_function:
                functional_generated.append(line)
        
        if functional_generated == expected_lines:
            print(f"\nEXITO: El código TAC coincide con lo esperado")
            return True
        else:
            print(f"\nFALLO: El código TAC no coincide")
            print("\nDIFERENCIAS:")
            print("Esperado vs Generado:")
            max_len = max(len(expected_lines), len(functional_generated))
            for i in range(max_len):
                exp = expected_lines[i] if i < len(expected_lines) else "---"
                gen = functional_generated[i] if i < len(functional_generated) else "---"
                symbol = "OK" if exp == gen else "XX"
                print(f"{symbol} {i+1:2d}: {exp}")
                if exp != gen:
                    print(f"     {i+1:2d}: {gen}")
            return False
            
    except Exception as e:
        print(f"\nERROR: Excepción durante la generación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Ejecuta TODOS los casos de prueba exactos del README_TAC_LANGUAGE.md"""
    
    tests_passed = 0
    total_tests = 0
    
    print("INICIANDO SUITE DE PRUEBAS TAC COMPLETA")
    print("Verificando TODOS los ejemplos exactos del README_TAC_LANGUAGE.md")
    
    # ========== 1. ATRIBUTOS Y MÉTODOS EN CLASES ==========
    
    # Programa 1: Acceso a campos
    total_tests += 1
    code1 = """
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
"""
    expected1 = """FUNCTION sum:
t0 := fp[-1][0] + fp[-1][4]
RETURN t0
END FUNCTION sum

FUNCTION main:
t0 := fp[0][0] + fp[0][4]
fp[4] := t0
END FUNCTION main"""
    if test_tac_program(code1, expected1, "1.1 - Atributos y Métodos - Acceso a campos"):
        tests_passed += 1
    
    # Programa 2: Llamada a método con parámetro
    total_tests += 1
    code2 = """
class Caja {
  var v: integer;
  function setv(a: integer): void { v = a; }
}

function main(): void {
  let c: Caja;
  // c válido
  c.setv(10);
}
"""
    expected2 = """FUNCTION setv:
fp[-1][0] := fp[-2]
RETURN 0
END FUNCTION setv

FUNCTION main:
PARAM fp[0]
PARAM 10
CALL setv,2
t0 := R
END FUNCTION main"""
    if test_tac_program(code2, expected2, "1.2 - Atributos y Métodos - Llamada con parámetro"):
        tests_passed += 1
    
    # Programa 3: Método con retorno
    total_tests += 1
    code3 = """
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
"""
    expected3 = """FUNCTION add:
t0 := fp[-1][0] + fp[-2]
fp[-1][0] := t0
RETURN t0
END FUNCTION add

FUNCTION main:
PARAM fp[0]
PARAM 5
CALL add,2
t0 := R
fp[4] := t0
END FUNCTION main"""
    if test_tac_program(code3, expected3, "1.3 - Atributos y Métodos - Método con retorno"):
        tests_passed += 1
    
    # ========== 2. ESTRUCTURAS DE CONTROL ==========
    
    # Programa 1: If simple
    total_tests += 1
    code4 = """
function main(): void {
  let x: integer; let y: integer;
  if (x < y) { x = y; }
}
"""
    expected4 = """FUNCTION main:
t0 := fp[0] < fp[4]
IF t0 > 0 GOTO IF_TRUE_0
GOTO IF_END_0
IF_TRUE_0:
fp[0] := fp[4]
IF_END_0:
END FUNCTION main"""
    if test_tac_program(code4, expected4, "2.1 - Estructuras de Control - If simple"):
        tests_passed += 1
    
    # Programa 2: If-else
    total_tests += 1
    code5 = """
function main(): void {
  let a: integer; let b: integer; let m: integer;
  if (a < b) { m = a; } else { m = b; }
}
"""
    expected5 = """FUNCTION main:
t0 := fp[0] < fp[4]
IF t0 > 0 GOTO IF_TRUE_0
GOTO IF_FALSE_0
IF_TRUE_0:
fp[8] := fp[0]
GOTO IF_END_0
IF_FALSE_0:
fp[8] := fp[4]
IF_END_0:
END FUNCTION main"""
    if test_tac_program(code5, expected5, "2.2 - Estructuras de Control - If-else"):
        tests_passed += 1
    
    # Programa 3: While
    total_tests += 1
    code6 = """
function main(): void {
  let i: integer;
  i = 0;
  while (i <= 3) { i = i + 1; }
}
"""
    expected6 = """FUNCTION main:
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
END FUNCTION main"""
    if test_tac_program(code6, expected6, "2.3 - Estructuras de Control - While loop"):
        tests_passed += 1
    
    # ========== 3. LLAMADAS A MÉTODOS DE OBJETOS ==========
    
    # Programa 1: Método simple
    total_tests += 1
    code7 = """
class C { function id(a: integer): integer { return a; } }
function main(): void { let c: C; let r: integer; r = c.id(7); }
"""
    expected7 = """FUNCTION id:
RETURN fp[-2]
END FUNCTION id

FUNCTION main:
PARAM fp[0]
PARAM 7
CALL id,2
t0 := R
fp[4] := t0
END FUNCTION main"""
    if test_tac_program(code7, expected7, "3.1 - Llamadas a Métodos - Método simple"):
        tests_passed += 1
    
    # Programa 2: Método con múltiples parámetros
    total_tests += 1
    code8 = """
class Math { function sum(a: integer, b: integer): integer { return a + b; } }
function main(): void { let m: Math; let x: integer; x = m.sum(2,3); }
"""
    expected8 = """FUNCTION sum:
t0 := fp[-2] + fp[-3]
RETURN t0
END FUNCTION sum

FUNCTION main:
PARAM fp[0]
PARAM 2
PARAM 3
CALL sum,3
t0 := R
fp[4] := t0
END FUNCTION main"""
    if test_tac_program(code8, expected8, "3.2 - Llamadas a Métodos - Múltiples parámetros"):
        tests_passed += 1
    
    # Programa 3: Método que modifica estado
    total_tests += 1
    code9 = """
class P { var x: integer; function inc(): integer { x = x + 1; return x; } }
function main(): void { let p: P; let v: integer; v = p.inc(); }
"""
    expected9 = """FUNCTION inc:
t0 := fp[-1][0] + 1
fp[-1][0] := t0
RETURN t0
END FUNCTION inc

FUNCTION main:
PARAM fp[0]
CALL inc,1
t0 := R
fp[4] := t0
END FUNCTION main"""
    if test_tac_program(code9, expected9, "3.3 - Llamadas a Métodos - Modificación de estado"):
        tests_passed += 1
    
    # ========== 4. ÁMBITOS (SCOPING) Y SHADOWING ==========
    
    # Programa 1: Shadowing global
    total_tests += 1
    code10 = """
var a: integer;
function main(): void {
  let a: integer;   // sombrea a la global
  a = 1;            // usa la local
}
"""
    expected10 = """FUNCTION main:
fp[0] := 1
END FUNCTION main"""
    if test_tac_program(code10, expected10, "4.1 - Ámbitos - Variable shadowing"):
        tests_passed += 1
    
    # Programa 2: Variables con nombres distintos
    total_tests += 1
    code11 = """
var g: integer;
function main(): void {
  let g_local: integer;
  g = 10;
  g_local = g + 1;
}
"""
    expected11 = """FUNCTION main:
G[0] := 10
t0 := G[0] + 1
fp[0] := t0
END FUNCTION main"""
    if test_tac_program(code11, expected11, "4.2 - Ámbitos - Global y local distintas"):
        tests_passed += 1
    
    # Programa 3: Shadow + uso explícito (sin calificador especial)
    total_tests += 1
    code11b = """
var a: integer;
function main(): void {
  let a: integer;   // shadow
  a = 2;
}
"""
    expected11b = """FUNCTION main:
fp[0] := 2
END FUNCTION main"""
    if test_tac_program(code11b, expected11b, "4.3 - Ámbitos - Shadow sin calificador"):
        tests_passed += 1
    
    # ========== 5. EXPRESIONES ARITMÉTICAS ==========
    
    # Programa 1: Precedencia de operadores
    total_tests += 1
    code12 = """
var a: integer;
function main(): void {
  let b: integer; let c: integer; let d: integer;
  a = b + c * d;
}
"""
    expected12 = """FUNCTION main:
t0 := fp[4] * fp[8]
t1 := fp[0] + t0
G[0] := t1
END FUNCTION main"""
    if test_tac_program(code12, expected12, "5.1 - Expresiones Aritméticas - Precedencia"):
        tests_passed += 1
    
    # Programa 2: Expresiones con paréntesis
    total_tests += 1
    code13 = """
function main(): void {
  let x: integer; let y: integer; let z: integer;
  z = (x - y) * (x + y);
}
"""
    expected13 = """FUNCTION main:
t0 := fp[0] - fp[4]
t1 := fp[0] + fp[4]
t2 := t0 * t1
fp[8] := t2
END FUNCTION main"""
    if test_tac_program(code13, expected13, "5.2 - Expresiones Aritméticas - Paréntesis"):
        tests_passed += 1
    
    # Programa 3: División con expresión compleja
    total_tests += 1
    code14 = """
function main(): void {
  let a: integer; let b: integer; let r: integer;
  r = a / (b + 1);
}
"""
    expected14 = """FUNCTION main:
t0 := fp[4] + 1
t1 := fp[0] / t0
fp[8] := t1
END FUNCTION main"""
    if test_tac_program(code14, expected14, "5.3 - Expresiones Aritméticas - División compleja"):
        tests_passed += 1
    
    # ========== 6. EXPRESIONES BOOLEANAS ==========
    
    # Programa 1: Operador relacional
    total_tests += 1
    code15 = """
function main(): void {
  let x: integer; let y: integer;
  if (x == y) { x = 0; }
}
"""
    expected15 = """FUNCTION main:
t0 := fp[0] == fp[4]
IF t0 > 0 GOTO IF_TRUE_0
GOTO IF_END_0
IF_TRUE_0:
fp[0] := 0
IF_END_0:
END FUNCTION main"""
    if test_tac_program(code15, expected15, "6.1 - Expresiones Booleanas - Operador relacional"):
        tests_passed += 1
    
    # Programa 2: Operadores lógicos con corto circuito
    total_tests += 1
    code16 = """
function main(): void {
  let x: integer; let y: integer;
  if (x < 100 || (x > 200 && x != y)) { x = 0; }
}
"""
    expected16 = """FUNCTION main:
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
END FUNCTION main"""
    if test_tac_program(code16, expected16, "6.2 - Expresiones Booleanas - Corto circuito complejo"):
        tests_passed += 1
    
    # Programa 3: Operador de negación
    total_tests += 1
    code17 = """
function main(): void {
  let a: integer; let b: integer;
  if (!(a <= b)) { a = b; }
}
"""
    expected17 = """FUNCTION main:
t0 := fp[0] <= fp[4]
IF t0 > 0 GOTO IF_FALSE_0
GOTO IF_TRUE_0
IF_FALSE_0:
GOTO IF_END_0
IF_TRUE_0:
fp[0] := fp[4]
IF_END_0:
END FUNCTION main"""
    if test_tac_program(code17, expected17, "6.3 - Expresiones Booleanas - Operador de negación"):
        tests_passed += 1
    
    # ========== RESUMEN ==========
    
    print(f"\n{'='*80}")
    print(f"RESUMEN DE PRUEBAS")
    print(f"{'='*80}")
    print(f"Pruebas exitosas: {tests_passed}")
    print(f"Pruebas fallidas: {total_tests - tests_passed}")
    print(f"Total ejecutadas: {total_tests}")
    print(f"Porcentaje éxito: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print(f"\nTODAS LAS PRUEBAS PASARON! El generador TAC funciona correctamente.")
        return True
    else:
        print(f"\nHay {total_tests - tests_passed} pruebas que necesitan corrección.")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)