class Acum {
  var acc: integer;

  function add(a: integer): integer {
    acc = acc + a;
    return acc;
  }
}

function main(): void {
  let a: Acum;
  let r: integer;
  r = a.add(5);
}