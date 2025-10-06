"""
Test directo para el operador de negación
"""
import sys
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from TACCodeGenerator import TACCodeGenerator

# Código de prueba con negación
code = """
function main(): void {
  let a: integer; let b: integer;
  if (!(a <= b)) { a = b; }
}
"""

print("CÓDIGO FUENTE:")
print(code)
print("\nCÓDIGO TAC GENERADO:")
print("-" * 40)

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
        print(f"[ERROR] Errores de sintaxis: {parser.getNumberOfSyntaxErrors()}")
    else:
        # Generar TAC
        tac_generator = TACCodeGenerator(emit_params=True)
        walker = ParseTreeWalker()
        walker.walk(tac_generator, tree)
        
        # Mostrar el código TAC generado
        tac_code = tac_generator.get_tac_code()
        if tac_code.strip():
            for i, line in enumerate(tac_code.split('\n'), 1):
                if line.strip():
                    print(f"{i:3d}: {line}")
        else:
            print("(Sin código TAC generado)")
            
except Exception as e:
    print(f"[ERROR] Error durante la generación: {str(e)}")
    import traceback
    traceback.print_exc()