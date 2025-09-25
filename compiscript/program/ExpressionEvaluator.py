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
        self.last_array_base = None
        self.last_array_dims = 0
    
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
    
        # == y !=  (solo mismo tipo entre {integer, string, boolean})
    def evaluate_equality_expr(self, ctx) -> SymbolType:
        if not ctx: return SymbolType.NULL
        if ctx.getChildCount() == 1:
            return self.evaluate_relational_expr(ctx.relationalExpr(0))

        left = self.evaluate_relational_expr(ctx.relationalExpr(0))
        for i in range(1, len(ctx.relationalExpr())):
            right = self.evaluate_relational_expr(ctx.relationalExpr(i))
            op = ctx.getChild(2*i - 1).getText()  # '==' o '!='

            ambos_basicos = (left in (SymbolType.INTEGER, SymbolType.STRING, SymbolType.BOOLEAN) and
                            right in (SymbolType.INTEGER, SymbolType.STRING, SymbolType.BOOLEAN))
            if not (ambos_basicos and left == right):
                self.add_error(ctx, f"El operador '{op}' requiere operandos del mismo tipo "
                                    f"(integer, string o boolean); obtuvo {left.value} y {right.value}")
                return SymbolType.NULL
            left = SymbolType.BOOLEAN
        return SymbolType.BOOLEAN

    # <, <=, >, >=  (solo integer vs integer)
    def evaluate_relational_expr(self, ctx) -> SymbolType:
        if not ctx: return SymbolType.NULL
        if ctx.getChildCount() == 1:
            return self.evaluate_additive_expr(ctx.additiveExpr(0))

        left = self.evaluate_additive_expr(ctx.additiveExpr(0))
        for i in range(1, len(ctx.additiveExpr())):
            right = self.evaluate_additive_expr(ctx.additiveExpr(i))
            op = ctx.getChild(2*i - 1).getText()
            if not (left == SymbolType.INTEGER and right == SymbolType.INTEGER):
                self.add_error(ctx, f"El operador '{op}' requiere integer {op} integer; "
                                    f"obtuvo {left.value} y {right.value}")
                return SymbolType.NULL
            left = SymbolType.BOOLEAN
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
            operator = ctx.getChild(2 * i - 1).getText()  # Get operator
            
            if operator == '+':
                # Addition: ONLY integer + integer OR string + string allowed
                if left_type == SymbolType.INTEGER and right_type == SymbolType.INTEGER:
                    left_type = SymbolType.INTEGER  # Integer addition
                elif left_type == SymbolType.STRING and right_type == SymbolType.STRING:
                    left_type = SymbolType.STRING  # String concatenation
                else:
                    # All other combinations are invalid (including mixing types)
                    self.add_error(ctx, f"Cannot add {left_type.value} and {right_type.value}. Only integer+integer or string+string are allowed.")
                    left_type = SymbolType.NULL
            else:  # operator == '-'
                if left_type != SymbolType.INTEGER or right_type != SymbolType.INTEGER:
                    self.add_error(ctx, f"Subtraction requires integers, got {left_type.value} and {right_type.value}")
                    left_type = SymbolType.NULL
        
        return left_type

    def evaluate_multiplicative_expr(self, ctx) -> SymbolType:
        if not ctx:
            return SymbolType.NULL
        if ctx.getChildCount() == 1:
            return self.evaluate_unary_expr(ctx.unaryExpr(0))

        def is_numeric(t): return t in (SymbolType.INTEGER, SymbolType.FLOAT)
        def numeric_result(a, b, op):
            # For division: integer / integer = integer (integer division)
            #               anything else with float = float  
            if op == '/':
                if a == SymbolType.INTEGER and b == SymbolType.INTEGER:
                    return SymbolType.INTEGER  # Integer division
                else:
                    return SymbolType.FLOAT    # Float division
            else:
                # For *, +, -: float if any operand is float, otherwise integer
                return SymbolType.FLOAT if SymbolType.FLOAT in (a, b) else SymbolType.INTEGER

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
        
        # Check for boolean literals first
        text = ctx.getText()
        if text in ['true', 'false']:
            return SymbolType.BOOLEAN
        elif text == 'null':
            return SymbolType.NULL
        
        if ctx.Literal():
            literal_text = ctx.Literal().getText()
            # String: "..."
            if len(literal_text) >= 2 and literal_text[0] == '"' and literal_text[-1] == '"':
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
        """Evalúa literales de arreglo y setea last_array_base/last_array_dims."""
        exprs = list(ctx.expression() or [])
        if not exprs:
            self.add_error(ctx, "Empty array literal is not allowed")
            self.last_array_base = None
            self.last_array_dims = 0
            return SymbolType.NULL

        # Evalúa cada elemento y recolecta (tipo, base, dims)
        infos = []
        for e in exprs:
            t = self.evaluate_expression(e)
            if t == SymbolType.ARRAY:
                base = self.last_array_base
                dims = self.last_array_dims or 1
            else:
                base = t
                dims = 0
            infos.append((t, base, dims, e))

        # ¿Algún elemento es un arreglo? -> arreglo anidado
# después de construir 'infos' = [(t, base, dims, e), ...]
        # si cualquier hijo fue NULL, ya habrá un mensaje específico: propágalo sin añadir más
        if any(t == SymbolType.NULL for (t, _, _, _) in infos):
            self.last_array_base = None
            self.last_array_dims = 0
            return SymbolType.NULL

        # a partir de aquí, todos son ARRAY; valida homogeneidad (base, dims)
        bases = {b for (_, b, _, _) in infos}
        dims_set = {d for (_, _, d, _) in infos}
        if len(bases) != 1 or len(dims_set) != 1:
            self.add_error(ctx, "Array elements must have the same nested array type")
            self.last_array_base = None
            self.last_array_dims = 0
            return SymbolType.NULL

        inner_base = next(iter(bases))
        inner_dims = next(iter(dims_set))
        self.last_array_base = inner_base
        self.last_array_dims = inner_dims + 1
        return SymbolType.ARRAY


        # Caso 1D: todos son primitivos → homogeneidad estricta
        expected = infos[0][1]  # el tipo base del primer elemento
        ok = self.validate_array_elements_type(exprs, expected, ctx)
        self.last_array_base = expected
        self.last_array_dims = 1
        return SymbolType.ARRAY if ok else SymbolType.NULL


    
    def validate_array_elements_type(self, elements, expected_type, ctx):
        """
        Verifica que todos los elementos de la lista sean del tipo esperado.
        Si algún elemento no es del tipo esperado, agrega un error.
        Retorna True si todos son válidos, False si hay error.
        """
        all_valid = True
        for elem in elements:
            # Si el elemento es un contexto (nodo ANTLR), obtener su tipo y texto
            if hasattr(elem, 'getText'):
                elem_type = self.evaluate_expression(elem)
                elem_value = elem.getText()
            else:
                # Elemento no es contexto: intentar inferir tipo (fallback)
                # Si viene un SymbolType directo, úsalo; en otro caso usar str()
                if isinstance(elem, SymbolType):
                    elem_type = elem
                else:
                    elem_type = None
                elem_value = str(elem)

            # Aplicar reglas estrictas: si la lista fue determinada como INTEGER, solo aceptar INTEGER;
            # si fue STRING, solo aceptar STRING; para otros tipos exigir igualdad.
            allowed = False
            if elem_type is None:
                # No se pudo determinar el tipo del elemento: marcar como inválido
                allowed = False
            elif expected_type == SymbolType.INTEGER:
                allowed = (elem_type == SymbolType.INTEGER)
            elif expected_type == SymbolType.STRING:
                allowed = (elem_type == SymbolType.STRING)
            else:
                allowed = (elem_type == expected_type)

            if not allowed:
                self.add_error(ctx, f"error no se puede agregar {elem_value} dado que la lista es tipo {expected_type.value}")
                all_valid = False

        return all_valid
    
    def evaluate_left_hand_side(self, ctx) -> SymbolType:
        """Evaluate left-hand side expressions (variables, function calls, etc.)"""
        if not ctx:
            return SymbolType.NULL
        
        # Start with primary atom
        base_type = self.evaluate_primary_atom(ctx.primaryAtom())
        
        # Check if the primary atom is 'super' for special handling
        is_super_expression = (hasattr(ctx.primaryAtom(), 'Identifier') and 
                              ctx.primaryAtom().Identifier() and
                              ctx.primaryAtom().Identifier().getText() == 'super')
        
        # Apply suffix operations sequentially, keeping track of context
        current_type = base_type
        suffix_ops = ctx.suffixOp() if hasattr(ctx, 'suffixOp') else []
        
        for i, suffix_ctx in enumerate(suffix_ops):
            suffix_type = type(suffix_ctx).__name__
            
            if suffix_type == 'PropertyAccessExprContext':
                # Property access - check if next operation is a call
                is_followed_by_call = (i + 1 < len(suffix_ops) and 
                                     type(suffix_ops[i + 1]).__name__ == 'CallExprContext')
                
                if is_followed_by_call:
                    # This is method access - store info for method call
                    if hasattr(suffix_ctx, 'Identifier') and suffix_ctx.Identifier():
                        property_name = suffix_ctx.Identifier().getText()
                        self.last_property_name = property_name
                        self.last_object_type = current_type
                        self.is_super_call = is_super_expression  # Track if this is super.method()
                    # Don't change current_type - keep it as the object type
                else:
                    # This is regular property access
                    current_type = self._handle_property_access(suffix_ctx, current_type)
                
            elif suffix_type == 'CallExprContext':
                # Function/method call
                if hasattr(self, 'last_property_name') and hasattr(self, 'last_object_type'):
                    # This is a method call - use the original object type and method name
                    method_name = self.last_property_name
                    object_type = self.last_object_type
                    is_super = getattr(self, 'is_super_call', False)
                    
                    if is_super:
                        current_type = self._handle_super_method_call(suffix_ctx, method_name)
                    else:
                        current_type = self._handle_method_call_with_name(suffix_ctx, object_type, method_name)
                    
                    # Clean up stored attributes
                    delattr(self, 'last_property_name')
                    delattr(self, 'last_object_type')
                    if hasattr(self, 'is_super_call'):
                        delattr(self, 'is_super_call')
                else:
                    # This is a direct function call (like super() or function())
                    if is_super_expression:
                        current_type = SymbolType.VOID  # super() constructor call
                    else:
                        current_type = self.evaluate_suffix_op(suffix_ctx, current_type)
                    
            else:
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
                
                # Special handling for 'super'
                if var_name == 'super':
                    current_scope = self.symbol_table.current_scope
                    while current_scope:
                        if current_scope.name.startswith('class_') or current_scope.name == 'init':
                            # super can be called as a function (constructor) or for property access
                            return SymbolType.CLASS  # Parent class type - can be called or accessed
                        current_scope = current_scope.parent
                    self.add_error(ctx, "'super' can only be used inside a class")
                    return SymbolType.NULL
                
                symbol = self.symbol_table.lookup(var_name)
                if not symbol:
                    # Don't report error for 'super' - it's handled above
                    if var_name != 'super':
                        self.add_error(ctx, f"Undefined identifier '{var_name}'")
                    return SymbolType.NULL
                
                # Check if it's a variable being used before initialization
                if (symbol.type not in [SymbolType.FUNCTION, SymbolType.CLASS] and 
                    not symbol.is_initialized and not symbol.is_constant):
                    self.add_error(ctx, f"Variable '{var_name}' is used before being initialized")
                
                if isinstance(symbol, FunctionSymbol):
                    self.last_function_name = var_name  # Store function name for call resolution
                    return SymbolType.FUNCTION
                elif isinstance(symbol, ClassSymbol):
                    return SymbolType.CLASS
                elif symbol.type == SymbolType.ARRAY:
                    self.last_array_base = symbol.array_type
                    self.last_array_dims = symbol.array_dimensions

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
                
                # Validate constructor parameters
                self._validate_constructor_call(ctx, class_symbol)
                
                # Return the specific class type (we'll use CLASS for now, but could be more specific)
                return SymbolType.CLASS
        
        elif ctx_type == 'SuperExprContext':
            # Super reference
            current_scope = self.symbol_table.current_scope
            while current_scope:
                if current_scope.name.startswith('class_') or current_scope.name == 'init':
                    return SymbolType.CLASS  # Parent class type
                current_scope = current_scope.parent
            
            self.add_error(ctx, "'super' can only be used inside a class")
            return SymbolType.NULL
        
        elif ctx_type == 'ThisExprContext':
            # This reference
            current_scope = self.symbol_table.current_scope
            while current_scope:
                if current_scope.name.startswith('class_') or current_scope.name == 'init':
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
            if base_type == SymbolType.FUNCTION:
                # Direct function call - look up function in symbol table
                return self._handle_function_call(ctx, base_type)
            elif base_type == SymbolType.CLASS:
                # Method call on class instance or super() call
                return self._handle_class_call(ctx, base_type)
            else:
                self.add_error(ctx, f"Cannot call non-function type {base_type.value}")
                return SymbolType.NULL
        
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
            return self._handle_property_access(ctx, base_type)
        
        return base_type
    
    def _handle_class_call(self, ctx, base_type: SymbolType) -> SymbolType:
        """Handle calls on class type (constructor calls, super calls, etc.)"""
        # This could be:
        # 1. super() - calling parent constructor
        # 2. new ClassName() - instantiating a class
        # 3. obj.method() - but this should be handled by _handle_method_call_with_name
        
        # For super() calls, return void (constructors don't return values)
        # For class instantiation, return the class type
        # For now, assume it's a constructor call
        return SymbolType.VOID
    
    def _handle_function_call(self, ctx, base_type: SymbolType) -> SymbolType:
        """Handle direct function calls"""
        # When we reach here, we need to find out what function is being called
        # The function name should be available from the context or symbol table
        
        # Try to get function name from the call context
        # This is tricky because at this point we only have the arguments part
        # We need to look up the function from the symbol table using the stored function reference
        
        # For now, we need to look up recently resolved function symbols
        # This is a limitation - in a full implementation, we'd pass the function symbol down
        
        # Let's check if we can find a function symbol that was recently looked up
        # Check for common function names that return specific types
        if hasattr(self, 'last_function_name'):
            func_name = self.last_function_name
            delattr(self, 'last_function_name')  # Clean up after use
            
            # Look up the function in symbol table to get its return type
            func_symbol = self.symbol_table.lookup(func_name)
            if func_symbol and isinstance(func_symbol, FunctionSymbol):
                # Validate parameter count for direct function calls
                self._validate_parameter_count(ctx, func_symbol, func_name)
                return func_symbol.return_type
            elif func_name == 'toString':
                return SymbolType.STRING
        
        # For user-defined functions, return NULL as default if we can't determine
        return SymbolType.NULL
    
    def _handle_super_method_call(self, ctx, method_name: str) -> SymbolType:
        """Handle super.method() calls"""
        # Determine return type based on parent class method
        if method_name == 'toString':
            return SymbolType.STRING
        elif method_name == 'getName':
            return SymbolType.STRING  
        elif method_name in ['getAge', 'getCredits']:
            return SymbolType.INTEGER
        elif method_name in ['init', 'constructor']:
            return SymbolType.VOID
        
        # Default assumption for unknown parent methods
        return SymbolType.STRING
    
    def _handle_method_call_with_name(self, ctx, base_type: SymbolType, method_name: str) -> SymbolType:
        """Handle method calls on class instances with known method name"""
        if base_type == SymbolType.NULL:
            self.add_error(ctx, f"Cannot call method on null object")
            return SymbolType.NULL
        elif base_type != SymbolType.CLASS:
            self.add_error(ctx, f"Cannot call method on non-object type {base_type.value}")
            return SymbolType.NULL
        
        # Special handling for 'super' methods
        if method_name == 'super':
            # This is super.method() - calling parent class method
            return SymbolType.STRING  # Most parent methods return string (like toString)
        
        # Try to find the method in the symbol table
        method_symbol = None
        
        # First, try to find in global scope (for all class methods)
        global_scope = self.symbol_table.get_global_scope()
        if global_scope:
            method_symbol = global_scope.lookup(method_name)
        
        # If not found globally, look for methods in class scopes
        # We need to search all scopes for class_* scopes
        if not method_symbol or not isinstance(method_symbol, FunctionSymbol):
            for scope in self.symbol_table.scopes:
                if scope.name.startswith('class_'):
                    method_symbol = scope.lookup(method_name)
                    if method_symbol and isinstance(method_symbol, FunctionSymbol):
                        break
        
        # If still not found, look in current scope and parent scopes (fallback)
        if not method_symbol or not isinstance(method_symbol, FunctionSymbol):
            current_scope = self.symbol_table.current_scope
            while current_scope and not method_symbol:
                method_symbol = current_scope.lookup(method_name)
                if method_symbol and isinstance(method_symbol, FunctionSymbol):
                    break
                current_scope = current_scope.parent
        
        # If found, validate parameter count and return the actual return type
        if method_symbol and isinstance(method_symbol, FunctionSymbol):
            # Validate parameter count
            self._validate_parameter_count(ctx, method_symbol, method_name)
            return method_symbol.return_type
        
        # Method not found - this is an error
        self.add_error(ctx, f"Method '{method_name}' does not exist in class")
        return SymbolType.NULL
    
    def _handle_method_call(self, ctx, base_type: SymbolType) -> SymbolType:
        """Handle method calls on class instances"""
        # For method calls on class instances, we need to determine the return type
        # This is a simplified approach - in a full implementation we'd look up the method signature
        
        # Extract method name from context if possible
        method_name = None
        if hasattr(ctx, 'Identifier') and ctx.Identifier():
            method_name = ctx.Identifier().getText()
        elif hasattr(ctx, 'getText'):
            # Try to extract method name from the full text
            call_text = ctx.getText()
            if '(' in call_text:
                method_name = call_text.split('(')[0]
        
        # Determine return type based on method name
        if method_name == 'toString':
            return SymbolType.STRING
        elif method_name == 'length':
            return SymbolType.INTEGER
        elif method_name in ['init', 'constructor']:
            return SymbolType.VOID
        
        # For unknown methods, assume they return a reasonable default
        # In a real implementation, we'd look up the method in the class definition
        return SymbolType.STRING  # Default assumption
    
    def _handle_property_access(self, ctx, base_type: SymbolType) -> SymbolType:
        """Handle property access on objects"""
        if base_type == SymbolType.NULL:
            self.add_error(ctx, f"Cannot access property of null object")
            return SymbolType.NULL
        elif base_type != SymbolType.CLASS:
            self.add_error(ctx, f"Cannot access property of non-object type {base_type.value}")
            return SymbolType.NULL
        
        # Extract property name from context
        property_name = None
        if hasattr(ctx, 'IDENTIFIER') and ctx.IDENTIFIER():
            property_name = ctx.IDENTIFIER().getText()
        elif hasattr(ctx, 'Identifier') and ctx.Identifier():
            property_name = ctx.Identifier().getText()
        else:
            return SymbolType.NULL
            
        # If this is a method name (will be followed by CallExpr), return FUNCTION type
        # Common method names that we recognize
        if property_name in ['toString', 'getName', 'getAge', 'length']:
            return SymbolType.FUNCTION
        
        # Special handling for super.property access
        # When we access super.toString, we want to treat it as a method that can be called
        if hasattr(self, 'last_property_name') and self.last_property_name == 'super':
            # This is accessing a property/method on super
            if property_name == 'toString':
                return SymbolType.FUNCTION
            
        # Try to find the property in current class scope or parent classes
        current_scope = self.symbol_table.current_scope
        while current_scope:
            if current_scope.name.startswith('class_'):
                # Look for the property in this class scope
                property_symbol = current_scope.lookup(property_name)
                if property_symbol:
                    return property_symbol.type
                break
            current_scope = current_scope.parent
        
        # Try to find the property in ALL class scopes (for obj.property access)
        property_found = False
        for scope in self.symbol_table.scopes:
            if scope.name.startswith('class_'):
                property_symbol = scope.lookup(property_name)
                if property_symbol:
                    property_found = True
                    return property_symbol.type
        
        # Property not found - this is an error
        self.add_error(ctx, f"Property '{property_name}' does not exist in class")
        return SymbolType.NULL
    
    def are_types_compatible(self, left: SymbolType, right: SymbolType, operation: str) -> bool:
        # No aceptes NULL como comodín
        if left == SymbolType.NULL or right == SymbolType.NULL:
            return False

        if operation == "assignment":
            # For assignments, types must match exactly (no implicit conversions)
            return left == right
        elif operation in ["==", "!="]:
            return left == right
        elif operation in ["+", "-", "*", "/", "%"]:
            if operation == "+":
                # Addition: ONLY integer + integer OR string + string
                return ((left == SymbolType.INTEGER and right == SymbolType.INTEGER) or
                       (left == SymbolType.STRING and right == SymbolType.STRING))
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
    
    def _validate_parameter_count(self, ctx, function_symbol: FunctionSymbol, function_name: str):
        """Validate that the number of arguments matches the function signature"""
        # Count the arguments passed in the call
        argument_count = 0
        if hasattr(ctx, 'arguments') and ctx.arguments():
            # Count the expressions in the arguments
            if hasattr(ctx.arguments(), 'expression') and ctx.arguments().expression():
                argument_expressions = ctx.arguments().expression()
                if isinstance(argument_expressions, list):
                    argument_count = len(argument_expressions)
                else:
                    argument_count = 1  # Single argument
        
        # Get expected parameter count
        expected_count = len(function_symbol.parameters)
        
        # Validate the counts match
        if argument_count != expected_count:
            self.add_error(ctx, f"Function '{function_name}' expects {expected_count} parameter(s), but {argument_count} were provided")
    
    def _validate_constructor_call(self, ctx, class_symbol):
        """Validate constructor call parameters"""
        if not isinstance(class_symbol, ClassSymbol):
            return
        
        # Get constructor
        constructor = class_symbol.constructor
        if not constructor:
            # No constructor defined - check if arguments were provided
            argument_count = 0
            if hasattr(ctx, 'arguments') and ctx.arguments():
                if hasattr(ctx.arguments(), 'expression') and ctx.arguments().expression():
                    argument_expressions = ctx.arguments().expression()
                    if isinstance(argument_expressions, list):
                        argument_count = len(argument_expressions)
                    else:
                        argument_count = 1
            
            if argument_count > 0:
                self.add_error(ctx, f"Class '{class_symbol.name}' has no constructor, but {argument_count} argument(s) were provided")
            return
        
        # Validate constructor parameters
        self._validate_parameter_count(ctx, constructor, f"{class_symbol.name} constructor")
