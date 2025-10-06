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
let result1: integer = obj.getValue(5);  // Error: getValue expects 0 parameters, got 1
let result2: void = obj.setValue();      // Error: setValue expects 1 parameter, got 0  
let result3: integer = obj.add(1);       // Error: add expects 2 parameters, got 1
let result4: integer = obj.add(1, 2, 3); // Error: add expects 2 parameters, got 3
let result5: integer = obj.add(1, 2);    // OK: correct number of parameters
