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
    
    def add_error(self, ctx, message: str):
        """Add a type error with context information"""
        line = ctx.start.line if ctx and ctx.start else "unknown"
        column = ctx.start.column if ctx and ctx.start else "unknown"
        error_msg = f"Line {line}:{column} - {message}"
        self.errors.append(error_msg)
    
    def evaluate_expression(self, ctx) -> SymbolType:
        """Evaluate an expression and return its type"""
        if not ctx:
            return SymbolType.NULL
        
        # Handle different expression types
        if isinstance(ctx, CompiscriptParser.ExpressionContext):
            return self.evaluate_assignment_expr(ctx.assignmentExpr())
        
        return SymbolType.NULL
    
    def _is_numeric(self, t):
        return t in (SymbolType.INTEGER, SymbolType.FLOAT)

    def _numeric_result(self, a, b, op=None):
        # Política sugerida:
        # - Promoción: si alguno es FLOAT -> FLOAT; si no -> INTEGER
        # - División: devuelve FLOAT (convención común). Si prefieres división entera para int/int, cámbialo.
        if op == '/':
            return SymbolType.FLOAT
        return SymbolType.FLOAT if SymbolType.FLOAT in (a, b) else SymbolType.INTEGER

    
    def evaluate_assignment_expr(self, ctx) -> SymbolType:
        """Evaluate assignment expressions"""
        if not ctx:
            return SymbolType.NULL
        
        # Check if it's an assignment
        if hasattr(ctx, 'lhs') and ctx.lhs:
            # Assignment expression
            left_type = self.evaluate_left_hand_side(ctx.lhs)
            right_type = self.evaluate_assignment_expr(ctx.assignmentExpr())
            
            # Check type compatibility
            if not self.are_types_compatible(left_type, right_type, "assignment"):
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
        """Evaluate additive expressions (+, -) with numeric-only operands (int/float)."""
        if not ctx:
            return SymbolType.NULL

        # Un solo operando: delega
        if ctx.getChildCount() == 1:
            return self.evaluate_multiplicative_expr(ctx.multiplicativeExpr(0))

        # Helper local
        def is_numeric(t):
            return t in (SymbolType.INTEGER, SymbolType.FLOAT)

        def numeric_result(a, b):
            # Promoción: si alguno es float -> float; si no -> integer
            return SymbolType.FLOAT if SymbolType.FLOAT in (a, b) else SymbolType.INTEGER

        left_type = self.evaluate_multiplicative_expr(ctx.multiplicativeExpr(0))

        for i in range(1, len(ctx.multiplicativeExpr())):
            right_type = self.evaluate_multiplicative_expr(ctx.multiplicativeExpr(i))
            op = ctx.getChild(2 * i - 1).getText()  # '+' o '-'

            # Ambos deben ser numéricos
            if not (is_numeric(left_type) and is_numeric(right_type)):
                self.add_error(ctx, f"Arithmetic '{op}' requires numeric operands, got {left_type.value} and {right_type.value}")
                left_type = SymbolType.NULL
                continue

            # Resultado con promoción a float si aplica
            left_type = numeric_result(left_type, right_type)

        return left_type

    def evaluate_multiplicative_expr(self, ctx) -> SymbolType:
        if not ctx:
            return SymbolType.NULL
        if ctx.getChildCount() == 1:
            return self.evaluate_unary_expr(ctx.unaryExpr(0))

        def is_numeric(t): return t in (SymbolType.INTEGER, SymbolType.FLOAT)
        def numeric_result(a, b, op):
            return SymbolType.FLOAT if (op == '/' or SymbolType.FLOAT in (a, b)) else SymbolType.INTEGER

        left_type = self.evaluate_unary_expr(ctx.unaryExpr(0))
        for i in range(1, len(ctx.unaryExpr())):
            right_type = self.evaluate_unary_expr(ctx.unaryExpr(i))
            op = ctx.getChild(2 * i - 1).getText()  # '*', '/', '%'

            if op == '%':
                if left_type == SymbolType.INTEGER and right_type == SymbolType.INTEGER:
                    left_type = SymbolType.INTEGER
                else:
                    self.add_error(ctx, f"Modulo requires integer operands, got {left_type.value} and {right_type.value}")
                    left_type = SymbolType.NULL
            else:
                if not (is_numeric(left_type) and is_numeric(right_type)):
                    self.add_error(ctx, f"Arithmetic '{op}' requires numeric operands, got {left_type.value} and {right_type.value}")
                    left_type = SymbolType.NULL
                else:
                    left_type = numeric_result(left_type, right_type, op)

        return left_type

    
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
            if operand_type not in (SymbolType.INTEGER, SymbolType.FLOAT):
                self.add_error(ctx, f"Unary minus requires numeric operand, got {operand_type.value}")
                return SymbolType.NULL
            return operand_type
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
        
        if ctx.Literal():
            literal_text = ctx.Literal().getText()
            # String: "..."
            if len(literal_text) >= 2 and literal_text[0] == '"' and literal_text[-1] == '"':
                return SymbolType.STRING

            # Numérico: float si tiene '.' o exponente (e/E); si no, integer
            if '.' in literal_text or 'e' in literal_text or 'E' in literal_text:
                return SymbolType.FLOAT
            return SymbolType.INTEGER
        elif ctx.arrayLiteral():
            # Array literal - determine element type
            return self.evaluate_array_literal(ctx.arrayLiteral())
        elif ctx.getText() == 'null':
            return SymbolType.NULL
        elif ctx.getText() in ['true', 'false']:
            return SymbolType.BOOLEAN
        
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
        # No aceptes NULL como comodín
        if left == SymbolType.NULL or right == SymbolType.NULL:
            return False

        if operation == "assignment":
            # Mismo tipo o ensanchamiento integer -> float
            return (left == right) or (left == SymbolType.FLOAT and right == SymbolType.INTEGER)

        elif operation in ["+", "-", "*", "/", "%"]:
            # Solo operandos numéricos; el chequeo detallado lo hacen evaluate_additive_expr/multiplicative_expr
            return self._is_numeric(left) and self._is_numeric(right)

        elif operation in ["==", "!="]:
            return left == right

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
