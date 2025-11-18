// Test de recursividad: Fibonacci
// Helpers "declarados" en el lenguaje; la implementación real la hace el backend MIPS.
function toString(x: integer): string {
  return "";
}

function printString(x: string): string { return x; }

function fibonacci(n: integer): integer {
  if (n <= 1) {
    return n;
  }
  let a: integer = fibonacci(n - 1);
  let b: integer = fibonacci(n - 2);
  let r: integer = a + b;
  return r;
}

// Programa principal - Prueba de Fibonacci
let log: string = "";
log = log + "Prueba: Fibonacci recursivo\n";
let nFib: integer = 10;
let k: integer = 0;
while (k <= nFib) {
  let fk: integer = fibonacci(k);
  log = log + "Fib(" + toString(k) + ") = " + toString(fk) + "\n";
  k = k + 1;
}
printString(log);

