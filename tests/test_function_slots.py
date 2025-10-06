"""
Test específico para el problema de slots fp en funciones
"""

import sys
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from TACCodeGenerator import TACCodeGenerator

def test_function_fp_slots():
    code = """
function main(){
    let n: integer;
    let f: integer;
    let i: integer; 
    i = 0;
    while(i<=20){
        i = i +1;
        m(i);
    }
}

function m(a: integer): integer{
    return 0;
}
    """
    
    print("CÓDIGO FUENTE:")
    print(code)
    print("\nCÓDIGO TAC:")
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
            return
        
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
                    
        print(f"\nSlots utilizados: {tac_generator.current_slot}")
        print(f"Variable slots: {tac_generator.variable_slots}")
                    
    except Exception as e:
        print(f"[ERROR] Error durante la generación: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_function_fp_slots()