class Punto {
  var x: integer;
  var y: integer;

  function sum(): integer {
    return x + y;
  }
}

function main(): void {
  let p: Punto;
  // (suponemos p valido)
  let s: integer;
  s = p.x + p.y;
}