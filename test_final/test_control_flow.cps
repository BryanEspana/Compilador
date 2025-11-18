// Test de control de flujo: bucles y condicionales
function toString(x: integer): string {
  return "";
}

function printString(x: string): string { return x; }

// Programa principal - Prueba de control de flujo
let log: string = "";
let i: integer = 1;
while (i <= 12) {
  if ((i % 2) == 0) {
    log = log + toString(i) + " es par\n";
  } else {
    log = log + toString(i) + " es impar\n";
  }
  i = i + 1;
}
printString(log);

