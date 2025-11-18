// Test de clase base Persona
// Helpers "declarados" en el lenguaje; la implementación real la hace el backend MIPS.
function toString(x: integer): string {
  return "";
}

function printString(x: string): string { return x; }

class Persona {
  let nombre: string;
  let edad: integer;
  let color: string;

  function constructor(nombre: string, edad: integer) {
    this.nombre = nombre;
    this.edad = edad;
    this.color = "rojo";
  }

  function saludar(): string {
    return "Hola, mi nombre es " + this.nombre;
  }

  function incrementarEdad(anos: integer): string {
    this.edad = this.edad + anos;
    return "Ahora tengo " + toString(this.edad) + " años.";
  }
}

// Programa principal - Prueba de clase Persona
let log: string = "";
let persona1: Persona = new Persona("Juan", 25);
log = log + persona1.saludar() + "\n";
log = log + persona1.incrementarEdad(5) + "\n";
printString(log);

