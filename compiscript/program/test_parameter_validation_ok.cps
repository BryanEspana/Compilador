class Test {
  function getValue(): integer {
    return 42;
  }
  
  function setValue(value: integer): void {
    // Set value
  }
  
  function add(a: integer, b: integer): integer {
    return a + b;
  }
}

let obj: Test = new Test();
let result1: integer = obj.getValue();    // OK: correct number of parameters (0)
obj.setValue(10);                         // OK: correct number of parameters (1)
let result2: integer = obj.add(1, 2);     // OK: correct number of parameters (2)
