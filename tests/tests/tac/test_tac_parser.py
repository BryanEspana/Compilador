"""
Tests for Three-Address Code (TAC) Parser
"""

import sys
import os
# Add the program directory to the path to import TAC modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from TACParser import TACParser
from TACInstruction import TACOperation

def test_parser_basic_operations():
    """Test parsing basic TAC operations"""
    print("=== Testing Parser - Basic Operations ===")
    
    parser = TACParser()
    
    # Test arithmetic operations
    tac_code = """
t1 = a + b
t2 = c * d
result = t1 - t2
"""
    
    instructions = parser.parse_text(tac_code)
    parser.print_instructions()
    parser.print_errors()
    
    assert len(instructions) == 3
    assert instructions[0].operation == TACOperation.ADD
    assert instructions[1].operation == TACOperation.MUL
    assert instructions[2].operation == TACOperation.SUB
    print("✅ Basic operations parsing test passed\n")

def test_parser_control_flow():
    """Test parsing control flow instructions"""
    print("=== Testing Parser - Control Flow ===")
    
    parser = TACParser()
    
    tac_code = """
L1:
if_false x goto L2
goto L3
L2:
t1 = 0
L3:
"""
    
    instructions = parser.parse_text(tac_code)
    parser.print_instructions()
    parser.print_errors()
    
    assert len(instructions) == 6
    assert instructions[0].operation == TACOperation.LABEL
    assert instructions[1].operation == TACOperation.IF_FALSE
    assert instructions[2].operation == TACOperation.GOTO
    print("✅ Control flow parsing test passed\n")

def test_parser_functions():
    """Test parsing function instructions"""
    print("=== Testing Parser - Functions ===")
    
    parser = TACParser()
    
    tac_code = """
param arg1
param arg2
call add, 2
return result
"""
    
    instructions = parser.parse_text(tac_code)
    parser.print_instructions()
    parser.print_errors()
    
    assert len(instructions) == 4
    assert instructions[0].operation == TACOperation.PARAM
    assert instructions[1].operation == TACOperation.PARAM
    assert instructions[2].operation == TACOperation.CALL
    assert instructions[3].operation == TACOperation.RETURN
    print("✅ Functions parsing test passed\n")

def test_parser_arrays():
    """Test parsing array operations"""
    print("=== Testing Parser - Arrays ===")
    
    parser = TACParser()
    
    tac_code = """
t1 = arr[i]
arr[j] = value
"""
    
    instructions = parser.parse_text(tac_code)
    parser.print_instructions()
    parser.print_errors()
    
    assert len(instructions) == 2
    assert instructions[0].operation == TACOperation.ARRAY_ACCESS
    assert instructions[1].operation == TACOperation.ARRAY_ASSIGN
    print("✅ Arrays parsing test passed\n")

def test_parser_objects():
    """Test parsing object operations"""
    print("=== Testing Parser - Objects ===")
    
    parser = TACParser()
    
    tac_code = """
t1 = obj.property
obj.field = value
obj = new ClassName
"""
    
    instructions = parser.parse_text(tac_code)
    parser.print_instructions()
    parser.print_errors()
    
    assert len(instructions) == 3
    assert instructions[0].operation == TACOperation.OBJECT_ACCESS
    assert instructions[1].operation == TACOperation.OBJECT_ASSIGN
    assert instructions[2].operation == TACOperation.NEW_OBJECT
    print("✅ Objects parsing test passed\n")

def test_parser_comments():
    """Test parsing comments"""
    print("=== Testing Parser - Comments ===")
    
    parser = TACParser()
    
    tac_code = """
// This is a comment
t1 = a + b
// Another comment
t2 = c * d
"""
    
    instructions = parser.parse_text(tac_code)
    parser.print_instructions()
    parser.print_errors()
    
    assert len(instructions) == 4  # 2 comments + 2 instructions
    assert instructions[0].comment == "This is a comment"
    assert instructions[2].comment == "Another comment"
    print("✅ Comments parsing test passed\n")

def test_parser_errors():
    """Test parsing error handling"""
    print("=== Testing Parser - Error Handling ===")
    
    parser = TACParser()
    
    tac_code = """
t1 = a + b
invalid instruction
t2 = c * d
"""
    
    instructions = parser.parse_text(tac_code)
    parser.print_instructions()
    parser.print_errors()
    
    assert len(instructions) == 2  # Only valid instructions
    assert len(parser.errors) >= 1  # At least one error for invalid instruction
    print("✅ Error handling test passed\n")

def test_parser_complex_expression():
    """Test parsing complex expressions"""
    print("=== Testing Parser - Complex Expressions ===")
    
    parser = TACParser()
    
    tac_code = """
// Complex expression: (a + b) * (c - d) / e
t1 = a + b
t2 = c - d
t3 = t1 * t2
result = t3 / e
"""
    
    instructions = parser.parse_text(tac_code)
    parser.print_instructions()
    parser.print_errors()
    
    assert len(instructions) == 5  # 1 comment + 4 instructions
    assert instructions[1].operation == TACOperation.ADD
    assert instructions[2].operation == TACOperation.SUB
    assert instructions[3].operation == TACOperation.MUL
    assert instructions[4].operation == TACOperation.DIV
    print("✅ Complex expressions parsing test passed\n")

def run_all_parser_tests():
    """Run all TAC parser tests"""
    print("🧪 Running Three-Address Code (TAC) Parser Tests")
    print("=" * 50)
    
    test_parser_basic_operations()
    test_parser_control_flow()
    test_parser_functions()
    test_parser_arrays()
    test_parser_objects()
    test_parser_comments()
    test_parser_errors()
    test_parser_complex_expression()
    
    print("✅ All TAC parser tests completed!")

if __name__ == "__main__":
    run_all_parser_tests()
