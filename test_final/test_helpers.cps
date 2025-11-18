// Test de funciones helper
// Helpers "declarados" en el lenguaje; la implementación real la hace el backend MIPS.
function toString(x: integer): string {
  return "";
}

function printInteger(x: integer): integer { return x; }
function printString(x: string): string { return x; }

// Programa principal - Prueba básica de helpers
let test: integer = 42;
let result: string = toString(test);
printString("Test helpers: " + result + "\n");

