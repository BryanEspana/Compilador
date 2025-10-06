"""
Test para verificar correcta separación de ámbitos globales y locales
"""

import sys
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from TACCodeGenerator import TACCodeGenerator

def test_scopes():
    code = """
let a: integer;

function main(){
    let b: integer;
    let a: integer;
    let c: integer;
    let d: integer;

    a = 1;
}

function suma(){
    let suma: integer;
    suma = 2;
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
                    
        print(f"\nVariables globales: {tac_generator.global_variables}")
        print(f"Ámbitos: {tac_generator.scope_variables}")
        print(f"Offset global actual: {tac_generator.current_global_offset}")
                    
    except Exception as e:
        print(f"[ERROR] Error durante la generación: {str(e)}")
        import traceback
        traceback.print_exc()

def test_simple_scope():
    """Test simple para verificar que la 'a' local se refiere correctamente"""
    code = """
let a: integer;

function main(){
    let b: integer;
    let a: integer;
    let c: integer;
    let d: integer;

    a = 1;
}
    """
    
    print("\n" + "="*60)
    print("TEST SIMPLE - La 'a' local debería estar en fp[4]:")
    print("="*60)
    
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
                    
        # Verificar resultado esperado
        if "fp[4] := 1" in tac_code:
            print("\n✓ CORRECTO: La variable local 'a' está en fp[4]")
        else:
            print("\n✗ INCORRECTO: La variable local 'a' no está en fp[4]")
            
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_scopes()
    test_simple_scope()