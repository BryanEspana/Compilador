// --- Utilidad global ---
function toString(x: integer): string {
  return "";
}

// --- Clase base ---
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
    return "Ahora tengo " + toString(this.edad) + " anos.";
  }
}

// --- Clase derivada ---
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
    return this.nombre + " esta estudiando en " + toString(this.grado) + " grado.";
  }

  function promedioNotas(nota1: integer, nota2: integer, nota3: integer): integer {
    let promedio: integer = (nota1 + nota2 + nota3) / 3; // division entera
    return promedio;
  }
}

// --- Programa principal ---
let log: string = "";

let nombre: string = "Erick";
let juan: Estudiante = new Estudiante(nombre, 20, 3);

// "Imprimir" = concatenar al log con saltos de linea
log = log + juan.saludar() + "\n";
log = log + juan.estudiar() + "\n";
log = log + juan.incrementarEdad(5) + "\n";

// Bucle (uso de while por compatibilidad)
let i: integer = 1;
while (i <= 5) {
  if ((i % 2) == 0) {
    log = log + toString(i) + " es par\n";
  } else {
    log = log + toString(i) + " es impar\n";
  }
  i = i + 1;
}

// Expresion aritmetica (entera)
let resultado: integer = (juan.edad * 2) + ((5 - 3) / 2);
log = log + "Resultado de la expresion: " + toString(resultado) + "\n";

// Ejemplo de promedio (entero)
let prom: integer = 0;
prom = juan.promedioNotas(90, 85, 95);
log = log + "Promedio (entero): " + toString(prom) + "\n";
