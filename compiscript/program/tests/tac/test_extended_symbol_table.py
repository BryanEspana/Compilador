"""
Tests for Extended Symbol Table with code generation support
"""

import sys
import os
# Add the program directory to the path to import modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from ExtendedSymbolTable import (
    ExtendedSymbolTable, ExtendedSymbol, ExtendedFunctionSymbol, ExtendedClassSymbol,
    ActivationRecord, TempVariableManager, MemoryType, SymbolType
)

def test_basic_symbol_creation():
    """Test basic extended symbol creation"""
    print("=== Testing Basic Extended Symbol Creation ===")
    
    # Test integer symbol
    int_symbol = ExtendedSymbol("x", SymbolType.INTEGER, value=42)
    assert int_symbol.name == "x"
    assert int_symbol.type == SymbolType.INTEGER
    assert int_symbol.value == 42
    assert int_symbol.memory_type == MemoryType.GLOBAL
    assert not int_symbol.is_temporary
    
    # Test string symbol
    str_symbol = ExtendedSymbol("message", SymbolType.STRING, value="Hello")
    assert str_symbol.name == "message"
    assert str_symbol.type == SymbolType.STRING
    assert str_symbol.value == "Hello"
    
    print("✅ Basic symbol creation test passed\n")

def test_memory_management():
    """Test memory management for symbols"""
    print("=== Testing Memory Management ===")
    
    symbol_table = ExtendedSymbolTable()
    
    # Define global variables
    x = ExtendedSymbol("x", SymbolType.INTEGER)
    y = ExtendedSymbol("y", SymbolType.FLOAT)
    z = ExtendedSymbol("z", SymbolType.STRING)
    
    symbol_table.define(x)
    symbol_table.define(y)
    symbol_table.define(z)
    
    # Check memory addresses
    assert x.memory_address == "global_0"
    assert y.memory_address == "global_4"
    assert z.memory_address == "global_12"
    
    # Check memory types
    assert x.memory_type == MemoryType.GLOBAL
    assert y.memory_type == MemoryType.GLOBAL
    assert z.memory_type == MemoryType.GLOBAL
    
    print("✅ Memory management test passed\n")

def test_temporary_variables():
    """Test temporary variable management"""
    print("=== Testing Temporary Variables ===")
    
    symbol_table = ExtendedSymbolTable()
    
    # Allocate temporary variables
    temp1 = symbol_table.allocate_temporary(SymbolType.INTEGER)
    temp2 = symbol_table.allocate_temporary(SymbolType.FLOAT)
    temp3 = symbol_table.allocate_temporary(SymbolType.BOOLEAN)
    
    # Check temporary properties
    assert temp1.is_temporary
    assert temp1.temp_id == 1
    assert temp1.name == "t1"
    assert temp1.type == SymbolType.INTEGER
    
    assert temp2.is_temporary
    assert temp2.temp_id == 2
    assert temp2.name == "t2"
    assert temp2.type == SymbolType.FLOAT
    
    assert temp3.is_temporary
    assert temp3.temp_id == 3
    assert temp3.name == "t3"
    assert temp3.type == SymbolType.BOOLEAN
    
    # Test freeing temporaries
    symbol_table.free_temporary(temp2)
    assert not temp2.is_live
    
    # Test reusing freed temporaries
    temp4 = symbol_table.allocate_temporary(SymbolType.STRING)
    assert temp4.temp_id == 2  # Should reuse freed temp2's ID
    assert temp4.name == "t2"
    
    print("✅ Temporary variables test passed\n")

def test_activation_records():
    """Test activation records for functions"""
    print("=== Testing Activation Records ===")
    
    symbol_table = ExtendedSymbolTable()
    
    # Create a function
    func = ExtendedFunctionSymbol("add", SymbolType.INTEGER)
    func.add_parameter("a", SymbolType.INTEGER)
    func.add_parameter("b", SymbolType.INTEGER)
    
    # Create activation record
    ar = symbol_table.create_function_activation_record(func)
    
    assert ar.function_name == "add"
    assert ar.return_type == SymbolType.INTEGER
    assert len(ar.parameters) == 0  # Parameters added separately
    
    # Add parameters to activation record
    param_a = ExtendedSymbol("a", SymbolType.INTEGER)
    param_b = ExtendedSymbol("b", SymbolType.INTEGER)
    ar.add_parameter(param_a)
    ar.add_parameter(param_b)
    
    assert len(ar.parameters) == 2
    assert param_a.memory_type == MemoryType.PARAMETER
    assert param_b.memory_type == MemoryType.PARAMETER
    
    # Add local variables
    local_var = ExtendedSymbol("result", SymbolType.INTEGER)
    ar.add_local_variable(local_var)
    
    assert len(ar.local_variables) == 1
    assert local_var.memory_type == MemoryType.LOCAL
    assert local_var.stack_offset == 8  # After 2 parameters (4 bytes each)
    
    print("✅ Activation records test passed\n")

def test_scope_management():
    """Test scope management with extended symbols"""
    print("=== Testing Scope Management ===")
    
    symbol_table = ExtendedSymbolTable()
    
    # Global scope
    global_var = ExtendedSymbol("global_var", SymbolType.INTEGER)
    symbol_table.define(global_var)
    assert global_var.scope_level == 0
    
    # Enter function scope
    func_scope = symbol_table.enter_scope("function_scope")
    local_var = ExtendedSymbol("local_var", SymbolType.STRING)
    symbol_table.define(local_var)
    assert local_var.scope_level == 1
    
    # Enter nested scope
    nested_scope = symbol_table.enter_scope("nested_scope")
    nested_var = ExtendedSymbol("nested_var", SymbolType.BOOLEAN)
    symbol_table.define(nested_var)
    assert nested_var.scope_level == 2
    
    # Test lookup
    found_global = symbol_table.lookup("global_var")
    assert found_global is not None
    assert found_global.scope_level == 0
    
    found_local = symbol_table.lookup("local_var")
    assert found_local is not None
    assert found_local.scope_level == 1
    
    # Exit scopes
    symbol_table.exit_scope()  # Exit nested
    symbol_table.exit_scope()  # Exit function
    
    print("✅ Scope management test passed\n")

def test_class_symbols():
    """Test extended class symbols"""
    print("=== Testing Extended Class Symbols ===")
    
    # Create a class
    person_class = ExtendedClassSymbol("Person")
    
    # Add attributes
    name_attr = ExtendedSymbol("name", SymbolType.STRING)
    age_attr = ExtendedSymbol("age", SymbolType.INTEGER)
    
    person_class.add_attribute(name_attr)
    person_class.add_attribute(age_attr)
    
    # Calculate object layout
    person_class.calculate_object_layout()
    
    assert person_class.object_size > 0
    assert "name" in person_class.attribute_offsets
    assert "age" in person_class.attribute_offsets
    
    print("✅ Class symbols test passed\n")

def test_label_generation():
    """Test label generation"""
    print("=== Testing Label Generation ===")
    
    symbol_table = ExtendedSymbolTable()
    
    # Generate labels
    label1 = symbol_table.generate_label()
    label2 = symbol_table.generate_label()
    label3 = symbol_table.generate_label("loop")
    
    assert label1 == "L1"
    assert label2 == "L2"
    assert label3 == "loop3"
    
    print("✅ Label generation test passed\n")

def test_memory_layout():
    """Test memory layout information"""
    print("=== Testing Memory Layout ===")
    
    symbol_table = ExtendedSymbolTable()
    
    # Add some symbols
    x = ExtendedSymbol("x", SymbolType.INTEGER)
    y = ExtendedSymbol("y", SymbolType.FLOAT)
    symbol_table.define(x)
    symbol_table.define(y)
    
    # Get memory layout
    layout = symbol_table.get_memory_layout()
    
    assert "global_offset" in layout
    assert "active_temps" in layout
    assert "activation_records" in layout
    assert layout["global_offset"] > 0
    
    print("✅ Memory layout test passed\n")

def test_temp_variable_manager():
    """Test temporary variable manager independently"""
    print("=== Testing Temp Variable Manager ===")
    
    temp_manager = TempVariableManager()
    
    # Allocate temporaries
    temp1 = temp_manager.allocate_temp(SymbolType.INTEGER, 0)
    temp2 = temp_manager.allocate_temp(SymbolType.FLOAT, 0)
    temp3 = temp_manager.allocate_temp(SymbolType.BOOLEAN, 1)
    
    assert temp1.temp_id == 1
    assert temp2.temp_id == 2
    assert temp3.temp_id == 3
    assert temp3.scope_level == 1
    
    # Test live temporaries
    live_temps = temp_manager.get_live_temps()
    assert len(live_temps) == 3
    
    # Free a temporary
    temp_manager.free_temp(2)
    live_temps = temp_manager.get_live_temps()
    assert len(live_temps) == 2
    assert not temp2.is_live
    
    # Allocate new temporary (should reuse ID 2)
    temp4 = temp_manager.allocate_temp(SymbolType.STRING, 0)
    assert temp4.temp_id == 2
    
    print("✅ Temp variable manager test passed\n")

def test_complex_scenario():
    """Test complex scenario with multiple features"""
    print("=== Testing Complex Scenario ===")
    
    symbol_table = ExtendedSymbolTable()
    
    # Global variables
    global_x = ExtendedSymbol("global_x", SymbolType.INTEGER)
    symbol_table.define(global_x)
    
    # Function definition
    func = ExtendedFunctionSymbol("calculate", SymbolType.INTEGER)
    func.add_parameter("a", SymbolType.INTEGER)
    func.add_parameter("b", SymbolType.INTEGER)
    
    # Create activation record
    ar = symbol_table.create_function_activation_record(func)
    
    # Add parameters
    param_a = ExtendedSymbol("a", SymbolType.INTEGER)
    param_b = ExtendedSymbol("b", SymbolType.INTEGER)
    ar.add_parameter(param_a)
    ar.add_parameter(param_b)
    
    # Enter function scope
    func_scope = symbol_table.enter_scope("calculate")
    
    # Local variables
    local_result = ExtendedSymbol("result", SymbolType.INTEGER)
    symbol_table.define(local_result)
    
    # Temporary variables
    temp1 = symbol_table.allocate_temporary(SymbolType.INTEGER)
    temp2 = symbol_table.allocate_temporary(SymbolType.INTEGER)
    
    # Generate labels
    start_label = symbol_table.generate_label("start")
    end_label = symbol_table.generate_label("end")
    
    # Verify everything
    assert global_x.memory_type == MemoryType.GLOBAL
    assert param_a.memory_type == MemoryType.PARAMETER
    assert local_result.memory_type == MemoryType.LOCAL
    assert temp1.is_temporary
    assert start_label == "start1"
    assert end_label == "end2"
    
    # Get memory layout
    layout = symbol_table.get_memory_layout()
    assert layout["active_temps"] == 2
    assert layout["activation_records"] == 1
    
    print("✅ Complex scenario test passed\n")

def run_all_extended_symbol_table_tests():
    """Run all extended symbol table tests"""
    print("🧪 Running Extended Symbol Table Tests")
    print("=" * 50)
    
    test_basic_symbol_creation()
    test_memory_management()
    test_temporary_variables()
    test_activation_records()
    test_scope_management()
    test_class_symbols()
    test_label_generation()
    test_memory_layout()
    test_temp_variable_manager()
    test_complex_scenario()
    
    print("✅ All Extended Symbol Table tests completed!")

if __name__ == "__main__":
    run_all_extended_symbol_table_tests()
