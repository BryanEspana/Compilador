// Demo simple de Compiscript
// Este archivo demuestra las caracteristicas basicas del lenguaje

// Constantes y variables
const PI: integer = 314;
let nombre: string = "Compiscript";
let edad: integer = 25;
let activo: boolean = true;

// Funcion simple
function saludar(nombre: string): string {
    return "Hola " + nombre + "!";
}

// Llamada a funcion
let mensaje: string = saludar("Mundo");
print(mensaje);

// Control de flujo
if (edad >= 18) {
    print("Eres mayor de edad");
} else {
    print("Eres menor de edad");
}

// Bucle while
let contador: integer = 0;
while (contador < 3) {
    print("Contador: " + contador);
    contador = contador + 1;
}

// Array simple
let numeros: integer[] = [1, 2, 3, 4, 5];
print("Primer numero: " + numeros[0]);

// Clase simple
class Persona {
    let nombre: string;
    let edad: integer;
    
    function constructor(nombre: string, edad: integer) {
        this.nombre = nombre;
        this.edad = edad;
    }
    
    function presentarse(): string {
        return "Me llamo " + this.nombre + " y tengo " + this.edad + " anos";
    }
}

// Crear instancia
let persona: Persona = new Persona("Ana", 30);
print(persona.presentarse());

print("Demo completado exitosamente!");
