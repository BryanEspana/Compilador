"""
Three-Address Code (TAC) Parser for Compiscript compiler
"""

from typing import List, Optional, Tuple
from TACInstruction import TACInstruction, TACOperation, TACGenerator

class TACParser:
    """Parser for Three-Address Code instructions"""
    
    def __init__(self):
        self.instructions: List[TACInstruction] = []
        self.errors: List[str] = []
    
    def _is_identifier(self, s: str) -> bool:
        """Check if string is a valid identifier (letters, digits, underscore)"""
        if not s:
            return False
        if not (s[0].isalpha() or s[0] == '_'):
            return False
        return all(c.isalnum() or c == '_' for c in s)
    
    def _is_number(self, s: str) -> bool:
        """Check if string is a number"""
        if not s:
            return False
        try:
            int(s)
            return True
        except ValueError:
            return False
    
    def _split_whitespace(self, s: str) -> List[str]:
        """Split string by whitespace and filter empty strings"""
        return [part for part in s.split() if part]
    
    def _parse_pattern_if_condition(self, line: str, prefix: str) -> Optional[Tuple[str, str]]:
        """Parse if_false/if_true pattern: 'prefix condition goto label'"""
        if not line.startswith(prefix):
            return None
        
        # Remove prefix and split by whitespace
        rest = line[len(prefix):].strip()
        parts = self._split_whitespace(rest)
        
        if len(parts) >= 3 and parts[1] == 'goto':
            condition = parts[0]
            label = parts[2]
            if self._is_identifier(condition) and self._is_identifier(label):
                return (condition, label)
        return None
    
    def _parse_pattern_call(self, line: str) -> Optional[Tuple[str, str]]:
        """Parse call pattern: 'call function_name, num_params'"""
        if not line.startswith('call '):
            return None
        
        rest = line[5:].strip()  # Remove 'call '
        if ',' not in rest:
            return None
        
        parts = rest.split(',', 1)
        if len(parts) == 2:
            function_name = parts[0].strip()
            num_params = parts[1].strip()
            if self._is_identifier(function_name) and self._is_number(num_params):
                return (function_name, num_params)
        return None
    
    def _parse_pattern_array_assign(self, line: str) -> Optional[Tuple[str, str, str]]:
        """Parse array assignment: 'array[index] = value'"""
        if '=' not in line:
            return None
        
        parts = line.split('=', 1)
        if len(parts) != 2:
            return None
        
        left = parts[0].strip()
        right = parts[1].strip()
        
        # Check for array[index] pattern
        if '[' in left and ']' in left:
            bracket_start = left.find('[')
            bracket_end = left.find(']')
            if bracket_start > 0 and bracket_end > bracket_start:
                array = left[:bracket_start].strip()
                index = left[bracket_start+1:bracket_end].strip()
                if self._is_identifier(array) and self._is_identifier(index):
                    return (array, index, right)
        return None
    
    def _parse_pattern_object_assign(self, line: str) -> Optional[Tuple[str, str, str]]:
        """Parse object assignment: 'object.property = value'"""
        if '=' not in line:
            return None
        
        parts = line.split('=', 1)
        if len(parts) != 2:
            return None
        
        left = parts[0].strip()
        right = parts[1].strip()
        
        # Check for object.property pattern
        if '.' in left:
            dot_pos = left.find('.')
            if dot_pos > 0 and dot_pos < len(left) - 1:
                object_name = left[:dot_pos].strip()
                property_name = left[dot_pos+1:].strip()
                if self._is_identifier(object_name) and self._is_identifier(property_name):
                    return (object_name, property_name, right)
        return None
    
    def _parse_pattern_array_access(self, expression: str) -> Optional[Tuple[str, str]]:
        """Parse array access: 'array[index]'"""
        if '[' not in expression or ']' not in expression:
            return None
        
        bracket_start = expression.find('[')
        bracket_end = expression.find(']')
        if bracket_start > 0 and bracket_end > bracket_start:
            array = expression[:bracket_start].strip()
            index = expression[bracket_start+1:bracket_end].strip()
            if self._is_identifier(array) and self._is_identifier(index):
                return (array, index)
        return None
    
    def _parse_pattern_object_access(self, expression: str) -> Optional[Tuple[str, str]]:
        """Parse object access: 'object.property'"""
        if '.' not in expression:
            return None
        
        dot_pos = expression.find('.')
        if dot_pos > 0 and dot_pos < len(expression) - 1:
            object_name = expression[:dot_pos].strip()
            property_name = expression[dot_pos+1:].strip()
            if self._is_identifier(object_name) and self._is_identifier(property_name):
                return (object_name, property_name)
        return None
    
    def _parse_pattern_new_object(self, expression: str) -> Optional[str]:
        """Parse new object: 'new ClassName'"""
        if not expression.startswith('new '):
            return None
        
        class_name = expression[4:].strip()  # Remove 'new '
        if self._is_identifier(class_name):
            return class_name
        return None
    
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
        result = self._parse_pattern_if_condition(line, 'if_false ')
        if result:
            condition, label = result
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
        result = self._parse_pattern_if_condition(line, 'if_true ')
        if result:
            condition, label = result
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
        result = self._parse_pattern_call(line)
        if result:
            function_name, num_params = result
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
        array_assign_result = self._parse_pattern_array_assign(line)
        if array_assign_result:
            array, index, value = array_assign_result
            return TACInstruction(
                operation=TACOperation.ARRAY_ASSIGN,
                result=array.strip(),
                arg1=index.strip(),
                arg2=value.strip()
            )
        
        # Check for object assignment: object.property = value
        object_assign_result = self._parse_pattern_object_assign(line)
        if object_assign_result:
            object_name, property_name, value = object_assign_result
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
        array_access_result = self._parse_pattern_array_access(expression)
        if array_access_result:
            array, index = array_access_result
            return TACInstruction(
                operation=TACOperation.ARRAY_ACCESS,
                result=result,
                arg1=array,
                arg2=index
            )
        
        # Check for object access: result = object.property
        object_access_result = self._parse_pattern_object_access(expression)
        if object_access_result:
            object_name, property_name = object_access_result
            return TACInstruction(
                operation=TACOperation.OBJECT_ACCESS,
                result=result,
                arg1=object_name,
                arg2=property_name
            )
        
        # Check for new object: result = new ClassName
        new_object_result = self._parse_pattern_new_object(expression)
        if new_object_result:
            class_name = new_object_result
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
