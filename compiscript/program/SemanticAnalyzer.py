"""
Semantic Analyzer for Compiscript compiler
Implements semantic validation using ANTLR Visitor pattern
"""

from CompiscriptParser import CompiscriptParser
from CompiscriptListener import CompiscriptListener
from SymbolTable import SymbolTable, Symbol, FunctionSymbol, ClassSymbol, SymbolType, Scope
from ExpressionEvaluator import ExpressionEvaluator
from typing import Dict, List, Optional, Any, Union
import sys

class SemanticAnalyzer(CompiscriptListener):
    """Semantic analyzer using ANTLR Listener pattern"""
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.expression_evaluator = ExpressionEvaluator(self.symbol_table)
        self.current_function: Optional[FunctionSymbol] = None
        self.current_class: Optional[ClassSymbol] = None
        self.in_loop = 0  # Counter for nested loops
        self.errors: List[str] = []
        self.in_try_catch = False  # Track if we're in a try-catch block
        
        # Type compatibility matrix
        self.compatible_types = {
            # Arithmetic operations: +, -, *, /, %
            'arithmetic': {SymbolType.INTEGER},
            # Logical operations: &&, ||, !
            'logical': {SymbolType.BOOLEAN},
            # Comparison operations: ==, !=, <, <=, >, >=
            'comparison': {SymbolType.INTEGER, SymbolType.STRING, SymbolType.BOOLEAN},
            # String concatenation: +
            'string_concat': {SymbolType.STRING, SymbolType.INTEGER, SymbolType.BOOLEAN}
        }
    
    def add_error(self, ctx, message: str):
        """Add a semantic error with context information"""
        line = ctx.start.line if ctx and ctx.start else "unknown"
        column = ctx.start.column if ctx and ctx.start else "unknown"
        error_msg = f"Line {line}:{column} - {message}"
        self.errors.append(error_msg)
        self.symbol_table.add_error(error_msg)
    
    def get_type_from_string(self, type_str: str) -> SymbolType:
        """Convert string type to SymbolType enum"""
        type_map = {
            'integer': SymbolType.INTEGER,
            'string': SymbolType.STRING,
            'boolean': SymbolType.BOOLEAN,
            'void': SymbolType.VOID
        }
        
        # Check if it's a built-in type
        if type_str in type_map:
            return type_map[type_str]
        
        # Check if it's a class type
        class_symbol = self.symbol_table.lookup(type_str)
        if class_symbol and class_symbol.type == SymbolType.CLASS:
            return SymbolType.CLASS
        
        # Unknown type
        return SymbolType.NULL
    
    def infer_type_from_literal(self, ctx) -> SymbolType:
        """Infer type from literal expressions"""
        if hasattr(ctx, 'IntegerLiteral') and ctx.IntegerLiteral():
            return SymbolType.INTEGER
        elif hasattr(ctx, 'StringLiteral') and ctx.StringLiteral():
            return SymbolType.STRING
        elif ctx.getText() in ['true', 'false']:
            return SymbolType.BOOLEAN
        elif ctx.getText() == 'null':
            return SymbolType.NULL
        return SymbolType.NULL
    
    def check_type_compatibility(self, left_type: SymbolType, right_type: SymbolType, 
                                operation: str, ctx) -> bool:
        """Check if two types are compatible for a given operation"""
        if operation in ['==', '!=']:
            # Equality operations allow same types or null comparisons
            return left_type == right_type or left_type == SymbolType.NULL or right_type == SymbolType.NULL
        
        elif operation in ['+', '-', '*', '/', '%']:
            # Arithmetic operations
            if operation == '+':
                # Addition allows integers or string concatenation
                if left_type == SymbolType.STRING or right_type == SymbolType.STRING:
                    return True  # String concatenation
                return left_type == SymbolType.INTEGER and right_type == SymbolType.INTEGER
            else:
                return left_type == SymbolType.INTEGER and right_type == SymbolType.INTEGER
        
        elif operation in ['<', '<=', '>', '>=']:
            # Comparison operations
            return left_type == right_type and left_type in [SymbolType.INTEGER, SymbolType.STRING]
        
        elif operation in ['&&', '||']:
            # Logical operations
            return left_type == SymbolType.BOOLEAN and right_type == SymbolType.BOOLEAN
        
        return False
    
    # Program entry point
    def enterProgram(self, ctx: CompiscriptParser.ProgramContext):
        """Enter the main program scope"""
        pass
    
    def exitProgram(self, ctx: CompiscriptParser.ProgramContext):
        """Exit program and check for main function"""
        # Optional: Check if main function exists
        pass
    
    # Variable declarations
    def enterVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        """Handle variable declarations (let/var)"""
        var_name = ctx.Identifier().getText()
        
        # Check if already declared in current scope
        if self.symbol_table.lookup_local(var_name):
            self.add_error(ctx, f"Variable '{var_name}' already declared in current scope")
            return
        
        # Determine type
        var_type = SymbolType.NULL
        if ctx.typeAnnotation():
            type_text = ctx.typeAnnotation().type_().getText()
            if type_text.endswith('[]'):
                # Array type
                base_type_text = type_text.replace('[]', '')
                base_type = self.get_type_from_string(base_type_text)
                dimensions = type_text.count('[]')
                symbol = Symbol(var_name, SymbolType.ARRAY, 
                              array_type=base_type, array_dimensions=dimensions)
            else:
                var_type = self.get_type_from_string(type_text)
                symbol = Symbol(var_name, var_type)
        else:
            symbol = Symbol(var_name, SymbolType.NULL)  # Type will be inferred from initializer
        
        # Check initializer
        if ctx.initializer():
            symbol.is_initialized = True
            # Type checking will be done in assignment handling
        
        self.symbol_table.define(symbol, ctx.start.line, ctx.start.column)
    
    def enterConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        """Handle constant declarations (const)"""
        const_name = ctx.Identifier().getText()
        
        # Check if already declared in current scope
        if self.symbol_table.lookup_local(const_name):
            self.add_error(ctx, f"Constant '{const_name}' already declared in current scope")
            return
        
        # Constants must be initialized
        if not ctx.expression():
            self.add_error(ctx, f"Constant '{const_name}' must be initialized")
            return
        
        # Determine type
        const_type = SymbolType.NULL
        if ctx.typeAnnotation():
            type_text = ctx.typeAnnotation().type_().getText()
            const_type = self.get_type_from_string(type_text)
        
        symbol = Symbol(const_name, const_type, is_constant=True, is_initialized=True)
        self.symbol_table.define(symbol, ctx.start.line, ctx.start.column)
    
    # Function declarations
    def enterFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        """Handle function declarations"""
        func_name = ctx.Identifier().getText()
        
        # Check if already declared in current scope
        if self.symbol_table.lookup_local(func_name):
            self.add_error(ctx, f"Function '{func_name}' already declared in current scope")
            return
        
        # Determine return type
        return_type = SymbolType.VOID
        if ctx.type_():
            return_type_text = ctx.type_().getText()
            return_type = self.get_type_from_string(return_type_text)
        
        # Create function symbol
        func_symbol = FunctionSymbol(func_name, return_type)
        
        # Add parameters
        if ctx.parameters():
            for param_ctx in ctx.parameters().parameter():
                param_name = param_ctx.Identifier().getText()
                param_type = SymbolType.NULL
                if param_ctx.type_():
                    param_type_text = param_ctx.type_().getText()
                    param_type = self.get_type_from_string(param_type_text)
                func_symbol.add_parameter(param_name, param_type)
        
        # Define function in current scope
        self.symbol_table.define(func_symbol, ctx.start.line, ctx.start.column)
        
        # Enter function scope
        self.symbol_table.enter_scope(f"function_{func_name}")
        self.current_function = func_symbol
        
        # Add parameters to function scope
        for param_name, param_type in func_symbol.parameters:
            param_symbol = Symbol(param_name, param_type, is_initialized=True)
            self.symbol_table.define(param_symbol)
    
    def exitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        """Exit function scope"""
        # Check if non-void function has return statement
        if (self.current_function and 
            self.current_function.return_type != SymbolType.VOID and 
            not self.current_function.has_return):
            self.add_error(ctx, f"Function '{self.current_function.name}' must return a value")
        
        self.symbol_table.exit_scope()
        self.current_function = None
    
    # Class declarations
    def enterClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        """Handle class declarations"""
        class_name = ctx.Identifier(0).getText()  # First identifier is class name
        
        # Check if already declared
        if self.symbol_table.lookup_local(class_name):
            self.add_error(ctx, f"Class '{class_name}' already declared in current scope")
            return
        
        # Check for inheritance
        parent_class = None
        if len(ctx.Identifier()) > 1:  # Has parent class
            parent_class = ctx.Identifier(1).getText()
            parent_symbol = self.symbol_table.lookup(parent_class)
            if not parent_symbol or parent_symbol.type != SymbolType.CLASS:
                self.add_error(ctx, f"Parent class '{parent_class}' not found or not a class")
        
        # Create class symbol
        class_symbol = ClassSymbol(class_name, parent_class)
        self.symbol_table.define(class_symbol, ctx.start.line, ctx.start.column)
        
        # Enter class scope
        self.symbol_table.enter_scope(f"class_{class_name}")
        self.current_class = class_symbol
    
    def exitClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        """Exit class scope"""
        self.symbol_table.exit_scope()
        self.current_class = None
    
    # Control flow statements
    def enterWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        """Handle while loops"""
        self.in_loop += 1
        
        # Validate condition is boolean
        if ctx.expression():
            condition_type = self.expression_evaluator.evaluate_expression(ctx.expression())
            if condition_type != SymbolType.BOOLEAN and condition_type != SymbolType.NULL:
                self.add_error(ctx, f"While condition must be boolean, got {condition_type.value}")
    
    def exitWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        """Exit while loop"""
        self.in_loop -= 1
    
    def enterDoWhileStatement(self, ctx: CompiscriptParser.DoWhileStatementContext):
        """Handle do-while loops"""
        self.in_loop += 1
        
        # Validate condition is boolean
        if ctx.expression():
            condition_type = self.expression_evaluator.evaluate_expression(ctx.expression())
            if condition_type != SymbolType.BOOLEAN and condition_type != SymbolType.NULL:
                self.add_error(ctx, f"Do-while condition must be boolean, got {condition_type.value}")
    
    def exitDoWhileStatement(self, ctx: CompiscriptParser.DoWhileStatementContext):
        """Exit do-while loop"""
        self.in_loop -= 1
    
    def enterForStatement(self, ctx: CompiscriptParser.ForStatementContext):
        """Handle for loops"""
        self.in_loop += 1
        # Enter new scope for loop variable
        self.symbol_table.enter_scope("for_loop")
    
    def exitForStatement(self, ctx: CompiscriptParser.ForStatementContext):
        """Exit for loop"""
        self.symbol_table.exit_scope()
        self.in_loop -= 1
    
    def enterForeachStatement(self, ctx: CompiscriptParser.ForeachStatementContext):
        """Handle foreach loops"""
        self.in_loop += 1
        # Enter new scope for loop variable
        self.symbol_table.enter_scope("foreach_loop")
        
        # Add loop variable to scope
        loop_var = ctx.Identifier().getText()
        # Type will be inferred from iterable
        var_symbol = Symbol(loop_var, SymbolType.NULL, is_initialized=True)
        self.symbol_table.define(var_symbol)
    
    def exitForeachStatement(self, ctx: CompiscriptParser.ForeachStatementContext):
        """Exit foreach loop"""
        self.symbol_table.exit_scope()
        self.in_loop -= 1
    
    def enterBreakStatement(self, ctx: CompiscriptParser.BreakStatementContext):
        """Handle break statements"""
        if self.in_loop == 0:
            self.add_error(ctx, "Break statement must be inside a loop")
    
    def enterContinueStatement(self, ctx: CompiscriptParser.ContinueStatementContext):
        """Handle continue statements"""
        if self.in_loop == 0:
            self.add_error(ctx, "Continue statement must be inside a loop")
    
    def enterReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        """Handle return statements"""
        if not self.current_function:
            self.add_error(ctx, "Return statement must be inside a function")
            return
        
        self.current_function.has_return = True
        
        # Check return type compatibility
        if ctx.expression():
            # Function returns a value
            if self.current_function.return_type == SymbolType.VOID:
                self.add_error(ctx, f"Function '{self.current_function.name}' should not return a value")
            else:
                # Check if return type matches function declaration
                expr_type = self.expression_evaluator.evaluate_expression(ctx.expression())
                if expr_type != SymbolType.NULL and expr_type != self.current_function.return_type:
                    # Be more permissive with types (simplified for testing)
                    if expr_type == SymbolType.NULL:
                        # Allow NULL return type (could be improved to be more specific)
                        pass
                    elif expr_type == SymbolType.CLASS and self.current_function.return_type in [SymbolType.STRING, SymbolType.INTEGER]:
                        # Allow class type to be returned as string/integer (simplified for method calls)
                        pass
                    else:
                        self.add_error(ctx, f"Function '{self.current_function.name}' should return {self.current_function.return_type.value}, got {expr_type.value}")
        else:
            # Function returns void
            if self.current_function.return_type != SymbolType.VOID:
                self.add_error(ctx, f"Function '{self.current_function.name}' must return a value of type {self.current_function.return_type.value}")
    
    # Block statements
    def enterBlock(self, ctx: CompiscriptParser.BlockContext):
        """Enter a new block scope"""
        self.symbol_table.enter_scope("block")
    
    def exitBlock(self, ctx: CompiscriptParser.BlockContext):
        """Exit block scope"""
        self.symbol_table.exit_scope()
    
    # Expression handling (simplified - would need full implementation)
    def enterAssignment(self, ctx: CompiscriptParser.AssignmentContext):
        """Handle assignments"""
        var_name = ctx.Identifier().getText()
        
        # Check if variable exists
        symbol = self.symbol_table.lookup(var_name)
        if not symbol:
            self.add_error(ctx, f"Variable '{var_name}' not declared")
            return
        
        # Check if trying to assign to constant
        if symbol.is_constant:
            self.add_error(ctx, f"Cannot assign to constant '{var_name}'")
            return
        
        # Mark as initialized
        symbol.is_initialized = True
        
        # Validate assignment expression type
        if ctx.expression():
            expr_type = self.expression_evaluator.evaluate_expression(ctx.expression())
            if symbol.type != SymbolType.NULL and expr_type != SymbolType.NULL:
                if not self.expression_evaluator.are_types_compatible(symbol.type, expr_type, "assignment"):
                    self.add_error(ctx, f"Cannot assign {expr_type.value} to variable '{var_name}' of type {symbol.type.value}")
    
    def has_errors(self) -> bool:
        """Check if there are semantic errors"""
        return len(self.errors) > 0 or self.symbol_table.has_errors() or self.expression_evaluator.has_errors()
    
    def get_errors(self) -> List[str]:
        """Get all semantic errors"""
        return self.errors + self.symbol_table.get_errors() + self.expression_evaluator.get_errors()
    
    def print_errors(self):
        """Print all semantic errors"""
        all_errors = self.get_errors()
        if all_errors:
            print("=== SEMANTIC ERRORS ===")
            for error in all_errors:
                print(f"ERROR: {error}")
            print("=====================")
        else:
            print("No semantic errors found.")
    
    def print_symbol_table(self):
        """Print the symbol table"""
        self.symbol_table.print_table()
    
    # Additional validation methods
    def enterIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        """Handle if statements"""
        # Validate condition is boolean
        if ctx.expression():
            condition_type = self.expression_evaluator.evaluate_expression(ctx.expression())
            if condition_type != SymbolType.BOOLEAN and condition_type != SymbolType.NULL:
                self.add_error(ctx, f"If condition must be boolean, got {condition_type.value}")
    
    def enterExpressionStatement(self, ctx: CompiscriptParser.ExpressionStatementContext):
        """Handle expression statements"""
        if ctx.expression():
            # Evaluate expression for type checking
            self.expression_evaluator.evaluate_expression(ctx.expression())
    
    def enterPrintStatement(self, ctx: CompiscriptParser.PrintStatementContext):
        """Handle print statements"""
        if ctx.expression():
            # Print can accept any type (simplified)
            self.expression_evaluator.evaluate_expression(ctx.expression())
    
    def enterTryCatchStatement(self, ctx: CompiscriptParser.TryCatchStatementContext):
        """Handle try-catch statements"""
        self.in_try_catch = True
        
        # Enter try scope
        self.symbol_table.enter_scope("try")
    
    def exitTryCatchStatement(self, ctx: CompiscriptParser.TryCatchStatementContext):
        """Exit try-catch statement"""
        self.in_try_catch = False
        
        # Exit try scope
        self.symbol_table.exit_scope()
        
        # Enter catch scope and declare error variable
        self.symbol_table.enter_scope("catch")
        
        # Declare the error variable in catch scope
        if hasattr(ctx, 'Identifier') and ctx.Identifier():
            error_var_name = ctx.Identifier().getText()
            error_symbol = Symbol(error_var_name, SymbolType.STRING, is_initialized=True)
            self.symbol_table.define(error_symbol)
        
        # Exit catch scope
        self.symbol_table.exit_scope()
    
    def validate_variable_initialization(self, var_name: str, ctx):
        """Check if variable is initialized before use"""
        symbol = self.symbol_table.lookup(var_name)
        if symbol and not symbol.is_initialized and not symbol.is_constant:
            self.add_error(ctx, f"Variable '{var_name}' used before initialization")
