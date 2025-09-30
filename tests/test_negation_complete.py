"""
Test completo para el operador de negación con múltiples casos
"""
import sys
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from TACCodeGenerator import TACCodeGenerator

def test_negation_case(code: str, description: str):
    print(f"\n{'='*50}")
    print(f"CASO: {description}")
    print(f"{'='*50}")
    print("CÓDIGO FUENTE:")
    print(code)
    print("\nCÓDIGO TAC GENERADO:")
    print("-" * 30)
    
    try:
        input_stream = InputStream(code)
        lexer = CompiscriptLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = CompiscriptParser(stream)
        tree = parser.program()
        
        if parser.getNumberOfSyntaxErrors() > 0:
            print(f"[ERROR] Errores de sintaxis: {parser.getNumberOfSyntaxErrors()}")
            return
        
        tac_generator = TACCodeGenerator(emit_params=True)
        walker = ParseTreeWalker()
        walker.walk(tac_generator, tree)
        
        tac_code = tac_generator.get_tac_code()
        if tac_code.strip():
            for i, line in enumerate(tac_code.split('\n'), 1):
                if line.strip():
                    print(f"{i:3d}: {line}")
        else:
            print("(Sin código TAC generado)")
            
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")

# Caso 1: Negación básica
test_negation_case("""
function main(): void {
  let a: integer; let b: integer;
  if (!(a <= b)) { a = b; }
}
""", "Negación básica !(a <= b)")

# Caso 2: Negación con variable booleana
test_negation_case("""
function test(): void {
  let flag: boolean;
  if (!flag) { flag = true; }
}
""", "Negación de variable booleana !flag")

# Caso 3: Negación con expresión compleja
test_negation_case("""
function complex(): void {
  let x: integer; let y: integer; let z: integer;
  if (!(x > y && z < 10)) { x = y + z; }
}
""", "Negación de expresión compleja !(x > y && z < 10)")

# Caso 4: Negación con else
test_negation_case("""
function withElse(): void {
  let a: integer; let b: integer;
  if (!(a == b)) { 
    a = 1; 
  } else { 
    b = 2; 
  }
}
""", "Negación con else !(a == b)")