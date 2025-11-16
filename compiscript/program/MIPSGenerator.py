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
        # Register management
        self.register_usage: Dict[str, Optional[str]] = {}  # variable -> register
        self.register_free: Set[str] = set(self.TEMP_REGISTERS + self.SAVED_REGISTERS)
        self.register_used: Set[str] = set()
        
        # Variable mapping
        self.variable_map: Dict[str, str] = {}  # variable -> register or stack location
        self.stack_variables: Dict[str, int] = {}  # variable -> stack offset
        self.global_variables: Dict[str, str] = {}  # variable -> label name
        
        # Stack management
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
        self.register_usage.clear()
        self.register_free = set(self.TEMP_REGISTERS + self.SAVED_REGISTERS)
        self.register_used.clear()
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
    
    def _generate_code(self, instructions: List[TACInstruction]):
        """Second pass: generate MIPS code"""
        i = 0
        while i < len(instructions):
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
        self._emit(f"{func_name}:")
        
        # Calculate frame size: saved registers + $ra + $fp + local variables
        # We'll update this as we process the function, but start with minimum
        num_saved = len(self.used_saved_registers)
        frame_size = num_saved * 4 + 8  # saved regs + $ra + $fp
        # Add space for local variables (will be updated)
        frame_size += self.stack_offset
        
        # Ensure frame size is multiple of 8 for alignment (MIPS convention)
        if frame_size % 8 != 0:
            frame_size += 4
        
        # Save frame pointer and return address
        self._emit("addi $sp, $sp, -{}".format(frame_size))
        self._emit("sw $fp, {}($sp)".format(frame_size - 4))
        self._emit("sw $ra, {}($sp)".format(frame_size - 8))
        
        # Save used saved registers
        saved_offset = frame_size - 12
        for reg in sorted(self.used_saved_registers):
            self._emit("sw {}, {}($sp)".format(reg, saved_offset))
            saved_offset -= 4
        
        # Set new frame pointer
        self._emit("move $fp, $sp")
        
        self.function_info[func_name]['frame_size'] = frame_size
        self.frame_size = frame_size
    
    def _emit_function_epilogue(self, func_name: str):
        """Emit function epilogue"""
        frame_size = self.function_info.get(func_name, {}).get('frame_size', 0)
        
        # Restore saved registers
        saved_offset = frame_size - 12
        for reg in sorted(self.used_saved_registers):
            self._emit("lw {}, {}($sp)".format(reg, saved_offset))
            saved_offset -= 4
        
        # Restore return address and frame pointer
        self._emit("lw $ra, {}($sp)".format(frame_size - 8))
        self._emit("lw $fp, {}($sp)".format(frame_size - 4))
        self._emit("addi $sp, $sp, {}".format(frame_size))
        self._emit("jr $ra")
    
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
    
    def get_register(self, variable_name: str, force_temp: bool = False) -> str:
        """
        Get register for variable or allocate new one
        Returns register name or stack location
        """
        # Check if variable already has a register
        if variable_name in self.variable_map:
            location = self.variable_map[variable_name]
            if location.startswith("$"):
                return location
            # It's in stack, load to register
            reg = self._allocate_register(force_temp)
            self._emit("lw {}, {}".format(reg, location))
            self.variable_map[variable_name] = reg
            return reg
        
        # Allocate new register
        reg = self._allocate_register(force_temp)
        self.variable_map[variable_name] = reg
        return reg
    
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
    
    def _spill_register(self, register: str) -> str:
        """Spill a register to stack and return it"""
        # Find variable using this register
        var_to_spill = None
        for var, reg in self.variable_map.items():
            if reg == register:
                var_to_spill = var
                break
        
        if var_to_spill:
            stack_loc = self._spill_to_stack()
            self._emit("sw {}, {}".format(register, stack_loc))
            self.variable_map[var_to_spill] = stack_loc
            self.register_free.add(register)
            self.register_used.discard(register)
        
        return register
    
    def _spill_to_stack(self) -> str:
        """Allocate space on stack and return location"""
        self.stack_offset += 4
        self.frame_size = max(self.frame_size, self.stack_offset)
        location = "{}($fp)".format(-self.stack_offset)
        return location
    
    def _free_register(self, register: str):
        """Free a register"""
        if register in self.register_used:
            self.register_used.discard(register)
            self.register_free.add(register)
            if register in self.used_saved_registers:
                self.used_saved_registers.discard(register)
    
    def _get_operand_location(self, operand: str) -> str:
        """Get register or immediate value for operand"""
        # Check if it's a number
        if operand and operand.replace('-', '').isdigit():
            return operand
        
        # Check if it's a register already
        if operand and operand.startswith("$"):
            return operand
        
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
            self._emit("move {}, $v0".format(result_reg))
            return
        
        src_loc = self._get_operand_location(source)
        dst_reg = self.get_register(result, force_temp=True)
        
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
        
        op1 = self._get_operand_location(arg1)
        op2 = self._get_operand_location(arg2)
        res_reg = self.get_register(result, force_temp=True)
        
        # Handle immediate values
        if op2.replace('-', '').isdigit() and int(op2) >= -32768 and int(op2) <= 32767:
            if op == "add":
                self._emit("addi {}, {}, {}".format(res_reg, op1, op2))
            elif op == "sub":
                self._emit("addi {}, {}, {}".format(res_reg, op1, "-" + op2 if not op2.startswith("-") else op2[1:]))
            else:
                # Load immediate first
                temp_reg = self._allocate_register(force_temp=True)
                self._emit("li {}, {}".format(temp_reg, op2))
                self._emit("{} {}, {}, {}".format(op, res_reg, op1, temp_reg))
        else:
            # Both operands in registers
            if not op1.startswith("$"):
                op1_reg = self._allocate_register(force_temp=True)
                self._emit("lw {}, {}".format(op1_reg, op1))
                op1 = op1_reg
            if not op2.startswith("$"):
                op2_reg = self._allocate_register(force_temp=True)
                self._emit("lw {}, {}".format(op2_reg, op2))
                op2 = op2_reg
            
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
            if not op1.startswith("$"):
                op1_reg = self._allocate_register(force_temp=True)
                self._emit("lw {}, {}".format(op1_reg, op1))
                op1 = op1_reg
            if not op2.startswith("$"):
                op2_reg = self._allocate_register(force_temp=True)
                self._emit("lw {}, {}".format(op2_reg, op2))
                op2 = op2_reg
            self._emit("slt {}, {}, {}".format(res_reg, op1, op2))
        elif op == "seq":  # a == b
            # seq $r, $a, $b -> sub $r, $a, $b; sltiu $r, $r, 1
            if not op1.startswith("$"):
                op1_reg = self._allocate_register(force_temp=True)
                self._emit("lw {}, {}".format(op1_reg, op1))
                op1 = op1_reg
            if not op2.startswith("$"):
                op2_reg = self._allocate_register(force_temp=True)
                self._emit("lw {}, {}".format(op2_reg, op2))
                op2 = op2_reg
            temp_reg = self._allocate_register(force_temp=True)
            self._emit("sub {}, {}, {}".format(temp_reg, op1, op2))
            self._emit("sltiu {}, {}, 1".format(res_reg, temp_reg))
        elif op == "sne":  # a != b
            # sne $r, $a, $b -> seq then not
            if not op1.startswith("$"):
                op1_reg = self._allocate_register(force_temp=True)
                self._emit("lw {}, {}".format(op1_reg, op1))
                op1 = op1_reg
            if not op2.startswith("$"):
                op2_reg = self._allocate_register(force_temp=True)
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
                self._emit("lw {}, {}".format(op1_reg, op1))
                op1 = op1_reg
            if not op2.startswith("$"):
                op2_reg = self._allocate_register(force_temp=True)
                self._emit("lw {}, {}".format(op2_reg, op2))
                op2 = op2_reg
            self._emit("slt {}, {}, {}".format(res_reg, op2, op1))
            self._emit("xori {}, {}, 1".format(res_reg, res_reg))
        elif op == "sgt":  # a > b
            # sgt $r, $a, $b -> slt $r, $b, $a
            if not op1.startswith("$"):
                op1_reg = self._allocate_register(force_temp=True)
                self._emit("lw {}, {}".format(op1_reg, op1))
                op1 = op1_reg
            if not op2.startswith("$"):
                op2_reg = self._allocate_register(force_temp=True)
                self._emit("lw {}, {}".format(op2_reg, op2))
                op2 = op2_reg
            self._emit("slt {}, {}, {}".format(res_reg, op2, op1))
        elif op == "sge":  # a >= b
            # sge $r, $a, $b -> slt $r, $a, $b; xori $r, $r, 1
            if not op1.startswith("$"):
                op1_reg = self._allocate_register(force_temp=True)
                self._emit("lw {}, {}".format(op1_reg, op1))
                op1 = op1_reg
            if not op2.startswith("$"):
                op2_reg = self._allocate_register(force_temp=True)
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
            # Pass on stack
            stack_offset = (param_index - 4) * 4
            if param_value.startswith("$"):
                self._emit("sw {}, {}($sp)".format(param_value, stack_offset))
            elif param_value.replace('-', '').isdigit():
                temp_reg = self._allocate_register(force_temp=True)
                self._emit("li {}, {}".format(temp_reg, param_value))
                self._emit("sw {}, {}($sp)".format(temp_reg, stack_offset))
            else:
                temp_reg = self._allocate_register(force_temp=True)
                self._emit("lw {}, {}".format(temp_reg, param_value))
                self._emit("sw {}, {}($sp)".format(temp_reg, stack_offset))
        
        self.param_stack[-1].append(param_value)
    
    def _emit_call(self, func_name: str, num_params: int):
        """Emit function call"""
        # Save caller-saved registers that might be in use
        # For simplicity, save all temp registers
        saved_regs = []
        for reg in self.TEMP_REGISTERS:
            if reg in self.register_used:
                saved_regs.append(reg)
        
        # Calculate stack space needed
        stack_params = max(0, num_params - 4)
        save_space = len(saved_regs) * 4
        total_space = stack_params * 4 + save_space + 4  # +4 for $ra
        
        if total_space > 0:
            self._emit("addi $sp, $sp, -{}".format(total_space))
        
        # Save $ra
        self._emit("sw $ra, {}($sp)".format(total_space - 4))
        
        # Save temp registers
        offset = total_space - 8
        for reg in saved_regs:
            self._emit("sw {}, {}($sp)".format(reg, offset))
            offset -= 4
        
        # Call function
        self._emit("jal {}".format(func_name))
        
        # Restore temp registers
        offset = total_space - 8
        for reg in saved_regs:
            self._emit("lw {}, {}($sp)".format(reg, offset))
            offset -= 4
        
        # Restore $ra
        self._emit("lw $ra, {}($sp)".format(total_space - 4))
        
        # Restore stack
        if total_space > 0:
            self._emit("addi $sp, $sp, {}".format(total_space))
        
        # Clear parameter stack
        if self.param_stack:
            self.param_stack.pop()
    
    def _emit_return(self, value: Optional[str] = None):
        """Emit return statement"""
        if value:
            value_reg = self._get_operand_location(value)
            if not value_reg.startswith("$"):
                # Load to $v0
                self._emit("lw $v0, {}".format(value_reg))
            else:
                self._emit("move $v0, {}".format(value_reg))
        # Epilogue will handle jr $ra
    
    def _emit_print(self, value: str):
        """Emit print statement"""
        value_reg = self._get_operand_location(value)
        
        # Use syscall for print integer
        # Load value to $a0
        if value_reg.startswith("$"):
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
        
        # Add generated code
        output.extend(self.text_section)
        
        # If no main function, add a simple one that exits
        if not has_main:
            output.append("")
            output.append("main:")
            output.append("    li $v0, 10  # syscall exit")
            output.append("    syscall")
        
        return "\n".join(output)

