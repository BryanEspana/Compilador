"""
Three-Address Code (TAC) Parser for Compiscript compiler
"""

import re
from typing import List, Optional, Tuple
from TACInstruction import TACInstruction, TACOperation, TACGenerator

class TACParser:
    """Parser for Three-Address Code instructions"""
    
    def __init__(self):
        self.instructions: List[TACInstruction] = []
        self.errors: List[str] = []
    
    def parse_line(self, line: str) -> Optional[TACInstruction]:
        """Parse a single line of TAC code"""
        line = line.strip()
        
        # Skip empty lines
        if not line:
            return None
        
        # Skip comments
        if line.startswith('//'):
            return TACInstruction(
                operation=TACOperation.ASSIGN,
                comment=line[2:].strip()
            )
        
        # Parse different instruction types
        if ':' in line and not '=' in line:
            # Label: label_name
            return self._parse_label(line)
        elif line.startswith('goto '):
            # Goto: goto label
            return self._parse_goto(line)
        elif line.startswith('if_false '):
            # If false: if_false condition goto label
            return self._parse_if_false(line)
        elif line.startswith('if_true '):
            # If true: if_true condition goto label
            return self._parse_if_true(line)
        elif line.startswith('call '):
            # Function call: call function_name, num_params
            return self._parse_call(line)
        elif line.startswith('return'):
            # Return: return [value]
            return self._parse_return(line)
        elif line.startswith('param '):
            # Parameter: param value
            return self._parse_param(line)
        elif line.startswith('print '):
            # Print: print value
            return self._parse_print(line)
        elif line.startswith('read '):
            # Read: read variable
            return self._parse_read(line)
        elif '=' in line:
            # Assignment or operation: result = arg1 [op arg2]
            return self._parse_assignment(line)
        else:
            self.errors.append(f"Unknown instruction format: {line}")
            return None
    
    def _parse_label(self, line: str) -> TACInstruction:
        """Parse label instruction"""
        label = line.replace(':', '').strip()
        return TACInstruction(
            operation=TACOperation.LABEL,
            label=label
        )
    
    def _parse_goto(self, line: str) -> TACInstruction:
        """Parse goto instruction"""
        label = line.replace('goto ', '').strip()
        return TACInstruction(
            operation=TACOperation.GOTO,
            label=label
        )
    
    def _parse_if_false(self, line: str) -> TACInstruction:
        """Parse if_false instruction"""
        # Format: if_false condition goto label
        match = re.match(r'if_false\s+(\w+)\s+goto\s+(\w+)', line)
        if match:
            condition, label = match.groups()
            return TACInstruction(
                operation=TACOperation.IF_FALSE,
                arg1=condition,
                label=label
            )
        else:
            self.errors.append(f"Invalid if_false format: {line}")
            return None
    
    def _parse_if_true(self, line: str) -> TACInstruction:
        """Parse if_true instruction"""
        # Format: if_true condition goto label
        match = re.match(r'if_true\s+(\w+)\s+goto\s+(\w+)', line)
        if match:
            condition, label = match.groups()
            return TACInstruction(
                operation=TACOperation.IF_TRUE,
                arg1=condition,
                label=label
            )
        else:
            self.errors.append(f"Invalid if_true format: {line}")
            return None
    
    def _parse_call(self, line: str) -> TACInstruction:
        """Parse function call instruction"""
        # Format: call function_name, num_params
        match = re.match(r'call\s+(\w+),\s*(\d+)', line)
        if match:
            function_name, num_params = match.groups()
            return TACInstruction(
                operation=TACOperation.CALL,
                arg1=function_name,
                arg2=num_params
            )
        else:
            self.errors.append(f"Invalid call format: {line}")
            return None
    
    def _parse_return(self, line: str) -> TACInstruction:
        """Parse return instruction"""
        # Format: return [value]
        if line == 'return':
            return TACInstruction(operation=TACOperation.RETURN)
        else:
            value = line.replace('return ', '').strip()
            return TACInstruction(
                operation=TACOperation.RETURN,
                arg1=value
            )
    
    def _parse_param(self, line: str) -> TACInstruction:
        """Parse parameter instruction"""
        value = line.replace('param ', '').strip()
        return TACInstruction(
            operation=TACOperation.PARAM,
            arg1=value
        )
    
    def _parse_print(self, line: str) -> TACInstruction:
        """Parse print instruction"""
        value = line.replace('print ', '').strip()
        return TACInstruction(
            operation=TACOperation.PRINT,
            arg1=value
        )
    
    def _parse_read(self, line: str) -> TACInstruction:
        """Parse read instruction"""
        variable = line.replace('read ', '').strip()
        return TACInstruction(
            operation=TACOperation.READ,
            result=variable
        )
    
    def _parse_assignment(self, line: str) -> TACInstruction:
        """Parse assignment or operation instruction"""
        # Check for array assignment first: array[index] = value
        array_assign_match = re.match(r'(\w+)\[(\w+)\]\s*=\s*(.+)', line)
        if array_assign_match:
            array, index, value = array_assign_match.groups()
            return TACInstruction(
                operation=TACOperation.ARRAY_ASSIGN,
                result=array.strip(),
                arg1=index.strip(),
                arg2=value.strip()
            )
        
        # Check for object assignment: object.property = value
        object_assign_match = re.match(r'(\w+)\.(\w+)\s*=\s*(.+)', line)
        if object_assign_match:
            object_name, property_name, value = object_assign_match.groups()
            return TACInstruction(
                operation=TACOperation.OBJECT_ASSIGN,
                result=object_name.strip(),
                arg1=property_name.strip(),
                arg2=value.strip()
            )
        
        # Split by '=' to get result and expression
        parts = line.split('=', 1)
        if len(parts) != 2:
            self.errors.append(f"Invalid assignment format: {line}")
            return None
        
        result = parts[0].strip()
        expression = parts[1].strip()
        
        # Check for binary operations
        binary_ops = {
            '+': TACOperation.ADD,
            '-': TACOperation.SUB,
            '*': TACOperation.MUL,
            '/': TACOperation.DIV,
            '%': TACOperation.MOD,
            '==': TACOperation.EQ,
            '!=': TACOperation.NE,
            '<': TACOperation.LT,
            '<=': TACOperation.LE,
            '>': TACOperation.GT,
            '>=': TACOperation.GE,
            '&&': TACOperation.AND,
            '||': TACOperation.OR
        }
        
        # Check for unary operations
        unary_ops = {
            'neg': TACOperation.NEG,
            'not': TACOperation.NOT
        }
        
        # Try to find binary operations
        for op_str, op_enum in binary_ops.items():
            if f' {op_str} ' in expression:
                operands = expression.split(f' {op_str} ')
                if len(operands) == 2:
                    return TACInstruction(
                        operation=op_enum,
                        result=result,
                        arg1=operands[0].strip(),
                        arg2=operands[1].strip()
                    )
        
        # Try to find unary operations
        for op_str, op_enum in unary_ops.items():
            if expression.startswith(f'{op_str} '):
                operand = expression.replace(f'{op_str} ', '').strip()
                return TACInstruction(
                    operation=op_enum,
                    result=result,
                    arg1=operand
                )
        
        # Check for array access: result = array[index]
        array_match = re.match(r'(\w+)\[(\w+)\]', expression)
        if array_match:
            array, index = array_match.groups()
            return TACInstruction(
                operation=TACOperation.ARRAY_ACCESS,
                result=result,
                arg1=array,
                arg2=index
            )
        
        
        # Check for object access: result = object.property
        object_match = re.match(r'(\w+)\.(\w+)', expression)
        if object_match:
            object_name, property_name = object_match.groups()
            return TACInstruction(
                operation=TACOperation.OBJECT_ACCESS,
                result=result,
                arg1=object_name,
                arg2=property_name
            )
        
        # Check for new object: result = new ClassName
        new_match = re.match(r'new\s+(\w+)', expression)
        if new_match:
            class_name = new_match.group(1)
            return TACInstruction(
                operation=TACOperation.NEW_OBJECT,
                result=result,
                arg1=class_name
            )
        
        # Check for string concatenation: result = str1 + str2
        if '+' in expression and not any(op in expression for op in ['==', '!=']):
            operands = expression.split('+')
            if len(operands) == 2:
                return TACInstruction(
                    operation=TACOperation.CONCAT,
                    result=result,
                    arg1=operands[0].strip(),
                    arg2=operands[1].strip()
                )
        
        # Simple assignment: result = value
        return TACInstruction(
            operation=TACOperation.ASSIGN,
            result=result,
            arg1=expression
        )
    
    def parse_text(self, text: str) -> List[TACInstruction]:
        """Parse TAC text and return list of instructions"""
        self.instructions = []
        self.errors = []
        
        lines = text.split('\n')
        for line_num, line in enumerate(lines, 1):
            instruction = self.parse_line(line)
            if instruction:
                self.instructions.append(instruction)
            elif line.strip():  # Only add error if line is not empty
                self.errors.append(f"Line {line_num}: Could not parse: {line}")
        
        return self.instructions
    
    def parse_file(self, filename: str) -> List[TACInstruction]:
        """Parse TAC file and return list of instructions"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
            return self.parse_text(content)
        except FileNotFoundError:
            self.errors.append(f"File not found: {filename}")
            return []
        except Exception as e:
            self.errors.append(f"Error reading file {filename}: {str(e)}")
            return []
    
    def get_errors(self) -> List[str]:
        """Get parsing errors"""
        return self.errors.copy()
    
    def has_errors(self) -> bool:
        """Check if there are parsing errors"""
        return len(self.errors) > 0
    
    def print_instructions(self) -> None:
        """Print parsed instructions"""
        print("=== PARSED TAC INSTRUCTIONS ===")
        for i, instruction in enumerate(self.instructions):
            if instruction.comment:
                print(f"{i:3d}: // {instruction.comment}")
            else:
                print(f"{i:3d}: {instruction}")
        print("===============================")
    
    def print_errors(self) -> None:
        """Print parsing errors"""
        if self.errors:
            print("=== PARSING ERRORS ===")
            for error in self.errors:
                print(f"ERROR: {error}")
            print("=====================")
        else:
            print("No parsing errors found.")

def test_parser():
    """Test the TAC parser"""
    print("=== Testing TAC Parser ===")
    
    # Test TAC code
    tac_code = """
// Test arithmetic operations
t1 = a + b
t2 = c * d
result = t1 - t2

// Test control flow
L1:
if_false x goto L2
goto L3
L2:
t3 = 0
L3:

// Test function call
param arg1
param arg2
call add, 2
return result

// Test array operations
t4 = arr[i]
arr[j] = value

// Test object operations
t5 = obj.property
obj.field = value
obj = new ClassName
"""
    
    parser = TACParser()
    instructions = parser.parse_text(tac_code)
    
    parser.print_instructions()
    parser.print_errors()
    
    print(f"Parsed {len(instructions)} instructions")
    print(f"Found {len(parser.errors)} errors")

if __name__ == "__main__":
    test_parser()
