"""
MIPS Code Generator for Compiscript compiler
Translates Three-Address Code (TAC) to MIPS assembly
"""

from typing import Dict, List, Optional, Set, Tuple
from TACInstruction import TACInstruction, TACOperation
import re


class MIPSGenerator:
    """Generates MIPS assembly code from TAC instructions"""
    
    # MIPS register sets
    TEMP_REGISTERS = [f"$t{i}" for i in range(10)]  # $t0-$t9
    SAVED_REGISTERS = [f"$s{i}" for i in range(8)]  # $s0-$s7
    ARG_REGISTERS = [f"$a{i}" for i in range(4)]   # $a0-$a3
    RETURN_REGISTERS = ["$v0", "$v1"]                # $v0-$v1
    
    def __init__(self):
        # ==================== Register Descriptors (Bidirectional) ====================
        # Descriptor bidireccional: registro <-> variables
        self.register_descriptor: Dict[str, Set[str]] = {}  # register -> {variables}
        self.variable_descriptor: Dict[str, str] = {}  # variable -> register or memory location
        
        # Conjuntos de registros disponibles
        self.register_free: Set[str] = set(self.TEMP_REGISTERS + self.SAVED_REGISTERS)
        self.register_used: Set[str] = set()
        
        # Legacy support (mantener compatibilidad)
        self.variable_map: Dict[str, str] = {}  # variable -> register or stack location
        self.stack_variables: Dict[str, int] = {}  # variable -> stack offset
        self.global_variables: Dict[str, str] = {}  # variable -> label name
        
        # ==================== Liveness Analysis ====================
        # Información de vida de variables (next use)
        self.next_use: Dict[str, Optional[int]] = {}  # variable -> next instruction index or None
        self.current_instruction_index = 0
        self.instructions: List[TACInstruction] = []
        
        # ==================== Stack Management ====================
        self.stack_offset = 0  # Current stack offset (grows downward)
        self.frame_size = 0    # Size of current function frame
        self.max_frame_size = 0
        
        # Function management
        self.function_info: Dict[str, Dict] = {}  # function_name -> {frame_size, saved_regs, etc}
        self.current_function: Optional[str] = None
        self.function_stack: List[str] = []
        
        # Label mapping
        self.label_map: Dict[str, str] = {}  # TAC label -> MIPS label
        self.label_counter = 0
        
        # Parameter passing
        self.param_counter = 0  # For tracking parameters in current call
        self.param_stack: List[str] = []  # Stack of parameter lists
        
        # Generated code
        self.mips_code: List[str] = []
        self.data_section: List[str] = []
        self.text_section: List[str] = []
        
        # Track which saved registers are used in current function
        self.used_saved_registers: Set[str] = set()
        
    def generate(self, tac_input) -> str:
        """
        Generate MIPS code from TAC instructions or TAC string
        Returns complete MIPS assembly as string
        """
        self._reset()
        
        # Handle both TACInstruction list and string
        if isinstance(tac_input, str):
            tac_instructions = self._parse_tac_string(tac_input)
        else:
            tac_instructions = tac_input
        
        # First pass: identify functions and labels
        self._analyze_tac(tac_instructions)
        
        # Second pass: generate code
        self._generate_code(tac_instructions)
        
        # Combine sections
        return self._format_output()
    
    def generate_from_tac_string(self, tac_code: str) -> str:
        """
        Generate MIPS from TAC string (for compatibility)
        """
        return self.generate(tac_code)
    
    def generate_to_file(self, filename: str, tac_input):
        """Generate MIPS code and write to file"""
        mips_code = self.generate(tac_input)
        with open(filename, 'w') as f:
            f.write(mips_code)
    
    def _reset(self):
        """Reset generator state"""
        # Reset descriptores
        self.register_descriptor.clear()
        self.variable_descriptor.clear()
        self.register_free = set(self.TEMP_REGISTERS + self.SAVED_REGISTERS)
        self.register_used.clear()
        
        # Reset liveness analysis
        self.next_use.clear()
        self.current_instruction_index = 0
        self.instructions.clear()
        
        # Reset legacy structures
        self.variable_map.clear()
        self.stack_variables.clear()
        self.global_variables.clear()
        self.stack_offset = 0
        self.frame_size = 0
        self.max_frame_size = 0
        self.function_info.clear()
        self.current_function = None
        self.function_stack.clear()
        self.label_map.clear()
        self.label_counter = 0
        self.param_counter = 0
        self.param_stack.clear()
        self.mips_code.clear()
        self.data_section.clear()
        self.text_section.clear()
        self.used_saved_registers.clear()
    
    def _analyze_tac(self, instructions: List[TACInstruction]):
        """First pass: analyze TAC to identify functions, labels, and variables"""
        for instr in instructions:
            if instr.operation == TACOperation.LABEL:
                label_name = instr.label
                if label_name:
                    self.label_map[label_name] = self._mips_label(label_name)
            
            # Identify function boundaries
            if instr.comment:
                if "FUNCTION" in instr.comment:
                    # Extract function name from comment like "FUNCTION main:"
                    match = re.search(r'FUNCTION\s+(\w+):', instr.comment)
                    if match:
                        func_name = match.group(1)
                        self.function_info[func_name] = {
                            'frame_size': 0,
                            'saved_registers': set(),
                            'local_vars': {}
                        }
    
    def _compute_next_use(self, instructions: List[TACInstruction]):
        """
        Calcular información de next-use para cada variable
        Análisis hacia atrás (backward) para determinar cuándo se usa cada variable
        """
        # Inicializar: todas las variables sin next-use
        for instr in instructions:
            if instr.result and not (instr.result.replace('-', '').isdigit()):
                self.next_use[instr.result] = None
            if instr.arg1 and not (instr.arg1.replace('-', '').isdigit() or instr.arg1 in ['R', None]):
                self.next_use[instr.arg1] = None
            if instr.arg2 and not (instr.arg2.replace('-', '').isdigit() or instr.arg2 in ['R', None]):
                self.next_use[instr.arg2] = None
        
        # Análisis hacia atrás
        for i in range(len(instructions) - 1, -1, -1):
            instr = instructions[i]
            
            # Variable definida en esta instrucción - marcar sin next-use
            if instr.result and not instr.result.replace('-', '').isdigit():
                self.next_use[instr.result] = None
            
            # Variables usadas - actualizar next-use
            if instr.arg1 and instr.arg1 not in [None, 'R']:
                if not instr.arg1.replace('-', '').replace('.', '').isdigit():
                    self.next_use[instr.arg1] = i
            
            if instr.arg2 and instr.arg2 not in [None, 'R']:
                if not instr.arg2.replace('-', '').replace('.', '').isdigit():
                    self.next_use[instr.arg2] = i
    
    def _generate_code(self, instructions: List[TACInstruction]):
        """Second pass: generate MIPS code with liveness analysis"""
        self.instructions = instructions
        
        # Computar información de next-use
        self._compute_next_use(instructions)
        
        i = 0
        while i < len(instructions):
            self.current_instruction_index = i
            instr = instructions[i]
            
            # Handle function declarations
            if instr.comment and "FUNCTION" in instr.comment:
                func_name = self._extract_function_name(instr.comment)
                if func_name:
                    i = self._generate_function(instructions, i, func_name)
                    continue
            
            # Handle regular instructions
            self._generate_instruction(instr)
            i += 1
    
    def _generate_function(self, instructions: List[TACInstruction], start_idx: int, func_name: str) -> int:
        """Generate code for a function"""
        self.current_function = func_name
        self.function_stack.append(func_name)
        self.used_saved_registers.clear()
        self.frame_size = 0
        self.stack_offset = 0
        self.stack_variables.clear()
        
        # Function prologue
        self._emit_function_prologue(func_name)
        
        # Generate function body
        i = start_idx + 1
        while i < len(instructions):
            instr = instructions[i]
            
            # Check for end of function
            if instr.comment and f"END FUNCTION {func_name}" in instr.comment:
                self._emit_function_epilogue(func_name)
                self.current_function = self.function_stack.pop() if self.function_stack else None
                return i + 1
            
            # Generate instruction
            self._generate_instruction(instr)
            i += 1
        
        # Should not reach here if function is properly closed
        self._emit_function_epilogue(func_name)
        self.current_function = self.function_stack.pop() if self.function_stack else None
        return i
    
    
    
    def _emit_function_prologue(self, func_name: str):
        """Emit function prologue"""
        self._emit(f"\n{func_name}:")
        
        # ✅ Detectar si la función es leaf (no llama a otras funciones)
        # Si es leaf, podemos omitir guardar $ra y simplificar el prólogo
        is_leaf = self._is_leaf_function(func_name)
        
        if is_leaf:
            # Prólogo mínimo para leaf function
            self._emit("# Prologo minimo (leaf function)")
            # Solo guardar $fp si realmente necesitamos variables locales
            # Para funciones muy simples como sumar(a,b), ni siquiera necesitamos $fp
            self.function_info[func_name]['frame_size'] = 0
            self.function_info[func_name]['is_leaf'] = True
            self.frame_size = 0
        else:
            # Prólogo completo para non-leaf function
            self._emit("# Prologo")
            
            # Espacio para $ra + $fp + variables locales
            base_frame_size = 8  # Mínimo: $ra(4) + $fp(4)
            
            # Reservar espacio en stack
            self._emit("addi $sp, $sp, -{}".format(base_frame_size))
            
            # Guardar $ra y $fp
            self._emit("sw $ra, 4($sp)")
            self._emit("sw $fp, 0($sp)")
            
            # Establecer nuevo frame pointer
            self._emit("move $fp, $sp")
            
            # Guardar frame size para el epílogo
            self.function_info[func_name]['frame_size'] = base_frame_size
            self.function_info[func_name]['is_leaf'] = False
            self.frame_size = base_frame_size
        
        self._emit("")

    def _is_leaf_function(self, func_name: str) -> bool:
        """Detect if function is leaf (doesn't call other functions)"""
        # Check if function calls other functions
        # We'll analyze the function body in the instruction list
        if not self.instructions:
            return True  # Assume leaf if no instructions yet
        
        # Find function boundaries
        in_function = False
        for instr in self.instructions:
            if instr.comment:
                if f"FUNCTION {func_name}:" in instr.comment:
                    in_function = True
                elif "END FUNCTION" in instr.comment and in_function:
                    break
            
            if in_function and instr.operation == TACOperation.CALL:
                return False  # Function calls another function
        
        return True  # No CALLs found
    
    def _emit_function_epilogue(self, func_name: str):
        """Emit function epilogue"""
        is_leaf = self.function_info.get(func_name, {}).get('is_leaf', False)
        frame_size = self.function_info.get(func_name, {}).get('frame_size', 0)
        
        if is_leaf and frame_size == 0:
            # Epílogo mínimo para leaf function
            self._emit("\n# Epilogo minimo")
            self._emit("jr $ra")
        else:
            # Epílogo completo
            self._emit("\n# Epilogo")
            
            # Restaurar $ra y $fp
            self._emit("lw $ra, 4($sp)")
            self._emit("lw $fp, 0($sp)")
            
            # Restaurar stack pointer
            self._emit("addi $sp, $sp, {}".format(frame_size))
            
            # Retornar
            self._emit("jr $ra")
        
        self._emit("")
    
    def _generate_instruction(self, instr: TACInstruction):
        """Generate MIPS code for a single TAC instruction"""
        if instr.comment:
            # Handle comments (skip or emit as comment)
            if not any(keyword in instr.comment for keyword in ["FUNCTION", "END FUNCTION"]):
                self._emit("# " + instr.comment)
            return
        
        op = instr.operation
        
        if op == TACOperation.LABEL:
            self._emit_label(instr.label)
        
        elif op == TACOperation.GOTO:
            self._emit_goto(instr.label)
        
        elif op == TACOperation.IF_FALSE:
            self._emit_if_false(instr.arg1, instr.label)
        
        elif op == TACOperation.IF_TRUE:
            self._emit_if_true(instr.arg1, instr.label)
        
        elif op == TACOperation.ASSIGN:
            self._emit_assign(instr.result, instr.arg1)
        
        elif op == TACOperation.ADD:
            self._emit_binary_op("add", instr.result, instr.arg1, instr.arg2)
        
        elif op == TACOperation.SUB:
            self._emit_binary_op("sub", instr.result, instr.arg1, instr.arg2)
        
        elif op == TACOperation.MUL:
            self._emit_multiply(instr.result, instr.arg1, instr.arg2)
        
        elif op == TACOperation.DIV:
            self._emit_divide(instr.result, instr.arg1, instr.arg2)
        
        elif op == TACOperation.MOD:
            self._emit_modulo(instr.result, instr.arg1, instr.arg2)
        
        elif op == TACOperation.NEG:
            self._emit_unary_op("sub", instr.result, instr.arg1)
        
        elif op == TACOperation.EQ:
            self._emit_compare("seq", instr.result, instr.arg1, instr.arg2)
        
        elif op == TACOperation.NE:
            self._emit_compare("sne", instr.result, instr.arg1, instr.arg2)
        
        elif op == TACOperation.LT:
            self._emit_compare("slt", instr.result, instr.arg1, instr.arg2)
        
        elif op == TACOperation.LE:
            self._emit_compare("sle", instr.result, instr.arg1, instr.arg2)
        
        elif op == TACOperation.GT:
            self._emit_compare("sgt", instr.result, instr.arg1, instr.arg2)
        
        elif op == TACOperation.GE:
            self._emit_compare("sge", instr.result, instr.arg1, instr.arg2)
        
        elif op == TACOperation.AND:
            self._emit_logical_and(instr.result, instr.arg1, instr.arg2)
        
        elif op == TACOperation.OR:
            self._emit_logical_or(instr.result, instr.arg1, instr.arg2)
        
        elif op == TACOperation.NOT:
            self._emit_logical_not(instr.result, instr.arg1)
        
        elif op == TACOperation.PARAM:
            self._emit_param(instr.arg1)
        
        elif op == TACOperation.CALL:
            self._emit_call(instr.arg1, int(instr.arg2) if instr.arg2 else 0)
        
        elif op == TACOperation.RETURN:
            self._emit_return(instr.arg1)
        
        elif op == TACOperation.PRINT:
            self._emit_print(instr.arg1)
        
        elif op == TACOperation.READ:
            self._emit_read(instr.result)
        
        elif op == TACOperation.ARRAY_ACCESS:
            self._emit_array_access(instr.result, instr.arg1, instr.arg2)
        
        elif op == TACOperation.ARRAY_ASSIGN:
            self._emit_array_assign(instr.result, instr.arg1, instr.arg2)
    
    # ==================== Register Management ====================
    
    def get_register(self, variable_name: str, force_temp: bool = False, avoid_spill: bool = False) -> str:
        """
        getReg() - Algoritmo mejorado de asignación de registros con análisis de liveness
        
        Estrategia de 3 pasos:
        1. Si la variable ya tiene un registro válido, retornarlo
        2. Si hay registros libres, asignar uno (preferir $t sobre $s)
        3. Si no hay libres, hacer spilling inteligente basado en:
           - Next-use information (variables con next-use más lejano)
           - Preferencia por registros temporales sobre saved
        
        Args:
            variable_name: Nombre de la variable que necesita registro
            force_temp: Preferir registros temporales ($t) sobre saved ($s)
            avoid_spill: Evitar spilling si es posible (usar stack directamente)
        
        Returns:
            Nombre del registro asignado (ej: "$t0")
        """
        # Paso 1: Verificar si la variable ya tiene un registro válido
        if variable_name in self.variable_descriptor:
            location = self.variable_descriptor[variable_name]
            if self._is_register(location):
                # Ya tiene un registro, verificar que aún sea válido
                if location in self.register_descriptor:
                    return location
        
        # Compatibilidad con código legacy
        if variable_name in self.variable_map:
            location = self.variable_map[variable_name]
            if location.startswith("$"):
                return location
        
        # Paso 2: Intentar asignar un registro libre
        free_reg = self._allocate_free_register(prefer_temp=force_temp or True)
        if free_reg:
            self._assign_register_to_variable(free_reg, variable_name)
            # Mantener compatibilidad
            self.variable_map[variable_name] = free_reg
            return free_reg
        
        # Paso 3: No hay registros libres - hacer spilling inteligente
        if avoid_spill:
            # En casos críticos, usar stack directamente
            stack_loc = self._allocate_stack_location(variable_name)
            self.variable_map[variable_name] = stack_loc
            return stack_loc
        
        # Seleccionar registro víctima basado en next-use y costo
        victim_reg = self._select_register_for_spilling(prefer_temp=force_temp or True)
        
        # Hacer spilling del registro víctima
        self._spill_register_contents(victim_reg)
        
        # Ahora el registro está libre, asignarlo
        self._assign_register_to_variable(victim_reg, variable_name)
        self.variable_map[variable_name] = victim_reg
        return victim_reg
    
    def _is_register(self, location: str) -> bool:
        """Verificar si una ubicación es un registro"""
        return location and location.startswith("$")
    
    def _allocate_free_register(self, prefer_temp: bool = True) -> Optional[str]:
        """
        Asignar un registro libre con preferencia configurable
        Prioridad: $t0-$t9 > $s0-$s7 (si prefer_temp=True)
        """
        if prefer_temp:
            # Intentar primero registros temporales
            for reg in self.TEMP_REGISTERS:
                if reg in self.register_free:
                    self.register_free.remove(reg)
                    self.register_used.add(reg)
                    self.register_descriptor[reg] = set()
                    return reg
            
            # Luego intentar registros saved
            for reg in self.SAVED_REGISTERS:
                if reg in self.register_free:
                    self.register_free.remove(reg)
                    self.register_used.add(reg)
                    self.used_saved_registers.add(reg)
                    self.register_descriptor[reg] = set()
                    return reg
        else:
            # Intentar primero saved registers
            for reg in self.SAVED_REGISTERS:
                if reg in self.register_free:
                    self.register_free.remove(reg)
                    self.register_used.add(reg)
                    self.used_saved_registers.add(reg)
                    self.register_descriptor[reg] = set()
                    return reg
            
            # Luego temporales
            for reg in self.TEMP_REGISTERS:
                if reg in self.register_free:
                    self.register_free.remove(reg)
                    self.register_used.add(reg)
                    self.register_descriptor[reg] = set()
                    return reg
        
        return None
    
    def _assign_register_to_variable(self, register: str, variable: str):
        """
        Asignar un registro a una variable y actualizar descriptores bidireccionales
        """
        # Actualizar descriptor de registro
        if register not in self.register_descriptor:
            self.register_descriptor[register] = set()
        self.register_descriptor[register].add(variable)
        
        # Actualizar descriptor de variable
        self.variable_descriptor[variable] = register
        
        # Marcar registro como usado
        self.register_used.add(register)
        if register in self.register_free:
            self.register_free.discard(register)
    
    def _allocate_register(self, force_temp: bool = False) -> str:
        """Allocate a free register"""
        if force_temp:
            # Try temp registers first
            for reg in self.TEMP_REGISTERS:
                if reg in self.register_free:
                    self.register_free.remove(reg)
                    self.register_used.add(reg)
                    return reg
        
        # Try temp registers
        for reg in self.TEMP_REGISTERS:
            if reg in self.register_free:
                self.register_free.remove(reg)
                self.register_used.add(reg)
                return reg
        
        # Try saved registers
        for reg in self.SAVED_REGISTERS:
            if reg in self.register_free:
                self.register_free.remove(reg)
                self.register_used.add(reg)
                self.used_saved_registers.add(reg)
                return reg
        
        # No free registers - need to spill
        # For simplicity, spill a temp register
        if self.TEMP_REGISTERS:
            reg = self.TEMP_REGISTERS[0]  # Spill $t0
            return self._spill_register(reg)
        
        # Last resort: use stack
        return self._spill_to_stack()
    
    def _select_register_for_spilling(self, prefer_temp: bool = True) -> str:
        """
        Seleccionar registro víctima para spilling usando análisis de costos
        
        Estrategia:
        1. Preferir registros temporales sobre saved (saved requieren restauración)
        2. Entre registros del mismo tipo, elegir el que contiene la variable
           con el next-use más lejano (o sin next-use)
        3. Evitar spilling de registros con resultados inmediatos
        """
        candidate_registers = []
        
        # Construir lista de candidatos con su "costo" de spilling
        register_pool = self.TEMP_REGISTERS if prefer_temp else self.SAVED_REGISTERS
        
        for reg in register_pool:
            if reg in self.register_used:
                # Calcular "costo" de hacer spill de este registro
                cost = self._calculate_spill_cost(reg)
                candidate_registers.append((reg, cost))
        
        # Si no hay candidatos en el pool preferido, usar el otro
        if not candidate_registers:
            other_pool = self.SAVED_REGISTERS if prefer_temp else self.TEMP_REGISTERS
            for reg in other_pool:
                if reg in self.register_used:
                    cost = self._calculate_spill_cost(reg)
                    # Penalizar registros saved con costo extra
                    if reg in self.SAVED_REGISTERS:
                        cost += 100
                    candidate_registers.append((reg, cost))
        
        if not candidate_registers:
            # Fallback: usar $t0
            return self.TEMP_REGISTERS[0]
        
        # Seleccionar registro con mayor costo (mejor candidato para spilling)
        candidate_registers.sort(key=lambda x: x[1], reverse=True)
        return candidate_registers[0][0]
    
    def _calculate_spill_cost(self, register: str) -> int:
        """
        Calcular costo de hacer spill de un registro
        Mayor valor = mejor candidato para spilling
        
        Factores:
        - Variables sin next-use = mayor prioridad (costo alto, 10000+)
        - Variables con next-use lejano = prioridad media (costo = distancia)
        - Variables con next-use cercano = prioridad baja (costo bajo)
        """
        if register not in self.register_descriptor:
            return 1000  # Registro vacío (no debería pasar)
        
        variables_in_reg = self.register_descriptor.get(register, set())
        if not variables_in_reg:
            return 1000  # Registro sin variables
        
        # Encontrar el next-use mínimo de todas las variables en el registro
        min_next_use = float('inf')
        for var in variables_in_reg:
            next_use = self.next_use.get(var, None)
            if next_use is None:
                # Variable sin next-use = nunca se usará de nuevo
                return 10000  # Costo muy alto = excelente candidato
            min_next_use = min(min_next_use, next_use)
        
        # Costo = distancia al próximo uso
        # Mayor distancia = mayor costo = mejor candidato
        if min_next_use == float('inf'):
            return 10000
        
        cost = int(min_next_use) - self.current_instruction_index
        return max(0, cost)
    
    def _spill_register_contents(self, register: str):
        """
        Hacer spilling del contenido de un registro a memoria (stack)
        Actualiza descriptores bidireccionales
        """
        if register not in self.register_descriptor:
            return
        
        variables_in_reg = list(self.register_descriptor.get(register, set()))
        
        for var in variables_in_reg:
            # Asignar ubicación en stack si no tiene
            if var not in self.stack_variables:
                stack_loc = self._allocate_stack_location(var)
            else:
                stack_loc = self._get_stack_location(var)
            
            # Guardar valor del registro en stack
            self._emit(f"sw {register}, {stack_loc}  # Spill {var}")
            
            # Actualizar descriptor de variable
            self.variable_descriptor[var] = stack_loc
            self.variable_map[var] = stack_loc
        
        # Limpiar registro
        self.register_descriptor[register].clear()
        self.register_used.discard(register)
        self.register_free.add(register)
        if register in self.used_saved_registers:
            self.used_saved_registers.discard(register)
    
    def _spill_register(self, register: str) -> str:
        """Spill a register to stack and return it (método legacy)"""
        # Usar nuevo método mejorado
        self._spill_register_contents(register)
        return register
    
    def _allocate_stack_location(self, variable: str) -> str:
        """
        Asignar ubicación en stack para una variable
        Retorna string con formato: -offset($fp)
        """
        if variable in self.stack_variables:
            return self._get_stack_location(variable)
        
        # Asignar nuevo offset en stack
        self.stack_offset += 4
        self.frame_size = max(self.frame_size, self.stack_offset)
        self.stack_variables[variable] = self.stack_offset
        
        location = f"-{self.stack_offset}($fp)"
        self.variable_descriptor[variable] = location
        return location
    
    def _get_stack_location(self, variable: str) -> str:
        """Obtener ubicación en stack de una variable existente"""
        if variable not in self.stack_variables:
            return self._allocate_stack_location(variable)
        
        offset = self.stack_variables[variable]
        return f"-{offset}($fp)"
    
    def _spill_to_stack(self) -> str:
        """Allocate space on stack and return location (método legacy)"""
        self.stack_offset += 4
        self.frame_size = max(self.frame_size, self.stack_offset)
        location = "{}($fp)".format(-self.stack_offset)
        return location
    
    def free_register(self, register: str, save_to_memory: bool = True):
        """
        Liberar un registro (con opción de guardar a memoria)
        Usado cuando sabemos que el valor ya no se necesita
        
        Args:
            register: Registro a liberar
            save_to_memory: Si True, guarda el contenido a stack antes de liberar
        """
        if register in self.register_descriptor:
            variables = list(self.register_descriptor[register])
            for var in variables:
                if save_to_memory and var in self.variable_descriptor:
                    if self.variable_descriptor[var] == register:
                        # Variable solo está en registro, moverla a stack
                        if var not in self.stack_variables:
                            stack_loc = self._allocate_stack_location(var)
                            self._emit(f"sw {register}, {stack_loc}  # Save {var} before freeing")
            
            self.register_descriptor[register].clear()
        
        self.register_used.discard(register)
        self.register_free.add(register)
        if register in self.used_saved_registers:
            self.used_saved_registers.discard(register)
    
    def _free_register(self, register: str):
        """Free a register (método legacy sin guardar)"""
        self.free_register(register, save_to_memory=False)
    
    def _get_operand_location(self, operand: str) -> str:
        """Get register or immediate value for operand"""
        # Check if it's a number
        if operand and operand.replace('-', '').isdigit():
            return operand
        
        # Check if it's a register already
        if operand and operand.startswith("$"):
            return operand
        
        # ✅ Check if it's a parameter reference (fp[-N])
        if operand and 'fp[' in operand and '-' in operand:
            param_index = self._extract_param_index(operand)
            if param_index is not None:
                # Map parameter index to register or stack location
                return self._get_parameter_location(param_index)
        
        # Check if it's in variable map
        if operand in self.variable_map:
            loc = self.variable_map[operand]
            if loc.startswith("$"):
                return loc
            # Load from stack
            reg = self._allocate_register(force_temp=True)
            self._emit("lw {}, {}".format(reg, loc))
            return reg
        
        # New variable - allocate register
        return self.get_register(operand, force_temp=True)
    
    def _extract_param_index(self, operand: str) -> Optional[int]:
        """
        Extraer índice de parámetro desde notación fp[-N]
        Ejemplo: fp[-2] -> 2, fp[-3] -> 3
        """
        import re
        match = re.search(r'fp\[(-\d+)\]', operand)
        if match:
            return abs(int(match.group(1)))
        return None
    
    def _get_parameter_location(self, param_index: int) -> str:
        """
        Obtener ubicación de un parámetro basado en su índice
        
        Convención MIPS:
        - Parámetros 1-4: vienen en $a0-$a3 (en orden)
        - Parámetros 5+: vienen en stack en 8($fp), 12($fp), ...
        
        TAC Notation:
        - fp[-1] = primer parámetro  -> $a0
        - fp[-2] = segundo parámetro -> $a1
        - fp[-3] = tercer parámetro  -> $a2
        - fp[-4] = cuarto parámetro  -> $a3
        
        Args:
            param_index: Índice del parámetro extraído de fp[-N] (N es param_index)
        
        Returns:
            Registro ($a0-$a3) o carga desde stack
        """
        if param_index <= 4:
            # Mapeo directo: fp[-1] -> $a0, fp[-2] -> $a1, fp[-3] -> $a2, fp[-4] -> $a3
            arg_reg_index = param_index - 1  # fp[-1] -> index 0 ($a0), fp[-2] -> index 1 ($a1)
            if 0 <= arg_reg_index < 4:
                return self.ARG_REGISTERS[arg_reg_index]
        
        # Parámetros adicionales (5+) están en el stack
        # fp[-5] -> 8($fp), fp[-6] -> 12($fp), etc.
        stack_offset = (param_index - 4) * 4 + 8
        
        # Cargar desde stack a un registro temporal
        reg = self._allocate_register(force_temp=True)
        self._emit(f"lw {reg}, {stack_offset}($fp)  # Load param {param_index}")
        return reg
    
    # ==================== Code Generation Methods ====================
    
    def _emit(self, code: str):
        """Emit MIPS instruction"""
        self.text_section.append(code)
    
    def _emit_label(self, label: str):
        """Emit label"""
        mips_label = self.label_map.get(label, self._mips_label(label))
        self._emit("{}:".format(mips_label))
    
    def _emit_goto(self, label: str):
        """Emit goto"""
        mips_label = self.label_map.get(label, self._mips_label(label))
        self._emit("j {}".format(mips_label))
    
    def _emit_if_false(self, condition: str, label: str):
        """Emit if_false: if condition is false (0), goto label"""
        cond_reg = self._get_operand_location(condition)
        mips_label = self.label_map.get(label, self._mips_label(label))
        self._emit("beq {}, $zero, {}".format(cond_reg, mips_label))
    
    def _emit_if_true(self, condition: str, label: str):
        """Emit if_true: if condition is true (non-zero), goto label"""
        cond_reg = self._get_operand_location(condition)
        mips_label = self.label_map.get(label, self._mips_label(label))
        self._emit("bne {}, $zero, {}".format(cond_reg, mips_label))
    
    def _emit_assign(self, result: str, source: str):
        """Emit assignment: result = source"""
        if not result:
            return
        
        # Special case: R is return value register
        if source == 'R':
            result_reg = self.get_register(result, force_temp=True)
            # Avoid unnecessary move if result is already mapped to $v0
            if result_reg != "$v0":
                self._emit("move {}, $v0".format(result_reg))
            return
        
        src_loc = self._get_operand_location(source)
        dst_reg = self.get_register(result, force_temp=True)
        
        # Avoid move if source and destination are the same register
        if src_loc == dst_reg:
            return  # No operation needed
        
        if src_loc.startswith("$"):
            self._emit("move {}, {}".format(dst_reg, src_loc))
        elif src_loc.replace('-', '').isdigit():
            # Immediate value
            self._emit("li {}, {}".format(dst_reg, src_loc))
        else:
            # Load from memory
            self._emit("lw {}, {}".format(dst_reg, src_loc))
    
    def _emit_binary_op(self, op: str, result: str, arg1: str, arg2: str):
        """Emit binary operation"""
        if not result:
            return
        
        # Obtener ubicaciones de operandos (ya maneja parámetros correctamente)
        op1 = self._get_operand_location(arg1)
        op2 = self._get_operand_location(arg2)
        res_reg = self.get_register(result, force_temp=True)
        
        # Caso 1: op2 es un valor inmediato pequeño
        if op2.replace('-', '').isdigit():
            imm_value = int(op2)
            if -32768 <= imm_value <= 32767:
                # Asegurar que op1 es un registro
                if not op1.startswith("$"):
                    op1_reg = self._allocate_register(force_temp=True)
                    self._emit("lw {}, {}".format(op1_reg, op1))
                    op1 = op1_reg
                
                if op == "add":
                    self._emit("addi {}, {}, {}".format(res_reg, op1, op2))
                    return
                elif op == "sub" and imm_value >= 0:
                    self._emit("addi {}, {}, {}".format(res_reg, op1, -imm_value))
                    return
        
        # Caso 2: Ambos operandos deben estar en registros
        # Asegurar que op1 es un registro
        if not op1.startswith("$"):
            if op1.replace('-', '').isdigit():
                op1_reg = self._allocate_register(force_temp=True)
                self._emit("li {}, {}".format(op1_reg, op1))
                op1 = op1_reg
            else:
                op1_reg = self._allocate_register(force_temp=True)
                self._emit("lw {}, {}".format(op1_reg, op1))
                op1 = op1_reg
        
        # Asegurar que op2 es un registro
        if not op2.startswith("$"):
            if op2.replace('-', '').isdigit():
                op2_reg = self._allocate_register(force_temp=True)
                self._emit("li {}, {}".format(op2_reg, op2))
                op2 = op2_reg
            else:
                op2_reg = self._allocate_register(force_temp=True)
                self._emit("lw {}, {}".format(op2_reg, op2))
                op2 = op2_reg
        
        # Emitir operación
        # Para ADD, usar addu para evitar excepciones de overflow
        if op == "add":
            self._emit("addu {}, {}, {}".format(res_reg, op1, op2))
        else:
            self._emit("{} {}, {}, {}".format(op, res_reg, op1, op2))
    
    def _emit_multiply(self, result: str, arg1: str, arg2: str):
        """Emit multiplication"""
        op1 = self._get_operand_location(arg1)
        op2 = self._get_operand_location(arg2)
        res_reg = self.get_register(result, force_temp=True)
        
        # Load operands if needed
        if not op1.startswith("$"):
            op1_reg = self._allocate_register(force_temp=True)
            self._emit("lw {}, {}".format(op1_reg, op1))
            op1 = op1_reg
        if not op2.startswith("$"):
            op2_reg = self._allocate_register(force_temp=True)
            self._emit("lw {}, {}".format(op2_reg, op2))
            op2 = op2_reg
        
        self._emit("mult {}, {}".format(op1, op2))
        self._emit("mflo {}".format(res_reg))
    
    def _emit_divide(self, result: str, arg1: str, arg2: str):
        """Emit division"""
        op1 = self._get_operand_location(arg1)
        op2 = self._get_operand_location(arg2)
        res_reg = self.get_register(result, force_temp=True)
        
        # Load operands if needed
        if not op1.startswith("$"):
            op1_reg = self._allocate_register(force_temp=True)
            self._emit("lw {}, {}".format(op1_reg, op1))
            op1 = op1_reg
        if not op2.startswith("$"):
            op2_reg = self._allocate_register(force_temp=True)
            self._emit("lw {}, {}".format(op2_reg, op2))
            op2 = op2_reg
        
        self._emit("div {}, {}".format(op1, op2))
        self._emit("mflo {}".format(res_reg))
    
    def _emit_modulo(self, result: str, arg1: str, arg2: str):
        """Emit modulo"""
        op1 = self._get_operand_location(arg1)
        op2 = self._get_operand_location(arg2)
        res_reg = self.get_register(result, force_temp=True)
        
        # Load operands if needed
        if not op1.startswith("$"):
            op1_reg = self._allocate_register(force_temp=True)
            self._emit("lw {}, {}".format(op1_reg, op1))
            op1 = op1_reg
        if not op2.startswith("$"):
            op2_reg = self._allocate_register(force_temp=True)
            self._emit("lw {}, {}".format(op2_reg, op2))
            op2 = op2_reg
        
        self._emit("div {}, {}".format(op1, op2))
        self._emit("mfhi {}".format(res_reg))
    
    def _emit_unary_op(self, op: str, result: str, operand: str):
        """Emit unary operation"""
        op_reg = self._get_operand_location(operand)
        res_reg = self.get_register(result, force_temp=True)
        
        if op == "sub":  # Negation
            self._emit("sub {}, $zero, {}".format(res_reg, op_reg))
        elif op == "not":  # Logical NOT
            self._emit("xori {}, {}, 1".format(res_reg, op_reg))
    
    def _emit_compare(self, op: str, result: str, arg1: str, arg2: str):
        """Emit comparison operation"""
        op1 = self._get_operand_location(arg1)
        op2 = self._get_operand_location(arg2)
        res_reg = self.get_register(result, force_temp=True)
        
        # MIPS doesn't have seq, sle, sge directly - need to implement
        if op == "slt":
            # Optimización: usar slti si op2 es inmediato
            if op2.replace('-', '').isdigit():
                imm_value = int(op2)
                if -32768 <= imm_value <= 32767:
                    if not op1.startswith("$"):
                        op1_reg = self._allocate_register(force_temp=True)
                        if op1.replace('-', '').isdigit():
                            self._emit("li {}, {}".format(op1_reg, op1))
                        else:
                            self._emit("lw {}, {}".format(op1_reg, op1))
                        op1 = op1_reg
                    self._emit("slti {}, {}, {}".format(res_reg, op1, op2))
                    return
            
            # Caso general: ambos en registros
            if not op1.startswith("$"):
                op1_reg = self._allocate_register(force_temp=True)
                if op1.replace('-', '').isdigit():
                    self._emit("li {}, {}".format(op1_reg, op1))
                else:
                    self._emit("lw {}, {}".format(op1_reg, op1))
                op1 = op1_reg
            if not op2.startswith("$"):
                op2_reg = self._allocate_register(force_temp=True)
                if op2.replace('-', '').isdigit():
                    self._emit("li {}, {}".format(op2_reg, op2))
                else:
                    self._emit("lw {}, {}".format(op2_reg, op2))
                op2 = op2_reg
            self._emit("slt {}, {}, {}".format(res_reg, op1, op2))
        elif op == "seq":  # a == b
            # seq $r, $a, $b -> sub $r, $a, $b; sltiu $r, $r, 1
            if not op1.startswith("$"):
                op1_reg = self._allocate_register(force_temp=True)
                if op1.replace('-', '').isdigit():
                    self._emit("li {}, {}".format(op1_reg, op1))
                else:
                    self._emit("lw {}, {}".format(op1_reg, op1))
                op1 = op1_reg
            if not op2.startswith("$"):
                op2_reg = self._allocate_register(force_temp=True)
                if op2.replace('-', '').isdigit():
                    self._emit("li {}, {}".format(op2_reg, op2))
                else:
                    self._emit("lw {}, {}".format(op2_reg, op2))
                op2 = op2_reg
            temp_reg = self._allocate_register(force_temp=True)
            self._emit("sub {}, {}, {}".format(temp_reg, op1, op2))
            self._emit("sltiu {}, {}, 1".format(res_reg, temp_reg))
        elif op == "sne":  # a != b
            # sne $r, $a, $b -> seq then not
            if not op1.startswith("$"):
                op1_reg = self._allocate_register(force_temp=True)
                if op1.replace('-', '').isdigit():
                    self._emit("li {}, {}".format(op1_reg, op1))
                else:
                    self._emit("lw {}, {}".format(op1_reg, op1))
                op1 = op1_reg
            if not op2.startswith("$"):
                op2_reg = self._allocate_register(force_temp=True)
                if op2.replace('-', '').isdigit():
                    self._emit("li {}, {}".format(op2_reg, op2))
                else:
                    self._emit("lw {}, {}".format(op2_reg, op2))
                op2 = op2_reg
            temp_reg = self._allocate_register(force_temp=True)
            self._emit("sub {}, {}, {}".format(temp_reg, op1, op2))
            self._emit("sltiu {}, {}, 1".format(temp_reg, temp_reg))
            self._emit("xori {}, {}, 1".format(res_reg, temp_reg))
        elif op == "sle":  # a <= b
            # sle $r, $a, $b -> slt $r, $b, $a; xori $r, $r, 1
            if not op1.startswith("$"):
                op1_reg = self._allocate_register(force_temp=True)
                if op1.replace('-', '').isdigit():
                    self._emit("li {}, {}".format(op1_reg, op1))
                else:
                    self._emit("lw {}, {}".format(op1_reg, op1))
                op1 = op1_reg
            if not op2.startswith("$"):
                op2_reg = self._allocate_register(force_temp=True)
                if op2.replace('-', '').isdigit():
                    self._emit("li {}, {}".format(op2_reg, op2))
                else:
                    self._emit("lw {}, {}".format(op2_reg, op2))
                op2 = op2_reg
            self._emit("slt {}, {}, {}".format(res_reg, op2, op1))
            self._emit("xori {}, {}, 1".format(res_reg, res_reg))
        elif op == "sgt":  # a > b
            # sgt $r, $a, $b -> slt $r, $b, $a
            if not op1.startswith("$"):
                op1_reg = self._allocate_register(force_temp=True)
                if op1.replace('-', '').isdigit():
                    self._emit("li {}, {}".format(op1_reg, op1))
                else:
                    self._emit("lw {}, {}".format(op1_reg, op1))
                op1 = op1_reg
            if not op2.startswith("$"):
                op2_reg = self._allocate_register(force_temp=True)
                if op2.replace('-', '').isdigit():
                    self._emit("li {}, {}".format(op2_reg, op2))
                else:
                    self._emit("lw {}, {}".format(op2_reg, op2))
                op2 = op2_reg
            self._emit("slt {}, {}, {}".format(res_reg, op2, op1))
        elif op == "sge":  # a >= b
            # sge $r, $a, $b -> slt $r, $a, $b; xori $r, $r, 1
            # Optimización: usar slti si op2 es inmediato
            if op2.replace('-', '').isdigit():
                imm_value = int(op2)
                if -32768 <= imm_value <= 32767:
                    if not op1.startswith("$"):
                        op1_reg = self._allocate_register(force_temp=True)
                        if op1.replace('-', '').isdigit():
                            self._emit("li {}, {}".format(op1_reg, op1))
                        else:
                            self._emit("lw {}, {}".format(op1_reg, op1))
                        op1 = op1_reg
                    self._emit("slti {}, {}, {}".format(res_reg, op1, op2))
                    self._emit("xori {}, {}, 1".format(res_reg, res_reg))
                    return
            
            # Caso general
            if not op1.startswith("$"):
                op1_reg = self._allocate_register(force_temp=True)
                if op1.replace('-', '').isdigit():
                    self._emit("li {}, {}".format(op1_reg, op1))
                else:
                    self._emit("lw {}, {}".format(op1_reg, op1))
                op1 = op1_reg
            if not op2.startswith("$"):
                op2_reg = self._allocate_register(force_temp=True)
                if op2.replace('-', '').isdigit():
                    self._emit("li {}, {}".format(op2_reg, op2))
                else:
                    self._emit("lw {}, {}".format(op2_reg, op2))
                op2 = op2_reg
            self._emit("slt {}, {}, {}".format(res_reg, op1, op2))
            self._emit("xori {}, {}, 1".format(res_reg, res_reg))
    
    def _emit_logical_and(self, result: str, arg1: str, arg2: str):
        """Emit logical AND"""
        op1 = self._get_operand_location(arg1)
        op2 = self._get_operand_location(arg2)
        res_reg = self.get_register(result, force_temp=True)
        
        # AND: result = (arg1 != 0) && (arg2 != 0)
        # Use sltu to check if non-zero
        temp1 = self._allocate_register(force_temp=True)
        temp2 = self._allocate_register(force_temp=True)
        self._emit("sltu {}, $zero, {}".format(temp1, op1))
        self._emit("sltu {}, $zero, {}".format(temp2, op2))
        self._emit("and {}, {}, {}".format(res_reg, temp1, temp2))
    
    def _emit_logical_or(self, result: str, arg1: str, arg2: str):
        """Emit logical OR"""
        op1 = self._get_operand_location(arg1)
        op2 = self._get_operand_location(arg2)
        res_reg = self.get_register(result, force_temp=True)
        
        # OR: result = (arg1 != 0) || (arg2 != 0)
        temp1 = self._allocate_register(force_temp=True)
        temp2 = self._allocate_register(force_temp=True)
        self._emit("sltu {}, $zero, {}".format(temp1, op1))
        self._emit("sltu {}, $zero, {}".format(temp2, op2))
        self._emit("or {}, {}, {}".format(res_reg, temp1, temp2))
    
    def _emit_logical_not(self, result: str, operand: str):
        """Emit logical NOT"""
        op_reg = self._get_operand_location(operand)
        res_reg = self.get_register(result, force_temp=True)
        
        # NOT: result = (operand == 0)
        self._emit("sltu {}, $zero, {}".format(res_reg, op_reg))
        self._emit("xori {}, {}, 1".format(res_reg, res_reg))
    
    def _emit_param(self, param: str):
        """Emit parameter passing"""
        param_value = self._get_operand_location(param)
        
        # Track parameter count
        if not self.param_stack:
            self.param_stack.append([])
        
        param_index = len(self.param_stack[-1])
        
        if param_index < 4:
            # Use argument registers $a0-$a3
            arg_reg = self.ARG_REGISTERS[param_index]
            if param_value.startswith("$"):
                self._emit("move {}, {}".format(arg_reg, param_value))
            elif param_value.replace('-', '').isdigit():
                self._emit("li {}, {}".format(arg_reg, param_value))
            else:
                self._emit("lw {}, {}".format(arg_reg, param_value))
        else:
            # ✅ CORREGIDO: Los parámetros extras se pasarán en el stack
            # Pero NO los guardamos aquí, se hace en _emit_call
            pass
        
        self.param_stack[-1].append(param_value)
    
    def _emit_call(self, func_name: str, num_params: int):
        """Emit function call"""
        # stack management
        
        # 1. Solo guardar registros temporales que realmente contienen datos importantes
        # Excluir registros que acabamos de usar solo para pasar parámetros
        saved_regs = []
        for reg in self.TEMP_REGISTERS:
            if reg in self.register_used:
                # Verificar si el registro contiene una variable que se usará después
                has_live_var = False
                if reg in self.register_descriptor:
                    for var in self.register_descriptor[reg]:
                        if var in self.next_use and self.next_use[var] is not None:
                            if self.next_use[var] > self.current_instruction_index:
                                has_live_var = True
                                break
                if has_live_var:
                    saved_regs.append(reg)
        
        # 2. Calculate necessary stack space
        stack_params = max(0, num_params - 4)  # Parameters that don't fit in $a0-$a3
        save_space = len(saved_regs) * 4
        
        # Space for: extra parameters + saved registers
        total_space = stack_params * 4 + save_space
        
        # 3. Adjust stack if necessary
        if total_space > 0:
            self._emit("addi $sp, $sp, -{}".format(total_space))
        
        # 4. Save temporal registers
        offset = total_space - 4
        for reg in saved_regs:
            self._emit("sw {}, {}($sp)".format(reg, offset))
            offset -= 4
        
        # 5. Pass extra parameters on stack (if more than 4)
        if num_params > 4 and self.param_stack:
            params = self.param_stack[-1]
            for i in range(4, num_params):
                if i < len(params):
                    param_value = params[i]
                    stack_offset = (i - 4) * 4
                    
                    if param_value.startswith("$"):
                        self._emit("sw {}, {}($sp)".format(param_value, stack_offset))
                    elif param_value.replace('-', '').isdigit():
                        temp_reg = "$t9"  # Usar $t9 temporalmente
                        self._emit("li {}, {}".format(temp_reg, param_value))
                        self._emit("sw {}, {}($sp)".format(temp_reg, stack_offset))
                    else:
                        temp_reg = "$t9"
                        self._emit("lw {}, {}".format(temp_reg, param_value))
                        self._emit("sw {}, {}($sp)".format(temp_reg, stack_offset))
        
        # 6. Call the function
        self._emit("jal {}".format(func_name))
        
        # 7. Restore temporal registers
        offset = total_space - 4
        for reg in saved_regs:
            self._emit("lw {}, {}($sp)".format(reg, offset))
            offset -= 4
        
        # 8. Restore stack
        if total_space > 0:
            self._emit("addi $sp, $sp, {}".format(total_space))
        
        # 9. Clear parameter stack
        if self.param_stack:
            self.param_stack.pop()
    
    def _emit_return(self, value: Optional[str] = None):
        """Emit return statement"""
        if value:
            value_reg = self._get_operand_location(value)
            # ✅ Evitar move innecesario si el valor ya está en $v0
            if value_reg == "$v0":
                pass  # Ya está en el registro de retorno
            elif value_reg.startswith("$"):
                self._emit("move $v0, {}".format(value_reg))
            elif value_reg.replace('-', '').isdigit():
                self._emit("li $v0, {}".format(value_reg))
            else:
                self._emit("lw $v0, {}".format(value_reg))
            # Epilogue will handle jr $ra
    
    def _emit_print(self, value: str):
        """Emit print statement"""
        value_reg = self._get_operand_location(value)
        
        # Use syscall for print integer
        # Load value to $a0
        # ✅ Evitar move innecesario si el valor ya está en $a0
        if value_reg == "$a0":
            pass  # Ya está en $a0
        elif value_reg == "$v0":
            # Caso común: print(resultado_de_funcion)
            self._emit("move $a0, $v0")
        elif value_reg.startswith("$"):
            self._emit("move $a0, {}".format(value_reg))
        elif value_reg.replace('-', '').isdigit():
            self._emit("li $a0, {}".format(value_reg))
        else:
            self._emit("lw $a0, {}".format(value_reg))
        
        # Syscall 1 = print integer
        self._emit("li $v0, 1")
        self._emit("syscall")
        
        # Print newline
        self._emit("li $v0, 4")  # print string
        self._emit("la $a0, newline")
        self._emit("syscall")
    
    def _emit_read(self, result: str):
        """Emit read statement"""
        result_reg = self.get_register(result, force_temp=True)
        
        # Syscall 5 = read integer
        self._emit("li $v0, 5")
        self._emit("syscall")
        self._emit("move {}, $v0".format(result_reg))
    
    def _emit_array_access(self, result: str, array: str, index: str):
        """Emit array access: result = array[index]"""
        array_reg = self._get_operand_location(array)
        index_reg = self._get_operand_location(index)
        result_reg = self.get_register(result, force_temp=True)
        
        # Calculate address: array + index * 4
        temp_reg = self._allocate_register(force_temp=True)
        self._emit("sll {}, {}, 2".format(temp_reg, index_reg))  # index * 4
        self._emit("add {}, {}, {}".format(temp_reg, array_reg, temp_reg))
        self._emit("lw {}, 0({})".format(result_reg, temp_reg))
    
    def _emit_array_assign(self, array: str, index: str, value: str):
        """Emit array assignment: array[index] = value"""
        array_reg = self._get_operand_location(array)
        index_reg = self._get_operand_location(index)
        value_reg = self._get_operand_location(value)
        
        # Calculate address
        temp_reg = self._allocate_register(force_temp=True)
        self._emit("sll {}, {}, 2".format(temp_reg, index_reg))
        self._emit("add {}, {}, {}".format(temp_reg, array_reg, temp_reg))
        self._emit("sw {}, 0({})".format(value_reg, temp_reg))
    
    # ==================== Helper Methods ====================
    
    def _mips_label(self, label: str) -> str:
        """Convert TAC label to MIPS label"""
        if label not in self.label_map:
            # Clean label name for MIPS
            clean_label = label.replace(":", "").replace("-", "_")
            self.label_map[label] = clean_label
        return self.label_map[label]
    
    def _extract_function_name(self, comment: str) -> Optional[str]:
        """Extract function name from comment"""
        match = re.search(r'FUNCTION\s+(\w+):', comment)
        return match.group(1) if match else None
    
    def _parse_tac_string(self, tac_code: str) -> List[TACInstruction]:
        """Parse TAC string into TACInstruction list"""
        instructions = []
        lines = tac_code.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove comments
            if ';' in line:
                comment_part = line.split(';', 1)[1].strip()
                line = line.split(';')[0].strip()
                if line:
                    instr = self._parse_tac_line(line)
                    if instr:
                        instr.comment = comment_part
                        instructions.append(instr)
                elif comment_part:
                    # Comment only line
                    instructions.append(TACInstruction(
                        operation=TACOperation.ASSIGN,
                        comment=comment_part
                    ))
                continue
            
            if line.startswith('//'):
                instructions.append(TACInstruction(
                    operation=TACOperation.ASSIGN,
                    comment=line[2:].strip()
                ))
                continue
            
            instr = self._parse_tac_line(line)
            if instr:
                instructions.append(instr)
        
        return instructions
    
    def _parse_tac_line(self, line: str) -> Optional[TACInstruction]:
        """Parse a single TAC line into TACInstruction"""
        line = line.strip()
        if not line:
            return None
        
        # Remove tabs/indentation
        line = line.lstrip('\t ')
        
        # FUNCTION declaration
        if line.startswith('FUNCTION'):
            match = re.match(r'FUNCTION\s+(\w+):', line)
            if match:
                return TACInstruction(
                    operation=TACOperation.ASSIGN,
                    comment=line
                )
        
        # END FUNCTION
        if line.startswith('END FUNCTION'):
            return TACInstruction(
                operation=TACOperation.ASSIGN,
                comment=line
            )
        
        # Label
        if line.endswith(':'):
            label = line[:-1].strip()
            return TACInstruction(
                operation=TACOperation.LABEL,
                label=label
            )
        
        # GOTO
        if line.startswith('GOTO '):
            label = line[5:].strip()
            return TACInstruction(
                operation=TACOperation.GOTO,
                label=label
            )
        
        # IF ... GOTO
        if line.startswith('IF '):
            match = re.match(r'IF\s+(\w+)\s+>\s+0\s+GOTO\s+(\w+)', line)
            if match:
                condition, label = match.groups()
                return TACInstruction(
                    operation=TACOperation.IF_TRUE,
                    arg1=condition,
                    label=label
                )
        
        # PARAM
        if line.startswith('PARAM '):
            param = line[6:].strip()
            return TACInstruction(
                operation=TACOperation.PARAM,
                arg1=param
            )
        
        # CALL
        if line.startswith('CALL '):
            rest = line[5:].strip()
            if ',' in rest:
                func_name, num_params = rest.split(',', 1)
                return TACInstruction(
                    operation=TACOperation.CALL,
                    arg1=func_name.strip(),
                    arg2=num_params.strip()
                )
        
        # RETURN
        if line.startswith('RETURN'):
            if line == 'RETURN':
                return TACInstruction(operation=TACOperation.RETURN)
            else:
                value = line[6:].strip()
                return TACInstruction(
                    operation=TACOperation.RETURN,
                    arg1=value
                )
        
        # PRINT
        if line.startswith('PRINT '):
            value = line[6:].strip()
            return TACInstruction(
                operation=TACOperation.PRINT,
                arg1=value
            )
        
        # Assignment: result := value
        if ' := ' in line:
            parts = line.split(' := ', 1)
            if len(parts) == 2:
                result = parts[0].strip()
                expr = parts[1].strip()
                
                # Check for binary operations
                binary_ops = {
                    ' + ': TACOperation.ADD,
                    ' - ': TACOperation.SUB,
                    ' * ': TACOperation.MUL,
                    ' / ': TACOperation.DIV,
                    ' % ': TACOperation.MOD,
                    ' == ': TACOperation.EQ,
                    ' != ': TACOperation.NE,
                    ' < ': TACOperation.LT,
                    ' <= ': TACOperation.LE,
                    ' > ': TACOperation.GT,
                    ' >= ': TACOperation.GE,
                    ' && ': TACOperation.AND,
                    ' || ': TACOperation.OR
                }
                
                for op_str, op_enum in binary_ops.items():
                    if op_str in expr:
                        operands = expr.split(op_str)
                        if len(operands) == 2:
                            return TACInstruction(
                                operation=op_enum,
                                result=result,
                                arg1=operands[0].strip(),
                                arg2=operands[1].strip()
                            )
                
                # Check for unary operations
                unary_ops = {
                    'neg ': TACOperation.NEG,
                    'not ': TACOperation.NOT
                }
                
                for op_str, op_enum in unary_ops.items():
                    if expr.startswith(op_str):
                        operand = expr[len(op_str):].strip()
                        return TACInstruction(
                            operation=op_enum,
                            result=result,
                            arg1=operand
                        )
                
                # Check for R (return value)
                if expr == 'R':
                    # This is assignment from return value
                    # We'll handle this as a special case
                    return TACInstruction(
                        operation=TACOperation.ASSIGN,
                        result=result,
                        arg1='R'
                    )
                
                # Simple assignment
                return TACInstruction(
                    operation=TACOperation.ASSIGN,
                    result=result,
                    arg1=expr
                )
        
        return None
    
    def _format_output(self) -> str:
        """Format final MIPS output"""
        output = []
        
        # Data section
        output.append(".data")
        output.append("    .align 2")
        output.append("newline: .asciiz \"\\n\"")
        output.append("")
        
        # Add global variables if any
        for var, label in self.global_variables.items():
            output.append("{}: .word 0".format(label))
        
        output.append("")
        
        # Text section
        output.append(".text")
        output.append("    .globl main")
        output.append("")
        
        # Check if main function exists
        has_main = any("main:" in line for line in self.text_section)
        
        # ✅ CORREGIR: Reemplazar el último jr $ra de main con syscall 10
        modified_text = []
        in_main = False
        main_end_index = -1
        
        for i, line in enumerate(self.text_section):
            if "main:" in line:
                in_main = True
                main_end_index = i
            elif in_main and ("\nsumar:" in line or "\n" in line and i > main_end_index and ":" in line and line.strip().endswith(":")):
                # Reached next function
                in_main = False
            
            modified_text.append(line)
            
            # Si estamos en main y encontramos "jr $ra", reemplazarlo con syscall 10
            if in_main and "jr $ra" in line and not "#" in line.split("jr $ra")[0]:
                # Reemplazar el último elemento agregado
                modified_text[-1] = line.replace("jr $ra", "li $v0, 10  # syscall exit\n    syscall")
        
        output.extend(modified_text)
        
        # If no main function, add a simple one that exits
        if not has_main:
            output.append("")
            output.append("main:")
            output.append("    li $v0, 10  # syscall exit")
            output.append("    syscall")
        
        return "\n".join(output)

