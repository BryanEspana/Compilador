# tests/test_comparisons.py
import os, sys
from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker
from antlr4.error.ErrorListener import ErrorListener

# Asegura que Python encuentre los módulos generados en .../program
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from SemanticAnalyzer import SemanticAnalyzer

class CollectingErrorListener(ErrorListener):
    def __init__(self):
        self.errors = []
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(f"Line {line}:{column} - {msg}")

PRELUDE = """
let xi: integer = 10;
let xs: string  = "hi";
let xb: boolean = true;
let xa: integer[] = [1,2];
"""

def compile_snippet(src: str):
    # Parser
    err_listener = CollectingErrorListener()
    lexer = CompiscriptLexer(InputStream(src))
    tokens = CommonTokenStream(lexer)
    parser = CompiscriptParser(tokens)
    parser.removeErrorListeners()
    parser.addErrorListener(err_listener)
    tree = parser.program()

    # Semántico
    analyzer = SemanticAnalyzer()
    walker = ParseTreeWalker()
    walker.walk(analyzer, tree)

    # Errores del analizador + errores internos del evaluador de expresiones
    sem_errors = list(getattr(analyzer, "errors", []))
    ee_errors = []
    ee = getattr(analyzer, "expression_evaluator", None)
    if ee is not None and hasattr(ee, "errors"):
        ee_errors = list(ee.errors)

    # Opcional: deduplicar para evitar mensajes repetidos
    all_errors = err_listener.errors + sem_errors + ee_errors
    # Mantener orden y quitar duplicados
    seen = set()
    uniq_errors = []
    for e in all_errors:
        if e not in seen:
            uniq_errors.append(e)
            seen.add(e)

    return uniq_errors

def run_case(name: str, snippet: str, expect_err: bool):
    code = PRELUDE + "\n" + snippet
    errors = compile_snippet(code)
    got_err = len(errors) > 0
    status = "PASS" if got_err == expect_err else "FAIL"
    print(f"[{status}] {name}")

    # Mostrar detalles según el resultado
    if status == "PASS":
        if expect_err:
            print("  ✅ Se detectaron errores (como se esperaba):")
            for e in errors:
                print("     •", e)
        else:
            print("  ✅ Compiló sin errores")
    else:
        # Caso FAIL: mostrar qué pasó
        print("  Source:", snippet.strip())
        if expect_err and not errors:
            print("  ❌ No se reportó error, pero se esperaba uno.")
        elif (not expect_err) and errors:
            print("  ❌ Aparecieron errores, pero no se esperaban:")
            for e in errors:
                print("     •", e)

def run_block(title: str, cases):
    print("\n" + title)
    print("-" * len(title))
    for (name, snippet, expect_err) in cases:
        run_case(name, snippet, expect_err)
    print()

def main():
    # == y != : solo mismo tipo entre {integer, string, boolean}
    eq_cases = [
        ("int == int (OK)",          "let r: boolean = 1 == 1;",                False),
        ("int != int (OK)",          "let r: boolean = xi != 2;",               False),
        ("string == string (OK)",    'let r: boolean = "a" == "b";',            False),
        ("bool != bool (OK)",        "let r: boolean = xb != false;",           False),

        ("int == string (ERR)",      "let r: boolean = xi == xs;",              True),
        ("int != string (ERR)",      "let r: boolean = xi != xs;",              True),
        ("string == bool (ERR)",     "let r: boolean = xs == xb;",              True),
        ("int == array (ERR)",       "let r: boolean = xi == xa;",              True),
        ("string == int (ERR)",      'let r: boolean = "a" == 1;',              True),
        ("bool == int (ERR)",        "let r: boolean = true == 1;",             True),
        ("int == null (ERR)",        "let r: boolean = xi == null;",            True),
        ("null != null (ERR)",       "let r: boolean = null != null;",          True),
    ]

    # <, <=, >, >= : solo integer vs integer
    rel_cases = [
        ("int < int (OK)",           "let r: boolean = 3 < 5;",                 False),
        ("int > int (OK)",           "let r: boolean = xi > 0;",                False),
        ("int <= int (OK)",          "let r: boolean = xi <= xi;",              False),
        ("int >= int (OK)",          "let r: boolean = 7 >= 2;",                False),

        ("string < string (ERR)",    'let r: boolean = "a" < "b";',             True),
        ("int < string (ERR)",       "let r: boolean = xi < xs;",               True),
        ("bool > bool (ERR)",        "let r: boolean = xb > xb;",               True),
        ("array >= int (ERR)",       "let r: boolean = xa >= xi;",              True),
        ("null < int (ERR)",         "let r: boolean = null < xi;",             True),
    ]

    run_block("Comparaciones de igualdad (==, !=)", eq_cases)
    run_block("Comparaciones relacionales (<, <=, >, >=)", rel_cases)

if __name__ == "__main__":
    main()
