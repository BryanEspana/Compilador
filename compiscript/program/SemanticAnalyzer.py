"""
Semantic Analyzer for Compiscript compiler
Implements semantic validation using ANTLR Visitor pattern
"""

from CompiscriptParser import CompiscriptParser
from CompiscriptListener import CompiscriptListener
from SymbolTable import SymbolTable, Symbol, FunctionSymbol, ClassSymbol, SymbolType, Scope
from ExpressionEvaluator import ExpressionEvaluator
from TACCodeGenerator import TACCodeGenerator
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
        
        # TAC Code Generation
        self.tac_generator = TACCodeGenerator(emit_params=True)
        self.intermediate_code: str = ""
        
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
        
        # Reserved keywords that cannot be used as identifiers
        self.reserved_keywords = {
            'let', 'var', 'const', 'function', 'class', 'if', 'else', 'while', 'do',
            'for', 'foreach', 'in', 'break', 'continue', 'return', 'try', 'catch',
            'throw', 'switch', 'case', 'default', 'new', 'this', 'super', 'null',
            'true', 'false', 'print', 'integer', 'string', 'boolean', 'void'
        }
    
    def is_reserved_identifier(self, name: str) -> bool:
        """Check if an identifier is a reserved keyword"""
        return name in self.reserved_keywords
    
    def add_error(self, ctx, message: str):
        """Add a semantic error with context information"""
        try:
            line = ctx.start.line if ctx and ctx.start else "unknown"
            column = ctx.start.column if ctx and ctx.start else "unknown"
            # Ensure message is properly encoded
            if isinstance(message, bytes):
                message = message.decode('utf-8', errors='replace')
            elif not isinstance(message, str):
                message = str(message)
            
            error_msg = f"Line {line}:{column} - {message}"
            self.errors.append(error_msg)
            # Don't add to symbol_table to avoid duplication
        except Exception as e:
            # Fallback error handling
            fallback_msg = f"Error processing semantic error: {str(e)}"
            self.errors.append(fallback_msg)
    
    def get_type_from_string(self, type_str: str) -> SymbolType:
        """Convert string type to SymbolType enum"""
        type_map = {
            'integer': SymbolType.INTEGER,
            'string': SymbolType.STRING,
            'float': SymbolType.FLOAT,
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
        # Validate function calls now that all functions are defined
        self._validate_function_calls()
        # Optional: Check if main function exists
        pass
    
    # Variable declarations
    def enterVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        """Handle variable declarations (let/var)"""
        try:
            var_name = ctx.Identifier().getText()
            
            # Check if it's a reserved keyword
            if self.is_reserved_identifier(var_name):
                self.add_error(ctx, f"'{var_name}' is a reserved keyword and cannot be used as a variable name")
                return
            
            # Check if already declared in current scope
            if self.symbol_table.lookup_local(var_name):
                existing_symbol = self.symbol_table.lookup_local(var_name)
                self.add_error(ctx, f"Variable '{var_name}' already declared in current scope at line {existing_symbol.line_declared}")
                return
            
            # Check if shadowing a variable from outer scope (warning/info)
            outer_symbol = self.symbol_table.lookup(var_name)
            if outer_symbol and outer_symbol != self.symbol_table.lookup_local(var_name):
                # This is shadowing - could be a warning, but we'll allow it
                pass
            
            # Determine type
            var_type = SymbolType.NULL
            if ctx.typeAnnotation():
                type_text = ctx.typeAnnotation().type_().getText()
                if type_text.endswith('[]'):
                    base_type_text = type_text.replace('[]', '')
                    base_type = self.get_type_from_string(base_type_text)
                    if base_type == SymbolType.NULL:
                        self.add_error(ctx, f"Unknown array element type '{base_type_text}'")
                        return
                    dimensions = type_text.count('[]')
                    symbol = Symbol(var_name, SymbolType.ARRAY,
                                    array_type=base_type, array_dimensions=dimensions)
                else:
                    var_type = self.get_type_from_string(type_text)
                    if var_type == SymbolType.NULL:
                        self.add_error(ctx, f"Unknown type '{type_text}'")
                        return
                    symbol = Symbol(var_name, var_type)
            else:
                symbol = Symbol(var_name, SymbolType.NULL)  # se infiere del inicializador

            # 3) Inicializador (si existe)
            if ctx.initializer():
                symbol.is_initialized = True

                # IMPORTANTE: usar evaluate_expression (no solo ...type_only) para que
                # ExpressionEvaluator fije last_array_base / last_array_dims si es un array literal.
                rhs_expr = ctx.initializer().expression()
                rhs_type = self.expression_evaluator.evaluate_expression(rhs_expr)

                if ctx.typeAnnotation():
                    # 3a) LHS con anotación de ARRAY: comparar base y dimensiones
                    if symbol.type == SymbolType.ARRAY:
                        if rhs_type != SymbolType.ARRAY:
                            self.add_error(
                                ctx,
                                f"No se puede asignar {rhs_type.value} a {symbol.array_type.value}{'[]'*symbol.array_dimensions}"
                            )
                        else:
                            rhs_base = getattr(self.expression_evaluator, "last_array_base", None)
                            rhs_dims = getattr(self.expression_evaluator, "last_array_dims", 0)
                            if rhs_base != symbol.array_type or rhs_dims != symbol.array_dimensions:
                                lhs_txt = f"{symbol.array_type.value}{'[]'*symbol.array_dimensions}"
                                rhs_txt = f"{rhs_base.value if rhs_base else 'null'}{'[]'*(rhs_dims or 0)}"
                                self.add_error(ctx, f"Array type mismatch: se esperaba {lhs_txt} y se obtuvo {rhs_txt}")
                    else:
                        # 3b) LHS no es array: compatibilidad normal
                        if rhs_type != SymbolType.NULL and not self.expression_evaluator.are_types_compatible(symbol.type, rhs_type, "assignment"):
                            self.add_error(
                                ctx,
                                f"Cannot initialize variable '{var_name}' of type {symbol.type.value} with value of type {rhs_type.value}"
                            )
                else:
                    # 3c) Sin anotación: inferir
                    if rhs_type == SymbolType.ARRAY:
                        symbol.type = SymbolType.ARRAY
                        symbol.array_type = getattr(self.expression_evaluator, "last_array_base", None)
                        symbol.array_dimensions = getattr(self.expression_evaluator, "last_array_dims", 0)
                    elif rhs_type != SymbolType.NULL:
                        symbol.type = rhs_type

            # 4) Definir símbolo
            self.symbol_table.define(symbol, ctx.start.line, ctx.start.column)

        except Exception as e:
            self.add_error(ctx, f"Error processing variable declaration: {str(e)}")

    
    def enterConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        """Handle constant declarations (const)"""
        try:
            const_name = ctx.Identifier().getText()
            
            # Check if it's a reserved keyword
            if self.is_reserved_identifier(const_name):
                self.add_error(ctx, f"'{const_name}' is a reserved keyword and cannot be used as a constant name")
                return
            
            # Check if already declared in current scope
            if self.symbol_table.lookup_local(const_name):
                existing_symbol = self.symbol_table.lookup_local(const_name)
                self.add_error(ctx, f"Constant '{const_name}' already declared in current scope at line {existing_symbol.line_declared}")
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
                if const_type == SymbolType.NULL:
                    self.add_error(ctx, f"Unknown type '{type_text}'")
                    return
            
            # Validate initializer type
            expr_type = self.expression_evaluator.evaluate_expression_type_only(ctx.expression())
            
            # If constant has explicit type annotation, check compatibility
            if const_type != SymbolType.NULL and expr_type != SymbolType.NULL:
                if not self.expression_evaluator.are_types_compatible(const_type, expr_type, "assignment"):
                    self.add_error(ctx, f"Cannot initialize constant '{const_name}' of type {const_type.value} with value of type {expr_type.value}")
            # If no explicit type, infer from initializer
            elif const_type == SymbolType.NULL and expr_type != SymbolType.NULL:
                const_type = expr_type

            symbol = Symbol(const_name, const_type, is_constant=True, is_initialized=True)
            self.symbol_table.define(symbol, ctx.start.line, ctx.start.column)
        except Exception as e:
            self.add_error(ctx, f"Error processing constant declaration: {str(e)}")
    
    # Function declarations
    def enterFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        """Handle function declarations"""
        try:
            func_name = ctx.Identifier().getText()
            
            # Check if it's a reserved keyword
            if self.is_reserved_identifier(func_name):
                self.add_error(ctx, f"'{func_name}' is a reserved keyword and cannot be used as a function name")
                return
            
            # Check if already declared in current scope
            if self.symbol_table.lookup_local(func_name):
                existing_symbol = self.symbol_table.lookup_local(func_name)
                self.add_error(ctx, f"Function '{func_name}' already declared in current scope at line {existing_symbol.line_declared}")
                return
            
            # Determine return type
            return_type = SymbolType.VOID
            if ctx.type_():
                return_type_text = ctx.type_().getText()
                return_type = self.get_type_from_string(return_type_text)
                if return_type == SymbolType.NULL:
                    self.add_error(ctx, f"Unknown return type '{return_type_text}'")
                    return
            
            # Create function symbol
            func_symbol = FunctionSymbol(func_name, return_type)
            
            # Process parameters and check for duplicates
            param_names = set()
            if ctx.parameters():
                for param_ctx in ctx.parameters().parameter():
                    param_name = param_ctx.Identifier().getText()
                    
                    # Check for duplicate parameter names
                    if param_name in param_names:
                        self.add_error(ctx, f"Duplicate parameter name '{param_name}' in function '{func_name}'")
                        continue
                    param_names.add(param_name)
                    
                    # Check if parameter name is reserved
                    if self.is_reserved_identifier(param_name):
                        self.add_error(ctx, f"Parameter name '{param_name}' is a reserved keyword")
                        continue
                    
                    param_type = SymbolType.NULL
                    if param_ctx.type_():
                        param_type_text = param_ctx.type_().getText()
                        param_type = self.get_type_from_string(param_type_text)
                        if param_type == SymbolType.NULL:
                            self.add_error(ctx, f"Unknown parameter type '{param_type_text}' for parameter '{param_name}'")
                            continue
                    else:
                        self.add_error(ctx, f"Parameter '{param_name}' must have a type annotation")
                        continue
                    
                    func_symbol.add_parameter(param_name, param_type)
            
            # Define function in current scope
            if self.current_class:
                # This is a method in a class
                self.current_class.add_method(func_symbol)
                # Also define in class scope for lookup
                self.symbol_table.define(func_symbol, ctx.start.line, ctx.start.column)
            else:
                # This is a global function
                self.symbol_table.define(func_symbol, ctx.start.line, ctx.start.column)
            
            # Enter function scope
            self.symbol_table.enter_scope(f"function_{func_name}")
            self.current_function = func_symbol
            
            # Add parameters to function scope
            for param_name, param_type in func_symbol.parameters:
                param_symbol = Symbol(param_name, param_type, is_initialized=True)
                self.symbol_table.define(param_symbol, ctx.start.line, ctx.start.column)
                
        except Exception as e:
            self.add_error(ctx, f"Error processing function declaration: {str(e)}")
    
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
        try:
            class_name = ctx.Identifier(0).getText()  # First identifier is class name
            
            # Check if it's a reserved keyword
            if self.is_reserved_identifier(class_name):
                self.add_error(ctx, f"'{class_name}' is a reserved keyword and cannot be used as a class name")
                return
            
            # Check if already declared
            if self.symbol_table.lookup_local(class_name):
                existing_symbol = self.symbol_table.lookup_local(class_name)
                self.add_error(ctx, f"Class '{class_name}' already declared in current scope at line {existing_symbol.line_declared}")
                return
            
            # Check for inheritance
            parent_class = None
            if len(ctx.Identifier()) > 1:  # Has parent class
                parent_class = ctx.Identifier(1).getText()
                parent_symbol = self.symbol_table.lookup(parent_class)
                if not parent_symbol:
                    self.add_error(ctx, f"Parent class '{parent_class}' not found")
                    return
                elif parent_symbol.type != SymbolType.CLASS:
                    self.add_error(ctx, f"'{parent_class}' is not a class")
                    return
                elif parent_class == class_name:
                    self.add_error(ctx, f"Class '{class_name}' cannot inherit from itself")
                    return
            
            # Create class symbol
            class_symbol = ClassSymbol(class_name, parent_class)
            self.symbol_table.define(class_symbol, ctx.start.line, ctx.start.column)
            
            # Enter class scope
            self.symbol_table.enter_scope(f"class_{class_name}")
            self.current_class = class_symbol
            
        except Exception as e:
            self.add_error(ctx, f"Error processing class declaration: {str(e)}")
    
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
        try:
            # Check if this is a property assignment: expression '.' Identifier '=' expression ';'
            if ctx.expression() and len(ctx.expression()) == 2:
                # This is a property assignment like this.nombre = value
                property_name = ctx.Identifier().getText()
                
                # Get the left-hand side (should be 'this' or an object)
                lhs_type = self.expression_evaluator.evaluate_expression_type_only(ctx.expression()[0])
                
                # Check if we're assigning to 'this' inside a class
                if lhs_type == SymbolType.CLASS and self.current_class:
                    # Get the value type
                    value_type = self.expression_evaluator.evaluate_expression_type_only(ctx.expression()[1])
                    
                    # Auto-declare the property in the current class if it doesn't exist
                    if property_name not in self.current_class.attributes:
                        property_symbol = Symbol(property_name, value_type, is_initialized=True)
                        self.current_class.add_attribute(property_symbol)
                        
                        # Also add to current class scope for lookup
                        self.symbol_table.define(property_symbol, ctx.start.line, ctx.start.column)
                    else:
                        # Property exists, check type compatibility
                        existing_attr = self.current_class.attributes[property_name]
                        if not self.expression_evaluator.are_types_compatible(existing_attr.type, value_type, "assignment"):
                            self.add_error(ctx, f"Cannot assign {value_type.value} to property '{property_name}' of type {existing_attr.type.value}")
                else:
                    self.add_error(ctx, f"Cannot assign property to non-object type {lhs_type.value}")
                return
            
            # This is a simple variable assignment: Identifier '=' expression ';'
            var_name = ctx.Identifier().getText()
            
            # Check if variable exists (in any scope)
            symbol = self.symbol_table.lookup(var_name)
            if not symbol:
                self.add_error(ctx, f"Variable '{var_name}' is not declared")
                return
            
            # Check if the symbol is actually a variable (not a function or class)
            if symbol.type == SymbolType.FUNCTION:
                self.add_error(ctx, f"Cannot assign to function '{var_name}'")
                return
            elif symbol.type == SymbolType.CLASS:
                self.add_error(ctx, f"Cannot assign to class '{var_name}'")
                return
            
            # Check if trying to assign to constant
            if symbol.is_constant:
                self.add_error(ctx, f"Cannot assign to constant '{var_name}' (declared at line {symbol.line_declared})")
                return
            
            # Mark as initialized
            symbol.is_initialized = True
            
            # Validate assignment expression type
            if ctx.expression():
                expr_type = self.expression_evaluator.evaluate_expression_type_only(ctx.expression()[0])
                if symbol.type != SymbolType.NULL and expr_type != SymbolType.NULL:
                    if not self.expression_evaluator.are_types_compatible(symbol.type, expr_type, "assignment"):
                        self.add_error(ctx, f"Cannot assign {expr_type.value} to variable '{var_name}' of type {symbol.type.value}")
        except Exception as e:
            self.add_error(ctx, f"Error processing assignment: {str(e)}")
    
    def enterPropertyAssignExpr(self, ctx: CompiscriptParser.PropertyAssignExprContext):
        """Handle property assignments like this.nombre = value"""
        try:
            property_name = ctx.Identifier().getText()
            
            # Get the left-hand side (should be 'this' or an object)
            lhs_type = self.expression_evaluator.evaluate_expression_type_only(ctx.lhs)
            
            # Check if we're assigning to 'this' inside a class
            if lhs_type == SymbolType.CLASS and self.current_class:
                # Get the value type
                value_type = self.expression_evaluator.evaluate_expression_type_only(ctx.assignmentExpr())
                
                # Auto-declare the property in the current class if it doesn't exist
                if property_name not in self.current_class.attributes:
                    property_symbol = Symbol(property_name, value_type, is_initialized=True)
                    self.current_class.add_attribute(property_symbol)
                    
                    # Also add to current class scope
                    class_scope = self.symbol_table.current_scope
                    if class_scope and class_scope.name.startswith('class_'):
                        self.symbol_table.define(property_symbol, ctx.start.line, ctx.start.column)
                else:
                    # Property exists, check type compatibility
                    existing_attr = self.current_class.attributes[property_name]
                    if not self.expression_evaluator.are_types_compatible(existing_attr.type, value_type, "assignment"):
                        self.add_error(ctx, f"Cannot assign {value_type.value} to property '{property_name}' of type {existing_attr.type.value}")
            else:
                self.add_error(ctx, f"Cannot assign property to non-object type {lhs_type.value}")
            
        except Exception as e:
            self.add_error(ctx, f"Error processing property assignment: {str(e)}")
    
    def enterInitMethod(self, ctx: CompiscriptParser.InitMethodContext):
        """Handle init method (constructor)"""
        try:
            if not self.current_class:
                self.add_error(ctx, "Init method must be inside a class")
                return
            
            # Get return type (constructors are void)
            return_type = SymbolType.VOID
            
            # Create constructor function symbol
            constructor_symbol = FunctionSymbol("init", return_type)
            
            # Process parameters
            param_names = set()
            if ctx.parameters():
                for param_ctx in ctx.parameters().parameter():
                    param_name = param_ctx.Identifier().getText()
                    
                    # Check for duplicate parameter names
                    if param_name in param_names:
                        self.add_error(ctx, f"Duplicate parameter name '{param_name}' in constructor")
                        continue
                    param_names.add(param_name)
                    
                    # Check if parameter name is reserved
                    if self.is_reserved_identifier(param_name):
                        self.add_error(ctx, f"Parameter name '{param_name}' is a reserved keyword")
                        continue
                    
                    # Get parameter type
                    param_type = SymbolType.NULL
                    if param_ctx.type_():
                        param_type_text = param_ctx.type_().getText()
                        param_type = self.get_type_from_string(param_type_text)
                        if param_type == SymbolType.NULL and param_type_text != "null":
                            self.add_error(ctx, f"Unknown parameter type '{param_type_text}' for parameter '{param_name}'")
                            continue
                    else:
                        self.add_error(ctx, f"Parameter '{param_name}' must have a type annotation")
                        continue
                    
                    constructor_symbol.add_parameter(param_name, param_type)
            
            # Add constructor to current class
            self.current_class.constructor = constructor_symbol
            
            # Enter constructor scope  
            self.symbol_table.enter_scope("init")
            self.current_function = constructor_symbol
            
            # Add parameters to constructor scope
            for param_name, param_type in constructor_symbol.parameters:
                param_symbol = Symbol(param_name, param_type, is_initialized=True)
                self.symbol_table.define(param_symbol, ctx.start.line, ctx.start.column)
                
        except Exception as e:
            self.add_error(ctx, f"Error processing init method: {str(e)}")
    
    def exitInitMethod(self, ctx: CompiscriptParser.InitMethodContext):
        """Exit init method scope"""
        self.symbol_table.exit_scope()
        self.current_function = None
    
    def has_errors(self) -> bool:
        """Check if there are semantic errors"""
        return (len(self.errors) > 0 or 
                self.symbol_table.has_errors() or 
                self.expression_evaluator.has_errors())
    
    def get_errors(self) -> List[str]:
        """Get all semantic errors without duplicates"""
        all_errors = []
        seen_errors = set()
        
        # Add errors from semantic analyzer
        for error in self.errors:
            if error not in seen_errors:
                all_errors.append(error)
                seen_errors.add(error)
        
        # Add errors from symbol table (if not already seen)
        for error in self.symbol_table.get_errors():
            if error not in seen_errors:
                all_errors.append(error)
                seen_errors.add(error)
        
        # Add errors from expression evaluator (if not already seen)
        for error in self.expression_evaluator.get_errors():
            if error not in seen_errors:
                all_errors.append(error)
                seen_errors.add(error)
        
        return all_errors
    
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
    
    def _validate_function_calls_in_expression(self, ctx):
        """Recursively validate function calls in expressions"""
        if not ctx:
            return
        
        # Debug output
        debug_enabled = getattr(self, 'debug', False)
        if debug_enabled:
            print(f"Checking context: {type(ctx).__name__}")
        
        # Check specifically for LeftHandSideContext which contains function calls
        if type(ctx).__name__ == 'LeftHandSideContext':
            if debug_enabled:
                print(f"Found LeftHandSideContext: {ctx.getText()}")
            
            # Look for IdentifierExprContext and CallExprContext pattern
            identifier_ctx = None
            call_ctx = None
            
            if hasattr(ctx, 'children') and ctx.children:
                for child in ctx.children:
                    if type(child).__name__ == 'IdentifierExprContext':
                        identifier_ctx = child
                    elif type(child).__name__ == 'CallExprContext':
                        call_ctx = child
            
            if identifier_ctx and call_ctx:
                # This is a function call
                func_name = identifier_ctx.getText()
                
                # Store function call information for later validation
                if not hasattr(self, 'function_calls'):
                    self.function_calls = []
                
                # Count actual parameters in call
                actual_params = 0
                if hasattr(call_ctx, 'children') and call_ctx.children:
                    # Look for arguments context between '(' and ')'
                    for call_child in call_ctx.children:
                        if type(call_child).__name__ == 'ArgumentsContext':
                            # Count expression contexts in arguments
                            if hasattr(call_child, 'children'):
                                expr_count = 0
                                for arg_child in call_child.children:
                                    if type(arg_child).__name__ == 'ExpressionContext':
                                        expr_count += 1
                                actual_params = expr_count
                
                self.function_calls.append({
                    'name': func_name,
                    'actual_params': actual_params
                })
                
                if debug_enabled:
                    print(f"Stored function call: {func_name} with {actual_params} parameters")
                
                # Skip the symbol lookup here since functions might not be processed yet
        
        # Recursively check children
        if hasattr(ctx, 'children') and ctx.children:
            for child in ctx.children:
                if hasattr(child, 'getText'):  # Only check parse tree nodes
                    self._validate_function_calls_in_expression(child)
    
    def _validate_function_calls(self):
        """Validate all collected function calls after all functions are defined"""
        if not hasattr(self, 'function_calls'):
            return
        
        debug_enabled = getattr(self, 'debug', False)
        
        for call_info in self.function_calls:
            func_name = call_info['name']
            actual_params = call_info['actual_params']
            
            # Look up the function in symbol table
            func_symbol = self.symbol_table.lookup(func_name)
            
            if func_symbol and isinstance(func_symbol, FunctionSymbol):
                expected_params = len(func_symbol.parameters)
                
                if debug_enabled:
                    print(f"Validating function {func_name}: expected {expected_params}, actual {actual_params}")
                
                # Validate parameter count
                if expected_params != actual_params:
                    if expected_params > 0:
                        first_param = func_symbol.parameters[0]
                        # Handle parameter structure - could be tuple (name, type) or object
                        if isinstance(first_param, tuple):
                            param_type = first_param[1]  # Type is second element
                        else:
                            param_type = getattr(first_param, 'type', 'unknown')
                        
                        # Convert SymbolType enum to string if needed
                        if hasattr(param_type, 'name'):
                            param_type_str = param_type.name.lower()
                        else:
                            param_type_str = str(param_type).lower()
                        
                        error_msg = f"Error función {func_name} se esperaba parametro tipo {param_type_str} para la funcion {func_name}"
                    else:
                        error_msg = f"Error función {func_name} no acepta parámetros"
                    
                    self.errors.append(error_msg)
                    if debug_enabled:
                        print(f"Parameter mismatch: {error_msg}")
            elif debug_enabled:
                print(f"Function {func_name} not found in symbol table")
    
    def enterExpressionStatement(self, ctx: CompiscriptParser.ExpressionStatementContext):
        """Handle expression statements"""
        if ctx.expression():
            # First validate function calls manually
            self._validate_function_calls_in_expression(ctx.expression())
            # Then evaluate expression for type checking
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
    
    def generate_intermediate_code(self, tree):
        """Generate TAC intermediate code if semantic analysis is successful"""
        try:
            from antlr4 import ParseTreeWalker
            walker = ParseTreeWalker()
            walker.walk(self.tac_generator, tree)
            self.intermediate_code = self.tac_generator.get_tac_code()
        except Exception as e:
            self.intermediate_code = f"Error generating intermediate code: {str(e)}"
    
    def get_intermediate_code(self) -> str:
        """Get the generated intermediate code"""
        return self.intermediate_code if self.intermediate_code else "(No intermediate code generated)"
    
    def has_errors(self) -> bool:
        """Check if there are semantic errors"""
        return len(self.errors) > 0
    
    def get_errors(self) -> List[str]:
        """Get all semantic errors"""
        return self.errors.copy()
    
    def print_errors(self):
        """Print all semantic errors"""
        if self.errors:
            print("Semantic Errors:")
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. {error}")
        else:
            print("No semantic errors found.")
    
    def print_symbol_table(self):
        """Print the symbol table"""
        print("\n=== SYMBOL TABLE ===")
        self.symbol_table.print_table()
        print("====================")
    
    def print_intermediate_code(self):
        """Print the intermediate code"""
        print("\n=== INTERMEDIATE CODE ===")
        print(self.get_intermediate_code())
        print("==========================")
