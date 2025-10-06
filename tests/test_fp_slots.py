"""
Test para verificar que los slots fp se asignen correctamente
"""

import sys
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from TACCodeGenerator import TACCodeGenerator

def test_fp_slots():
    # Código que debería mostrar fp[8] en función main si hay 8 variables globales antes
    code = """
        var a: integer = 1;
        var b: integer = 2;
        var c: integer = 3;
        var d: integer = 4;
        var e: integer = 5;
        var f: integer = 6;
        var g: integer = 7;
        var h: integer = 8;
        
        function main(): integer {
            var x: integer = 0;
            return x;
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
    test_fp_slots()