// Test cases that should pass semantic analysis
// Testing basic variable declarations and assignments

// Constants
const PI: integer = 314;
const MESSAGE: string = "Hello World";
const FLAG: boolean = true;

// Variables with type annotations
let age: integer = 25;
let name: string = "Alice";
let isActive: boolean = false;

// Variables without type annotations (type inference)
let count = 10;
let greeting = "Hi there";
let ready = true;

// Arrays
let numbers: integer[] = [1, 2, 3, 4, 5];
let words: string[] = ["hello", "world"];
let matrix: integer[][] = [[1, 2], [3, 4]];

// Functions
function add(a: integer, b: integer): integer {
    return a + b;
}

function greet(name: string): string {
    return "Hello " + name;
}

function isEven(n: integer): boolean {
    return n % 2 == 0;
}

// Function calls
let sum: integer = add(5, 3);
let message: string = greet("Bob");
let even: boolean = isEven(4);

// Control flow with proper boolean conditions
if (age > 18) {
    print("Adult");
} else {
    print("Minor");
}

let i: integer = 0;
while (i < 5) {
    print("Count: " + i);
    i = i + 1;
}

do {
    print("At least once");
    i = i - 1;
} while (i > 0);

for (let j: integer = 0; j < 3; j = j + 1) {
    print("Loop: " + j);
}

foreach (num in numbers) {
    if (num > 3) {
        break;
    }
    if (num == 2) {
        continue;
    }
    print("Number: " + num);
}

// Classes
class Person {
    let name: string;
    let age: integer;
    
    function constructor(name: string, age: integer) {
        this.name = name;
        this.age = age;
    }
    
    function getName(): string {
        return this.name;
    }
    
    function getAge(): integer {
        return this.age;
    }
}

class Student : Person {
    let grade: integer;
    
    function constructor(name: string, age: integer, grade: integer) {
        this.name = name;
        this.age = age;
        this.grade = grade;
    }
    
    function getGrade(): integer {
        return this.grade;
    }
}

// Object creation and method calls
let person: Person = new Person("John", 30);
let student: Student = new Student("Jane", 20, 85);

print(person.getName());
print(student.getGrade());

// Array access
let firstNumber: integer = numbers[0];
let firstRow: integer[] = matrix[0];
let element: integer = matrix[0][1];

// Recursion
function factorial(n: integer): integer {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

let fact: integer = factorial(5);

// Switch statement
switch (age) {
    case 18:
        print("Just became adult");
    case 21:
        print("Can drink");
    default:
        print("Other age");
}

print("All tests passed!");
