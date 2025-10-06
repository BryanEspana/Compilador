class Caja {
  var v: integer;
  var z: integer;
  var w: integer;
  function setv(a: integer, b: integer, c: integer): void { v = a; z = b; w = c; }
}

function main(): void {
  let c: Caja;      // c valido
  c.setv(10, 2, 3);
}