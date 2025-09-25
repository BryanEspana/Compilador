"""
Three-Address Code (TAC) Instruction definitions for Compiscript compiler
"""

from enum import Enum
from typing import Optional, List, Any, Union
from dataclasses import dataclass

class TACOperation(Enum):
    """TAC operation types"""
    # Assignment operations
    ASSIGN = "assign"
    COPY = "copy"
    
    # Arithmetic operations
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    NEG = "neg"  # Unary minus
    
    # Comparison operations
    EQ = "eq"
    NE = "ne"
    LT = "lt"
    LE = "le"
    GT = "gt"
    GE = "ge"
    
    # Logical operations
    AND = "and"
    OR = "or"
    NOT = "not"
    
    # Control flow operations
    GOTO = "goto"
    IF_FALSE = "if_false"
    IF_TRUE = "if_true"
    LABEL = "label"
    
    # Function operations
    CALL = "call"
    RETURN = "return"
    PARAM = "param"
    
    # Array operations
    ARRAY_ACCESS = "array_access"
    ARRAY_ASSIGN = "array_assign"
    
    # Object operations
    OBJECT_ACCESS = "object_access"
    OBJECT_ASSIGN = "object_assign"
    NEW_OBJECT = "new_object"
    
    # String operations
    CONCAT = "concat"
    
    # Input/Output operations
    PRINT = "print"
    READ = "read"

@dataclass
class TACInstruction:
    """Represents a single TAC instruction"""
    operation: TACOperation
    result: Optional[str] = None      # Destination variable/register
    arg1: Optional[str] = None        # First operand
    arg2: Optional[str] = None        # Second operand
    label: Optional[str] = None       # Label for control flow
    comment: Optional[str] = None     # Optional comment
    
    def __str__(self) -> str:
        """String representation of TAC instruction"""
        if self.operation == TACOperation.LABEL:
            return f"{self.label}:"
        
        if self.operation == TACOperation.GOTO:
            return f"goto {self.label}"
        
        if self.operation == TACOperation.IF_FALSE:
            return f"if_false {self.arg1} goto {self.label}"
        
        if self.operation == TACOperation.IF_TRUE:
            return f"if_true {self.arg1} goto {self.label}"
        
        if self.operation == TACOperation.CALL:
            return f"call {self.arg1}, {self.arg2}"  # function_name, num_params
        
        if self.operation == TACOperation.RETURN:
            if self.arg1:
                return f"return {self.arg1}"
            else:
                return "return"
        
        if self.operation == TACOperation.PARAM:
            return f"param {self.arg1}"
        
        if self.operation == TACOperation.PRINT:
            return f"print {self.arg1}"
        
        if self.operation == TACOperation.READ:
            return f"read {self.result}"
        
        # Binary operations: result = arg1 op arg2
        if self.arg2 is not None:
            return f"{self.result} = {self.arg1} {self.operation.value} {self.arg2}"
        
        # Unary operations: result = op arg1
        if self.arg1 is not None:
            return f"{self.result} = {self.operation.value} {self.arg1}"
        
        # Assignment: result = arg1
        if self.arg1 is not None:
            return f"{self.result} = {self.arg1}"
        
        return f"{self.operation.value}"

class TACGenerator:
    """Generates Three-Address Code instructions"""
    
    def __init__(self):
        self.instructions: List[TACInstruction] = []
        self.temp_counter = 0
        self.label_counter = 0
        self.current_scope = None
        
    def generate_temp_var(self, prefix: str = "t") -> str:
        """Generate a unique temporary variable name"""
        self.temp_counter += 1
        return f"{prefix}{self.temp_counter}"
    
    def generate_label(self, prefix: str = "L") -> str:
        """Generate a unique label name"""
        self.label_counter += 1
        return f"{prefix}{self.label_counter}"
    
    def add_instruction(self, instruction: TACInstruction) -> None:
        """Add a TAC instruction to the list"""
        self.instructions.append(instruction)
    
    def add_comment(self, comment: str) -> None:
        """Add a comment to the TAC code"""
        self.instructions.append(TACInstruction(
            operation=TACOperation.ASSIGN,
            comment=comment
        ))
    
    # Assignment operations
    def add_assign(self, result: str, arg1: str) -> None:
        """Add assignment instruction: result = arg1"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.ASSIGN,
            result=result,
            arg1=arg1
        ))
    
    def add_copy(self, result: str, arg1: str) -> None:
        """Add copy instruction: result = arg1"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.COPY,
            result=result,
            arg1=arg1
        ))
    
    # Arithmetic operations
    def add_add(self, result: str, arg1: str, arg2: str) -> None:
        """Add addition instruction: result = arg1 + arg2"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.ADD,
            result=result,
            arg1=arg1,
            arg2=arg2
        ))
    
    def add_sub(self, result: str, arg1: str, arg2: str) -> None:
        """Add subtraction instruction: result = arg1 - arg2"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.SUB,
            result=result,
            arg1=arg1,
            arg2=arg2
        ))
    
    def add_mul(self, result: str, arg1: str, arg2: str) -> None:
        """Add multiplication instruction: result = arg1 * arg2"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.MUL,
            result=result,
            arg1=arg1,
            arg2=arg2
        ))
    
    def add_div(self, result: str, arg1: str, arg2: str) -> None:
        """Add division instruction: result = arg1 / arg2"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.DIV,
            result=result,
            arg1=arg1,
            arg2=arg2
        ))
    
    def add_mod(self, result: str, arg1: str, arg2: str) -> None:
        """Add modulo instruction: result = arg1 % arg2"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.MOD,
            result=result,
            arg1=arg1,
            arg2=arg2
        ))
    
    def add_neg(self, result: str, arg1: str) -> None:
        """Add negation instruction: result = -arg1"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.NEG,
            result=result,
            arg1=arg1
        ))
    
    # Comparison operations
    def add_eq(self, result: str, arg1: str, arg2: str) -> None:
        """Add equality instruction: result = arg1 == arg2"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.EQ,
            result=result,
            arg1=arg1,
            arg2=arg2
        ))
    
    def add_ne(self, result: str, arg1: str, arg2: str) -> None:
        """Add inequality instruction: result = arg1 != arg2"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.NE,
            result=result,
            arg1=arg1,
            arg2=arg2
        ))
    
    def add_lt(self, result: str, arg1: str, arg2: str) -> None:
        """Add less than instruction: result = arg1 < arg2"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.LT,
            result=result,
            arg1=arg1,
            arg2=arg2
        ))
    
    def add_le(self, result: str, arg1: str, arg2: str) -> None:
        """Add less or equal instruction: result = arg1 <= arg2"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.LE,
            result=result,
            arg1=arg1,
            arg2=arg2
        ))
    
    def add_gt(self, result: str, arg1: str, arg2: str) -> None:
        """Add greater than instruction: result = arg1 > arg2"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.GT,
            result=result,
            arg1=arg1,
            arg2=arg2
        ))
    
    def add_ge(self, result: str, arg1: str, arg2: str) -> None:
        """Add greater or equal instruction: result = arg1 >= arg2"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.GE,
            result=result,
            arg1=arg1,
            arg2=arg2
        ))
    
    # Logical operations
    def add_and(self, result: str, arg1: str, arg2: str) -> None:
        """Add logical AND instruction: result = arg1 && arg2"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.AND,
            result=result,
            arg1=arg1,
            arg2=arg2
        ))
    
    def add_or(self, result: str, arg1: str, arg2: str) -> None:
        """Add logical OR instruction: result = arg1 || arg2"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.OR,
            result=result,
            arg1=arg1,
            arg2=arg2
        ))
    
    def add_not(self, result: str, arg1: str) -> None:
        """Add logical NOT instruction: result = !arg1"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.NOT,
            result=result,
            arg1=arg1
        ))
    
    # Control flow operations
    def add_goto(self, label: str) -> None:
        """Add goto instruction: goto label"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.GOTO,
            label=label
        ))
    
    def add_if_false(self, condition: str, label: str) -> None:
        """Add if_false instruction: if_false condition goto label"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.IF_FALSE,
            arg1=condition,
            label=label
        ))
    
    def add_if_true(self, condition: str, label: str) -> None:
        """Add if_true instruction: if_true condition goto label"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.IF_TRUE,
            arg1=condition,
            label=label
        ))
    
    def add_label(self, label: str) -> None:
        """Add label instruction: label:"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.LABEL,
            label=label
        ))
    
    # Function operations
    def add_call(self, function_name: str, num_params: int, result: str = None) -> None:
        """Add function call instruction: result = call function_name, num_params"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.CALL,
            result=result,
            arg1=function_name,
            arg2=str(num_params)
        ))
    
    def add_return(self, value: str = None) -> None:
        """Add return instruction: return value"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.RETURN,
            arg1=value
        ))
    
    def add_param(self, param: str) -> None:
        """Add parameter instruction: param param"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.PARAM,
            arg1=param
        ))
    
    # Array operations
    def add_array_access(self, result: str, array: str, index: str) -> None:
        """Add array access instruction: result = array[index]"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.ARRAY_ACCESS,
            result=result,
            arg1=array,
            arg2=index
        ))
    
    def add_array_assign(self, array: str, index: str, value: str) -> None:
        """Add array assignment instruction: array[index] = value"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.ARRAY_ASSIGN,
            result=array,
            arg1=index,
            arg2=value
        ))
    
    # Object operations
    def add_object_access(self, result: str, object: str, property: str) -> None:
        """Add object property access instruction: result = object.property"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.OBJECT_ACCESS,
            result=result,
            arg1=object,
            arg2=property
        ))
    
    def add_object_assign(self, object: str, property: str, value: str) -> None:
        """Add object property assignment instruction: object.property = value"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.OBJECT_ASSIGN,
            result=object,
            arg1=property,
            arg2=value
        ))
    
    def add_new_object(self, result: str, class_name: str) -> None:
        """Add object creation instruction: result = new class_name"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.NEW_OBJECT,
            result=result,
            arg1=class_name
        ))
    
    # String operations
    def add_concat(self, result: str, arg1: str, arg2: str) -> None:
        """Add string concatenation instruction: result = arg1 + arg2"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.CONCAT,
            result=result,
            arg1=arg1,
            arg2=arg2
        ))
    
    # Input/Output operations
    def add_print(self, value: str) -> None:
        """Add print instruction: print value"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.PRINT,
            arg1=value
        ))
    
    def add_read(self, result: str) -> None:
        """Add read instruction: read result"""
        self.add_instruction(TACInstruction(
            operation=TACOperation.READ,
            result=result
        ))
    
    def get_instructions(self) -> List[TACInstruction]:
        """Get all generated TAC instructions"""
        return self.instructions.copy()
    
    def clear(self) -> None:
        """Clear all instructions and reset counters"""
        self.instructions.clear()
        self.temp_counter = 0
        self.label_counter = 0
    
    def to_string(self) -> str:
        """Convert all instructions to string representation"""
        lines = []
        for i, instruction in enumerate(self.instructions):
            if instruction.comment:
                lines.append(f"// {instruction.comment}")
            else:
                lines.append(str(instruction))
        return "\n".join(lines)
    
    def print_instructions(self) -> None:
        """Print all instructions to console"""
        print("=== THREE-ADDRESS CODE ===")
        for i, instruction in enumerate(self.instructions):
            if instruction.comment:
                print(f"// {instruction.comment}")
            else:
                print(f"{i:3d}: {instruction}")
        print("=========================")
