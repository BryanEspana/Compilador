// Test strict addition validation
// These should ALL produce errors (invalid operations)
let uno: integer = 5 + "Hola";
let dos: string = 5 + "Hola";
let tres: boolean = 5 + "Hola";
let cuatro: boolean = true + 4;
let cinco: boolean = false + "string";
let seis: integer = "text" + 42;
let siete: string = 10 + "world";

// These should be valid (correct operations)
let validInt1: integer = 5 + 3;
let validStr1: string = "Hello" + "World";

// These should produce TYPE MISMATCH errors (valid operation, wrong variable type)
let invalidAssign1: boolean = 5 + 3;        // integer result assigned to boolean
let invalidAssign2: boolean = "A" + "B";    // string result assigned to boolean

// These should produce OPERATION errors (invalid operations)
let invalidOp1: integer = true + false;     // boolean + boolean
let invalidOp2: string = true + false;      // boolean + boolean

print("Strict addition validation test");
