// Test cases that should fail semantic analysis
// Each error is commented to explain what should be detected

// 1. Type mismatch in variable assignment
let age: integer = "twenty"; // ERROR: Cannot assign string to integer

// 2. Using undefined variable
print(undefinedVar); // ERROR: Undefined identifier 'undefinedVar'

// 3. Redeclaration in same scope
let count: integer = 5;
let count: string = "five"; // ERROR: Variable 'count' already declared

// 4. Constant without initialization
// const EMPTY; // ERROR: Constant must be initialized (commented out as it's syntax error)

// 5. Assignment to constant
const MAX: integer = 100;
MAX = 200; // ERROR: Cannot assign to constant

// 6. Type mismatch in arithmetic operations
let result: integer = 5 + "hello"; // ERROR: Cannot add integer and string (unless string concatenation)
let wrong: integer = true * false; // ERROR: Arithmetic operation requires integers

// 7. Type mismatch in logical operations
let logicalError: boolean = 5 && true; // ERROR: Logical AND requires boolean operands
let anotherError: boolean = !42; // ERROR: Logical NOT requires boolean operand

// 8. Wrong condition types in control structures
if (42) { // ERROR: If condition must be boolean
    print("This should not work");
}

while ("hello") { // ERROR: While condition must be boolean
    print("Wrong condition");
}

// 9. Function call with wrong number of arguments
function testFunc(a: integer, b: string): void {
    print(a + b);
}

testFunc(5); // ERROR: Wrong number of arguments
testFunc(5, "test", true); // ERROR: Too many arguments

// 10. Function call with wrong argument types
testFunc("five", 42); // ERROR: Wrong argument types

// 11. Return type mismatch
function shouldReturnInteger(): integer {
    return "not an integer"; // ERROR: Return type mismatch
}

function shouldReturnVoid(): void {
    return 42; // ERROR: Void function should not return value
}

// 12. Missing return in non-void function
function missingReturn(x: integer): integer {
    if (x > 0) {
        print("Positive");
    }
    // ERROR: Function must return a value
}

// 13. Break/continue outside of loop
break; // ERROR: Break must be inside loop
continue; // ERROR: Continue must be inside loop

// 14. Return outside of function
return 5; // ERROR: Return must be inside function

// 15. Array index with wrong type
let numbers: integer[] = [1, 2, 3];
let element: integer = numbers["invalid"]; // ERROR: Array index must be integer

// 16. Property access on non-object
let primitive: integer = 42;
print(primitive.someProperty); // ERROR: Cannot access property of non-object

// 17. Method call on non-object
primitive.someMethod(); // ERROR: Cannot call method on non-object

// 18. Undefined class
let obj: UndefinedClass = new UndefinedClass(); // ERROR: Class not found

// 19. 'this' outside of class
function outsideClass(): void {
    print(this.name); // ERROR: 'this' can only be used inside class
}

// 20. Using uninitialized variable
let uninitialized: integer;
print(uninitialized); // ERROR: Variable used before initialization

// 21. Class inheritance from non-existent class
class BadChild : NonExistentParent { // ERROR: Parent class not found
    let value: integer;
}

// 22. Comparison of incompatible types
let comparison: boolean = 5 < "hello"; // ERROR: Cannot compare integer and string

// 23. Array type mismatch
let mixedArray: integer[] = [1, "two", 3]; // ERROR: Array elements must have same type

// 24. Wrong ternary condition
let ternaryResult: integer = 5 ? 10 : 20; // ERROR: Ternary condition must be boolean

// 25. Incompatible ternary branches
let incompatibleTernary: integer = true ? 5 : "hello"; // ERROR: Ternary branches must have compatible types

print("These should all be errors!");
