"""
Three-Address Code (TAC) Generator for Compiscript compiler
Generates TAC following the exact specification:
- Temporales: t0, t1, t2, ...
- Frame pointer: fp[k] para acceder a slots
- Llamadas: CALL f (y el valor de retorno queda en R)
- Asignación del retorno: tX := R
- Parámetros: PARAM argN                 # Emitir parámetros simples
                num_args = 0
                if args_text.strip():
                    args = [arg.strip() for arg in args_text.split(',') if arg.strip()]
                    num_args = len(args)
                    for arg in args:
                        arg_result = self._evaluate_simple_operand(arg)
                        if self.emit_params:
                            self.emit(f"PARAM {arg_result}")
                
                # Emitir llamada con formato CALL func,num_args
                self.emit(f"CALL {func_name},{num_args}")ALL f (emit_params flag)
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
        
        # Contadores específicos para diferentes tipos de labels
        self.while_counter = 0
        self.if_counter = 0
        
        # Sistema de indentación para mejor legibilidad
        self.indent_level = 0
        self.use_indentation = True
        
        # Stack para gestionar contextos
        self.current_function = None
        self.function_stack: List[str] = []
        self.scope_depth = 0
        self.loop_labels: List[tuple] = []  # (continue_label, break_label)
        
        # Mapeo de variables con información de ámbito
        self.global_variables: Dict[str, int] = {}  # nombre -> desplazamiento global
        self.local_variables: Dict[str, int] = {}   # nombre -> desplazamiento local 
        self.current_global_offset = 0
        self.current_local_offset = 0
        
        # Stack de ámbitos para manejar funciones anidadas
        self.scope_stack = ["global"]
        
        # Variables por ámbito (para restaurar al salir de funciones)
        self.scope_variables = {"global": {}}
        
        # Resultados de expresiones para el visitor pattern
        self.expression_results: Dict[int, str] = {}
        
        # Optimización: rastrear el temporal asociado a cada variable local
        # para evitar asignaciones innecesarias cuando se retorna inmediatamente
        self.variable_to_temp: Dict[str, str] = {}  # nombre_var -> temporal
    
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
    
    def new_variable_slot(self, var_name: str, var_type: str = "integer") -> tuple:
        """Asigna un nuevo slot para variable (global o local según ámbito actual)"""
        type_size = self._get_type_size(var_type)
        
        if self.scope_stack[-1] == "global":
            # Variable global
            offset = self.current_global_offset
            self.global_variables[var_name] = offset
            self.scope_variables["global"][var_name] = offset
            self.current_global_offset += type_size
            return ("G", offset)
        else:
            # Variable local de función
            offset = self.current_local_offset
            self.local_variables[var_name] = offset
            current_scope = self.scope_stack[-1]
            if current_scope not in self.scope_variables:
                self.scope_variables[current_scope] = {}
            self.scope_variables[current_scope][var_name] = offset
            self.current_local_offset += type_size
            return ("fp", offset)
    
    def _get_type_size(self, var_type: str) -> int:
        """Obtiene el tamaño en bytes de un tipo de datos"""
        type_sizes = {
            "integer": 4,
            "float": 8,
            "boolean": 1,
            "string": 8,  # pointer
            "void": 0
        }
        return type_sizes.get(var_type, 4)  # default integer = 4 bytes
    
    def get_variable_slot(self, var_name: str, var_type: str = "integer") -> str:
        """Obtiene el slot para una variable (busca en ámbito local primero, luego global)"""
        # Buscar primero en ámbito local actual
        current_scope = self.scope_stack[-1]
        if current_scope != "global" and current_scope in self.scope_variables:
            if var_name in self.scope_variables[current_scope]:
                offset = self.scope_variables[current_scope][var_name]
                return f"fp[{offset}]"
        
        # Buscar en variables locales de la función actual
        if var_name in self.local_variables and current_scope != "global":
            offset = self.local_variables[var_name]
            return f"fp[{offset}]"
        
        # Buscar en variables globales
        if var_name in self.global_variables:
            offset = self.global_variables[var_name]
            return f"G[{offset}]"
        
        # Variable no encontrada, crearla en el ámbito actual
        memory_type, offset = self.new_variable_slot(var_name, var_type)
        return f"{memory_type}[{offset}]"
    
    def get_variable_slot_lazy(self, var_name: str) -> str:
        """Obtiene el slot para una variable, creándola si es necesario"""
        return self.get_variable_slot(var_name, "integer")
    
    def emit(self, instruction: str, comment: str = None):
        """Emite una instrucción TAC con indentación automática y comentario opcional"""
        if instruction.strip():  # No líneas en blanco
            # Agregar comentario si se proporciona
            if comment:
                instruction = f"{instruction}      ; {comment}"
            
            if self.use_indentation and self.current_function:
                # Solo indentar si estamos dentro de una función
                # Labels no se indentan, el resto sí (con 1 tab)
                if instruction.endswith(':') or instruction.startswith('//') or instruction.startswith(';') or instruction.startswith('FUNCTION') or instruction.startswith('END FUNCTION'):
                    # Labels, comentarios y declaraciones de función van sin indentación
                    self.instructions.append(instruction)
                else:
                    # Instrucciones regulares se indentan con 1 tab dentro de funciones
                    self.instructions.append(f"\t{instruction}")
            else:
                self.instructions.append(instruction)
    
    def emit_comment(self, comment: str):
        """Emite un comentario (no indentado)"""
        self.instructions.append(f"; {comment}")
    
    def indent_in(self):
        """Aumenta el nivel de indentación"""
        if self.use_indentation:
            self.indent_level += 1
    
    def indent_out(self):
        """Disminuye el nivel de indentación"""
        if self.use_indentation and self.indent_level > 0:
            self.indent_level -= 1
    
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
    
    def emit_call(self, func_name: str, num_params: int = 0):
        """Emite CALL f,num_params"""
        self.emit(f"CALL {func_name},{num_params}")
    
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
        
        # Entrar en nuevo ámbito de función
        self.scope_stack.append(f"function_{func_name}")
        current_scope = self.scope_stack[-1]
        self.scope_variables[current_scope] = {}
        
        # Resetear contador local para esta función
        self.current_local_offset = 0
        self.local_variables.clear()
        
        # Resetear contador de temporales para cada función (para mejor legibilidad)
        self.temp_counter = 0
        
        # Resetear mapeo de variables a temporales para optimización
        self.variable_to_temp.clear()
        
        # Los slots de parámetros serán negativos para diferenciarlos
        
        # Detectar si la función está declarada dentro de una clase (método)
        is_method = False
        parent = getattr(ctx, 'parentCtx', None)
        while parent:
            if type(parent).__name__ == 'ClassDeclarationContext':
                is_method = True
                break
            parent = getattr(parent, 'parentCtx', None)

        # Asignar slots para parámetros (negativos para parámetros)
        # Si es un método de clase, reservar fp[-1] para 'this' y desplazar parámetros
        if ctx.parameters() and ctx.parameters().parameter():
            for i, param in enumerate(ctx.parameters().parameter()):
                    if param.Identifier():
                        param_name = param.Identifier().getText()
                        # Usar slots negativos para parámetros; si es método, desplazar en 1
                        base_shift = 1 if is_method else 0
                        param_offset = -(i + 1 + base_shift)
                        self.local_variables[param_name] = param_offset
                        self.scope_variables[current_scope][param_name] = param_offset

            # Si es un método, reservar 'this' en offset 0 (primer slot de objeto)
            if is_method:
                # 'this' estará disponible como fp[-1]
                self.local_variables['this'] = 0
                self.scope_variables[current_scope]['this'] = 0

        # Record start index of function body in instructions to detect missing RETURN
        self.current_function_start = len(self.instructions)
        self.emit(f"FUNCTION {func_name}:")
        # Indentar el contenido de la función
        self.indent_in()
    
    def exitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        """Salida de declaración de función"""
        if self.current_function:
            # NO agregar RETURN automático - solo si está explícito en el código
            # Comentado: if not self.instructions or not self.instructions[-1].strip().startswith("RETURN"):
            #     self.emit("RETURN")
            
            # If constructor has no RETURN, emit RETURN 0 per TAC convention
            try:
                func_name = self.current_function
                # scan instructions emitted since function start for a RETURN
                has_return = False
                for instr in self.instructions[self.current_function_start:]:
                    if instr.strip().startswith('RETURN'):
                        has_return = True
                        break
                if func_name == 'constructor' and not has_return:
                    self.emit_return('0')
            except Exception:
                pass

            # Des-indentar antes del END FUNCTION
            self.indent_out()
            self.emit(f"END FUNCTION {self.current_function}")
            
            # Salir del ámbito de función
            if len(self.scope_stack) > 1:
                self.scope_stack.pop()
            
            self.function_stack.pop()
            self.current_function = self.function_stack[-1] if self.function_stack else None
            self.scope_depth -= 1
    
    # ==================== VARIABLE DECLARATIONS ====================
    
    def enterVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        """Declaración de variable"""
        if not ctx.Identifier():
            return
        
        var_name = ctx.Identifier().getText()
        
        # Extraer tipo de datos
        var_type = "integer"  # default
        if ctx.typeAnnotation() and ctx.typeAnnotation().type_():
            var_type = ctx.typeAnnotation().type_().getText()
        
        # SIEMPRE reservar slot para declaraciones (para calcular desplazamientos correctos)
        # pero solo generar código TAC si hay inicializador
        memory_type, offset = self.new_variable_slot(var_name, var_type)
        
        # Solo generar código TAC si hay inicializador explícito
        if ctx.initializer() and ctx.initializer().expression():
            result = self.visit_expression(ctx.initializer().expression())
            
            # OPTIMIZACIÓN: Si el resultado es un temporal (tX), no lo asignamos a memoria
            # Solo guardamos la asociación para que return pueda usarlo directamente
            if result.startswith('t') and result[1:].isdigit():
                # Es un temporal, guardamos la asociación sin emitir asignación
                self.variable_to_temp[var_name] = result
            else:
                # No es un temporal (es un literal, variable, etc), emitir asignación normal
                self.emit_assign(f"{memory_type}[{offset}]", result)
                self.variable_to_temp[var_name] = f"{memory_type}[{offset}]"
    
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
        # BUT first handle complex concatenations that include function calls or string literals
        # Move this check before Identifier-based early returns so returns like:
        #   "Ahora tengo " + toString(this.edad) + " años."
        # get decomposed into PARAM/CALL + concat steps.
        if '+' in text and ('"' in text or 'toString' in text or '(' in text):
            result = self._handle_complex_concatenation(text)
            if result:
                return result

        if text.isalnum() and not text.isdigit():
            return self.get_variable_slot_lazy(text)
        
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
            return self.get_variable_slot_lazy(var_name)
        
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

    def _split_expression_by_plus(self, text: str) -> list:
        parts = []
        current_part = ""
        paren_depth = 0
        in_quotes = False
        i = 0
        while i < len(text):
            c = text[i]
            if c == '"' and (i == 0 or text[i-1] != '\\'):
                in_quotes = not in_quotes
                current_part += c
            elif in_quotes:
                current_part += c
            elif c == '(':
                paren_depth += 1
                current_part += c
            elif c == ')':
                paren_depth -= 1
                current_part += c
            elif c == '+' and paren_depth == 0:
                if current_part.strip():
                    parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += c
            i += 1
        if current_part.strip():
            parts.append(current_part.strip())
        return parts

    def _handle_complex_concatenation(self, text: str) -> str:
        """Convierte concatenaciones complejas con llamadas a función en secuencia TAC.
        Devuelve el temporal final que contiene la concatenación.
        """
        parts = self._split_expression_by_plus(text)
        if len(parts) < 2:
            return None

        # Quick path: if there are exactly 2 parts and neither part is a function call,
        # emit a single binary '+' operation (result := left + right) to match the
        # target intermediate code when concatenating a literal with a field.
        simple_parts = [p.strip() for p in parts]
        simple_no_calls = all(('(' not in p and ')' not in p) for p in simple_parts)
        if len(simple_parts) == 2 and simple_no_calls:
            left = simple_parts[0]
            right = simple_parts[1]
            # Evaluate operands directly without creating unnecessary temporaries for literals
            left_res = left if left.startswith('"') and left.endswith('"') else self._evaluate_simple_operand(left)
            right_res = right if right.startswith('"') and right.endswith('"') else self._evaluate_simple_operand(right)

            result_temp = self.new_temp()
            # emit binary '+' using emit_binary_op to produce: t := left + right
            self.emit_binary_op(result_temp, left_res, '+', right_res)
            return result_temp

        # For complex concatenations with 3+ parts, build incrementally
        current_result = None
        for i, part in enumerate(parts):
            part = part.strip()
            # function call like toString(arg)
            if '(' in part and ')' in part:
                # parse name and arg
                name, rest = part.split('(', 1)
                name = name.strip()
                args_text = rest.rstrip(')')
                args = [a.strip() for a in args_text.split(',') if a.strip()]
                # Evaluate args and emit PARAMs
                for a in args:
                    arg_res = self._evaluate_simple_operand(a) if isinstance(a, str) else self.visit_expression(a)
                    # if arg_res is a slot like fp[...] or a temp, emit as PARAM
                    self.emit_param(arg_res)
                # emit call
                self.emit_call(name, len(args))
                temp = self.new_temp()
                self.emit_assign(temp, 'R')
                part_result = temp
            # literal - use directly without creating temp
            elif part.startswith('"') and part.endswith('"'):
                part_result = part
            # property or variable
            else:
                part_result = self._evaluate_simple_operand(part)

            if current_result is None:
                current_result = part_result
            else:
                # concatenate current_result with part_result using binary operator
                tmp = self.new_temp()
                self.emit_binary_op(tmp, current_result, '+', part_result)
                current_result = tmp

        return current_result
    
    def _parse_binary_expression(self, text: str) -> str:
        """Parsea expresiones binarias simples desde texto - ORDEN DE PRECEDENCIA CORRECTO"""
        if not text:
            return None
        
        # Quitar paréntesis externos si envuelven toda la expresión
        text = text.strip()
        while text.startswith('(') and text.endswith(')'):
            # Verificar que los paréntesis son balanceados y envuelven toda la expresión
            depth = 0
            is_wrapping = True
            for i, c in enumerate(text):
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                # Si depth llega a 0 antes del final, los paréntesis no envuelven todo
                if depth == 0 and i < len(text) - 1:
                    is_wrapping = False
                    break
            
            if is_wrapping:
                text = text[1:-1].strip()
            else:
                break
        
        # Verificar si hay paréntesis para llamadas a función (después de quitar paréntesis externos)
        if "(" in text and ")" in text and not any(op in text for op in ['||', '&&', '==', '!=', '<=', '>=', '<', '>', '+', '-', '*', '/', '%']):
            # Posible llamada a función
            func_match = text.split('(', 1)
            if len(func_match) == 2:
                func_name = func_match[0].strip()
                args_text = func_match[1].rstrip(')')
                
                # Contar argumentos
                num_args = 0
                if args_text.strip():
                    args = [arg.strip() for arg in args_text.split(',') if arg.strip()]
                    num_args = len(args)
                    for arg in args:
                        arg_result = self._evaluate_simple_operand(arg)
                        if self.emit_params:
                            self.emit(f"PARAM {arg_result}")
                
                # Emitir llamada con formato CALL func,num_args
                self.emit(f"CALL {func_name},{num_args}")
                
                # Retornar resultado
                result = self.new_temp()
                self.emit_assign(result, "R")
                return result
        
        # Operadores en orden de MENOR a MAYOR precedencia
        # Los operadores de menor precedencia se evalúan ÚLTIMO (de derecha a izquierda en parsing)
        operators_by_precedence = [
            ['||'],           # OR lógico - menor precedencia  
            ['&&'],           # AND lógico
            ['==', '!='],     # Igualdad
            ['<', '<=', '>', '>='], # Relacionales
            ['+', '-'],       # Suma/resta
            ['*', '/', '%']   # Multiplicación/división - MAYOR precedencia
        ]
        
        # Buscar operadores de MENOR a MAYOR precedencia
        # Encontrar el operador de menor precedencia para dividir por ahí
        for operator_group in operators_by_precedence:
            # Buscar el último operador de este grupo (de derecha a izquierda)
            # pero RESPETANDO paréntesis - solo buscar fuera de paréntesis
            best_split = None
            best_op = None
            best_index = -1
            
            for op in operator_group:
                if op in text and not (text.startswith('"') and text.endswith('"')):
                    # Encontrar la última ocurrencia de este operador, evitando <= cuando buscamos <
                    if op == '<' and '<=' in text:
                        continue  # Evitar confusión con <=
                    if op == '>' and '>=' in text:
                        continue  # Evitar confusión con >=
                    
                    # Buscar el último operador FUERA de paréntesis
                    paren_depth = 0
                    for i in range(len(text) - 1, -1, -1):
                        if text[i] == ')':
                            paren_depth += 1
                        elif text[i] == '(':
                            paren_depth -= 1
                        elif paren_depth == 0 and text[i:i+len(op)] == op:
                            # Found operator outside parentheses
                            if i > 0 and i > best_index:  # Debe haber algo antes
                                left_part = text[:i].strip()
                                right_part = text[i + len(op):].strip()
                                if left_part and right_part:
                                    best_split = (left_part, right_part)
                                    best_op = op
                                    best_index = i
                                    break
            
            if best_split:
                left, right = best_split
                
                # Evaluar recursivamente con precedencia correcta
                left_result = self._parse_expression_with_precedence(left)
                right_result = self._parse_expression_with_precedence(right)
                
                # Generar código TAC
                result = self.new_temp()
                self.emit_binary_op(result, left_result, best_op, right_result)
                return result
        
        return None
    
    def _parse_expression_with_precedence(self, expr: str) -> str:
        """Parser recursivo que respeta precedencia de operadores"""
        expr = expr.strip()
        
        # Casos base: literales y variables
        if expr.isdigit():
            return expr
        elif expr.startswith('"') and expr.endswith('"'):
            return expr
        elif expr == "true":
            return "1"
        elif expr == "false":
            return "0"
        elif expr.isalnum():
            return self.get_variable_slot_lazy(expr)
        
        # Intentar parsear como expresión binaria
        result = self._parse_binary_expression(expr)
        if result:
            return result
        
        # Fallback
        return self._evaluate_simple_operand(expr)
    
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
            return self.get_variable_slot_lazy(operand)

        # Manejo de acceso a propiedades: this.prop o obj.prop
        if '.' in operand:
            parts = operand.split('.', 1)
            base = parts[0].strip()
            prop = parts[1].strip()

            # Buscar offset de la propiedad en la tabla global (las propiedades de clase se reservan globalmente)
            prop_offset = None
            if prop in self.global_variables:
                prop_offset = self.global_variables[prop]
            elif 'global' in self.scope_variables and prop in self.scope_variables['global']:
                prop_offset = self.scope_variables['global'][prop]

            # Base 'this' => acceder al objeto actual en fp[-1]
            if base == 'this':
                if prop_offset is not None:
                    return f"fp[-1][{prop_offset}]"
                else:
                    return "fp[-1]"

            # Base es una variable/identificador: obtener su slot y anexar [offset]
            base_slot = self.get_variable_slot_lazy(base)
            if prop_offset is not None:
                return f"{base_slot}[{prop_offset}]"
            return base_slot
        
        return "0"
    
    def _evaluate_from_children(self, ctx) -> str:
        """Evalúa expresión desde los children del contexto - evita recursión infinita"""
        if not hasattr(ctx, 'children') or not ctx.children:
            return "0"
        
        # Obtener el texto completo de la expresión y usar el parser textual 
        # en lugar de recursión infinita por el AST
        full_text = ctx.getText()
        
        # Si es una expresión simple (variable, literal), devolverla directamente
        if full_text.isdigit():
            return full_text
        elif full_text.startswith('"') and full_text.endswith('"'):
            return full_text
        elif full_text == "true":
            return "1"
        elif full_text == "false":
            return "0"
        elif full_text.isalnum():
            return self.get_variable_slot_lazy(full_text)
        
        # Para expresiones complejas, usar el parser textual que respeta precedencia
        result = self._parse_binary_expression(full_text)
        if result:
            return result
        
        # Fallback: revisar children manualmente sin recursión infinita
        children = ctx.children
        
        # Caso con 3 children: operando1 operador operando2
        if len(children) == 3:
            left_child = children[0]
            op_child = children[1] 
            right_child = children[2]
            
            # Obtener operador
            if hasattr(op_child, 'getText'):
                op_text = op_child.getText()
            else:
                op_text = str(op_child)
            
            # Evaluar operandos SIN recursión infinita
            left_text = left_child.getText() if hasattr(left_child, 'getText') else str(left_child)
            right_text = right_child.getText() if hasattr(right_child, 'getText') else str(right_child)
            
            left_result = self._evaluate_simple_operand(left_text)
            right_result = self._evaluate_simple_operand(right_text)
            
            result = self.new_temp()
            self.emit_binary_op(result, left_result, op_text, right_result)
            return result
        
        # Caso con 1 child: evaluar directamente
        elif len(children) == 1:
            child = children[0]
            child_text = child.getText() if hasattr(child, 'getText') else str(child)
            return self._evaluate_simple_operand(child_text)
        
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
                return self.get_variable_slot_lazy(var_name)
        
        if hasattr(ctx, 'Identifier') and ctx.Identifier():
            var_name = ctx.Identifier().getText()
            return self.get_variable_slot_lazy(var_name)
        
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
            
            num_params = 0
            if expressions:
                if isinstance(expressions, list):
                    num_params = len(expressions)
                    for arg in expressions:
                        if hasattr(arg, 'getText'):
                            arg_result = self.visit_expression(arg)
                            self.emit(f"PARAM {arg_result}")
                else:
                    # Es una sola expresión
                    num_params = 1
                    if hasattr(expressions, 'getText'):
                        arg_result = self.visit_expression(expressions)
                        self.emit(f"PARAM {arg_result}")
        
        # Emitir CALL con número de parámetros
        self.emit(f"CALL {func_name},{num_params}")
        
        # El resultado queda en R, asignarlo a un temporal
        result = self.new_temp()
        self.emit_assign(result, "R")
        return result
    
    # ==================== STATEMENTS ====================
    
    def enterExpressionStatement(self, ctx: CompiscriptParser.ExpressionStatementContext):
        """Statement de expresión"""
        if ctx.expression():
            # Verificar si es una llamada a función directa
            expr_text = ctx.expression().getText()
            if "(" in expr_text and ")" in expr_text:
                # Es una llamada a función, procesarla específicamente
                self._process_function_call_statement(expr_text)
            else:
                self.visit_expression(ctx.expression())
    
    def _process_function_call_statement(self, call_text: str):
        """Procesa un statement que es una llamada a función"""
        if "(" in call_text and ")" in call_text:
            func_match = call_text.split('(', 1)
            if len(func_match) == 2:
                func_name = func_match[0].strip()
                args_text = func_match[1].rstrip(')')
                
                # Emitir parámetros
                num_args = 0
                if args_text.strip():
                    args = [arg.strip() for arg in args_text.split(',') if arg.strip()]
                    num_args = len(args)
                    for arg in args:
                        arg_result = self._evaluate_simple_operand(arg)
                        self.emit(f"PARAM {arg_result}")
                
                # Emitir llamada
                self.emit(f"CALL {func_name},{num_args}")
                
                # Asignar resultado a temporal (aunque no se use)
                result = self.new_temp()
                self.emit_assign(result, "R")
    
    def enterAssignment(self, ctx: CompiscriptParser.AssignmentContext):
        """Asignación directa"""
        # Support both simple assignments and property assignments
        # assignment rule in grammar supports both:
        # Identifier '=' expression
        # expression '.' Identifier '=' expression  (property assignment)

        # Property assignment: expression '.' Identifier '=' expression
        try:
            # Si el ctx tiene children like [base, '.', Identifier, '=', expr, ';']
            children = ctx.children
            if children and len(children) >= 5 and children[1].getText() == '.':
                # property assignment
                base_text = children[0].getText()
                prop_name = children[2].getText()
                rhs_ctx = children[4]

                # Obtener slot del right-hand-side
                rhs = self.visit_expression(rhs_ctx)

                # Obtener offset de la propiedad (se esperan propiedades reservadas en scope_variables['global'])
                prop_offset = None
                if prop_name in self.global_variables:
                    prop_offset = self.global_variables[prop_name]
                elif 'global' in self.scope_variables and prop_name in self.scope_variables['global']:
                    prop_offset = self.scope_variables['global'][prop_name]

                # Resolver base slot
                if base_text == 'this':
                    if prop_offset is not None:
                        target = f"fp[-1][{prop_offset}]"
                    else:
                        target = "fp[-1]"
                else:
                    base_slot = self.get_variable_slot_lazy(base_text)
                    if prop_offset is not None:
                        target = f"{base_slot}[{prop_offset}]"
                    else:
                        target = base_slot

                self.emit_assign(target, rhs)
                return
        except Exception:
            # Fallthrough to simple assignment handling
            pass

        # Simple identifier assignment
        if not ctx.Identifier():
            return

        var_name = ctx.Identifier().getText()
        var_slot = self.get_variable_slot_lazy(var_name)  # Reservar slot cuando se use

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
        """Statement if - Formato correcto:
        t := eval(cond)
        IF t > 0 GOTO IF_TRUE_k
        GOTO IF_FALSE_k
        IF_TRUE_k:
          ...
          GOTO IF_END_k
        IF_FALSE_k:
          ...
        IF_END_k:
        """
        if not ctx.expression():
            return
        
        # Usar ID único para este if
        if_id = self.if_counter
        self.if_counter += 1
        
        # Generar labels con el mismo ID
        true_label = f"IF_TRUE_{if_id}"
        false_label = f"IF_FALSE_{if_id}"
        end_label = f"IF_END_{if_id}"
        
        # t := eval(cond)
        condition = self.visit_expression(ctx.expression())
        condition_temp = self.new_temp()
        self.emit_assign(condition_temp, condition)
        
        # IF t > 0 GOTO IF_TRUE_k
        self.emit(f"IF {condition_temp} > 0 GOTO {true_label}")
        
        # GOTO IF_FALSE_k
        self.emit(f"GOTO {false_label}")
        
        # IF_TRUE_k:
        self.emit_label(true_label)
        
        # Indentar el contenido del if
        self.indent_in()
        
        # Guardar labels para exitIfStatement
        self.loop_labels.append((true_label, false_label, end_label))
    
    def exitIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        """Salida de if statement"""
        if not self.loop_labels:
            return
        
        true_label, false_label, end_label = self.loop_labels.pop()
        
        # Des-indentar antes de los labels finales
        self.indent_out()
        
        # Verificar si hay bloque else
        has_else = ctx.block() and len(ctx.block()) > 1
        
        if has_else:
            # GOTO IF_END_k (saltar del bloque then)
            self.emit(f"GOTO {end_label}")
            
            # IF_FALSE_k: (inicio del bloque else)
            self.emit_label(false_label)
            
            # Indentar el contenido del else
            self.indent_in()
            # El bloque else se procesa automáticamente
            # (se des-indentará automáticamente al final)
            self.indent_out()
            
            # IF_END_k: (final)
            self.emit_label(end_label)
        else:
            # No hay else, IF_FALSE_k es el final
            self.emit_label(false_label)
    
    def enterWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        """Statement while - Formato correcto:
        STARTWHILE_k:
          t := eval(cond)
          IF t > 0 GOTO LABEL_TRUE_k  
          GOTO ENDWHILE_k
        LABEL_TRUE_k:
          emit(body)
          GOTO STARTWHILE_k
        ENDWHILE_k:
        """
        if not ctx.expression():
            return
        
        # Usar ID único para este while
        while_id = self.while_counter
        self.while_counter += 1
        
        # Generar labels con el mismo ID
        start_label = f"STARTWHILE_{while_id}"
        true_label = f"LABEL_TRUE_{while_id}"
        end_label = f"ENDWHILE_{while_id}"
        
        # STARTWHILE_k:
        self.emit_label(start_label)
        
        # t := eval(cond)
        condition = self.visit_expression(ctx.expression())
        
        # IF t > 0 GOTO LABEL_TRUE_k (usar directamente el temporal de la expresión)
        self.emit(f"IF {condition} > 0 GOTO {true_label}")
        
        # GOTO ENDWHILE_k  
        self.emit(f"GOTO {end_label}")
        
        # LABEL_TRUE_k:
        self.emit_label(true_label)
        
        # Guardar labels para exitWhileStatement
        self.loop_labels.append((start_label, end_label))
    
    def exitWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        """Salida de while statement"""
        if not self.loop_labels:
            return
        
        start_label, end_label = self.loop_labels.pop()
        
        # GOTO STARTWHILE_k (volver al inicio del loop)
        self.emit(f"GOTO {start_label}")
        
        # ENDWHILE_k:
        self.emit_label(end_label)
    
    def enterReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        """Statement return"""
        if ctx.expression():
            # Quick-path: if the raw expression text looks like a complex concatenation
            # that includes function calls or string literals, force decomposition
            # via _handle_complex_concatenation to emit PARAM/CALL concat sequences.
            try:
                expr_text = ctx.expression().getText()
                
                # OPTIMIZACIÓN: Si el return es de una variable simple que tiene temporal asociado,
                # retornar directamente el temporal
                if expr_text.isalnum() and expr_text in self.variable_to_temp:
                    temp = self.variable_to_temp[expr_text]
                    self.emit_return(temp)
                    return
                
                if '+' in expr_text and ('"' in expr_text or 'toString' in expr_text or '(' in expr_text):
                    res = self._handle_complex_concatenation(expr_text)
                    if res:
                        self.emit_return(res)
                        return
            except Exception:
                pass

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