"""
Expression Evaluator for Compiscript compiler
Handles type checking and evaluation of expressions
"""

from CompiscriptParser import CompiscriptParser
from SymbolTable import SymbolTable, Symbol, FunctionSymbol, ClassSymbol, SymbolType
from typing import Optional, List, Union, Any

class ExpressionEvaluator:
    """Evaluates expressions and performs type checking"""
    
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.errors: List[str] = []
        self.suppress_assignment_errors = False  # Flag to suppress assignment error reporting
    
    def add_error(self, ctx, message: str):
        """Add a type error with context information"""
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
        except Exception as e:
            # Fallback error handling
            fallback_msg = f"Error processing type error: {str(e)}"
            self.errors.append(fallback_msg)
    
    def evaluate_expression_type_only(self, ctx) -> SymbolType:
        """Evaluate an expression and return its type without reporting assignment errors"""
        old_suppress = self.suppress_assignment_errors
        self.suppress_assignment_errors = True
        try:
            result = self.evaluate_expression(ctx)
            return result
        finally:
            self.suppress_assignment_errors = old_suppress
    
    def evaluate_expression(self, ctx) -> SymbolType:
        """Evaluate an expression and return its type"""
        if not ctx:
            return SymbolType.NULL
        
        try:
            # Handle different expression types
            if isinstance(ctx, CompiscriptParser.ExpressionContext):
                return self.evaluate_assignment_expr(ctx.assignmentExpr())
            
            return SymbolType.NULL
        except Exception as e:
            # Add error but continue processing
            self.add_error(ctx, f"Error evaluating expression: {str(e)}")
            return SymbolType.NULL
    
    def evaluate_assignment_expr(self, ctx) -> SymbolType:
        """Evaluate assignment expressions"""
        if not ctx:
            return SymbolType.NULL
        
        # Check if it's an assignment
        if hasattr(ctx, 'lhs') and ctx.lhs:
            # Assignment expression
            left_type = self.evaluate_left_hand_side(ctx.lhs)
            right_type = self.evaluate_assignment_expr(ctx.assignmentExpr())
            
            # Check type compatibility (only report if not suppressed)
            if not self.are_types_compatible(left_type, right_type, "assignment"):
                if not self.suppress_assignment_errors:
                    self.add_error(ctx, f"Cannot assign {right_type.value} to {left_type.value}")
            
            return left_type
        else:
            # Not an assignment, evaluate as conditional expression
            return self.evaluate_conditional_expr(ctx.conditionalExpr())
    
    def evaluate_conditional_expr(self, ctx) -> SymbolType:
        """Evaluate ternary conditional expressions"""
        if not ctx:
            return SymbolType.NULL
        
        # Check if it's a ternary expression
        if ctx.getChildCount() > 1:  # Has ? and :
            condition_type = self.evaluate_logical_or_expr(ctx.logicalOrExpr())
            true_type = self.evaluate_expression(ctx.expression(0))
            false_type = self.evaluate_expression(ctx.expression(1))
            
            # Condition must be boolean
            if condition_type != SymbolType.BOOLEAN:
                self.add_error(ctx, f"Ternary condition must be boolean, got {condition_type.value}")
            
            # Both branches should have compatible types
            if not self.are_types_compatible(true_type, false_type, "ternary"):
                self.add_error(ctx, f"Ternary branches have incompatible types: {true_type.value} and {false_type.value}")
                return SymbolType.NULL
            
            return true_type
        else:
            return self.evaluate_logical_or_expr(ctx.logicalOrExpr())
    
    def evaluate_logical_or_expr(self, ctx) -> SymbolType:
        """Evaluate logical OR expressions"""
        if not ctx:
            return SymbolType.NULL
        
        if ctx.getChildCount() == 1:
            return self.evaluate_logical_and_expr(ctx.logicalAndExpr(0))
        
        # Multiple operands with ||
        result_type = SymbolType.BOOLEAN
        for i in range(len(ctx.logicalAndExpr())):
            operand_type = self.evaluate_logical_and_expr(ctx.logicalAndExpr(i))
            if operand_type != SymbolType.BOOLEAN:
                self.add_error(ctx, f"Logical OR operand must be boolean, got {operand_type.value}")
                result_type = SymbolType.NULL
        
        return result_type
    
    def evaluate_logical_and_expr(self, ctx) -> SymbolType:
        """Evaluate logical AND expressions"""
        if not ctx:
            return SymbolType.NULL
        
        if ctx.getChildCount() == 1:
            return self.evaluate_equality_expr(ctx.equalityExpr(0))
        
        # Multiple operands with &&
        result_type = SymbolType.BOOLEAN
        for i in range(len(ctx.equalityExpr())):
            operand_type = self.evaluate_equality_expr(ctx.equalityExpr(i))
            if operand_type != SymbolType.BOOLEAN:
                self.add_error(ctx, f"Logical AND operand must be boolean, got {operand_type.value}")
                result_type = SymbolType.NULL
        
        return result_type
    
    def evaluate_equality_expr(self, ctx) -> SymbolType:
        """Evaluate equality expressions (==, !=)"""
        if not ctx:
            return SymbolType.NULL
        
        if ctx.getChildCount() == 1:
            return self.evaluate_relational_expr(ctx.relationalExpr(0))
        
        # Multiple operands with == or !=
        left_type = self.evaluate_relational_expr(ctx.relationalExpr(0))
        
        for i in range(1, len(ctx.relationalExpr())):
            right_type = self.evaluate_relational_expr(ctx.relationalExpr(i))
            operator = ctx.getChild(2 * i - 1).getText()  # Get operator
            
            if not self.are_types_compatible(left_type, right_type, operator):
                self.add_error(ctx, f"Cannot compare {left_type.value} and {right_type.value} with {operator}")
            
            left_type = right_type
        
        return SymbolType.BOOLEAN
    
    def evaluate_relational_expr(self, ctx) -> SymbolType:
        """Evaluate relational expressions (<, <=, >, >=)"""
        if not ctx:
            return SymbolType.NULL
        
        if ctx.getChildCount() == 1:
            return self.evaluate_additive_expr(ctx.additiveExpr(0))
        
        # Multiple operands with relational operators
        left_type = self.evaluate_additive_expr(ctx.additiveExpr(0))
        
        for i in range(1, len(ctx.additiveExpr())):
            right_type = self.evaluate_additive_expr(ctx.additiveExpr(i))
            operator = ctx.getChild(2 * i - 1).getText()  # Get operator
            
            if not self.are_types_compatible(left_type, right_type, operator):
                self.add_error(ctx, f"Cannot compare {left_type.value} and {right_type.value} with {operator}")
            
            left_type = right_type
        
        return SymbolType.BOOLEAN
    
    def evaluate_additive_expr(self, ctx) -> SymbolType:
        """Evaluate additive expressions (+, -)"""
        if not ctx:
            return SymbolType.NULL
        
        if ctx.getChildCount() == 1:
            return self.evaluate_multiplicative_expr(ctx.multiplicativeExpr(0))
        
        # Multiple operands with + or -
        left_type = self.evaluate_multiplicative_expr(ctx.multiplicativeExpr(0))
        
        for i in range(1, len(ctx.multiplicativeExpr())):
            right_type = self.evaluate_multiplicative_expr(ctx.multiplicativeExpr(i))
            operator = ctx.getChild(2 * i - 1).getText()  # Get operator
            
            if operator == '+':
                # Addition allows integer + integer or string concatenation
                if left_type == SymbolType.STRING or right_type == SymbolType.STRING:
                    left_type = SymbolType.STRING  # String concatenation
                elif left_type == SymbolType.INTEGER and right_type == SymbolType.INTEGER:
                    left_type = SymbolType.INTEGER  # Integer addition
                else:
                    self.add_error(ctx, f"Cannot add {left_type.value} and {right_type.value}")
                    left_type = SymbolType.NULL
            else:  # operator == '-'
                if left_type != SymbolType.INTEGER or right_type != SymbolType.INTEGER:
                    self.add_error(ctx, f"Subtraction requires integers, got {left_type.value} and {right_type.value}")
                    left_type = SymbolType.NULL
        
        return left_type
    
    def evaluate_multiplicative_expr(self, ctx) -> SymbolType:
        """Evaluate multiplicative expressions (*, /, %)"""
        if not ctx:
            return SymbolType.NULL
        
        if ctx.getChildCount() == 1:
            return self.evaluate_unary_expr(ctx.unaryExpr(0))
        
        # Multiple operands with *, /, or %
        left_type = self.evaluate_unary_expr(ctx.unaryExpr(0))
        
        for i in range(1, len(ctx.unaryExpr())):
            right_type = self.evaluate_unary_expr(ctx.unaryExpr(i))
            operator = ctx.getChild(2 * i - 1).getText()  # Get operator
            
            if not self.are_types_compatible(left_type, right_type, operator):
                self.add_error(ctx, f"Arithmetic operation {operator} requires integers, got {left_type.value} and {right_type.value}")
                left_type = SymbolType.NULL
        
        return left_type if left_type != SymbolType.NULL else SymbolType.INTEGER
    
    def evaluate_unary_expr(self, ctx) -> SymbolType:
        """Evaluate unary expressions (-, !)"""
        if not ctx:
            return SymbolType.NULL
        
        if ctx.getChildCount() == 1:
            return self.evaluate_primary_expr(ctx.primaryExpr())
        
        # Unary operator
        operator = ctx.getChild(0).getText()
        operand_type = self.evaluate_unary_expr(ctx.unaryExpr())
        
        if operator == '-':
            if operand_type != SymbolType.INTEGER:
                self.add_error(ctx, f"Unary minus requires integer, got {operand_type.value}")
                return SymbolType.NULL
            return SymbolType.INTEGER
        elif operator == '!':
            if operand_type != SymbolType.BOOLEAN:
                self.add_error(ctx, f"Logical NOT requires boolean, got {operand_type.value}")
                return SymbolType.NULL
            return SymbolType.BOOLEAN
        
        return SymbolType.NULL
    
    def evaluate_primary_expr(self, ctx) -> SymbolType:
        """Evaluate primary expressions"""
        if not ctx:
            return SymbolType.NULL
        
        if ctx.literalExpr():
            return self.evaluate_literal_expr(ctx.literalExpr())
        elif ctx.leftHandSide():
            return self.evaluate_left_hand_side(ctx.leftHandSide())
        elif ctx.expression():
            # Parenthesized expression
            return self.evaluate_expression(ctx.expression())
        
        return SymbolType.NULL
    
    def evaluate_literal_expr(self, ctx) -> SymbolType:
        """Evaluate literal expressions"""
        if not ctx:
            return SymbolType.NULL
        
        # Check for boolean literals first
        text = ctx.getText()
        if text in ['true', 'false']:
            return SymbolType.BOOLEAN
        elif text == 'null':
            return SymbolType.NULL
        
        if ctx.Literal():
            literal_text = ctx.Literal().getText()
            if literal_text.startswith('"') and literal_text.endswith('"'):
                return SymbolType.STRING
            elif literal_text in ['true', 'false']:
                return SymbolType.BOOLEAN
            else:
                # All numeric literals (integers, floats, etc.) are treated as INTEGER
                return SymbolType.INTEGER
        elif ctx.arrayLiteral():
            # Array literal - determine element type
            return self.evaluate_array_literal(ctx.arrayLiteral())
        
        return SymbolType.NULL
    
    def evaluate_array_literal(self, ctx) -> SymbolType:
        """Evaluate array literals"""
        if not ctx or not ctx.expression():
            return SymbolType.ARRAY  # Empty array
        
        # Check all elements have the same type
        element_type = None
        for expr_ctx in ctx.expression():
            expr_type = self.evaluate_expression(expr_ctx)
            if element_type is None:
                element_type = expr_type
            elif element_type != expr_type:
                self.add_error(ctx, f"Array elements must have the same type, found {element_type.value} and {expr_type.value}")
                return SymbolType.NULL
        
        return SymbolType.ARRAY  # Should store element type info
    
    def evaluate_left_hand_side(self, ctx) -> SymbolType:
        """Evaluate left-hand side expressions (variables, function calls, etc.)"""
        if not ctx:
            return SymbolType.NULL
        
        # Start with primary atom
        base_type = self.evaluate_primary_atom(ctx.primaryAtom())
        
        # Apply suffix operations
        current_type = base_type
        for suffix_ctx in ctx.suffixOp():
            current_type = self.evaluate_suffix_op(suffix_ctx, current_type)
        
        return current_type
    
    def evaluate_primary_atom(self, ctx) -> SymbolType:
        """Evaluate primary atoms (identifiers, new expressions, this)"""
        if not ctx:
            return SymbolType.NULL
        
        # Check the specific type of primary atom based on context type
        ctx_type = type(ctx).__name__
        
        if ctx_type == 'IdentifierExprContext':
            # Variable or function reference
            if hasattr(ctx, 'Identifier') and ctx.Identifier():
                var_name = ctx.Identifier().getText()
                symbol = self.symbol_table.lookup(var_name)
                if not symbol:
                    self.add_error(ctx, f"Undefined identifier '{var_name}'")
                    return SymbolType.NULL
                

                
                if isinstance(symbol, FunctionSymbol):
                    return SymbolType.FUNCTION
                elif isinstance(symbol, ClassSymbol):
                    return SymbolType.CLASS
                elif symbol.type == SymbolType.ARRAY:
                    return SymbolType.ARRAY
                else:
                    return symbol.type
        
        elif ctx_type == 'NewExprContext':
            # New expression
            if hasattr(ctx, 'Identifier') and ctx.Identifier():
                class_name = ctx.Identifier().getText()
                class_symbol = self.symbol_table.lookup(class_name)
                if not class_symbol or class_symbol.type != SymbolType.CLASS:
                    self.add_error(ctx, f"Class '{class_name}' not found")
                    return SymbolType.NULL
                # Return the specific class type (we'll use CLASS for now, but could be more specific)
                return SymbolType.CLASS
        
        elif ctx_type == 'ThisExprContext':
            # This reference
            current_scope = self.symbol_table.current_scope
            while current_scope:
                if current_scope.name.startswith('class_'):
                    return SymbolType.CLASS  # Current class type
                current_scope = current_scope.parent
            
            self.add_error(ctx, "'this' can only be used inside a class")
            return SymbolType.NULL
        
        return SymbolType.NULL
    
    def evaluate_suffix_op(self, ctx, base_type: SymbolType) -> SymbolType:
        """Evaluate suffix operations (function calls, array access, property access)"""
        if not ctx:
            return base_type
        
        # Check the specific type of suffix operation based on context type
        ctx_type = type(ctx).__name__
        

        
        if ctx_type == 'CallExprContext':
            # Function call
            if base_type != SymbolType.FUNCTION and base_type != SymbolType.CLASS:
                self.add_error(ctx, f"Cannot call non-function type {base_type.value}")
                return SymbolType.NULL
            
            # For class method calls, try to determine return type
            if base_type == SymbolType.CLASS:
                # This is a method call on a class instance
                # For now, return a generic type (could be improved to look up the actual method)
                return SymbolType.NULL  # Simplified - could return the method's return type
            else:
                # This is a function call
                # For now, return a generic type (could be improved to look up the actual function)
                return SymbolType.NULL  # Simplified - could return the function's return type
        
        elif ctx_type == 'IndexExprContext':
            # Array indexing
            if base_type != SymbolType.ARRAY:
                self.add_error(ctx, f"Cannot index non-array type {base_type.value}")
                return SymbolType.NULL
            
            if hasattr(ctx, 'expression') and ctx.expression():
                index_type = self.evaluate_expression(ctx.expression())
                if index_type != SymbolType.INTEGER:
                    self.add_error(ctx, f"Array index must be integer, got {index_type.value}")
            
            return SymbolType.NULL  # Should return array element type
        
        elif ctx_type == 'PropertyAccessExprContext':
            # Property access
            if base_type != SymbolType.CLASS and base_type != SymbolType.NULL:
                self.add_error(ctx, f"Cannot access property of non-object type {base_type.value}")
                return SymbolType.NULL
            
            # For class instances, allow property access (simplified)
            # In a full implementation, we would look up the property in the class definition
            # For now, return the same type as the base (class instance)
            return base_type  # Return the class type instead of NULL
        
        return base_type
    
    def are_types_compatible(self, left: SymbolType, right: SymbolType, operation: str) -> bool:
        """Check if two types are compatible for a given operation"""
        if left == SymbolType.NULL or right == SymbolType.NULL:
            return True  # Null is compatible with everything (simplified)
        
        if operation == "assignment":
            # For assignments, types must match exactly (no implicit conversions)
            return left == right
        elif operation in ["==", "!="]:
            return left == right
        elif operation in ["+", "-", "*", "/", "%"]:
            if operation == "+":
                # String concatenation or integer addition
                return ((left == SymbolType.STRING or right == SymbolType.STRING) or 
                       (left == SymbolType.INTEGER and right == SymbolType.INTEGER))
            else:
                # Arithmetic operations require integers
                return left == SymbolType.INTEGER and right == SymbolType.INTEGER
        elif operation in ["<", "<=", ">", ">="]:
            return left == right and left in [SymbolType.INTEGER, SymbolType.STRING]
        elif operation in ["&&", "||"]:
            return left == SymbolType.BOOLEAN and right == SymbolType.BOOLEAN
        elif operation == "ternary":
            return left == right
        
        return False
    
    def get_errors(self) -> List[str]:
        """Get all type errors"""
        return self.errors.copy()
    
    def has_errors(self) -> bool:
        """Check if there are type errors"""
        return len(self.errors) > 0
