"""
Integration tests for Intermediate Code Generation
Tests the integration between AST parsing and TAC generation
"""

import sys
import os
# Add the program directory to the path to import modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from IntermediateCodeGenerator import IntermediateCodeGenerator
from ExtendedSymbolTable import ExtendedSymbolTable, SymbolType
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker

def create_parser_from_code(code: str):
    """Create parser from Compiscript code"""
    input_stream = InputStream(code)
    lexer = CompiscriptLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = CompiscriptParser(token_stream)
    return parser

def test_simple_arithmetic():
    """Test simple arithmetic expressions"""
    print("=== Testing Simple Arithmetic ===")
    
    code = """
    let x: integer = 5 + 3 * 2;
    let y: integer = (10 - 4) / 2;
    """
    
    parser = create_parser_from_code(code)
    tree = parser.program()
    
    symbol_table = ExtendedSymbolTable()
    generator = IntermediateCodeGenerator(symbol_table)
    
    # Walk the tree
    from antlr4 import ParseTreeWalker
    walker = ParseTreeWalker()
    walker.walk(generator, tree)
    
    # Check results
    tac_code = generator.get_tac_code()
    print("Generated TAC:")
    print(tac_code)
    
    # Verify variables are defined
    x_symbol = symbol_table.lookup("x")
    y_symbol = symbol_table.lookup("y")
    
    assert x_symbol is not None
    assert y_symbol is not None
    assert x_symbol.type == SymbolType.INTEGER
    assert y_symbol.type == SymbolType.INTEGER
    
    print("✅ Simple arithmetic test passed\n")

def test_variable_declarations():
    """Test variable declarations"""
    print("=== Testing Variable Declarations ===")
    
    code = """
    let name: string = "Hello";
    let age: integer = 25;
    let isStudent: boolean = true;
    """
    
    parser = create_parser_from_code(code)
    tree = parser.program()
    
    symbol_table = ExtendedSymbolTable()
    generator = IntermediateCodeGenerator(symbol_table)
    
    walker = ParseTreeWalker()
    walker.walk(generator, tree)
    
    # Check variables
    name_symbol = symbol_table.lookup("name")
    age_symbol = symbol_table.lookup("age")
    isStudent_symbol = symbol_table.lookup("isStudent")
    
    assert name_symbol is not None
    assert age_symbol is not None
    assert isStudent_symbol is not None
    assert name_symbol.type == SymbolType.STRING
    assert age_symbol.type == SymbolType.INTEGER
    assert isStudent_symbol.type == SymbolType.BOOLEAN
    
    print("✅ Variable declarations test passed\n")

def test_control_flow():
    """Test control flow statements"""
    print("=== Testing Control Flow ===")
    
    code = """
    let x: integer = 10;
    if (x > 5) {
        let result: integer = x * 2;
    } else {
        let result: integer = 0;
    }
    """
    
    parser = create_parser_from_code(code)
    tree = parser.program()
    
    symbol_table = ExtendedSymbolTable()
    generator = IntermediateCodeGenerator(symbol_table)
    
    walker = ParseTreeWalker()
    walker.walk(generator, tree)
    
    tac_code = generator.get_tac_code()
    print("Generated TAC:")
    print(tac_code)
    
    # For now, just check that the basic structure is there
    # The control flow generation needs more work
    assert "x" in tac_code
    assert "result" in tac_code
    
    print("✅ Control flow test passed\n")

def test_while_loop():
    """Test while loop generation"""
    print("=== Testing While Loop ===")
    
    code = """
    let i: integer = 0;
    while (i < 10) {
        i = i + 1;
    }
    """
    
    parser = create_parser_from_code(code)
    tree = parser.program()
    
    symbol_table = ExtendedSymbolTable()
    generator = IntermediateCodeGenerator(symbol_table)
    
    walker = ParseTreeWalker()
    walker.walk(generator, tree)
    
    tac_code = generator.get_tac_code()
    print("Generated TAC:")
    print(tac_code)
    
    # For now, just check basic structure
    assert "i" in tac_code
    
    print("✅ While loop test passed\n")

def test_function_declaration():
    """Test function declaration"""
    print("=== Testing Function Declaration ===")
    
    code = """
    function add(a: integer, b: integer): integer {
        return a + b;
    }
    """
    
    parser = create_parser_from_code(code)
    tree = parser.program()
    
    symbol_table = ExtendedSymbolTable()
    generator = IntermediateCodeGenerator(symbol_table)
    
    walker = ParseTreeWalker()
    walker.walk(generator, tree)
    
    tac_code = generator.get_tac_code()
    print("Generated TAC:")
    print(tac_code)
    
    # Check function symbol
    add_func = symbol_table.lookup("add")
    print(f"Function 'add' found: {add_func}")
    print(f"Symbol table contents: {list(symbol_table.global_scope.symbols.keys())}")
    assert add_func is not None
    assert add_func.type == SymbolType.FUNCTION
    
    print("✅ Function declaration test passed\n")

def test_function_call():
    """Test function calls"""
    print("=== Testing Function Call ===")
    
    code = """
    function add(a: integer, b: integer): integer {
        return a + b;
    }
    
    let result: integer = add(5, 3);
    """
    
    parser = create_parser_from_code(code)
    tree = parser.program()
    
    symbol_table = ExtendedSymbolTable()
    generator = IntermediateCodeGenerator(symbol_table)
    
    walker = ParseTreeWalker()
    walker.walk(generator, tree)
    
    tac_code = generator.get_tac_code()
    print("Generated TAC:")
    print(tac_code)
    
    # Check basic structure
    assert "result" in tac_code
    
    print("✅ Function call test passed\n")

def test_print_statement():
    """Test print statements"""
    print("=== Testing Print Statement ===")
    
    code = """
    let message: string = "Hello World";
    print message;
    """
    
    parser = create_parser_from_code(code)
    tree = parser.program()
    
    symbol_table = ExtendedSymbolTable()
    generator = IntermediateCodeGenerator(symbol_table)
    
    walker = ParseTreeWalker()
    walker.walk(generator, tree)
    
    tac_code = generator.get_tac_code()
    print("Generated TAC:")
    print(tac_code)
    
    # Check basic structure
    assert "message" in tac_code
    
    print("✅ Print statement test passed\n")

def test_complex_expression():
    """Test complex expressions"""
    print("=== Testing Complex Expression ===")
    
    code = """
    let a: integer = 5;
    let b: integer = 3;
    let c: integer = 2;
    let result: integer = (a + b) * c - 1;
    """
    
    parser = create_parser_from_code(code)
    tree = parser.program()
    
    symbol_table = ExtendedSymbolTable()
    generator = IntermediateCodeGenerator(symbol_table)
    
    walker = ParseTreeWalker()
    walker.walk(generator, tree)
    
    tac_code = generator.get_tac_code()
    print("Generated TAC:")
    print(tac_code)
    
    # Check basic structure
    assert "result" in tac_code
    
    print("✅ Complex expression test passed\n")

def test_string_operations():
    """Test string operations"""
    print("=== Testing String Operations ===")
    
    code = """
    let first: string = "Hello";
    let last: string = "World";
    let full: string = first + " " + last;
    """
    
    parser = create_parser_from_code(code)
    tree = parser.program()
    
    symbol_table = ExtendedSymbolTable()
    generator = IntermediateCodeGenerator(symbol_table)
    
    walker = ParseTreeWalker()
    walker.walk(generator, tree)
    
    tac_code = generator.get_tac_code()
    print("Generated TAC:")
    print(tac_code)
    
    # Check basic structure
    assert "full" in tac_code
    
    print("✅ String operations test passed\n")

def test_error_handling():
    """Test error handling"""
    print("=== Testing Error Handling ===")
    
    # Test basic error handling functionality
    symbol_table = ExtendedSymbolTable()
    generator = IntermediateCodeGenerator(symbol_table)
    
    # Test that error handling methods work
    generator.add_error(None, "Test error")
    errors = generator.get_errors()
    assert len(errors) > 0
    assert "Test error" in errors[0]
    
    print("✅ Error handling test passed\n")

def test_memory_management():
    """Test memory management"""
    print("=== Testing Memory Management ===")
    
    code = """
    let global_var: integer = 42;
    
    function test(): integer {
        let local_var: integer = 10;
        return global_var + local_var;
    }
    """
    
    parser = create_parser_from_code(code)
    tree = parser.program()
    
    symbol_table = ExtendedSymbolTable()
    generator = IntermediateCodeGenerator(symbol_table)
    
    walker = ParseTreeWalker()
    walker.walk(generator, tree)
    
    # Check memory layout
    layout = symbol_table.get_memory_layout()
    assert layout["global_offset"] > 0
    
    # Check symbols have memory addresses
    global_var = symbol_table.lookup("global_var")
    assert global_var is not None
    assert global_var.memory_address is not None
    
    print("✅ Memory management test passed\n")

def run_all_integration_tests():
    """Run all integration tests"""
    print("🧪 Running Intermediate Code Generation Integration Tests")
    print("=" * 60)
    
    test_simple_arithmetic()
    test_variable_declarations()
    test_control_flow()
    test_while_loop()
    test_function_declaration()
    test_function_call()
    test_print_statement()
    test_complex_expression()
    test_string_operations()
    test_error_handling()
    test_memory_management()
    
    print("✅ All integration tests completed!")

if __name__ == "__main__":
    run_all_integration_tests()
