#!/usr/bin/env python3

import sys
import os

# Agregar el directorio actual al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from TACCodeGenerator import TACCodeGenerator
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from antlr4.tree.Tree import ParseTreeWalker

def test_precedence():
    """Test específico para verificar la precedencia de operadores"""
    
    print("=== TESTING OPERATOR PRECEDENCE ===")
    
    # Test case 1: a = b + c + d (suma simple)
    code1 = """
function main(){
    let b: integer;
    let a: integer;
    let c: integer;
    let d: integer;

    a = b + c + d;
}
"""
    
    # Test case 2: a = b + c * d (con multiplicación)
    code2 = """
function main(){
    let b: integer;
    let a: integer;
    let c: integer;
    let d: integer;

    a = b + c * d;
}
"""
    
    test_cases = [
        ("b + c + d", code1),
        ("b + c * d", code2)
    ]
    
    for description, code in test_cases:
        print(f"\n--- Test: {description} ---")
        
        try:
            # Lexer y Parser
            input_stream = InputStream(code)
            lexer = CompiscriptLexer(input_stream)
            token_stream = CommonTokenStream(lexer)
            parser = CompiscriptParser(token_stream)
            
            # Parse
            tree = parser.program()
            
            # Generar TAC
            generator = TACCodeGenerator()
            walker = ParseTreeWalker()
            walker.walk(generator, tree)
            
            # Mostrar resultado
            tac_code = generator.get_tac_code()
            print("Generated TAC:")
            print(tac_code)
            
            # Mostrar mapping de variables
            print("\nVariable slots:")
            for var_name, offset in generator.local_variables.items():
                print(f"  {var_name} -> fp[{offset}]")
                
            # Debug info
            print(f"\nDebug info:")
            print(f"  Temporary counter: {generator.temp_counter}")
            print(f"  Local offset counter: {generator.current_local_offset}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        print("=" * 50)

if __name__ == "__main__":
    test_precedence()