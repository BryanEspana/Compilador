"""
Intermediate Code Generator for Compiscript compiler
Generates Three-Address Code (TAC) from AST using semantic analysis
"""

from CompiscriptParser import CompiscriptParser
from CompiscriptListener import CompiscriptListener
from ExtendedSymbolTable import (
    ExtendedSymbolTable, ExtendedSymbol, ExtendedFunctionSymbol, ExtendedClassSymbol,
    ActivationRecord, MemoryType, SymbolType
)
from TACInstruction import TACGenerator, TACOperation, TACInstruction
from typing import Dict, List, Optional, Any, Union
import sys

class IntermediateCodeGenerator(CompiscriptListener):
    """Generates Three-Address Code from AST using semantic analysis"""
    
    def __init__(self, symbol_table: ExtendedSymbolTable = None):
        self.symbol_table = symbol_table or ExtendedSymbolTable()
        self.tac_generator = TACGenerator()
        self.current_function: Optional[ExtendedFunctionSymbol] = None
        self.current_class: Optional[ExtendedClassSymbol] = None
        self.current_activation_record: Optional[ActivationRecord] = None
        self.in_loop = 0
        self.loop_labels: List[str] = []
        self.errors: List[str] = []
        
        # Track expression results for complex expressions
        self.expression_results: Dict[str, ExtendedSymbol] = {}
        
        # Initialize built-ins
        self._init_builtins()
    
    def _init_builtins(self):
        """Initialize built-in functions with TAC generation"""
        # Print function
        print_func = ExtendedFunctionSymbol("print", SymbolType.VOID)
        print_func.add_parameter("value", SymbolType.STRING)
        self.symbol_table.global_scope.define(print_func)
    
    def add_error(self, ctx, message: str):
        """Add an error with context information"""
        try:
            line = ctx.start.line if ctx and ctx.start else "unknown"
            column = ctx.start.column if ctx and ctx.start else "unknown"
            error_msg = f"Line {line}:{column} - {message}"
            self.errors.append(error_msg)
        except Exception as e:
            self.errors.append(f"Error: {str(e)}")
    
    def get_tac_code(self) -> str:
        """Get the generated TAC code as string"""
        return self.tac_generator.to_string()
    
    def get_instructions(self) -> List[TACInstruction]:
        """Get the generated TAC instructions"""
        return self.tac_generator.get_instructions()
    
    def print_tac_code(self):
        """Print the generated TAC code"""
        self.tac_generator.print_instructions()
    
    # ==================== PROGRAM STRUCTURE ====================
    
    def enterProgram(self, ctx: CompiscriptParser.ProgramContext):
        """Enter program - initialize global scope"""
        self.tac_generator.add_comment("=== COMPISCRIPT PROGRAM ===")
    
    def exitProgram(self, ctx: CompiscriptParser.ProgramContext):
        """Exit program - finalize TAC generation"""
        self.tac_generator.add_comment("=== END OF PROGRAM ===")
    
    # ==================== VARIABLE DECLARATIONS ====================
    
    def enterVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        """Handle variable declarations"""
        if not ctx.Identifier():
            return
        
        var_name = ctx.Identifier().getText()
        
        # Get type annotation if present
        var_type = SymbolType.INTEGER  # Default type
        if ctx.typeAnnotation() and ctx.typeAnnotation().type_():
            var_type = self._get_symbol_type(ctx.typeAnnotation().type_().getText())
        
        # Create extended symbol
        symbol = ExtendedSymbol(var_name, var_type)
        
        # Define in symbol table
        if not self.symbol_table.define(symbol, ctx.start.line, ctx.start.column):
            self.add_error(ctx, f"Variable '{var_name}' already declared")
            return
        
        # Generate TAC for initialization if present
        if ctx.initializer() and ctx.initializer().expression():
            self.tac_generator.add_comment(f"Initialize variable {var_name}")
            result_symbol = self._evaluate_expression(ctx.initializer().expression())
            if result_symbol:
                self.tac_generator.add_assign(var_name, result_symbol.name)
                symbol.is_initialized = True
    
    def _get_symbol_type(self, type_str: str) -> SymbolType:
        """Convert string type to SymbolType"""
        type_map = {
            'integer': SymbolType.INTEGER,
            'string': SymbolType.STRING,
            'boolean': SymbolType.BOOLEAN,
            'float': SymbolType.FLOAT,
            'void': SymbolType.VOID
        }
        return type_map.get(type_str, SymbolType.INTEGER)
    
    # ==================== EXPRESSIONS ====================
    
    def _evaluate_expression(self, ctx) -> Optional[ExtendedSymbol]:
        """Evaluate expression and return result symbol"""
        if not ctx:
            return None
        
        # Handle different expression types based on context type
        ctx_type = type(ctx).__name__
        
        if 'AssignmentExprContext' in ctx_type:
            return self._evaluate_assignment(ctx)
        elif 'ConditionalExprContext' in ctx_type:
            return self._evaluate_conditional(ctx)
        elif 'LogicalOrExprContext' in ctx_type:
            return self._evaluate_logical_or(ctx)
        elif 'LogicalAndExprContext' in ctx_type:
            return self._evaluate_logical_and(ctx)
        elif 'EqualityExprContext' in ctx_type:
            return self._evaluate_equality(ctx)
        elif 'RelationalExprContext' in ctx_type:
            return self._evaluate_relational(ctx)
        elif 'AdditiveExprContext' in ctx_type:
            return self._evaluate_additive(ctx)
        elif 'MultiplicativeExprContext' in ctx_type:
            return self._evaluate_multiplicative(ctx)
        elif 'UnaryExprContext' in ctx_type:
            return self._evaluate_unary(ctx)
        elif 'PrimaryExprContext' in ctx_type:
            return self._evaluate_primary(ctx)
        elif 'LeftHandSideContext' in ctx_type:
            return self._evaluate_left_hand_side(ctx)
        
        # Fallback to attribute-based checking
        if hasattr(ctx, 'primary') and ctx.primary():
            return self._evaluate_primary(ctx.primary())
        elif hasattr(ctx, 'leftHandSide') and ctx.leftHandSide():
            return self._evaluate_left_hand_side(ctx.leftHandSide())
        elif hasattr(ctx, 'unary') and ctx.unary():
            return self._evaluate_unary(ctx)
        elif hasattr(ctx, 'multiplicative') and ctx.multiplicative():
            return self._evaluate_multiplicative(ctx)
        elif hasattr(ctx, 'additive') and ctx.additive():
            return self._evaluate_additive(ctx)
        elif hasattr(ctx, 'relational') and ctx.relational():
            return self._evaluate_relational(ctx)
        elif hasattr(ctx, 'equality') and ctx.equality():
            return self._evaluate_equality(ctx)
        elif hasattr(ctx, 'logicalAnd') and ctx.logicalAnd():
            return self._evaluate_logical_and(ctx)
        elif hasattr(ctx, 'logicalOr') and ctx.logicalOr():
            return self._evaluate_logical_or(ctx)
        elif hasattr(ctx, 'assignment') and ctx.assignment():
            return self._evaluate_assignment(ctx)
        
        return None
    
    def _evaluate_conditional(self, ctx) -> Optional[ExtendedSymbol]:
        """Evaluate conditional expressions (ternary operator)"""
        if hasattr(ctx, 'logicalOrExpr') and ctx.logicalOrExpr():
            return self._evaluate_logical_or(ctx.logicalOrExpr())
        return None
    
    def _evaluate_primary(self, ctx) -> Optional[ExtendedSymbol]:
        """Evaluate primary expressions (literals, identifiers, etc.)"""
        if hasattr(ctx, 'literalExpr') and ctx.literalExpr():
            return self._evaluate_literal(ctx.literalExpr())
        elif hasattr(ctx, 'leftHandSide') and ctx.leftHandSide():
            return self._evaluate_left_hand_side(ctx.leftHandSide())
        elif hasattr(ctx, 'expression') and ctx.expression():
            return self._evaluate_expression(ctx.expression())
        
        return None
    
    def _evaluate_literal(self, ctx) -> Optional[ExtendedSymbol]:
        """Evaluate literal expressions"""
        if hasattr(ctx, 'IntegerLiteral') and ctx.IntegerLiteral():
            value = ctx.IntegerLiteral().getText()
            temp = self.symbol_table.allocate_temporary(SymbolType.INTEGER)
            self.tac_generator.add_assign(temp.name, value)
            return temp
        
        elif hasattr(ctx, 'StringLiteral') and ctx.StringLiteral():
            value = ctx.StringLiteral().getText()
            temp = self.symbol_table.allocate_temporary(SymbolType.STRING)
            self.tac_generator.add_assign(temp.name, value)
            return temp
        
        elif hasattr(ctx, 'BooleanLiteral') and ctx.BooleanLiteral():
            value = ctx.BooleanLiteral().getText()
            temp = self.symbol_table.allocate_temporary(SymbolType.BOOLEAN)
            self.tac_generator.add_assign(temp.name, value)
            return temp
        
        elif hasattr(ctx, 'null') and ctx.null():
            temp = self.symbol_table.allocate_temporary(SymbolType.NULL)
            self.tac_generator.add_assign(temp.name, "null")
            return temp
        
        elif hasattr(ctx, 'true') and ctx.true():
            temp = self.symbol_table.allocate_temporary(SymbolType.BOOLEAN)
            self.tac_generator.add_assign(temp.name, "true")
            return temp
        
        elif hasattr(ctx, 'false') and ctx.false():
            temp = self.symbol_table.allocate_temporary(SymbolType.BOOLEAN)
            self.tac_generator.add_assign(temp.name, "false")
            return temp
        
        return None
    
    def _evaluate_left_hand_side(self, ctx) -> Optional[ExtendedSymbol]:
        """Evaluate left hand side expressions including function calls"""
        if hasattr(ctx, 'primaryAtom') and ctx.primaryAtom():
            atom = ctx.primaryAtom()
            if hasattr(atom, 'Identifier') and atom.Identifier():
                var_name = atom.Identifier().getText()
                symbol = self.symbol_table.lookup(var_name)
                if not symbol:
                    self.add_error(ctx, f"Variable '{var_name}' not declared")
                    return None
                
                # Check for function calls
                if hasattr(ctx, 'suffixOp') and ctx.suffixOp():
                    for suffix in ctx.suffixOp():
                        if hasattr(suffix, 'arguments') and suffix.arguments():
                            # This is a function call
                            return self._handle_function_call(var_name, suffix.arguments())
                
                return symbol
        elif hasattr(ctx, 'Identifier') and ctx.Identifier():
            # Direct identifier access
            var_name = ctx.Identifier().getText()
            symbol = self.symbol_table.lookup(var_name)
            if not symbol:
                self.add_error(ctx, f"Variable '{var_name}' not declared")
                return None
            return symbol
        
        return None
    
    def _handle_function_call(self, func_name: str, arguments_ctx) -> Optional[ExtendedSymbol]:
        """Handle function call with arguments"""
        func_symbol = self.symbol_table.lookup(func_name)
        
        if not func_symbol or not isinstance(func_symbol, ExtendedFunctionSymbol):
            return None
        
        # Evaluate arguments
        arg_count = 0
        if arguments_ctx and hasattr(arguments_ctx, 'expression') and arguments_ctx.expression():
            for arg in arguments_ctx.expression():
                result = self._evaluate_expression(arg)
                if result:
                    self.tac_generator.add_param(result.name)
                    arg_count += 1
        
        # Generate function call
        result_temp = self.symbol_table.allocate_temporary(func_symbol.return_type)
        self.tac_generator.add_call(func_name, arg_count, result_temp.name)
        
        return result_temp
    
    def _evaluate_unary(self, ctx) -> Optional[ExtendedSymbol]:
        """Evaluate unary expressions"""
        if not hasattr(ctx, 'unaryOp') or not ctx.unaryOp():
            return self._evaluate_primary(ctx.primary())
        
        op = ctx.unaryOp().getText()
        operand = self._evaluate_primary(ctx.primary())
        
        if not operand:
            return None
        
        result = self.symbol_table.allocate_temporary(operand.type)
        
        if op == '-':
            self.tac_generator.add_neg(result.name, operand.name)
        elif op == '!':
            self.tac_generator.add_not(result.name, operand.name)
        
        return result
    
    def _evaluate_multiplicative(self, ctx) -> Optional[ExtendedSymbol]:
        """Evaluate multiplicative expressions (*, /, %)"""
        if hasattr(ctx, 'unary') and ctx.unary():
            left = self._evaluate_unary(ctx.unary())
            if not left:
                return None
            
            if hasattr(ctx, 'multiplicativeOp') and ctx.multiplicativeOp():
                op = ctx.multiplicativeOp().getText()
                right = self._evaluate_multiplicative(ctx.multiplicative())
                
                if not right:
                    return left
                
                result = self.symbol_table.allocate_temporary(left.type)
                
                if op == '*':
                    self.tac_generator.add_mul(result.name, left.name, right.name)
                elif op == '/':
                    self.tac_generator.add_div(result.name, left.name, right.name)
                elif op == '%':
                    self.tac_generator.add_mod(result.name, left.name, right.name)
                
                return result
            else:
                return left
        
        return None
    
    def _evaluate_additive(self, ctx) -> Optional[ExtendedSymbol]:
        """Evaluate additive expressions (+, -)"""
        if hasattr(ctx, 'multiplicative') and ctx.multiplicative():
            left = self._evaluate_multiplicative(ctx.multiplicative())
            if not left:
                return None
            
            if hasattr(ctx, 'additiveOp') and ctx.additiveOp():
                op = ctx.additiveOp().getText()
                right = self._evaluate_additive(ctx.additive())
                
                if not right:
                    return left
                
                result = self.symbol_table.allocate_temporary(left.type)
                
                if op == '+':
                    if left.type == SymbolType.STRING or right.type == SymbolType.STRING:
                        self.tac_generator.add_concat(result.name, left.name, right.name)
                    else:
                        self.tac_generator.add_add(result.name, left.name, right.name)
                elif op == '-':
                    self.tac_generator.add_sub(result.name, left.name, right.name)
                
                return result
            else:
                return left
        
        return None
    
    def _evaluate_relational(self, ctx) -> Optional[ExtendedSymbol]:
        """Evaluate relational expressions (<, <=, >, >=)"""
        if hasattr(ctx, 'additive') and ctx.additive():
            left = self._evaluate_additive(ctx.additive())
            if not left:
                return None
            
            if hasattr(ctx, 'relationalOp') and ctx.relationalOp():
                op = ctx.relationalOp().getText()
                right = self._evaluate_relational(ctx.relational())
                
                if not right:
                    return left
                
                result = self.symbol_table.allocate_temporary(SymbolType.BOOLEAN)
                
                if op == '<':
                    self.tac_generator.add_lt(result.name, left.name, right.name)
                elif op == '<=':
                    self.tac_generator.add_le(result.name, left.name, right.name)
                elif op == '>':
                    self.tac_generator.add_gt(result.name, left.name, right.name)
                elif op == '>=':
                    self.tac_generator.add_ge(result.name, left.name, right.name)
                
                return result
            else:
                return left
        
        return None
    
    def _evaluate_equality(self, ctx) -> Optional[ExtendedSymbol]:
        """Evaluate equality expressions (==, !=)"""
        if hasattr(ctx, 'relational') and ctx.relational():
            left = self._evaluate_relational(ctx.relational())
            if not left:
                return None
            
            if hasattr(ctx, 'equalityOp') and ctx.equalityOp():
                op = ctx.equalityOp().getText()
                right = self._evaluate_equality(ctx.equality())
                
                if not right:
                    return left
                
                result = self.symbol_table.allocate_temporary(SymbolType.BOOLEAN)
                
                if op == '==':
                    self.tac_generator.add_eq(result.name, left.name, right.name)
                elif op == '!=':
                    self.tac_generator.add_ne(result.name, left.name, right.name)
                
                return result
            else:
                return left
        
        return None
    
    def _evaluate_logical_and(self, ctx) -> Optional[ExtendedSymbol]:
        """Evaluate logical AND expressions (&&)"""
        if hasattr(ctx, 'equality') and ctx.equality():
            left = self._evaluate_equality(ctx.equality())
            if not left:
                return None
            
            if hasattr(ctx, 'logicalAndOp') and ctx.logicalAndOp():
                right = self._evaluate_logical_and(ctx.logicalAnd())
                
                if not right:
                    return left
                
                result = self.symbol_table.allocate_temporary(SymbolType.BOOLEAN)
                self.tac_generator.add_and(result.name, left.name, right.name)
                
                return result
            else:
                return left
        
        return None
    
    def _evaluate_logical_or(self, ctx) -> Optional[ExtendedSymbol]:
        """Evaluate logical OR expressions (||)"""
        if hasattr(ctx, 'logicalAnd') and ctx.logicalAnd():
            left = self._evaluate_logical_and(ctx.logicalAnd())
            if not left:
                return None
            
            if hasattr(ctx, 'logicalOrOp') and ctx.logicalOrOp():
                right = self._evaluate_logical_or(ctx.logicalOr())
                
                if not right:
                    return left
                
                result = self.symbol_table.allocate_temporary(SymbolType.BOOLEAN)
                self.tac_generator.add_or(result.name, left.name, right.name)
                
                return result
            else:
                return left
        
        return None
    
    def _evaluate_assignment(self, ctx) -> Optional[ExtendedSymbol]:
        """Evaluate assignment expressions"""
        if hasattr(ctx, 'leftHandSide') and ctx.leftHandSide():
            lhs = ctx.leftHandSide()
            if hasattr(lhs, 'Identifier') and lhs.Identifier():
                var_name = lhs.Identifier().getText()
                symbol = self.symbol_table.lookup(var_name)
                
                if not symbol:
                    self.add_error(ctx, f"Variable '{var_name}' not declared")
                    return None
                
                if symbol.is_constant:
                    self.add_error(ctx, f"Cannot assign to constant '{var_name}'")
                    return None
                
                # Evaluate right-hand side
                if hasattr(ctx, 'assignmentExpr') and ctx.assignmentExpr():
                    result = self._evaluate_expression(ctx.assignmentExpr())
                    if result:
                        self.tac_generator.add_assign(var_name, result.name)
                        symbol.is_initialized = True
                        return result
                
                return symbol
        
        return None
    
    # ==================== CONTROL FLOW ====================
    
    def enterIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        """Handle if statements with else"""
        if not ctx.expression():
            return
        
        # Evaluate condition
        condition = self._evaluate_expression(ctx.expression())
        if not condition:
            return
        
        # Generate labels
        else_label = self.symbol_table.generate_label("else")
        end_label = self.symbol_table.generate_label("endif")
        
        # Generate conditional jump
        self.tac_generator.add_if_false(condition.name, else_label)
        
        # Store labels for else and end
        self.loop_labels.extend([else_label, end_label])
    
    def exitIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        """Exit if statement"""
        if len(self.loop_labels) >= 2:
            else_label = self.loop_labels[-2]
            end_label = self.loop_labels[-1]
            
            # Check if there's an else block
            if ctx.block() and len(ctx.block()) > 1:  # Has else block
                # Jump to end after if block
                self.tac_generator.add_goto(end_label)
                # Generate else label
                self.tac_generator.add_label(else_label)
            else:
                # No else block, just generate end label
                self.tac_generator.add_label(end_label)
            
            # Remove labels
            self.loop_labels = self.loop_labels[:-2]
    
    def enterWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        """Handle while statements"""
        if not ctx.expression():
            return
        
        # Generate labels
        loop_label = self.symbol_table.generate_label("while")
        end_label = self.symbol_table.generate_label("endwhile")
        
        # Store labels
        self.loop_labels.extend([loop_label, end_label])
        self.in_loop += 1
        
        # Generate loop start
        self.tac_generator.add_label(loop_label)
        
        # Evaluate condition
        condition = self._evaluate_expression(ctx.expression())
        if condition:
            self.tac_generator.add_if_false(condition.name, end_label)
    
    def exitWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        """Exit while statement"""
        if len(self.loop_labels) >= 2:
            loop_label = self.loop_labels[-2]
            end_label = self.loop_labels[-1]
            
            # Jump back to loop start
            self.tac_generator.add_goto(loop_label)
            
            # Generate end label
            self.tac_generator.add_label(end_label)
            
            # Remove labels
            self.loop_labels = self.loop_labels[:-2]
        
        self.in_loop = max(0, self.in_loop - 1)
    
    # ==================== FUNCTIONS ====================
    
    def enterFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        """Handle function declarations"""
        if not ctx.Identifier():
            return
        
        func_name = ctx.Identifier().getText()
        return_type = SymbolType.VOID  # Default return type
        if ctx.type_():
            return_type = self._get_symbol_type(ctx.type_().getText())
        
        # Create function symbol
        func_symbol = ExtendedFunctionSymbol(func_name, return_type)
        
        # Add parameters
        if ctx.parameters() and ctx.parameters().parameter():
            for param in ctx.parameters().parameter():
                if param.Identifier() and param.type_():
                    param_name = param.Identifier().getText()
                    param_type = self._get_symbol_type(param.type_().getText())
                    func_symbol.add_parameter(param_name, param_type)
        
        # Define function in symbol table
        if not self.symbol_table.define(func_symbol, ctx.start.line, ctx.start.column):
            self.add_error(ctx, f"Function '{func_name}' already declared")
            return
        
        self.current_function = func_symbol
        
        # Create activation record
        self.current_activation_record = self.symbol_table.create_function_activation_record(func_symbol)
        
        # Enter function scope
        self.symbol_table.enter_scope(f"function_{func_name}")
        
        # Generate function label
        self.tac_generator.add_label(f"function_{func_name}")
    
    def exitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        """Exit function declaration"""
        if self.current_function:
            # Generate return if no explicit return
            if not self._has_explicit_return():
                self.tac_generator.add_return()
            
            # Exit function scope
            self.symbol_table.exit_scope()
            self.current_function = None
            self.current_activation_record = None
    
    def _has_explicit_return(self) -> bool:
        """Check if function has explicit return statement"""
        # This is a simplified check - in practice, you'd track this during parsing
        return False
    
    def enterReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        """Handle return statements"""
        if not self.current_function:
            self.add_error(ctx, "Return statement outside function")
            return
        
        if ctx.expression():
            result = self._evaluate_expression(ctx.expression())
            if result:
                self.tac_generator.add_return(result.name)
        else:
            self.tac_generator.add_return()
    
    # ==================== FUNCTION CALLS ====================
    
    def enterCallExpr(self, ctx: CompiscriptParser.CallExprContext):
        """Handle function calls"""
        # This is called when we encounter a function call in suffixOp
        # The function name should be in the parent context
        pass  # We'll handle this in the expression evaluation
    
    # ==================== PRINT STATEMENTS ====================
    
    def enterPrintStatement(self, ctx: CompiscriptParser.PrintStatementContext):
        """Handle print statements"""
        if hasattr(ctx, 'expression') and ctx.expression():
            result = self._evaluate_expression(ctx.expression())
            if result:
                self.tac_generator.add_print(result.name)
    
    # ==================== ERROR HANDLING ====================
    
    def get_errors(self) -> List[str]:
        """Get all errors"""
        return self.errors.copy()
    
    def has_errors(self) -> bool:
        """Check if there are errors"""
        return len(self.errors) > 0
