"""
Extended Symbol Table implementation for Compiscript compiler
Supports intermediate code generation with memory addresses, temporary variables, and activation records
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from SymbolTable import SymbolType, Symbol, FunctionSymbol, ClassSymbol, Scope

class MemoryType(Enum):
    """Types of memory allocation"""
    GLOBAL = "global"
    LOCAL = "local"
    PARAMETER = "parameter"
    TEMPORARY = "temporary"
    CONSTANT = "constant"

class ActivationRecord:
    """Represents an activation record for function calls"""
    
    def __init__(self, function_name: str, return_type: SymbolType):
        self.function_name = function_name
        self.return_type = return_type
        self.local_variables: Dict[str, 'ExtendedSymbol'] = {}
        self.parameters: List['ExtendedSymbol'] = []
        self.temp_variables: List['ExtendedSymbol'] = []
        self.stack_offset = 0
        self.return_address = None
        self.static_link = None  # For nested functions
        self.dynamic_link = None  # For function calls
        
    def add_local_variable(self, symbol: 'ExtendedSymbol'):
        """Add a local variable to this activation record"""
        self.local_variables[symbol.name] = symbol
        symbol.memory_type = MemoryType.LOCAL
        symbol.stack_offset = self.stack_offset
        self.stack_offset += self._get_size_for_type(symbol.type)
    
    def add_parameter(self, symbol: 'ExtendedSymbol'):
        """Add a parameter to this activation record"""
        self.parameters.append(symbol)
        symbol.memory_type = MemoryType.PARAMETER
        symbol.stack_offset = self.stack_offset
        self.stack_offset += self._get_size_for_type(symbol.type)
    
    def add_temp_variable(self, symbol: 'ExtendedSymbol'):
        """Add a temporary variable to this activation record"""
        self.temp_variables.append(symbol)
        symbol.memory_type = MemoryType.TEMPORARY
        symbol.stack_offset = self.stack_offset
        self.stack_offset += self._get_size_for_type(symbol.type)
    
    def _get_size_for_type(self, symbol_type: SymbolType) -> int:
        """Get memory size for a symbol type"""
        size_map = {
            SymbolType.INTEGER: 4,
            SymbolType.FLOAT: 8,
            SymbolType.BOOLEAN: 1,
            SymbolType.STRING: 8,  # Pointer to string
            SymbolType.ARRAY: 8,   # Pointer to array
            SymbolType.CLASS: 8,   # Pointer to object
            SymbolType.FUNCTION: 8, # Function pointer
            SymbolType.VOID: 0,
            SymbolType.NULL: 8
        }
        return size_map.get(symbol_type, 4)
    
    def __str__(self):
        return f"ActivationRecord({self.function_name}, offset={self.stack_offset})"

class ExtendedSymbol(Symbol):
    """Extended symbol with information for code generation"""
    
    def __init__(self, name: str, symbol_type: SymbolType, value: Any = None, 
                 is_constant: bool = False, is_initialized: bool = False,
                 array_type: Optional[SymbolType] = None, array_dimensions: int = 0):
        super().__init__(name, symbol_type, value, is_constant, is_initialized, 
                        array_type, array_dimensions)
        
        # Memory management
        self.memory_address: Optional[str] = None
        self.memory_type: MemoryType = MemoryType.GLOBAL
        self.stack_offset: int = 0
        self.register: Optional[str] = None
        
        # Temporary variable management
        self.is_temporary: bool = False
        self.temp_id: Optional[int] = None
        self.last_used: int = 0  # For optimization
        self.is_live: bool = True  # For liveness analysis
        
        # Scope information
        self.scope_level: int = 0
        self.activation_record: Optional[ActivationRecord] = None
        
        # Code generation
        self.initialization_code: List[str] = []
        self.cleanup_code: List[str] = []
    
    def set_memory_info(self, address: str, memory_type: MemoryType, offset: int = 0):
        """Set memory information for the symbol"""
        self.memory_address = address
        self.memory_type = memory_type
        self.stack_offset = offset
    
    def set_temporary_info(self, temp_id: int, is_temp: bool = True):
        """Set temporary variable information"""
        self.temp_id = temp_id
        self.is_temporary = is_temp
    
    def __str__(self):
        base_str = super().__str__()
        if self.is_temporary:
            return f"{base_str} [TEMP{self.temp_id}]"
        if self.memory_address:
            return f"{base_str} [{self.memory_type.value}:{self.memory_address}]"
        return base_str

class ExtendedFunctionSymbol(FunctionSymbol):
    """Extended function symbol with activation record support"""
    
    def __init__(self, name: str, return_type: SymbolType, parameters: List[tuple] = None):
        super().__init__(name, return_type, parameters)
        self.activation_record: Optional[ActivationRecord] = None
        self.local_vars_count = 0
        self.temp_vars_count = 0
        self.stack_size = 0
    
    def create_activation_record(self) -> ActivationRecord:
        """Create activation record for this function"""
        self.activation_record = ActivationRecord(self.name, self.return_type)
        return self.activation_record

class ExtendedClassSymbol(ClassSymbol):
    """Extended class symbol with object layout information"""
    
    def __init__(self, name: str, parent_class: Optional[str] = None):
        super().__init__(name, parent_class)
        self.object_size = 0
        self.method_table: Dict[str, int] = {}  # Method name -> offset
        self.attribute_offsets: Dict[str, int] = {}  # Attribute name -> offset
        self.vtable_offset = 0
    
    def calculate_object_layout(self):
        """Calculate memory layout for objects of this class"""
        offset = 0
        # Add parent class attributes first
        if self.parent_class:
            # This would be calculated from parent class
            offset = 8  # Assume parent object size
        
        # Add own attributes
        for attr_name, attr in self.attributes.items():
            self.attribute_offsets[attr_name] = offset
            offset += self._get_size_for_type(attr.type)
        
        self.object_size = offset
    
    def _get_size_for_type(self, symbol_type: SymbolType) -> int:
        """Get memory size for a symbol type"""
        size_map = {
            SymbolType.INTEGER: 4,
            SymbolType.FLOAT: 8,
            SymbolType.BOOLEAN: 1,
            SymbolType.STRING: 8,
            SymbolType.ARRAY: 8,
            SymbolType.CLASS: 8,
            SymbolType.FUNCTION: 8,
            SymbolType.VOID: 0,
            SymbolType.NULL: 8
        }
        return size_map.get(symbol_type, 4)

class TempVariableManager:
    """Manages temporary variables for code generation"""
    
    def __init__(self):
        self.temp_vars: Dict[int, ExtendedSymbol] = {}
        self.free_temps: List[int] = []
        self.temp_counter = 0
        self.current_scope_level = 0
    
    def allocate_temp(self, symbol_type: SymbolType, scope_level: int = 0) -> ExtendedSymbol:
        """Allocate a temporary variable"""
        temp_id = self._get_next_temp_id()
        temp_name = f"t{temp_id}"
        
        temp_symbol = ExtendedSymbol(
            name=temp_name,
            symbol_type=symbol_type
        )
        
        temp_symbol.set_temporary_info(temp_id, True)
        temp_symbol.scope_level = scope_level
        temp_symbol.memory_type = MemoryType.TEMPORARY
        
        self.temp_vars[temp_id] = temp_symbol
        return temp_symbol
    
    def free_temp(self, temp_id: int):
        """Free a temporary variable"""
        if temp_id in self.temp_vars:
            self.temp_vars[temp_id].is_live = False
            self.free_temps.append(temp_id)
    
    def _get_next_temp_id(self) -> int:
        """Get next available temporary variable ID"""
        if self.free_temps:
            return self.free_temps.pop(0)
        self.temp_counter += 1
        return self.temp_counter
    
    def get_live_temps(self) -> List[ExtendedSymbol]:
        """Get all live temporary variables"""
        return [temp for temp in self.temp_vars.values() if temp.is_live]
    
    def optimize_temps(self):
        """Optimize temporary variable usage"""
        # Simple optimization: reuse freed temporaries
        # More complex optimizations could be added here
        pass

class ExtendedSymbolTable:
    """Extended symbol table with code generation support"""
    
    def __init__(self):
        self.global_scope = Scope("global")
        self.current_scope = self.global_scope
        self.scopes = [self.global_scope]
        self.errors: List[str] = []
        
        # Code generation support
        self.temp_manager = TempVariableManager()
        self.activation_records: List[ActivationRecord] = []
        self.current_activation_record: Optional[ActivationRecord] = None
        self.global_memory_offset = 0
        self.label_counter = 0
        
        # Initialize built-ins
        self._init_builtins()
    
    def _init_builtins(self):
        """Initialize built-in functions"""
        print_func = ExtendedFunctionSymbol("print", SymbolType.VOID)
        print_func.add_parameter("value", SymbolType.STRING)
        self.global_scope.define(print_func)
    
    def enter_scope(self, name: str) -> Scope:
        """Enter a new scope"""
        new_scope = Scope(name, self.current_scope)
        self.current_scope = new_scope
        self.scopes.append(new_scope)
        return new_scope
    
    def exit_scope(self):
        """Exit current scope and clean up temporaries"""
        # Free all temporaries in current scope
        current_level = self._get_scope_level()
        for temp in self.temp_manager.get_live_temps():
            if temp.scope_level == current_level:
                self.temp_manager.free_temp(temp.temp_id)
        
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent
    
    def _get_scope_level(self) -> int:
        """Get current scope level (0 = global)"""
        level = 0
        scope = self.current_scope
        while scope.parent:
            level += 1
            scope = scope.parent
        return level
    
    def define(self, symbol: ExtendedSymbol, line: int = None, column: int = None) -> bool:
        """Define a symbol in current scope"""
        symbol.line_declared = line
        symbol.column_declared = column
        symbol.scope_level = self._get_scope_level()
        
        # Set memory information
        if symbol.scope_level == 0:  # Global scope
            symbol.memory_type = MemoryType.GLOBAL
            symbol.memory_address = f"global_{self.global_memory_offset}"
            self.global_memory_offset += self._get_size_for_type(symbol.type)
        else:  # Local scope
            symbol.memory_type = MemoryType.LOCAL
            if self.current_activation_record:
                self.current_activation_record.add_local_variable(symbol)
        
        if not self.current_scope.define(symbol):
            self.errors.append(f"Symbol '{symbol.name}' already declared in current scope")
            return False
        return True
    
    def create_function_activation_record(self, function: ExtendedFunctionSymbol) -> ActivationRecord:
        """Create activation record for function call"""
        ar = function.create_activation_record()
        self.activation_records.append(ar)
        self.current_activation_record = ar
        return ar
    
    def allocate_temporary(self, symbol_type: SymbolType) -> ExtendedSymbol:
        """Allocate a temporary variable"""
        return self.temp_manager.allocate_temp(symbol_type, self._get_scope_level())
    
    def free_temporary(self, temp_symbol: ExtendedSymbol):
        """Free a temporary variable"""
        if temp_symbol.is_temporary and temp_symbol.temp_id:
            self.temp_manager.free_temp(temp_symbol.temp_id)
    
    def generate_label(self, prefix: str = "L") -> str:
        """Generate a unique label"""
        self.label_counter += 1
        return f"{prefix}{self.label_counter}"
    
    def lookup(self, name: str) -> Optional[ExtendedSymbol]:
        """Look up a symbol starting from current scope"""
        symbol = self.current_scope.lookup(name)
        return symbol if isinstance(symbol, (ExtendedSymbol, ExtendedFunctionSymbol, ExtendedClassSymbol)) else None
    
    def lookup_local(self, name: str) -> Optional[ExtendedSymbol]:
        """Look up a symbol only in current scope"""
        symbol = self.current_scope.lookup_local(name)
        return symbol if isinstance(symbol, (ExtendedSymbol, ExtendedFunctionSymbol, ExtendedClassSymbol)) else None
    
    def add_error(self, error: str):
        """Add a semantic error"""
        self.errors.append(error)
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    def get_errors(self) -> List[str]:
        """Get all errors"""
        return self.errors.copy()
    
    def _get_size_for_type(self, symbol_type: SymbolType) -> int:
        """Get memory size for a symbol type"""
        size_map = {
            SymbolType.INTEGER: 4,
            SymbolType.FLOAT: 8,
            SymbolType.BOOLEAN: 1,
            SymbolType.STRING: 8,
            SymbolType.ARRAY: 8,
            SymbolType.CLASS: 8,
            SymbolType.FUNCTION: 8,
            SymbolType.VOID: 0,
            SymbolType.NULL: 8
        }
        return size_map.get(symbol_type, 4)
    
    def print_table(self):
        """Print the entire extended symbol table for debugging"""
        def print_scope(scope: Scope, indent: int = 0):
            prefix = "  " * indent
            print(f"{prefix}{scope}")
            for symbol in scope.symbols.values():
                if isinstance(symbol, ExtendedSymbol):
                    print(f"{prefix}  {symbol}")
                else:
                    print(f"{prefix}  {symbol}")
            for child in scope.children:
                print_scope(child, indent + 1)
        
        print("=== EXTENDED SYMBOL TABLE ===")
        print_scope(self.global_scope)
        print(f"Global memory offset: {self.global_memory_offset}")
        print(f"Active temporaries: {len(self.temp_manager.get_live_temps())}")
        print("=============================")
    
    def get_memory_layout(self) -> Dict[str, Any]:
        """Get memory layout information for code generation"""
        return {
            "global_offset": self.global_memory_offset,
            "active_temps": len(self.temp_manager.get_live_temps()),
            "activation_records": len(self.activation_records),
            "current_ar": self.current_activation_record.function_name if self.current_activation_record else None
        }
