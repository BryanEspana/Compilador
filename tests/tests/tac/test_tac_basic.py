"""
Basic tests for Three-Address Code (TAC) generation
"""

import sys
import os
# Add the program directory to the path to import TAC modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from TACInstruction import TACGenerator, TACOperation, TACInstruction

def test_basic_arithmetic():
    """Test basic arithmetic operations"""
    print("=== Testing Basic Arithmetic Operations ===")
    
    generator = TACGenerator()
    
    # Test: result = a + b
    generator.add_add("t1", "a", "b")
    
    # Test: result = c * d
    generator.add_mul("t2", "c", "d")
    
    # Test: result = (a + b) * (c - d)
    generator.add_add("t3", "a", "b")
    generator.add_sub("t4", "c", "d")
    generator.add_mul("result", "t3", "t4")
    
    # Test: result = -x
    generator.add_neg("t5", "x")
    
    generator.print_instructions()
    print()

def test_comparison_operations():
    """Test comparison operations"""
    print("=== Testing Comparison Operations ===")
    
    generator = TACGenerator()
    
    # Test: result = a == b
    generator.add_eq("t1", "a", "b")
    
    # Test: result = x < y
    generator.add_lt("t2", "x", "y")
    
    # Test: result = p >= q
    generator.add_ge("t3", "p", "q")
    
    generator.print_instructions()
    print()

def test_logical_operations():
    """Test logical operations"""
    print("=== Testing Logical Operations ===")
    
    generator = TACGenerator()
    
    # Test: result = a && b
    generator.add_and("t1", "a", "b")
    
    # Test: result = x || y
    generator.add_or("t2", "x", "y")
    
    # Test: result = !z
    generator.add_not("t3", "z")
    
    generator.print_instructions()
    print()

def test_control_flow():
    """Test control flow operations"""
    print("=== Testing Control Flow Operations ===")
    
    generator = TACGenerator()
    
    # Test: if (x > 0) { ... }
    generator.add_gt("t1", "x", "0")
    generator.add_if_false("t1", "L1")
    generator.add_comment("if body")
    generator.add_goto("L2")
    generator.add_label("L1")
    generator.add_comment("else body")
    generator.add_label("L2")
    
    generator.print_instructions()
    print()

def test_function_operations():
    """Test function operations"""
    print("=== Testing Function Operations ===")
    
    generator = TACGenerator()
    
    # Test: function call
    generator.add_param("arg1")
    generator.add_param("arg2")
    generator.add_call("add", 2, "result")
    
    # Test: return statement
    generator.add_return("result")
    
    generator.print_instructions()
    print()

def test_array_operations():
    """Test array operations"""
    print("=== Testing Array Operations ===")
    
    generator = TACGenerator()
    
    # Test: result = arr[i]
    generator.add_array_access("t1", "arr", "i")
    
    # Test: arr[j] = value
    generator.add_array_assign("arr", "j", "value")
    
    generator.print_instructions()
    print()

def test_object_operations():
    """Test object operations"""
    print("=== Testing Object Operations ===")
    
    generator = TACGenerator()
    
    # Test: result = obj.property
    generator.add_object_access("t1", "obj", "property")
    
    # Test: obj.field = value
    generator.add_object_assign("obj", "field", "value")
    
    # Test: obj = new ClassName
    generator.add_new_object("obj", "ClassName")
    
    generator.print_instructions()
    print()

def test_string_operations():
    """Test string operations"""
    print("=== Testing String Operations ===")
    
    generator = TACGenerator()
    
    # Test: result = str1 + str2
    generator.add_concat("result", "str1", "str2")
    
    generator.print_instructions()
    print()

def test_input_output():
    """Test input/output operations"""
    print("=== Testing Input/Output Operations ===")
    
    generator = TACGenerator()
    
    # Test: print statement
    generator.add_print("message")
    
    # Test: read statement
    generator.add_read("input_var")
    
    generator.print_instructions()
    print()

def test_complex_expression():
    """Test complex expression generation"""
    print("=== Testing Complex Expression ===")
    
    generator = TACGenerator()
    
    # Test: result = (a + b) * (c - d) / e
    generator.add_comment("Complex expression: (a + b) * (c - d) / e")
    
    # Step 1: t1 = a + b
    generator.add_add("t1", "a", "b")
    
    # Step 2: t2 = c - d
    generator.add_sub("t2", "c", "d")
    
    # Step 3: t3 = t1 * t2
    generator.add_mul("t3", "t1", "t2")
    
    # Step 4: result = t3 / e
    generator.add_div("result", "t3", "e")
    
    generator.print_instructions()
    print()

def test_temp_variable_generation():
    """Test temporary variable generation"""
    print("=== Testing Temporary Variable Generation ===")
    
    generator = TACGenerator()
    
    # Generate some temporary variables
    temp1 = generator.generate_temp_var()
    temp2 = generator.generate_temp_var()
    temp3 = generator.generate_temp_var("x")
    
    print(f"Generated temps: {temp1}, {temp2}, {temp3}")
    
    # Use them in instructions
    generator.add_add(temp1, "a", "b")
    generator.add_mul(temp2, "c", "d")
    generator.add_sub(temp3, temp1, temp2)
    
    generator.print_instructions()
    print()

def test_label_generation():
    """Test label generation"""
    print("=== Testing Label Generation ===")
    
    generator = TACGenerator()
    
    # Generate some labels
    label1 = generator.generate_label()
    label2 = generator.generate_label()
    label3 = generator.generate_label("loop")
    
    print(f"Generated labels: {label1}, {label2}, {label3}")
    
    # Use them in instructions
    generator.add_label(label1)
    generator.add_comment("Start of loop")
    generator.add_goto(label2)
    generator.add_label(label2)
    generator.add_comment("End of loop")
    
    generator.print_instructions()
    print()

def run_all_tests():
    """Run all TAC tests"""
    print("🧪 Running Three-Address Code (TAC) Tests")
    print("=" * 50)
    
    test_basic_arithmetic()
    test_comparison_operations()
    test_logical_operations()
    test_control_flow()
    test_function_operations()
    test_array_operations()
    test_object_operations()
    test_string_operations()
    test_input_output()
    test_complex_expression()
    test_temp_variable_generation()
    test_label_generation()
    
    print("✅ All TAC tests completed!")

if __name__ == "__main__":
    run_all_tests()
