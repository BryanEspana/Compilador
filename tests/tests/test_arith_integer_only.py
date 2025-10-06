# tests/test_arith_integer_only.py
import os, sys
from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker
from antlr4.error.ErrorListener import ErrorListener

# Asegura que Python encuentre los módulos generados en .../program
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from SemanticAnalyzer import SemanticAnalyzer

# Captura errores sintácticos del parser
class CollectingErrorListener(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errors = []
    def syntaxError(self, line, column, msg, e):
        self.errors.append(f"Line {line}:{column} - {msg}")

PRELUDE = """
// Identificadores de distintos tipos
let xi: integer = 10;
let xs: string  = "hi";
let xb: boolean = true;
let xa: integer[] = [1,2];
"""

def compile_snippet(src: str):
    # Construye compilación y devuelve lista de errores (sintácticos + semánticos)
    err_listener = CollectingErrorListener()
    lexer = CompiscriptLexer(InputStream(src))
    tokens = CommonTokenStream(lexer)
    parser = CompiscriptParser(tokens)
    parser.removeErrorListeners()
    parser.addErrorListener(err_listener)

    tree = parser.program()

    analyzer = SemanticAnalyzer()
    walker = ParseTreeWalker()
    walker.walk(analyzer, tree)

    # Junta errores semánticos de SemanticAnalyzer y (si expone) del ExpressionEvaluator
    sem_errors = list(getattr(analyzer, "errors", []))
    expr_errors = []
    ee = getattr(analyzer, "expression_evaluator", None)
    if ee is not None and hasattr(ee, "get_errors"):
        expr_errors = list(ee.get_errors())

    return err_listener.errors + sem_errors + expr_errors

def show_section(title):
    print("\n" + title)
    print("-" * len(title))

def run_case(n, snippet):
    code = PRELUDE + "\n" + snippet
    errors = compile_snippet(code)
    print(f"test {n}: {snippet.strip()}")
    if errors:
        # Muestra todos los errores (o el primero si prefieres)
        for e in errors:
            print("  ❌", e)
    else:
        print("  ✅ Compiló sin errores")

def main():
    # + (solo integers)
    show_section("Verificación de operación aritmética +")
    run_case(1,  "let a: integer = 1 + 1;")
    run_case(2,  "let a: integer = xi + 1;")        # identifier integer OK
    run_case(3,  "let a: integer = 1 + xi;")        # identifier integer OK
    run_case(4,  "let a: integer = 1 + \"x\";")     # int + string -> ERROR
    run_case(5,  "let a: integer = \"x\" + 1;")     # string + int -> ERROR
    run_case(6,  "let a: integer = true + 1;")      # boolean + int -> ERROR
    run_case(7,  "let a: integer = xi + xb;")       # int + boolean -> ERROR
    run_case(8,  "let a: integer = [1,2] + 1;")     # array + int -> ERROR
    run_case(9,  "let a: integer = 1 + 2 + 3;")     # encadenado integers -> OK
    run_case(10, "let a: integer = 1 + 2 + xi;")    # encadenado con id int -> OK
    run_case(11, "let a: string = \"x\" + \"x\";") # encadenado con string -> ERROR

    # - (solo integers)
    show_section("Verificación de operación aritmética -")
    run_case(1,  "let b: integer = 4 - 2;")
    run_case(2,  "let b: integer = xi - 2;")
    run_case(3,  "let b: integer = 4 - xi;")
    run_case(4,  "let b: integer = \"x\" - 1;")     # ERROR
    run_case(5,  "let b: integer = true - 1;")      # ERROR
    run_case(6,  "let b: integer = xa - 1;")        # ERROR
    run_case(7,  "let b: integer = 7 - 2 - xi;")    # OK

    # * (solo integers)
    show_section("Verificación de operación aritmética *")
    run_case(1,  "let c: integer = 3 * 2;")
    run_case(2,  "let c: integer = xi * 2;")
    run_case(3,  "let c: integer = 3 * xi;")
    run_case(4,  "let c: integer = \"x\" * 2;")     # ERROR
    run_case(5,  "let c: integer = true * 2;")      # ERROR
    run_case(6,  "let c: integer = xa * 2;")        # ERROR

    # / (solo integers)
    show_section("Verificación de operación aritmética /")
    run_case(1,  "let d: integer = 8 / 2;")
    run_case(2,  "let d: integer = xi / 2;")
    run_case(3,  "let d: integer = 8 / xi;")
    run_case(4,  "let d: integer = \"x\" / 2;")     # ERROR
    run_case(5,  "let d: integer = true / 2;")      # ERROR
    run_case(6,  "let d: integer = xa / 2;")        # ERROR

if __name__ == "__main__":
    main()
