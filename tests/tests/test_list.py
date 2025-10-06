# tests/test_lists_only.py
import os, sys
from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker
from antlr4.error.ErrorListener import ErrorListener

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
let xi: integer = 42;
let xs: string  = "hi";
let xb: boolean = false;
"""

def compile_snippet(src: str):
    pel = CollectingErrorListener()
    lexer = CompiscriptLexer(InputStream(src))
    tokens = CommonTokenStream(lexer)
    parser = CompiscriptParser(tokens)
    parser.removeErrorListeners()
    parser.addErrorListener(pel)
    tree = parser.program()

    analyzer = SemanticAnalyzer()
    walker = ParseTreeWalker()
    walker.walk(analyzer, tree)

    sem_errors = list(getattr(analyzer, "errors", []))
    ee_errors = []
    ee = getattr(analyzer, "expression_evaluator", None)
    if ee is not None and hasattr(ee, "errors"):
        ee_errors = list(ee.errors)

    all_errs = pel.errors + sem_errors + ee_errors
    seen, uniq = set(), []
    for e in all_errs:
        if e not in seen:
            uniq.append(e); seen.add(e)
    return uniq

def run_case(n, snippet):
    print(f"test {n}: {snippet.strip()}")
    code = PRELUDE + "\n" + snippet
    errs = compile_snippet(code)
    if errs:
        for e in errs:
            print("  ❌", e)
    else:
        print("  ✅ Compiló sin errores")

def main():
    print("Verificación de listas:")
    print("-----------------------")

    i = 1
    # OK: 1D homogéneos con anotación
    run_case(i,   "let a: integer[] = [1,2,3];"); i+=1
    run_case(i,   'let b: string[]  = ["a","b"];'); i+=1
    run_case(i,   "let c: boolean[] = [true, false];"); i+=1

    # ERR: 1D heterogéneo (sin anotación e inferido)
    run_case(i,   'let bad = [1, "x"];'); i+=1

    # ERR: anotación vs literal de distinto tipo
    run_case(i,   'let bad2: integer[] = ["x"];'); i+=1
    run_case(i,   'let bad3: boolean[] = [1];'); i+=1

    # OK: inferencia + acceso simple (si tu indexación ya está lista)
    # Puedes omitir este si aún no implementas indexado
    # run_case(i,   "let d = [1,2,3]; let x: integer = d[0];"); i+=1

    # OK: 2D homogéneo (sin indexar)
    run_case(i,   "let m: integer[][] = [[1,2],[3,4]];"); i+=1

    # ERR: 2D heterogéneo
    run_case(i,   'let m2: integer[][] = [[1,2],[3,"x"]];'); i+=1

if __name__ == "__main__":
    main()
