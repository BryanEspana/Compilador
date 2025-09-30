// Test scope validation
// These should produce errors

// 1. Reserved keyword as variable name
let let: integer = 5;
let function: string = "test";
const class: boolean = true;

// 2. Redeclaration in same scope
let x: integer = 10;
let x: string = "hello";  // Error: redeclaration

// 3. Function redeclaration
function test(): void {}
function test(param: integer): integer { return 1; }  // Error: redeclaration

// 4. Class redeclaration
class MyClass {}
class MyClass {}  // Error: redeclaration

// 5. Use of undeclared variable
let valid: integer = undeclaredVar;  // Error: undeclared

// 6. Use before initialization
let uninit: integer;
let result: integer = uninit + 5;  // Error: use before init

// 7. Assignment to undeclared variable
notDeclared = 42;  // Error: undeclared

// 8. Assignment to function
function myFunc(): void {}
myFunc = 5;  // Error: cannot assign to function

// 9. Assignment to class
class TestClass {}
TestClass = 10;  // Error: cannot assign to class

// 10. Assignment to constant
const PI: integer = 314;
PI = 315;  // Error: cannot assign to constant

// 11. Duplicate parameter names
function badFunc(param: integer, param: string): void {}  // Error: duplicate param

// 12. Reserved keyword as parameter
function badFunc2(let: integer): void {}  // Error: reserved keyword

// 13. Class inheriting from non-existent class
class BadChild : NonExistentParent {}  // Error: parent not found

// 14. Class inheriting from non-class
let notAClass: integer = 5;
class BadChild2 : notAClass {}  // Error: not a class

// 15. Class inheriting from itself
class SelfRef : SelfRef {}  // Error: self-inheritance

// Valid code that should work
{
    let blockVar: integer = 42;  // Valid: new scope
    {
        let innerVar: string = "nested";  // Valid: deeper scope
        let blockVar: string = "shadow";  // Valid: shadowing outer scope
    }
}

function validFunc(param1: integer, param2: string): integer {
    let localVar: integer = param1 + 5;  // Valid: using parameter
    return localVar;
}

class ValidClass {
    let attribute: string;
    
    function method(): void {
        let methodVar: integer = 10;  // Valid: method scope
    }
}

print("Scope validation test");
