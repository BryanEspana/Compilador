"""
Test para verificar desplazamientos correctos basados en tamaño de tipos
"""

import sys
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from TACCodeGenerator import TACCodeGenerator

def test_offsets():
    code = """
function main(){
    let n: integer;
    let f: integer;
    let i: integer;
    let d;
    //n = 0;
    f = 6;
    //n = f + i * d;
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
        
        # Verificar desplazamientos esperados
        expected = {
            'n': 0,   # integer: 0
            'f': 4,   # integer: 4 
            'i': 8,   # integer: 8
            'd': 12   # default integer: 12
        }
        
        print("\nDesplazamientos esperados vs reales:")
        for var, expected_offset in expected.items():
            if var in tac_generator.variable_slots:
                real_offset = tac_generator.variable_slots[var]
                status = "✓" if real_offset == expected_offset else "✗"
                print(f"  {var}: esperado={expected_offset}, real={real_offset} {status}")
                    
    except Exception as e:
        print(f"[ERROR] Error durante la generación: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_offsets()