// Test type validation

// These should produce TYPE ERRORS (semantic errors)
let radius: integer = "Prado es gei";
let nombre: string = 5;
let flag: boolean = "true";
const PI: integer = "3.14";

// These should be valid
let validInt: integer = 42;
let validStr: string = "hello";
let validBool: boolean = true;
const VALID_CONST: string = "constant";

// Type inference (no explicit type)
let inferredInt = 100;
let inferredStr = "world";
let inferredBool = false;

print("Type validation test");
