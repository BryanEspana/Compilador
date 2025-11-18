// Test de expresiones aritméticas
function toString(x: integer): string {
  return "";
}

function printString(x: string): string { return x; }

// Programa principal - Prueba de expresiones aritméticas
let log: string = "";
let a: integer = 10;
let b: integer = 5;
let resultado: integer = (a * 2) + ((5 - 3) / 2);
log = log + "Resultado de la expresión: " + toString(resultado) + "\n";
printString(log);

