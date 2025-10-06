"""
Test para verificar que los temporales se reinicien por función
"""
import sys
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from TACCodeGenerator import TACCodeGenerator

# Test con múltiples funciones
code = """
class Punto {
  var x: integer;
  var y: integer;

  function sum(): integer {
    return x + y;
  }
}

function main(): void {
  let p: Punto;
  let s: integer;
  s = p.x + p.y;
}
"""

print("CÓDIGO FUENTE:")
print(code)

try:
    input_stream = InputStream(code)
    lexer = CompiscriptLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = CompiscriptParser(stream)
    tree = parser.program()
    
    if parser.getNumberOfSyntaxErrors() > 0:
        print(f"ERROR: {parser.getNumberOfSyntaxErrors()} errores de sintaxis")
    else:
        tac_generator = TACCodeGenerator(emit_params=True)
        walker = ParseTreeWalker()
        walker.walk(tac_generator, tree)
        
        tac_code = tac_generator.get_tac_code()
        print("\nCÓDIGO TAC GENERADO:")
        for i, line in enumerate(tac_code.split('\n'), 1):
            if line.strip():
                print(f"{i:3d}: {line}")
                
        print("\nCÓDIGO TAC ESPERADO:")
        print("FUNCTION sum:")
        print("t0 := fp[-1][0] + fp[-1][4]")
        print("RETURN t0")
        print("END FUNCTION sum")
        print("")
        print("FUNCTION main:")  
        print("t0 := fp[0][0] + fp[0][4]")  # Debería ser t0, no t1
        print("fp[4] := t0")
        print("END FUNCTION main")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()