import sys
import os
from antlr4 import *
from antlr4.tree.Tree import TerminalNode
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from SemanticAnalyzer import SemanticAnalyzer
from MIPSGenerator import MIPSGenerator

def print_tree(tree, parser, indent=0):
    """Print the parse tree for debugging"""
    if isinstance(tree, TerminalNode):
        print("  " * indent + f"Terminal: {tree.getText()}")
    else:
        rule_name = parser.ruleNames[tree.getRuleIndex()]
        print("  " * indent + f"Rule: {rule_name}")
        for child in tree.children or []:
            print_tree(child, parser, indent + 1)

def main(argv):
    if len(argv) < 2:
        print("Usage: python Driver.py <source_file.cps> [--mips]")
        print("  --mips: Generate MIPS assembly code")
        return
    
    # Check for --mips flag
    generate_mips = '--mips' in argv
    if generate_mips:
        argv.remove('--mips')
    
    try:
        # Lexical and Syntactic Analysis
        print(f"Compiling: {argv[1]}")
        print("=" * 50)
        
        input_stream = FileStream(argv[1])
        lexer = CompiscriptLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = CompiscriptParser(stream)
        
        # Parse the program
        tree = parser.program()
        
        # Check for syntax errors
        if parser.getNumberOfSyntaxErrors() > 0:
            print(f"[ERROR] Syntax errors found: {parser.getNumberOfSyntaxErrors()}")
            return
        
        print("[OK] Syntax analysis completed successfully")
        
        # Semantic Analysis
        print("\n[INFO] Starting semantic analysis...")
        semantic_analyzer = SemanticAnalyzer()
        
        # Walk the parse tree
        walker = ParseTreeWalker()
        walker.walk(semantic_analyzer, tree)
        
        # Report results
        if semantic_analyzer.has_errors():
            print("\n[ERROR] Semantic analysis failed:")
            semantic_analyzer.print_errors()
        else:
            print("\n[OK] Semantic analysis completed successfully")
            print("\n[INFO] Symbol Table:")
            semantic_analyzer.print_symbol_table()
            
            # Generate TAC code
            tac_code = semantic_analyzer.tac_generator.get_tac_code()
            print("\n[INFO] Three-Address Code generated")
            
            # Generate MIPS if requested
            if generate_mips:
                print("\n[INFO] Generating MIPS assembly code...")
                mips_generator = MIPSGenerator()
                mips_code = mips_generator.generate(tac_code)
                
                # Write to file
                base_name = os.path.splitext(os.path.basename(argv[1]))[0]
                mips_filename = f"{base_name}.asm"
                mips_generator.generate_to_file(mips_filename, tac_code)
                
                print(f"[OK] MIPS assembly code written to: {mips_filename}")
                print(f"\n[INFO] MIPS Code Preview (first 20 lines):")
                print("-" * 50)
                lines = mips_code.split('\n')
                for i, line in enumerate(lines[:20], 1):
                    print(f"{i:3d}: {line}")
                if len(lines) > 20:
                    print(f"... ({len(lines) - 20} more lines)")
        
        # Optional: Print parse tree (uncomment for debugging)
        # print("\n[DEBUG] Parse Tree:")
        # print_tree(tree, parser)
        
    except Exception as e:
        print(f"[ERROR] Compilation failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main(sys.argv)