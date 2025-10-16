Codigo:
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
    return "Ahora tengo " + toString(this.edad) + " años.";
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
    return this.nombre + " está estudiando en " + toString(this.grado) + " grado.";
  }

  function promedioNotas(nota1: integer, nota2: integer, nota3: integer): integer {
    let promedio: integer = (nota1 + nota2 + nota3) / 3; // división entera
    return promedio;
  }
}

// --- Programa principal ---
let log: string = "";

let nombre: string = "Erick";
let juan: Estudiante = new Estudiante(nombre, 20, 3);

// "Imprimir" = concatenar al log con saltos de línea
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

// Expresión aritmética (entera)
let resultado: integer = (juan.edad * 2) + ((5 - 3) / 2);
log = log + "Resultado de la expresión: " + toString(resultado) + "\n";

// Ejemplo de promedio (entero)
let prom: integer = 0;
prom = juan.promedioNotas(90, 85, 95);
log = log + "Promedio (entero): " + toString(prom) + "\n";

// Nota: 'log' contiene todas las salidas.

Codigo intermedio generado:
// === COMPISCRIPT PROGRAM ===
FUNCTION toString:
	RETURN ""
END FUNCTION toString
FUNCTION constructor:
	fp[-1][0] := fp[-2]
	fp[-1][8] := fp[-3]
	fp[-1][12] := "rojo"
	RETURN 0
END FUNCTION constructor
FUNCTION saludar:
	t0 := "Hola, mi nombre es " + fp[-1][0]
	RETURN t0
END FUNCTION saludar
FUNCTION incrementarEdad:
	t0 := fp[-1][8] + fp[-2]
	fp[-1][8] := t0
	PARAM fp[-1][8]
	CALL toString,1
	t1 := R
	t2 := "Ahora tengo " + t1
	t3 := t2 + " años."
	RETURN t3
END FUNCTION incrementarEdad
FUNCTION constructor:
	fp[-1][0] := fp[-2]
	fp[-1][8] := fp[-3]
	fp[-1][12] := "rojo"
	fp[-1][20] := fp[-4]
	RETURN 0
END FUNCTION constructor
FUNCTION estudiar:
	t0 := fp[-1][0] + " está estudiando en "
	PARAM fp[-1][20]
	CALL toString,1
	t1 := R
	t2 := t0 + t1
	t3 := t2 + " grado."
	RETURN t3
END FUNCTION estudiar
FUNCTION promedioNotas:
	t0 := fp[-2] + fp[-3]
	t1 := t0 + fp[-4]
	t2 := t1 / 3
	fp[0] := t2
	RETURN t2
END FUNCTION promedioNotas
G[24] := ""
G[32] := "Erick"
PARAM G[32]
PARAM 20
PARAM 3
CALL newEstudiante,3
t3 := R
G[40] := t3
PARAM G[40]
CALL saludar,1
t4 := R
t5 := G[24] + t4
t6 := t5 + "\n"
G[24] := t6
PARAM G[40]
CALL estudiar,1
t7 := R
t8 := G[24] + t7
t9 := t8 + "\n"
G[24] := t9
PARAM G[40]
PARAM 5
CALL incrementarEdad,2
t10 := R
t11 := G[24] + t10
t12 := t11 + "\n"
G[24] := t12
G[44] := 1
STARTWHILE_0:
t13 := G[44] <= 5
IF t13 > 0 GOTO LABEL_TRUE_0
GOTO ENDWHILE_0
LABEL_TRUE_0:
t14 := G[44] % 2
t15 := t14 == 0
IF t15 > 0 GOTO IF_TRUE_0
GOTO IF_FALSE_0
IF_TRUE_0:
PARAM G[44]
CALL toString,1
t16 := R
t17 := G[24] + t16
t18 := t17 + " es par\n"
G[24] := t18
GOTO IF_END_0
IF_FALSE_0:
PARAM G[44]
CALL toString,1
t19 := R
t20 := G[24] + t19
t21 := t20 + " es impar\n"
G[24] := t21
IF_END_0:
t22 := G[44] + 1
G[44] := t22
GOTO STARTWHILE_0
ENDWHILE_0:
t23 := G[40][8] * 2
t24 := 5 - 3
t25 := t24 / 2
t26 := t23 + t25
G[48] := t26
t27 := G[24] + "Resultado de la expresión: "
PARAM G[48]
CALL toString,1
t28 := R
t29 := t27 + t28
t30 := t29 + "\n"
G[24] := t30
G[52] := 0
PARAM G[40]
PARAM 90
PARAM 85
PARAM 95
CALL promedioNotas,4
t31 := R
G[52] := t31
t32 := G[24] + "Promedio (entero): "
PARAM G[52]
CALL toString,1
t33 := R
t34 := t32 + t33
t35 := t34 + "\n"
G[24] := t35
// === END OF PROGRAM ===
