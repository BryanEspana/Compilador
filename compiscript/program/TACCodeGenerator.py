"""
Three-Address Code (TAC) Generator for Compiscript compiler
Generates TAC following the exact specification:
- Temporales: t0, t1, t2, ...
- Frame pointer: fp[k] para acceder a slots
- Llamadas: CALL f (y el valor de retorno queda en R)
- Asignación del retorno: tX := R
- Parámetros: PARAM argN antes del CALL f (emit_params flag)
- Saltos/labels: LABEL_..., IF t > 0 GOTO L (verdadero ≡ entero > 0)
- Funciones: FUNCTION name: ...cuerpo... END FUNCTION name
"""

from CompiscriptParser import CompiscriptParser
from CompiscriptListener import CompiscriptListener
from typing import Dict, List, Optional, Any, Union
import sys

class TACCodeGenerator(CompiscriptListener):
    """Generates Three-Address Code from AST following exact specification"""
    
    def __init__(self, emit_params: bool = True):
        self.instructions: List[str] = []
        self.temp_counter = 0
        self.label_counter = 0
        self.fp_counter = 0
        self.emit_params = emit_params
        
        # Stack para gestionar contextos
        self.current_function = None
        self.function_stack: List[str] = []
        self.scope_depth = 0
        self.loop_labels: List[tuple] = []  # (continue_label, break_label)
        
        # Mapeo de variables a fp slots
        self.variable_slots: Dict[str, int] = {}
        self.current_slot = 0
        
        # Resultados de expresiones para el visitor pattern
        self.expression_results: Dict[int, str] = {}
    
    def new_temp(self) -> str:
        """Genera un nuevo temporal: t0, t1, t2, ..."""
        temp_name = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp_name
    
    def new_label(self, prefix: str = "LABEL") -> str:
        """Genera un nuevo label: LABEL_1, LABEL_2, ..."""
        label_name = f"{prefix}_{self.label_counter}"
        self.label_counter += 1
        return label_name
    
    def new_fp_slot(self, var_name: str = None) -> int:
        """Asigna un nuevo slot fp[k]"""
        slot = self.current_slot
        self.current_slot += 1
        if var_name:
            self.variable_slots[var_name] = slot
        return slot
    
    def get_fp_slot(self, var_name: str) -> str:
        """Obtiene el slot fp[k] para una variable"""
        if var_name not in self.variable_slots:
            self.new_fp_slot(var_name)
        return f"fp[{self.variable_slots[var_name]}]"
    
    def emit(self, instruction: str):
        """Emite una instrucción TAC"""
        if instruction.strip():  # No líneas en blanco
            self.instructions.append(instruction)
    
    def emit_label(self, label: str):
        """Emite un label"""
        self.emit(f"{label}:")
    
    def emit_goto(self, label: str):
        """Emite GOTO label"""
        self.emit(f"GOTO {label}")
    
    def emit_if_goto(self, condition: str, label: str):
        """Emite IF condition > 0 GOTO label"""
        self.emit(f"IF {condition} > 0 GOTO {label}")
    
    def emit_assign(self, target: str, source: str):
        """Emite asignación: target := source"""
        self.emit(f"{target} := {source}")
    
    def emit_binary_op(self, result: str, left: str, op: str, right: str):
        """Emite operación binaria: result := left op right"""
        self.emit(f"{result} := {left} {op} {right}")
    
    def emit_unary_op(self, result: str, op: str, operand: str):
        """Emite operación unaria: result := op operand"""
        self.emit(f"{result} := {op} {operand}")
    
    def emit_param(self, arg: str):
        """Emite PARAM arg"""
        if self.emit_params:
            self.emit(f"PARAM {arg}")
    
    def emit_call(self, func_name: str):
        """Emite CALL f"""
        self.emit(f"CALL {func_name}")
    
    def emit_return(self, value: str = None):
        """Emite RETURN value"""
        if value:
            self.emit(f"RETURN {value}")
        else:
            self.emit("RETURN")
    
    def get_tac_code(self) -> str:
        """Obtiene el código TAC generado como string"""
        return "\n".join(self.instructions)
    
    def print_tac_code(self):
        """Imprime el código TAC generado"""
        print("=== THREE-ADDRESS CODE ===")
        for i, instruction in enumerate(self.instructions):
            print(f"{i+1:3d}: {instruction}")
        print("===========================")
    
    # ==================== PROGRAM STRUCTURE ====================
    
    def enterProgram(self, ctx: CompiscriptParser.ProgramContext):
        """Entrada del programa"""
        self.emit("// === COMPISCRIPT PROGRAM ===")
    
    def exitProgram(self, ctx: CompiscriptParser.ProgramContext):
        """Salida del programa"""
        self.emit("// === END OF PROGRAM ===")
    
    # ==================== FUNCTION DECLARATIONS ====================
    
    def enterFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        """Entrada de declaración de función"""
        if not ctx.Identifier():
            return
        
        func_name = ctx.Identifier().getText()
        self.current_function = func_name
        self.function_stack.append(func_name)
        self.scope_depth += 1
        
        # Resetear slots para nueva función
        old_slots = self.variable_slots.copy()
        old_slot_counter = self.current_slot
        self.variable_slots.clear()
        self.current_slot = 0
        
        # Asignar slots para parámetros (negativos si lo prefieres)
        if ctx.parameters() and ctx.parameters().parameter():
            for i, param in enumerate(ctx.parameters().parameter()):
                if param.Identifier():
                    param_name = param.Identifier().getText()
                    # Usar slots negativos para parámetros
                    self.variable_slots[param_name] = -(i + 1)
        
        self.emit(f"FUNCTION {func_name}:")
    
    def exitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        """Salida de declaración de función"""
        if self.current_function:
            # Asegurar que hay un RETURN al final
            if not self.instructions or not self.instructions[-1].strip().startswith("RETURN"):
                self.emit("RETURN")
            
            self.emit(f"END FUNCTION {self.current_function}")
            
            self.function_stack.pop()
            self.current_function = self.function_stack[-1] if self.function_stack else None
            self.scope_depth -= 1
    
    # ==================== VARIABLE DECLARATIONS ====================
    
    def enterVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        """Declaración de variable"""
        if not ctx.Identifier():
            return
        
        var_name = ctx.Identifier().getText()
        slot = self.get_fp_slot(var_name)
        
        # Si hay inicializador, evaluarlo
        if ctx.initializer() and ctx.initializer().expression():
            result = self.visit_expression(ctx.initializer().expression())
            self.emit_assign(slot, result)
        else:
            # Verificar si hay asignación directa en el texto
            text = ctx.getText()
            if "=" in text:
                # Buscar posibles llamadas a función en la inicialización
                if "(" in text and ")" in text:
                    # Es posible que sea una llamada a función, dejar que se procese después
                    self.emit_assign(slot, "0")  # Temporal
                else:
                    # Extraer valor inicial básico
                    parts = text.split("=")
                    if len(parts) > 1:
                        value = parts[1].strip().rstrip(";")
                        if value.isdigit():
                            self.emit_assign(slot, value)
                        elif value.startswith('"') and value.endswith('"'):
                            self.emit_assign(slot, value)
                        elif value == "true":
                            self.emit_assign(slot, "1")
                        elif value == "false":
                            self.emit_assign(slot, "0")
                        else:
                            # Puede ser una variable
                            if value.isalnum():
                                self.emit_assign(slot, self.get_fp_slot(value))
                            else:
                                self.emit_assign(slot, "0")
                    else:
                        self.emit_assign(slot, "0")
            else:
                self.emit_assign(slot, "0")
    
    # ==================== EXPRESSIONS ====================
    
    def visit_expression(self, ctx) -> str:
        """Visita una expresión y retorna el temporal con el resultado"""
        if not ctx:
            return "0"
        
        # Usar id del contexto como clave para evitar problemas de hash
        ctx_id = id(ctx)
        if ctx_id in self.expression_results:
            return self.expression_results[ctx_id]
        
        result = self._evaluate_expression(ctx)
        self.expression_results[ctx_id] = result
        return result
    
    def _evaluate_expression(self, ctx) -> str:
        """Evalúa una expresión específica"""
        if not ctx:
            return "0"
        
        # Verificar que el contexto tiene getText
        if not hasattr(ctx, 'getText'):
            return "0"
        
        # Obtener el texto completo para casos simples
        text = ctx.getText()
        
        # Casos simples: literales directos
        if text.isdigit():
            return text
        
        if text.startswith('"') and text.endswith('"'):
            return text
        
        if text == "true":
            return "1"
        
        if text == "false":
            return "0"
        
        # Variables simples (sin operaciones)
        if text.isalnum() and not text.isdigit():
            return self.get_fp_slot(text)
        
        # Analizar expresiones más complejas
        ctx_type = type(ctx).__name__
        
        # Literales usando método correcto
        if hasattr(ctx, 'IntegerLiteral') and ctx.IntegerLiteral():
            return ctx.IntegerLiteral().getText()
        
        if hasattr(ctx, 'StringLiteral') and ctx.StringLiteral():
            return ctx.StringLiteral().getText()
        
        if hasattr(ctx, 'BooleanLiteral') and ctx.BooleanLiteral():
            return "1" if ctx.BooleanLiteral().getText() == "true" else "0"
        
        # Variables (identificadores)
        if hasattr(ctx, 'Identifier') and ctx.Identifier():
            var_name = ctx.Identifier().getText()
            return self.get_fp_slot(var_name)
        
        # Expresiones con children (más robusto)
        if hasattr(ctx, 'children') and ctx.children:
            result = self._evaluate_from_children(ctx)
            if result != "0":
                return result
        
        # Intentar parsear expresiones binarias desde el texto
        result = self._parse_binary_expression(text)
        if result:
            return result
        
        # Fallback para expresiones anidadas
        for attr in ['expression', 'primary', 'literalExpr', 'leftHandSide']:
            if hasattr(ctx, attr):
                child = getattr(ctx, attr)
                if callable(child):
                    child_ctx = child()
                    if child_ctx:
                        return self.visit_expression(child_ctx)
                elif child:
                    return self.visit_expression(child)
        
        return "0"  # Fallback
    
    def _parse_binary_expression(self, text: str) -> str:
        """Parsea expresiones binarias simples desde texto"""
        if not text:
            return None
        
        # Verificar si hay paréntesis para llamadas a función
        if "(" in text and ")" in text and not any(op in text for op in ['||', '&&', '==', '!=', '<=', '>=', '<', '>', '+', '-', '*', '/', '%']):
            # Posible llamada a función
            func_match = text.split('(', 1)
            if len(func_match) == 2:
                func_name = func_match[0].strip()
                args_text = func_match[1].rstrip(')')
                
                # Emitir parámetros simples
                if args_text.strip():
                    args = [arg.strip() for arg in args_text.split(',') if arg.strip()]
                    for arg in args:
                        arg_result = self._evaluate_simple_operand(arg)
                        if self.emit_params:
                            self.emit_param(arg_result)
                
                # Emitir llamada
                self.emit_call(func_name)
                
                # Retornar resultado
                result = self.new_temp()
                self.emit_assign(result, "R")
                return result
        
        # Operadores en orden de precedencia (de menor a mayor)
        operators = ['||', '&&', '==', '!=', '<=', '>=', '<', '>', '+', '-', '*', '/', '%']
        
        for op in operators:
            if op in text and not (text.startswith('"') and text.endswith('"')):
                parts = text.split(op, 1)  # Solo el primer split
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    # Evaluar recursivamente
                    left_result = self._evaluate_simple_operand(left)
                    right_result = self._evaluate_simple_operand(right)
                    
                    # Generar código TAC
                    result = self.new_temp()
                    self.emit_binary_op(result, left_result, op, right_result)
                    return result
        
        return None
    
    def _evaluate_simple_operand(self, operand: str) -> str:
        """Evalúa un operando simple"""
        operand = operand.strip()
        
        if operand.isdigit():
            return operand
        
        if operand.startswith('"') and operand.endswith('"'):
            return operand
        
        if operand == "true":
            return "1"
        
        if operand == "false":
            return "0"
        
        if operand.isalnum():
            return self.get_fp_slot(operand)
        
        return "0"
    
    def _evaluate_from_children(self, ctx) -> str:
        """Evalúa expresión desde los children del contexto"""
        if not hasattr(ctx, 'children') or not ctx.children:
            return "0"
        
        children = ctx.children
        
        # Caso con 3 children: operando1 operador operando2
        if len(children) == 3:
            left_child = children[0]
            op_child = children[1]
            right_child = children[2]
            
            # Si el operador es un token terminal, obtener texto
            if hasattr(op_child, 'getText'):
                op_text = op_child.getText()
            else:
                op_text = str(op_child)
            
            # Evaluar operandos recursivamente
            left_result = self.visit_expression(left_child) if hasattr(left_child, 'getText') else self._evaluate_simple_operand(str(left_child))
            right_result = self.visit_expression(right_child) if hasattr(right_child, 'getText') else self._evaluate_simple_operand(str(right_child))
            
            result = self.new_temp()
            self.emit_binary_op(result, left_result, op_text, right_result)
            return result
        
        # Caso con 2 children: operador unario + operando
        elif len(children) == 2:
            op_child = children[0]
            operand_child = children[1]
            
            op_text = op_child.getText() if hasattr(op_child, 'getText') else str(op_child)
            operand_result = self.visit_expression(operand_child) if hasattr(operand_child, 'getText') else self._evaluate_simple_operand(str(operand_child))
            
            result = self.new_temp()
            self.emit_unary_op(result, op_text, operand_result)
            return result
        
        # Caso con 1 child: evaluar el child
        elif len(children) == 1:
            child = children[0]
            if hasattr(child, 'getText'):
                child_text = child.getText()
                # Si es un contexto complejo, evaluarlo recursivamente
                if hasattr(child, 'children'):
                    return self.visit_expression(child)
                else:
                    return self._evaluate_simple_operand(child_text)
            else:
                return self._evaluate_simple_operand(str(child))
        
        return "0"
    
    def _handle_additive_expression(self, ctx) -> str:
        """Maneja expresiones aditivas (+, -)"""
        # Buscar operandos y operador
        operands = []
        operators = []
        
        # Buscar en los hijos del contexto
        if hasattr(ctx, 'multiplicative') and ctx.multiplicative():
            operands.append(self.visit_expression(ctx.multiplicative()))
        
        if hasattr(ctx, 'additive') and ctx.additive():
            operands.append(self.visit_expression(ctx.additive()))
        
        if hasattr(ctx, 'additiveOp') and ctx.additiveOp():
            operators.append(ctx.additiveOp().getText())
        
        # Si no hay operador, retornar el primer operando
        if not operators or len(operands) < 2:
            return operands[0] if operands else "0"
        
        # Generar código para la operación
        result = self.new_temp()
        self.emit_binary_op(result, operands[0], operators[0], operands[1])
        return result
    
    def _handle_multiplicative_expression(self, ctx) -> str:
        """Maneja expresiones multiplicativas (*, /, %)"""
        operands = []
        operators = []
        
        if hasattr(ctx, 'unary') and ctx.unary():
            operands.append(self.visit_expression(ctx.unary()))
        
        if hasattr(ctx, 'multiplicative') and ctx.multiplicative():
            operands.append(self.visit_expression(ctx.multiplicative()))
        
        if hasattr(ctx, 'multiplicativeOp') and ctx.multiplicativeOp():
            operators.append(ctx.multiplicativeOp().getText())
        
        if not operators or len(operands) < 2:
            return operands[0] if operands else "0"
        
        result = self.new_temp()
        self.emit_binary_op(result, operands[0], operators[0], operands[1])
        return result
    
    def _handle_relational_expression(self, ctx) -> str:
        """Maneja expresiones relacionales (<, <=, >, >=)"""
        operands = []
        operators = []
        
        if hasattr(ctx, 'additive') and ctx.additive():
            operands.append(self.visit_expression(ctx.additive()))
        
        if hasattr(ctx, 'relational') and ctx.relational():
            operands.append(self.visit_expression(ctx.relational()))
        
        if hasattr(ctx, 'relationalOp') and ctx.relationalOp():
            operators.append(ctx.relationalOp().getText())
        
        if not operators or len(operands) < 2:
            return operands[0] if operands else "0"
        
        result = self.new_temp()
        self.emit_binary_op(result, operands[0], operators[0], operands[1])
        return result
    
    def _handle_equality_expression(self, ctx) -> str:
        """Maneja expresiones de igualdad (==, !=)"""
        operands = []
        operators = []
        
        if hasattr(ctx, 'relational') and ctx.relational():
            operands.append(self.visit_expression(ctx.relational()))
        
        if hasattr(ctx, 'equality') and ctx.equality():
            operands.append(self.visit_expression(ctx.equality()))
        
        if hasattr(ctx, 'equalityOp') and ctx.equalityOp():
            operators.append(ctx.equalityOp().getText())
        
        if not operators or len(operands) < 2:
            return operands[0] if operands else "0"
        
        result = self.new_temp()
        self.emit_binary_op(result, operands[0], operators[0], operands[1])
        return result
    
    def _handle_logical_and_expression(self, ctx) -> str:
        """Maneja expresiones lógicas AND (&&)"""
        operands = []
        
        if hasattr(ctx, 'equality') and ctx.equality():
            operands.append(self.visit_expression(ctx.equality()))
        
        if hasattr(ctx, 'logicalAnd') and ctx.logicalAnd():
            operands.append(self.visit_expression(ctx.logicalAnd()))
        
        if len(operands) < 2:
            return operands[0] if operands else "0"
        
        result = self.new_temp()
        self.emit_binary_op(result, operands[0], "&&", operands[1])
        return result
    
    def _handle_logical_or_expression(self, ctx) -> str:
        """Maneja expresiones lógicas OR (||)"""
        operands = []
        
        if hasattr(ctx, 'logicalAnd') and ctx.logicalAnd():
            operands.append(self.visit_expression(ctx.logicalAnd()))
        
        if hasattr(ctx, 'logicalOr') and ctx.logicalOr():
            operands.append(self.visit_expression(ctx.logicalOr()))
        
        if len(operands) < 2:
            return operands[0] if operands else "0"
        
        result = self.new_temp()
        self.emit_binary_op(result, operands[0], "||", operands[1])
        return result
    
    def _handle_unary_expression(self, ctx) -> str:
        """Maneja expresiones unarias (-, !)"""
        if hasattr(ctx, 'unaryOp') and ctx.unaryOp():
            op = ctx.unaryOp().getText()
            if hasattr(ctx, 'primary') and ctx.primary():
                operand = self.visit_expression(ctx.primary())
                result = self.new_temp()
                self.emit_unary_op(result, op, operand)
                return result
        
        # Si no hay operador unario, evaluar el primary
        if hasattr(ctx, 'primary') and ctx.primary():
            return self.visit_expression(ctx.primary())
        
        return "0"
    
    def _handle_left_hand_side(self, ctx) -> str:
        """Maneja lado izquierdo (variables, llamadas a función)"""
        # Verificar si es una llamada a función
        if hasattr(ctx, 'suffixOp') and ctx.suffixOp():
            for suffix in ctx.suffixOp():
                if hasattr(suffix, 'arguments') and suffix.arguments():
                    # Es una llamada a función
                    func_name = None
                    if hasattr(ctx, 'primaryAtom') and ctx.primaryAtom():
                        if hasattr(ctx.primaryAtom(), 'Identifier'):
                            func_name = ctx.primaryAtom().Identifier().getText()
                    
                    if func_name:
                        return self._handle_function_call(func_name, suffix.arguments())
        
        # Es una variable simple
        if hasattr(ctx, 'primaryAtom') and ctx.primaryAtom():
            if hasattr(ctx.primaryAtom(), 'Identifier'):
                var_name = ctx.primaryAtom().Identifier().getText()
                return self.get_fp_slot(var_name)
        
        if hasattr(ctx, 'Identifier') and ctx.Identifier():
            var_name = ctx.Identifier().getText()
            return self.get_fp_slot(var_name)
        
        return "0"
    
    def _handle_function_call(self, func_name: str, arguments_ctx) -> str:
        """Maneja llamadas a función"""
        # Evaluar argumentos y emitir PARAM si está habilitado
        if arguments_ctx:
            # Intentar obtener expresiones de diferentes formas
            expressions = None
            if hasattr(arguments_ctx, 'expression'):
                expressions = arguments_ctx.expression()
            elif hasattr(arguments_ctx, 'children'):
                # Buscar expresiones en los children
                expressions = []
                for child in arguments_ctx.children:
                    if hasattr(child, 'getText') and child.getText() not in [',', '(', ')']:
                        expressions.append(child)
            
            if expressions:
                if isinstance(expressions, list):
                    for arg in expressions:
                        if hasattr(arg, 'getText'):
                            arg_result = self.visit_expression(arg)
                            self.emit_param(arg_result)
                else:
                    # Es una sola expresión
                    if hasattr(expressions, 'getText'):
                        arg_result = self.visit_expression(expressions)
                        self.emit_param(arg_result)
        
        # Emitir CALL
        self.emit_call(func_name)
        
        # El resultado queda en R, asignarlo a un temporal
        result = self.new_temp()
        self.emit_assign(result, "R")
        return result
    
    # ==================== STATEMENTS ====================
    
    def enterExpressionStatement(self, ctx: CompiscriptParser.ExpressionStatementContext):
        """Statement de expresión"""
        if ctx.expression():
            self.visit_expression(ctx.expression())
    
    def enterAssignment(self, ctx: CompiscriptParser.AssignmentContext):
        """Asignación directa"""
        if not ctx.Identifier():
            return
        
        var_name = ctx.Identifier().getText()
        var_slot = self.get_fp_slot(var_name)
        
        # Verificar si expression() devuelve una lista o un contexto único
        expr = ctx.expression()
        if expr:
            if isinstance(expr, list):
                # Si es una lista, tomar el primer elemento
                if len(expr) > 0:
                    rhs = self.visit_expression(expr[0])
                else:
                    rhs = "0"
            else:
                # Es un contexto único
                rhs = self.visit_expression(expr)
            self.emit_assign(var_slot, rhs)
    
    # ==================== CONTROL FLOW ====================
    
    def enterIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        """Statement if"""
        if not ctx.expression():
            return
        
        # Evaluar condición
        condition = self.visit_expression(ctx.expression())
        
        # Generar labels
        else_label = self.new_label("ELSE")
        end_label = self.new_label("ENDIF")
        
        # IF condition > 0 GOTO else_label (saltar si falso)
        # Invertir la lógica: si condition <= 0, saltar a else
        temp_condition = self.new_temp()
        self.emit_assign(temp_condition, condition)
        
        # Emitir salto condicional invertido
        self.emit(f"IF {temp_condition} <= 0 GOTO {else_label}")
        
        # Guardar labels para usar en exit
        self.loop_labels.append((else_label, end_label))
    
    def exitIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        """Salida de if statement"""
        if not self.loop_labels:
            return
        
        else_label, end_label = self.loop_labels.pop()
        
        # Verificar si hay bloque else
        if ctx.block() and len(ctx.block()) > 1:  # Hay else
            self.emit_goto(end_label)
            self.emit_label(else_label)
            # El bloque else se procesa automáticamente
        else:
            # No hay else, solo emitir el label
            self.emit_label(else_label)
        
        # Al final emitir end_label solo si hay else
        if ctx.block() and len(ctx.block()) > 1:
            self.emit_label(end_label)
    
    def enterWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        """Statement while"""
        if not ctx.expression():
            return
        
        # Generar labels
        loop_label = self.new_label("WHILE")
        end_label = self.new_label("ENDWHILE")
        
        # Emitir label de inicio de loop
        self.emit_label(loop_label)
        
        # Evaluar condición
        condition = self.visit_expression(ctx.expression())
        
        # IF condition <= 0 GOTO end_label (salir si falso)
        self.emit(f"IF {condition} <= 0 GOTO {end_label}")
        
        # Guardar labels
        self.loop_labels.append((loop_label, end_label))
    
    def exitWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        """Salida de while statement"""
        if not self.loop_labels:
            return
        
        loop_label, end_label = self.loop_labels.pop()
        
        # Saltar de vuelta al inicio
        self.emit_goto(loop_label)
        
        # Emitir label de salida
        self.emit_label(end_label)
    
    def enterReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        """Statement return"""
        if ctx.expression():
            result = self.visit_expression(ctx.expression())
            self.emit_return(result)
        else:
            self.emit_return()
    
    def enterPrintStatement(self, ctx: CompiscriptParser.PrintStatementContext):
        """Statement print"""
        if ctx.expression():
            result = self.visit_expression(ctx.expression())
            # Para print, podemos usar una llamada especial o instrucción específica
            self.emit(f"PRINT {result}")