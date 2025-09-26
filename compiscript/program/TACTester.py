"""
Driver de prueba para el generador TAC
Prueba la generación de código de tres direcciones con diferentes casos
"""

import sys
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from TACCodeGenerator import TACCodeGenerator

def test_tac_generation(code: str, description: str, emit_params: bool = True):
    """Prueba la generación TAC para un código dado"""
    print(f"\n{'='*60}")
    print(f"PRUEBA: {description}")
    print(f"{'='*60}")
    print("CÓDIGO FUENTE:")
    print(code)
    print(f"\nCÓDIGO TAC (emit_params={emit_params}):")
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
        tac_generator = TACCodeGenerator(emit_params=emit_params)
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

def main():
    """Función principal con casos de prueba"""
    
    # Caso 1: Operaciones aritméticas básicas
    test_tac_generation("""
        var a: integer = 5;
        var b: integer = 10;
        var c: integer = a + b * 2;
    """, "Operaciones aritméticas básicas")
    
    # Caso 2: Expresiones relacionales y lógicas
    test_tac_generation("""
        var x: integer = 10;
        var y: integer = 20;
        var result: boolean = x < y && y > 15;
    """, "Expresiones relacionales y lógicas")
    
    # Caso 3: Statement if-else
    test_tac_generation("""
        var age: integer = 18;
        if (age >= 18) {
            var message: string = "Adult";
        } else {
            var message: string = "Minor";
        }
    """, "Statement if-else")
    
    # Caso 4: Loop while
    test_tac_generation("""
        var i: integer = 0;
        while (i < 5) {
            i = i + 1;
        }
    """, "Loop while")
    
    # Caso 5: Función simple
    test_tac_generation("""
        function add(a: integer, b: integer): integer {
            return a + b;
        }
        
        var result: integer = add(5, 3);
    """, "Función simple con llamada")
    
    # Caso 6: Función sin parámetros en CALL (emit_params=false)
    test_tac_generation("""
        function getValue(): integer {
            return 42;
        }
        
        var x: integer = getValue();
    """, "Función sin emit_params", emit_params=False)
    
    # Caso 7: Programa más complejo
    test_tac_generation("""
        function factorial(n: integer): integer {
            if (n <= 1) {
                return 1;
            } else {
                return n * factorial(n - 1);
            }
        }
        
        var num: integer = 5;
        var fact: integer = factorial(num);
        print(fact);
    """, "Factorial recursivo")

if __name__ == '__main__':
    main()