// Test de herencia: Estudiante hereda de Persona
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

// Clase derivada
class Estudiante : Persona {
  let grado: integer;

  function constructor(nombre: string, edad: integer, grado: integer) {
    // No hay 'super': inicializamos campos heredados directamente
    this.nombre = nombre;
    this.edad = edad;
    this.color = "rojo";
    this.grado = grado;
  }

  function estudiar(): string {
    return this.nombre + " está estudiando en " + toString(this.grado) + " año en la Universidad del Valle de Guatemala (UVG).";
  }

  function promedioNotas(n1: integer, n2: integer, n3: integer, n4: integer, n5: integer, n6: integer): integer {
    let promedio: integer = (n1 + n2 + n3 + n4 + n5 + n6) / 6; // división entera
    return promedio;
  }
}

// Programa principal - Prueba de herencia
let log: string = "";
let estudiante1: Estudiante = new Estudiante("María", 20, 3);
log = log + estudiante1.saludar() + "\n";
log = log + estudiante1.estudiar() + "\n";
log = log + estudiante1.incrementarEdad(2) + "\n";
let prom: integer = estudiante1.promedioNotas(90, 85, 95, 88, 92, 87);
log = log + "Promedio (entero): " + toString(prom) + "\n";
printString(log);

