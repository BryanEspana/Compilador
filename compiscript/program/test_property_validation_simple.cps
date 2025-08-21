class Persona {
  let nombre: string;
  let edad: integer;
  let color: string;

  function constructor(nombre: string, edad: integer) {
    this.nombre = nombre;
    this.edad = edad;
    this.color = "rojo";
  }
}

class Estudiante : Persona {
  let grado: integer;

  function constructor(nombre: string, edad: integer, grado: integer) {
    this.nombre = nombre;
    this.edad = edad;
    this.color = "rojo";
    this.grado = grado;
  }
}

let juan: Estudiante = new Estudiante("Juan", 20, 3);

// Estas propiedades SI existen - deben funcionar
let nombre_ok: string = juan.nombre;
let edad_ok: integer = juan.edad;
let grado_ok: integer = juan.grado;
let color_ok: string = juan.color;

// Esta propiedad NO existe - debe dar error
let edades_error: integer = juan.edades;
