class Persona {
    init(nombre: string, apellido: string, edad: integer) {
        this.nombre = nombre;
        this.apellido = apellido;
        this.edad = edad;
    }
    
    function toString(): string {
        return this.nombre + " " + this.apellido;
    }
}

class Estudiante : Persona {
    init(nombre: string, apellido: string, edad: integer, carnet: string, creditos: integer) {
        super(nombre, apellido, edad);
        this.carnet = carnet;
        this.creditos = creditos;
        this.color = "azul";
    }
    
    function toString(): string {
        return super.toString() + " - " + this.carnet;
    }
}

let est: Estudiante = new Estudiante("Juan", "Perez", 20, "2021001", 15);
let str: string = est.toString();
let nombre: string = est.nombre;
let carnet: string = est.carnet;
let color: string = est.color;
