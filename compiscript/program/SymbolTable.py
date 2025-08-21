"""
Symbol Table implementation for Compiscript compiler
Handles scopes, symbol resolution, and type information
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union

class SymbolType(Enum):
    """Types supported by Compiscript"""
    INTEGER = "integer"
    STRING = "string"
    FLOAT = "float"
    BOOLEAN = "boolean"
    NULL = "null"
    ARRAY = "array"
    FUNCTION = "function"
    CLASS = "class"
    VOID = "void"

class Symbol:
    """Represents a symbol in the symbol table"""
    
    def __init__(self, name: str, symbol_type: SymbolType, value: Any = None, 
                 is_constant: bool = False, is_initialized: bool = False,
                 array_type: Optional[SymbolType] = None, array_dimensions: int = 0):
        self.name = name
        self.type = symbol_type
        self.value = value
        self.is_constant = is_constant
        self.is_initialized = is_initialized
        self.array_type = array_type  # For arrays, the type of elements
        self.array_dimensions = array_dimensions  # Number of array dimensions
        self.line_declared = None
        self.column_declared = None
    
    def __str__(self):
        type_str = self.type.value
        if self.type == SymbolType.ARRAY:
            type_str = f"{self.array_type.value}{'[]' * self.array_dimensions}"
        return f"Symbol({self.name}: {type_str}, const={self.is_constant}, init={self.is_initialized})"

class FunctionSymbol(Symbol):
    """Represents a function symbol with parameters and return type"""
    
    def __init__(self, name: str, return_type: SymbolType, parameters: List[tuple] = None):
        super().__init__(name, SymbolType.FUNCTION)
        self.return_type = return_type
        self.parameters = parameters or []  # List of (name, type) tuples
        self.has_return = False  # Track if function has return statement
    
    def add_parameter(self, param_name: str, param_type: SymbolType):
        self.parameters.append((param_name, param_type))
    
    def __str__(self):
        params = ", ".join([f"{name}: {ptype.value}" for name, ptype in self.parameters])
        return f"Function({self.name}({params}) -> {self.return_type.value})"

class ClassSymbol(Symbol):
    """Represents a class symbol with methods and attributes"""
    
    def __init__(self, name: str, parent_class: Optional[str] = None):
        super().__init__(name, SymbolType.CLASS)
        self.parent_class = parent_class
        self.methods: Dict[str, FunctionSymbol] = {}
        self.attributes: Dict[str, Symbol] = {}
        self.constructor: Optional[FunctionSymbol] = None
    
    def add_method(self, method: FunctionSymbol):
        if method.name == "constructor":
            self.constructor = method
        self.methods[method.name] = method
    
    def add_attribute(self, attribute: Symbol):
        self.attributes[attribute.name] = attribute
    
    def __str__(self):
        parent = f" : {self.parent_class}" if self.parent_class else ""
        return f"Class({self.name}{parent})"

class Scope:
    """Represents a scope in the program"""
    
    def __init__(self, name: str, parent: Optional['Scope'] = None):
        self.name = name
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.children: List['Scope'] = []
        if parent:
            parent.children.append(self)
    
    def define(self, symbol: Symbol) -> bool:
        """Define a symbol in this scope. Returns False if already exists."""
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol in this scope or parent scopes"""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None
    
    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up a symbol only in this scope"""
        return self.symbols.get(name)
    
    def __str__(self):
        return f"Scope({self.name}, symbols={len(self.symbols)})"

class SymbolTable:
    """Main symbol table managing all scopes"""
    
    def __init__(self):
        self.global_scope = Scope("global")
        self.current_scope = self.global_scope
        self.scopes = [self.global_scope]
        self.errors: List[str] = []
        
        # Initialize built-in functions
        self._init_builtins()
    
    def _init_builtins(self):
        """Initialize built-in functions like print"""
        print_func = FunctionSymbol("print", SymbolType.VOID)
        print_func.add_parameter("value", SymbolType.STRING)  # Simplified - print accepts any type
        self.global_scope.define(print_func)
    
    def enter_scope(self, name: str) -> Scope:
        """Enter a new scope"""
        new_scope = Scope(name, self.current_scope)
        self.current_scope = new_scope
        self.scopes.append(new_scope)
        return new_scope
    
    def exit_scope(self):
        """Exit current scope"""
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent
    
    def get_global_scope(self) -> Scope:
        """Get the global scope"""
        return self.global_scope
    
    def define(self, symbol: Symbol, line: int = None, column: int = None) -> bool:
        """Define a symbol in current scope"""
        symbol.line_declared = line
        symbol.column_declared = column
        
        if not self.current_scope.define(symbol):
            self.errors.append(f"Symbol '{symbol.name}' already declared in current scope")
            return False
        return True
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol starting from current scope"""
        return self.current_scope.lookup(name)
    
    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up a symbol only in current scope"""
        return self.current_scope.lookup_local(name)
    
    def add_error(self, error: str):
        """Add a semantic error"""
        self.errors.append(error)
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    def get_errors(self) -> List[str]:
        """Get all errors"""
        return self.errors.copy()
    
    def print_table(self):
        """Print the entire symbol table for debugging"""
        def print_scope(scope: Scope, indent: int = 0):
            prefix = "  " * indent
            print(f"{prefix}{scope}")
            for symbol in scope.symbols.values():
                print(f"{prefix}  {symbol}")
            for child in scope.children:
                print_scope(child, indent + 1)
        
        print("=== SYMBOL TABLE ===")
        print_scope(self.global_scope)
        print("==================")
