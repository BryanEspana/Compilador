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

class BooleanExpression:
    """Representa una expresión booleana con etiquetas de salto para corto circuito"""
    def __init__(self, true_label: str = None, false_label: str = None):
        self.true_label = true_label    # B.true - salto cuando es verdadero
        self.false_label = false_label  # B.false - salto cuando es falso

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
        
        # Información de clases y sus campos
        self.class_fields: Dict[str, Dict[str, int]] = {}  # class_name -> {field_name -> offset}
        self.current_class = None
        self.current_field_offset = 0
        
        # Control para evitar procesamiento automático de bloques
        self._skip_automatic_processing = False
        
        # Set de contextos ya procesados para evitar duplicaciones
        self._processed_contexts = set()
    
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
    
    def _get_field_offset(self, field_name: str) -> int:
        """Obtiene el offset de un campo de clase (por bytes: 0, 4, 8, ...)"""
        if self.current_class and self.current_class in self.class_fields:
            return self.class_fields[self.current_class].get(field_name, 0)
        # Si no se encuentra, asumir que es el primer campo
        return 0
    
    def _register_field(self, class_name: str, field_name: str, field_type: str = "integer"):
        """Registra un campo de clase con su offset"""
        if class_name not in self.class_fields:
            self.class_fields[class_name] = {}
            self.current_field_offset = 0
        
        # Asignar offset y avanzar según tamaño del tipo
        field_size = self._get_type_size(field_type)
        self.class_fields[class_name][field_name] = self.current_field_offset
        self.current_field_offset += field_size
    
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
        
        # EN MÉTODOS DE CLASE: Si la variable es un campo de clase, usar acceso via this
        if (hasattr(self, 'current_class') and self.current_class and 
            self.current_class in self.class_fields and 
            var_name in self.class_fields[self.current_class]):
            # Es un campo de la clase actual, acceder via this (fp[-1])
            field_offset = self.class_fields[self.current_class][var_name]
            return f"fp[-1][{field_offset}]"
        
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
    
    def emit(self, instruction: str):
        """Emite una instrucción TAC con indentación automática"""
        if instruction.strip():  # No líneas en blanco
            if self.use_indentation and self.current_function:
                # Solo indentar si estamos dentro de una función
                # Labels no se indentan, el resto sí (con 1 tab)
                if instruction.endswith(':') or instruction.startswith('//') or instruction.startswith('FUNCTION') or instruction.startswith('END FUNCTION'):
                    # Labels, comentarios y declaraciones de función van sin indentación
                    self.instructions.append(instruction)
                else:
                    # Instrucciones regulares se indentan con 1 tab dentro de funciones
                    self.instructions.append(f"\t{instruction}")
            else:
                self.instructions.append(instruction)
    
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
    
    # ==================== SHORT CIRCUIT EVALUATION ====================
    
    def evaluate_boolean_expression(self, ctx, true_label: str, false_label: str):
        """Evalúa expresión booleana con corto circuito - NO materializa valor, solo genera saltos
        
        Siguiendo las reglas:
        - B.true: label a donde saltar si es verdadero
        - B.false: label a donde saltar si es falso
        - Para operadores && y ||: implementa corto circuito real
        """
        if not ctx:
            # Expresión vacía = falsa
            self.emit_goto(false_label)
            return
            
        expr_text = ctx.getText()
        
        # Casos base: literales booleanos
        if expr_text == "true":
            self.emit_goto(true_label)
            return
        elif expr_text == "false":
            self.emit_goto(false_label) 
            return
        
        # Operador de negación (!)
        if expr_text.startswith("!"):
            # Para negación, intercambiar las etiquetas true y false
            inner_expr = expr_text[1:].strip()
            # Remover paréntesis externos si los hay
            if inner_expr.startswith("(") and inner_expr.endswith(")"):
                inner_expr = inner_expr[1:-1].strip()
            
            # Crear contexto para la expresión interna
            inner_ctx = self._parse_expression_context(inner_expr)
            # Evaluar con etiquetas intercambiadas
            self.evaluate_boolean_expression(inner_ctx, false_label, true_label)
            return
            
        # Variables booleanas
        if expr_text.isalnum() and not expr_text.isdigit():
            var_slot = self.get_variable_slot_lazy(expr_text)
            self.emit_if_goto(var_slot, true_label)
            self.emit_goto(false_label)
            return
            
        # Operadores lógicos con corto circuito
        if "||" in expr_text:
            self._evaluate_or_expression(ctx, true_label, false_label)
        elif "&&" in expr_text:
            self._evaluate_and_expression(ctx, true_label, false_label)
        elif any(op in expr_text for op in ["==", "!=", "<=", ">=", "<", ">"]):
            self._evaluate_relational_expression(ctx, true_label, false_label)
        else:
            # Expresión compleja - evaluar y usar resultado
            result = self.visit_expression(ctx)
            self.emit_if_goto(result, true_label)
            self.emit_goto(false_label)
    
    def _evaluate_or_expression(self, ctx, true_label: str, false_label: str):
        """Implementa A || B con corto circuito:
        Si A es verdadero, salta directo a true_label
        Si A es falso, evalúa B
        """
        # Encontrar operandos
        left_expr, right_expr = self._split_logical_expression(ctx.getText(), "||")
        
        if left_expr and right_expr:
            # Crear label intermedio para continuar con B si A es falso
            continue_label = self.new_label("OR_CONTINUE")
            
            # Evaluar operando izquierdo
            # Si es verdadero, salta directo a true_label (corto circuito)
            # Si es falso, continúa evaluando B
            left_ctx = self._parse_expression_context(left_expr)
            self.evaluate_boolean_expression(left_ctx, true_label, continue_label)
            
            # Label para continuar: A era falso, evaluar B
            self.emit_label(continue_label)
            right_ctx = self._parse_expression_context(right_expr)
            self.evaluate_boolean_expression(right_ctx, true_label, false_label)
    
    def _evaluate_and_expression(self, ctx, true_label: str, false_label: str):
        """Implementa A && B con corto circuito:
        Si A es falso, salta directo a false_label
        Si A es verdadero, evalúa B
        """
        # Encontrar operandos  
        left_expr, right_expr = self._split_logical_expression(ctx.getText(), "&&")
        
        if left_expr and right_expr:
            # Crear label intermedio para cuando A es verdadero
            intermediate_label = self.new_label("AND_CONTINUE")
            
            # Evaluar operando izquierdo
            # Si es falso, salta directo a false_label sin evaluar B
            left_ctx = self._parse_expression_context(left_expr)
            self.evaluate_boolean_expression(left_ctx, intermediate_label, false_label)
            
            # Label intermedio: A es verdadero, evaluar B
            self.emit_label(intermediate_label)
            right_ctx = self._parse_expression_context(right_expr)
            self.evaluate_boolean_expression(right_ctx, true_label, false_label)
    
    def _evaluate_relational_expression(self, ctx, true_label: str, false_label: str):
        """Evalúa expresión relacional (<, <=, >, >=, ==, !=) con saltos directos"""
        expr_text = ctx.getText()
        
        # Buscar el operador relacional
        for op in ["<=", ">=", "==", "!=", "<", ">"]:
            if op in expr_text:
                parts = expr_text.split(op, 1)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    left_result = self._evaluate_simple_operand(left)
                    right_result = self._evaluate_simple_operand(right)
                    
                    # Generar temporal para comparación
                    temp = self.new_temp()
                    self.emit_binary_op(temp, left_result, op, right_result)
                    
                    # Saltar según resultado (verdadero si > 0)
                    self.emit_if_goto(temp, true_label)
                    self.emit_goto(false_label)
                    return
        
        # Fallback: evaluar como expresión normal
        result = self.visit_expression(ctx)
        self.emit_if_goto(result, true_label)
        self.emit_goto(false_label)
    
    def _split_logical_expression(self, expr_text: str, operator: str) -> tuple:
        """Divide una expresión lógica en operandos izquierdo y derecho"""
        # Buscar la última ocurrencia del operador (precedencia correcta)
        index = expr_text.rfind(operator)
        if index > 0:
            left = expr_text[:index].strip()
            right = expr_text[index + len(operator):].strip()
            return (left, right)
        return (None, None)
    
    def _parse_expression_context(self, expr_text: str):
        """Crea un contexto mock para una expresión desde texto"""
        # Por simplicidad, crear un objeto mock con getText()
        class MockContext:
            def __init__(self, text):
                self._text = text
            def getText(self):
                return self._text
        return MockContext(expr_text)
    
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
        
        # Reiniciar contador de temporales por función
        self.temp_counter = 0
        
        # Verificar si es un método de clase (tiene contexto de clase)
        is_class_method = hasattr(self, 'current_class') and self.current_class
        
        # Asignar slots para parámetros usando fp[-k] donde k empieza en 1
        param_slot = -1  # this = fp[-1] para métodos de clase
        
        # Para métodos de clase, el primer parámetro es 'this'
        if is_class_method:
            self.local_variables['this'] = param_slot
            self.scope_variables[current_scope]['this'] = param_slot
            param_slot -= 1  # Siguiente parámetro será fp[-2]
        
        # Asignar slots para parámetros explícitos
        if ctx.parameters() and ctx.parameters().parameter():
            for param in ctx.parameters().parameter():
                if param.Identifier():
                    param_name = param.Identifier().getText()
                    self.local_variables[param_name] = param_slot
                    self.scope_variables[current_scope][param_name] = param_slot
                    param_slot -= 1  # fp[-2], fp[-3], fp[-4], etc.
        
        self.emit(f"FUNCTION {func_name}:")
        # Indentar el contenido de la función
        self.indent_in()
    
    def exitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        """Salida de declaración de función"""
        if self.current_function:
            # Agregar RETURN automático para funciones void si no hay return explícito
            if not self.instructions or not self.instructions[-1].strip().startswith("RETURN"):
                # Determinar el tipo de retorno
                return_type = "void"  # default
                if hasattr(ctx, 'typeAnnotation') and ctx.typeAnnotation():
                    if hasattr(ctx.typeAnnotation(), 'type_') and ctx.typeAnnotation().type_():
                        return_type = ctx.typeAnnotation().type_().getText()
                
                # Para funciones void, NO emitir RETURN automático según especificación README
                if return_type != "void":
                    self.emit("RETURN")
            
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
            self.emit_assign(f"{memory_type}[{offset}]", result)
    
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
        
        # PRIMERO: Intentar parsear como expresión binaria (concatenación, aritmética, etc.)
        # Esto debe ir ANTES de los casos simples para manejar expresiones complejas
        if any(op in text for op in ['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||']):
            result = self._parse_binary_expression(text)
            if result:
                return result
        
        # DESPUÉS: Casos simples solo si NO es una expresión compleja
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
        
        # Manejo de expresiones OOP
        result = self._handle_oop_expressions(ctx, text)
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
    
    def _handle_oop_expressions(self, ctx, text: str) -> str:
        """Maneja expresiones orientadas a objetos"""
        
        # 1. Expresiones new ClassName(args)
        if text.startswith("new") and "(" in text:
            return self._parse_new_expression(text)
        
        # 2. Acceso a campos: obj.field o this.field
        if "." in text and not "(" in text:  # Acceso a campo (no método)
            return self._parse_field_access(text)
        
        # 3. Llamadas a métodos: obj.method(args) o super.method(args)
        if "." in text and "(" in text:
            return self._parse_method_call(text, ctx)
        
        # 4. Referencia a 'this'
        if text == "this":
            return self.get_variable_slot_lazy('this')
        
        return None
    
    def _parse_new_expression(self, text: str) -> str:
        """Parsea expresión new ClassName(args)"""
        # new Persona("Juan", 25)
        parts = text.split("new", 1)
        if len(parts) < 2:
            return None
            
        remaining = parts[1].strip()
        if "(" not in remaining:
            return None
            
        class_name = remaining.split("(", 1)[0].strip()
        args_part = remaining.split("(", 1)[1].rstrip(")")
        
        # Evaluar argumentos
        args = []
        if args_part.strip():
            arg_texts = [arg.strip() for arg in args_part.split(",")]
            for arg_text in arg_texts:
                args.append(self._evaluate_simple_operand(arg_text))
        
        return self._handle_new_expression(class_name, args)
    
    def _parse_field_access(self, text: str) -> str:
        """Parsea acceso a campos: obj.field o this.field"""
        parts = text.split(".", 1)
        if len(parts) != 2:
            return None
            
        obj_name, field_name = parts
        
        if obj_name == "this":
            return self._handle_this_access(field_name)
        else:
            # Para objetos no-this, determinar clase y offset
            obj_slot = self.get_variable_slot_lazy(obj_name)
            field_offset = self._get_field_offset_for_object(obj_name, field_name)
            return f"{obj_slot}[{field_offset}]"
    
    def _parse_method_call(self, text: str, ctx) -> str:
        """Parsea llamadas a métodos: obj.method(args) o super.method(args)"""
        if "(" not in text or ")" not in text:
            return None
            
        # obj.method(args)
        dot_pos = text.find(".")
        paren_pos = text.find("(")
        
        if dot_pos == -1 or paren_pos == -1 or dot_pos > paren_pos:
            return None
            
        obj_part = text[:dot_pos]
        method_part = text[dot_pos+1:paren_pos]
        args_part = text[paren_pos+1:text.rfind(")")]
        
        # Evaluar argumentos
        args = []
        if args_part.strip():
            arg_texts = [arg.strip() for arg in args_part.split(",")]
            for arg_text in arg_texts:
                args.append(self._evaluate_simple_operand(arg_text))
        
        if obj_part == "super":
            return self._handle_super_call(method_part, args)
        elif obj_part == "this":
            # this.method() - usar this como objeto
            this_slot = self.get_variable_slot_lazy('this')
            return self._handle_method_call(this_slot, method_part, args)
        else:
            obj_slot = self.get_variable_slot_lazy(obj_part)
            return self._handle_method_call(obj_slot, method_part, args)
    
    def _parse_binary_expression(self, text: str) -> str:
        """Parsea expresiones binarias simples desde texto - ORDEN DE PRECEDENCIA CORRECTO"""
        if not text:
            return None
        
        text = text.strip()

        # Manejar paréntesis anidados primero
        if text.startswith('(') and text.endswith(')'):
            # Verificar que los paréntesis están balanceados y cubren toda la expresión
            inner_text = text[1:-1].strip()
            if self._are_parentheses_balanced(inner_text):
                # Es una expresión completamente entre paréntesis
                return self._parse_binary_expression(inner_text)
        
        # Verificar si hay paréntesis para llamadas a función
        if "(" in text and ")" in text and not any(op in text for op in ['||', '&&', '==', '!=', '<=', '>=', '<', '>', '+', '-', '*', '/', '%']):
            # Posible llamada a función
            func_match = text.split('(', 1)
            if len(func_match) == 2:
                func_name = func_match[0].strip()
                args_text = func_match[1].rstrip(')')
                
                # CORREGIR: Verificar si es llamada a método (obj.method)
                if "." in func_name:
                    dot_pos = func_name.find(".")
                    obj_name = func_name[:dot_pos]
                    method_name = func_name[dot_pos+1:]
                    
                    # Emitir 'this' como primer parámetro
                    obj_slot = self.get_variable_slot_lazy(obj_name)
                    self.emit(f"PARAM {obj_slot}")
                    
                    # Emitir argumentos explícitos
                    num_args = 1  # Contar 'this'
                    if args_text.strip():
                        args = [arg.strip() for arg in args_text.split(',') if arg.strip()]
                        num_args += len(args)
                        for arg in args:
                            arg_result = self._evaluate_simple_operand(arg)
                            self.emit(f"PARAM {arg_result}")
                    
                    # Emitir llamada al método (sin prefijo del objeto)
                    self.emit(f"CALL {method_name},{num_args}")
                else:
                    # Llamada a función normal
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
        operators_by_precedence = [
            ['||'],           # OR lógico - menor precedencia  
            ['&&'],           # AND lógico
            ['==', '!='],     # Igualdad
            ['<', '<=', '>', '>='], # Relacionales
            ['+', '-'],       # Suma/resta
            ['*', '/', '%']   # Multiplicación/división - MAYOR precedencia
        ]
        
        # NUEVO: Buscar operadores respetando paréntesis
        for operator_group in operators_by_precedence:
            best_split = self._find_operator_outside_parentheses(text, operator_group)
            
            if best_split:
                left, right, op = best_split
                
                # Evaluar recursivamente con precedencia correcta
                left_result = self._parse_expression_with_precedence(left)
                right_result = self._parse_expression_with_precedence(right)
                
                # Generar código TAC
                result = self.new_temp()
                self.emit_binary_op(result, left_result, op, right_result)
                return result
        
        return None
    
    def _are_parentheses_balanced(self, text: str) -> bool:
        """Verifica si los paréntesis están balanceados"""
        count = 0
        for char in text:
            if char == '(':
                count += 1
            elif char == ')':
                count -= 1
                if count < 0:
                    return False
        return count == 0
    
    def _find_operator_outside_parentheses(self, text: str, operators: list) -> tuple:
        """Encuentra operadores fuera de paréntesis, de derecha a izquierda"""
        paren_depth = 0
        
        # Buscar de derecha a izquierda para respetar asociatividad
        for i in range(len(text) - 1, -1, -1):
            char = text[i]
            
            if char == ')':
                paren_depth += 1
            elif char == '(':
                paren_depth -= 1
            elif paren_depth == 0:  # Solo considerar operadores fuera de paréntesis
                # Buscar operadores en la posición actual
                for op in operators:
                    if text[i:i+len(op)] == op:
                        # Verificar que no es parte de <= o >=
                        if op == '<' and i+1 < len(text) and text[i+1] == '=':
                            continue
                        if op == '>' and i+1 < len(text) and text[i+1] == '=':
                            continue
                        if op == '=' and i > 0 and text[i-1] in ['<', '>', '!', '=']:
                            continue
                        
                        # Verificar que hay contenido antes y después
                        if i > 0 and i + len(op) < len(text):
                            left_part = text[:i].strip()
                            right_part = text[i + len(op):].strip()
                            if left_part and right_part:
                                return (left_part, right_part, op)
        
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
        elif "." in expr and not any(op in expr for op in ['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=']):
            # Es un acceso a campo sin operadores
            return self._parse_field_access(expr)
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
        
        # NUEVO: Remover paréntesis externos no balanceados
        while operand.startswith('(') and not operand.endswith(')'):
            operand = operand[1:].strip()
        while operand.endswith(')') and not operand.startswith('('):
            operand = operand[:-1].strip()
        
        # Manejar paréntesis balanceados
        if operand.startswith('(') and operand.endswith(')'):
            inner = operand[1:-1].strip()
            if self._are_parentheses_balanced(inner):
                return self._parse_expression_with_precedence(inner)
        
        if operand.isdigit():
            return operand
        
        if operand.startswith('"') and operand.endswith('"'):
            return operand
        
        if operand == "true":
            return "1"
        
        if operand == "false":
            return "0"
        
        # Manejar acceso a campos obj.field
        if "." in operand:
            field_access = self._parse_field_access(operand)
            if field_access:
                return field_access
        
        # CORREGIR: Variables deben resolverse a sus slots correctos
        if operand.isalnum():
            return self.get_variable_slot_lazy(operand)
        
        # Si es una expresión compleja, usar parser recursivo
        complex_result = self._parse_binary_expression(operand)
        if complex_result:
            return complex_result
        
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
        """Procesa un statement que es una llamada a función o método"""
        if "(" in call_text and ")" in call_text:
            func_match = call_text.split('(', 1)
            if len(func_match) == 2:
                func_name = func_match[0].strip()
                args_text = func_match[1].rstrip(')')
                
                # Verificar si es llamada a método (obj.method)
                if "." in func_name:
                    dot_pos = func_name.find(".")
                    obj_name = func_name[:dot_pos]
                    method_name = func_name[dot_pos+1:]
                    
                    # Emitir 'this' como primer parámetro
                    obj_slot = self.get_variable_slot_lazy(obj_name)
                    self.emit(f"PARAM {obj_slot}")
                    
                    # Emitir argumentos explícitos
                    num_args = 1  # Contar 'this'
                    if args_text.strip():
                        args = [arg.strip() for arg in args_text.split(',') if arg.strip()]
                        num_args += len(args)
                        for arg in args:
                            arg_result = self._evaluate_simple_operand(arg)
                            self.emit(f"PARAM {arg_result}")
                    
                    # Emitir llamada al método (sin prefijo del objeto)
                    self.emit(f"CALL {method_name},{num_args}")
                else:
                    # Llamada a función normal
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
        """Asignación directa o a campo de objeto"""
        # Verificar si ya fue procesado manualmente
        if self._is_already_processed(ctx):
            return
        
        # Manejar tanto assignment simple como property assignment
        if hasattr(ctx, 'expression') and ctx.expression():
            expressions = ctx.expression()
            
            # Caso 1: Asignación a propiedad obj.field = value
            if len(expressions) >= 2:
                # expression '.' Identifier '=' expression ';'
                obj_expr = expressions[0]
                value_expr = expressions[1]
                field_name = ctx.Identifier().getText() if ctx.Identifier() else None
                
                if field_name:
                    obj_result = self.visit_expression(obj_expr)
                    value_result = self.visit_expression(value_expr)
                    
                    # Manejar this.field = value
                    obj_text = obj_expr.getText() if hasattr(obj_expr, 'getText') else str(obj_expr)
                    if obj_text == "this":
                        # Buscar el offset del campo en la clase actual
                        current_class_name = self.current_class if self.current_class else None
                        if current_class_name and current_class_name in self.class_fields:
                            field_offset = self.class_fields[current_class_name].get(field_name, 0)
                            self.emit(f'fp[-1][{field_offset}] := {value_result}')
                    else:
                        self._handle_field_assignment(obj_result, field_name, value_result)
                return
        
        # Caso 2: Asignación simple var = value
        if not ctx.Identifier():
            return
        
        var_name = ctx.Identifier().getText()
        
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
            
            # CORREGIR: Si es un campo de clase en método de clase, usar fp[-1][offset]
            if (hasattr(self, 'current_class') and self.current_class and 
                self.current_class in self.class_fields and 
                var_name in self.class_fields[self.current_class]):
                field_offset = self.class_fields[self.current_class][var_name]
                self.emit(f"fp[-1][{field_offset}] := {rhs}")
            else:
                # Asignación normal
                var_slot = self.get_variable_slot_lazy(var_name)
                self.emit_assign(var_slot, rhs)
    
    def _mark_context_as_processed(self, ctx):
        """Marca un contexto y todos sus descendientes como ya procesados"""
        self._processed_contexts.add(id(ctx))
        
        # Marcar recursivamente todos los hijos
        if hasattr(ctx, 'children') and ctx.children:
            for child in ctx.children:
                if hasattr(child, 'children'):  # Es un contexto de parser
                    self._mark_context_as_processed(child)
    
    def _is_already_processed(self, ctx):
        """Verifica si un contexto ya fue procesado"""
        return id(ctx) in self._processed_contexts
    
    def _process_block_statements(self, block_ctx):
        """Procesa manualmente las declaraciones de un bloque"""
        if not block_ctx or not hasattr(block_ctx, 'statement'):
            return
        
        statements = block_ctx.statement()
        if statements:
            for stmt in statements:
                self._process_statement(stmt)
    
    def _process_statement(self, stmt_ctx):
        """Procesa manualmente una declaración individual"""
        if not stmt_ctx:
            return
        
        # Procesar diferentes tipos de declaraciones
        if hasattr(stmt_ctx, 'assignment') and stmt_ctx.assignment():
            self._process_assignment_manually(stmt_ctx.assignment())
        elif hasattr(stmt_ctx, 'variableDeclaration') and stmt_ctx.variableDeclaration():
            self.enterVariableDeclaration(stmt_ctx.variableDeclaration())
        elif hasattr(stmt_ctx, 'expressionStatement') and stmt_ctx.expressionStatement():
            self.enterExpressionStatement(stmt_ctx.expressionStatement())
        elif hasattr(stmt_ctx, 'printStatement') and stmt_ctx.printStatement():
            self.enterPrintStatement(stmt_ctx.printStatement())
        elif hasattr(stmt_ctx, 'returnStatement') and stmt_ctx.returnStatement():
            self.enterReturnStatement(stmt_ctx.returnStatement())
        elif hasattr(stmt_ctx, 'ifStatement') and stmt_ctx.ifStatement():
            self.enterIfStatement(stmt_ctx.ifStatement())
        elif hasattr(stmt_ctx, 'whileStatement') and stmt_ctx.whileStatement():
            self.enterWhileStatement(stmt_ctx.whileStatement())
    
    def _process_assignment_manually(self, assign_ctx):
        """Procesa asignación manualmente (evita duplicados) - incluye asignaciones a campos"""
        if not assign_ctx:
            return
            
        # Detectar si es asignación a campo basándose en el texto
        if hasattr(assign_ctx, 'getText'):
            assign_text = assign_ctx.getText()
            
            # Buscar patrón obj.field = value
            if "." in assign_text and "=" in assign_text:
                # this.nombre = n; -> parsear manualmente
                eq_pos = assign_text.find("=")
                dot_pos = assign_text.find(".")
                
                if dot_pos < eq_pos:
                    obj_field = assign_text[:eq_pos].strip()
                    value_part = assign_text[eq_pos+1:].strip().rstrip(";")
                    
                    if "." in obj_field:
                        obj_name, field_name = obj_field.split(".", 1)
                        value_result = self._evaluate_simple_operand(value_part)
                        
                        if obj_name == "this":
                            field_offset = self._get_field_offset(field_name)
                            self.emit(f"fp[-1][{field_offset}] := {value_result}")
                            return
        
        # Asignación simple
        if not assign_ctx.Identifier():
            return
        
        var_name = assign_ctx.Identifier().getText()
        var_slot = self.get_variable_slot_lazy(var_name)
        
        expr = assign_ctx.expression()
        if expr:
            if isinstance(expr, list):
                if len(expr) > 0:
                    rhs = self.visit_expression(expr[0])
                else:
                    rhs = "0"
            else:
                rhs = self.visit_expression(expr)
            self.emit_assign(var_slot, rhs)

    def enterBlock(self, ctx: CompiscriptParser.BlockContext):
        """Evita procesamiento automático de bloques ya procesados"""
        if self._is_already_processed(ctx):
            return
        # Permitir procesamiento normal para otros casos
    
    def exitBlock(self, ctx: CompiscriptParser.BlockContext):
        """Salida de bloque - no hacer nada especial"""
        pass

    # ==================== CONTROL FLOW ====================
    
    def enterIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        """Statement if con CORTO CIRCUITO - Siguiendo S → if(B)S₁ [else S₂]:
        
        Formato con corto circuito:
        B.true = IF_TRUE_k, B.false = IF_FALSE_k o IF_END_k
        
        Para if-else:
        etiqueta(B.true) || código(S₁) || gen('goto' IF_END_k) ||
        etiqueta(B.false) || código(S₂)
        
        Para if simple:
        etiqueta(B.true) || código(S₁) 
        B.false = IF_END_k = siguiente declaración
        """
        if not ctx.expression():
            return
        
        # Usar ID único para este if - sufijo numérico consistente
        if_id = self.if_counter
        self.if_counter += 1
        
        # Generar labels con el mismo ID k
        true_label = f"IF_TRUE_{if_id}"
        false_label = f"IF_FALSE_{if_id}" 
        end_label = f"IF_END_{if_id}"
        
        # Verificar si hay bloque ELSE
        has_else = ctx.block() and len(ctx.block()) > 1
        
        # CORTO CIRCUITO: evalúar B con B.true y B.false apropiados
        # Para expresiones negadas, siempre generar IF_FALSE_k para claridad
        expr_text = ctx.expression().getText()
        is_negated = expr_text.strip().startswith('!')
        
        if has_else or is_negated:
            # B.false = IF_FALSE_k (inicio del else o manejo de negación)
            self.evaluate_boolean_expression(ctx.expression(), true_label, false_label)
        else:
            # B.false = IF_END_k (no hay else ni negación, salta al final)
            self.evaluate_boolean_expression(ctx.expression(), true_label, end_label)
        
        # IF_TRUE_k: código del bloque THEN
        self.emit_label(true_label)
        if ctx.block() and len(ctx.block()) > 0:
            self._process_block_statements(ctx.block()[0])  # S₁
        
        if has_else:
            # gen('goto' IF_END_k) - saltar el else
            self.emit_goto(end_label)
            
            # IF_FALSE_k: código del bloque ELSE  
            self.emit_label(false_label)
            self._process_block_statements(ctx.block()[1])  # S₂
            
            # IF_END_k: continuación
            self.emit_label(end_label)
        elif is_negated:
            # Sin else pero con negación: generar IF_FALSE_k que salte a IF_END_k
            self.emit_label(false_label)
            self.emit_goto(end_label)
            
            # IF_END_k: continuación
            self.emit_label(end_label)
        else:
            # Sin else ni negación: IF_END_k ya es el destino de B.false
            self.emit_label(end_label)
        
        # Marcar contexto como procesado para evitar duplicación
        self._mark_context_as_processed(ctx)
    
    def exitIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        """Salida de if statement - Ya se procesó todo manualmente en enterIfStatement"""
        # No hacer nada - ya se procesó todo manualmente
        pass
    
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
    
    # ==================== OBJECT-ORIENTED PROGRAMMING ====================
    
    def enterClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        """Declaración de clase"""
        if not ctx.Identifier():
            return
            
        class_name = ctx.Identifier(0).getText()  # Primer identificador es el nombre de clase
        
        # Manejar herencia si existe
        self.current_class = class_name
        self.current_field_offset = 0  # Resetear offset de campos
        
        # Registrar campos de la clase manualmente
        if hasattr(ctx, 'children') and ctx.children:
            for child in ctx.children:
                # Buscar declaraciones de variables directamente en los hijos
                if hasattr(child, 'variableDeclaration') and child.variableDeclaration():
                    var_decl = child.variableDeclaration()
                    if var_decl and var_decl.Identifier():
                        field_name = var_decl.Identifier().getText()
                        field_type = "integer"  # default
                        if var_decl.typeAnnotation() and var_decl.typeAnnotation().type_():
                            field_type = var_decl.typeAnnotation().type_().getText()
                        self._register_field(class_name, field_name, field_type)
        
        if len(ctx.Identifier()) > 1:
            # Hay herencia: class Child extends Parent
            parent_class = ctx.Identifier(1).getText()
            self.emit(f"// CLASS {class_name} extends {parent_class}")
        else:
            self.emit(f"// CLASS {class_name}")
    
    def exitClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        """Salida de declaración de clase"""
        if hasattr(self, 'current_class'):
            self.emit(f"// END CLASS {self.current_class}")
            self.current_class = None
    
    def enterInitMethod(self, ctx: CompiscriptParser.InitMethodContext):
        """Método constructor init"""
        if not hasattr(self, 'current_class') or not self.current_class:
            return
            
        # Generar función constructora con nombre de clase
        constructor_name = f"{self.current_class}_init"
        self.current_function = constructor_name
        self.function_stack.append(constructor_name)
        self.scope_depth += 1
        
        # Entrar en nuevo ámbito de función
        self.scope_stack.append(f"function_{constructor_name}")
        current_scope = self.scope_stack[-1]
        self.scope_variables[current_scope] = {}
        
        # Resetear contador local para esta función
        self.current_local_offset = 4  # Reservar slot para 'this' en fp[0]
        self.local_variables.clear()
        
        # Primer parámetro siempre es 'this'
        self.local_variables['this'] = 0
        self.scope_variables[current_scope]['this'] = 0
        
        # Asignar slots para parámetros (empezando desde fp[4])
        if ctx.parameters() and ctx.parameters().parameter():
            for i, param in enumerate(ctx.parameters().parameter()):
                if param.Identifier():
                    param_name = param.Identifier().getText()
                    param_offset = (i + 1) * 4  # fp[4], fp[8], fp[12], etc.
                    self.local_variables[param_name] = param_offset
                    self.scope_variables[current_scope][param_name] = param_offset
        
        self.emit(f"FUNCTION init:")
        self.indent_in()
    
    def exitInitMethod(self, ctx: CompiscriptParser.InitMethodContext):
        """Salida de método constructor"""
        if self.current_function:
            self.indent_out()
            self.emit(f"END FUNCTION init")
            
            # Salir del ámbito de función
            if len(self.scope_stack) > 1:
                self.scope_stack.pop()
            
            self.function_stack.pop()
            self.current_function = self.function_stack[-1] if self.function_stack else None
            self.scope_depth -= 1
    
    def _handle_this_access(self, field_name: str) -> str:
        """Maneja acceso a this.campo usando offsets correctos"""
        # Calcular offset del campo (por bytes: 0, 4, 8, 12, ...)
        field_offset = self._get_field_offset(field_name)
        # this está en fp[-1], acceder al campo usando offset
        return f"fp[-1][{field_offset}]"
    
    def _handle_new_expression(self, class_name: str, args: list) -> str:
        """Maneja creación de objetos new ClassName(args)"""
        # Crear objeto
        result = self.new_temp()
        self.emit(f"{result} = NEW {class_name}")
        
        # Llamar constructor con el objeto como primer parámetro
        self.emit(f"PARAM {result}")  # this
        for arg in args:
            self.emit_param(arg)  # argumentos del constructor
            
        self.emit_call("init", len(args) + 1)  # Llamar init directamente
        
        return result
    
    def _handle_field_assignment(self, obj: str, field: str, value: str):
        """Maneja asignación a campos: obj.field = value"""
        self.emit(f'{obj}."{field}" = {value}')
    
    def _handle_field_access(self, obj: str, field: str) -> str:
        """Maneja acceso a campos: obj.field"""
        # Determinar offset del campo
        field_offset = self._get_field_offset_for_object_by_slot(obj, field)
        return f"{obj}[{field_offset}]"
    
    def _handle_method_call(self, obj: str, method: str, args: list) -> str:
        """Maneja llamadas a métodos: obj.method(args)"""
        # Emitir parámetros: primero 'obj' (this), luego argumentos
        self.emit(f"PARAM {obj}")
        for arg in args:
            self.emit(f"PARAM {arg}")
            
        # Llamar método directamente usando nombre del método
        total_params = len(args) + 1  # this + argumentos
        self.emit(f"CALL {method},{total_params}")
        
        # Resultado en temporal
        result = self.new_temp()
        self.emit_assign(result, "R")
        return result
    
    def _handle_super_call(self, method: str, args: list) -> str:
        """Maneja llamadas super.method(args)"""
        # super.method() se traduce como llamada directa al método de la clase padre
        # En este caso simplificado, llamamos directamente al método
        
        # Emitir 'this' como primer parámetro
        this_slot = self.get_variable_slot_lazy('this')
        self.emit_param(this_slot)
        
        # Emitir argumentos
        for arg in args:
            self.emit_param(arg)
            
        # Llamar método padre
        self.emit_call(method, len(args) + 1)
        
        result = self.new_temp()
        self.emit_assign(result, "R")
        return result
    
    def _get_field_offset(self, field_name: str) -> int:
        """Obtiene el offset de un campo de clase (por bytes: 0, 4, 8, ...)"""
        if self.current_class and self.current_class in self.class_fields:
            return self.class_fields[self.current_class].get(field_name, 0)
        # Si no se encuentra, asumir que es el primer campo
        return 0
    
    def _register_field(self, class_name: str, field_name: str, field_type: str = "integer"):
        """Registra un campo de clase con su offset"""
        if class_name not in self.class_fields:
            self.class_fields[class_name] = {}
            self.current_field_offset = 0
        
        # Asignar offset y avanzar según tamaño del tipo
        field_size = self._get_type_size(field_type)
        self.class_fields[class_name][field_name] = self.current_field_offset
        self.current_field_offset += field_size
    
    def _register_class_fields(self, class_name: str, class_body):
        """Registra todos los campos de una clase con sus offsets"""
        if class_name not in self.class_fields:
            self.class_fields[class_name] = {}
            
        field_offset = 0
        
        # Buscar declaraciones de variables en el cuerpo de la clase
        if hasattr(class_body, 'children'):
            for child in class_body.children:
                if hasattr(child, 'variableDeclaration') and child.variableDeclaration():
                    var_decl = child.variableDeclaration()
                    if var_decl.Identifier():
                        field_name = var_decl.Identifier().getText()
                        
                        # Determinar tipo del campo
                        field_type = "integer"  # default
                        if var_decl.typeAnnotation() and var_decl.typeAnnotation().type_():
                            field_type = var_decl.typeAnnotation().type_().getText()
                        
                        # Registrar campo con offset
                        self.class_fields[class_name][field_name] = field_offset
                        field_offset += self._get_type_size(field_type)
    
    def _get_field_offset_for_object(self, obj_name: str, field_name: str) -> int:
        """Obtiene el offset de un campo para un objeto específico"""
        # Buscar en todas las clases registradas el campo
        for class_name, fields in self.class_fields.items():
            if field_name in fields:
                offset = fields[field_name]
                return offset
        
        return 0
    
    def _get_field_offset_for_object_by_slot(self, obj_slot: str, field_name: str) -> int:
        """Obtiene el offset de un campo basado en el slot del objeto"""
        # Por simplicidad, usar la clase actual
        return self._get_field_offset_for_object("", field_name)