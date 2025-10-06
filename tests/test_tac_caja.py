import sys
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from TACCodeGenerator import TACCodeGenerator

def test_tac_generation(source_file):
    """Test TAC generation for a source file"""
    try:
        print(f"Generating TAC for: {source_file}")
        print("=" * 50)
        
        # Parse the input
        input_stream = FileStream(source_file)
        lexer = CompiscriptLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = CompiscriptParser(stream)
        
        # Parse the program
        tree = parser.program()
        
        if parser.getNumberOfSyntaxErrors() > 0:
            print(f"[ERROR] Syntax errors: {parser.getNumberOfSyntaxErrors()}")
            return
        
        print("[OK] Parsing completed successfully")
        
        # Generate TAC
        print("\n[INFO] Generating Three-Address Code...")
        tac_generator = TACCodeGenerator()
        
        # Walk the parse tree
        walker = ParseTreeWalker()
        walker.walk(tac_generator, tree)
        
        # Print generated TAC
        print("\n[INFO] Generated TAC Code:")
        print("=" * 30)
        print(tac_generator.get_tac_code())
        print("=" * 30)
        
    except Exception as e:
        print(f"[ERROR] TAC generation failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_tac_caja.py <source_file.cps>")
    else:
        test_tac_generation(sys.argv[1])