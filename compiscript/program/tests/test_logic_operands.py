# tests/test_logic_operands.py
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
        super().__init__()
        self.errors = []
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(f"Line {line}:{column} - {msg}")

PRELUDE = """
// Identificadores de distintos tipos
let xb: boolean = true;
let xi: integer = 1;
let xs: string  = "hi";
let xa: integer[] = [1,2];
"""

def compile_snippet(src: str):
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

    sem_errors = list(getattr(analyzer, "errors", []))
    ee = getattr(analyzer, "expression_evaluator", None)
    expr_errors = list(ee.get_errors()) if (ee and hasattr(ee, "get_errors")) else []

    return err_listener.errors + sem_errors + expr_errors

def show_section(title):
    print("\n" + title)
    print("-" * len(title))

def run_case(n, snippet):
    code = PRELUDE + "\n" + snippet
    errors = compile_snippet(code)
    print(f"test {n}: {snippet.strip()}")
    if errors:
        for e in errors:
            print("  ❌", e)
    else:
        print("  ✅ Compiló sin errores")

def main():
    # && (solo boolean)
    show_section("Verificación de operación lógica && (AND)")
    cases_and = [
        ('let r: boolean = true && false;',          False),
        ('let r: boolean = xb && true;',             False),
        ('let r: boolean = xb && xb;',               False),

        ('let r: boolean = xi && xb;',               True),
        ('let r: boolean = xs && xb;',               True),
        ('let r: boolean = xa && xb;',               True),
        ('let r: boolean = true && xi;',             True),
        ('let r: boolean = xi && xi;',               True),
        ('let r: boolean = "x" && "y";',             True),
        ('let r: boolean = null && xb;',             True),
        ('let r: boolean = xb && null;',             True),
    ]
    for i, (code, expect_err) in enumerate(cases_and, 1):
        run_case(i, code)

    # || (solo boolean)
    show_section("Verificación de operación lógica || (OR)")
    cases_or = [
        ('let r: boolean = true || false;',          False),
        ('let r: boolean = false || xb;',            False),
        ('let r: boolean = xb || xb;',               False),

        ('let r: boolean = xi || xb;',               True),
        ('let r: boolean = xs || xb;',               True),
        ('let r: boolean = xa || xb;',               True),
        ('let r: boolean = true || xi;',             True),
        ('let r: boolean = xi || xi;',               True),
        ('let r: boolean = "x" || "y";',             True),
        ('let r: boolean = null || xb;',             True),
        ('let r: boolean = xb || null;',             True),
    ]
    for i, (code, expect_err) in enumerate(cases_or, 1):
        run_case(i, code)

    # ! (solo boolean)
    show_section("Verificación de operación lógica ! (NOT)")
    cases_not = [
        ('let r: boolean = !true;',                  False),
        ('let r: boolean = !xb;',                    False),

        ('let r: boolean = !xi;',                    True),
        ('let r: boolean = !"x";',                   True),
        ('let r: boolean = !xa;',                    True),
        ('let r: boolean = !null;',                  True),
    ]
    for i, (code, expect_err) in enumerate(cases_not, 1):
        run_case(i, code)

if __name__ == "__main__":
    main()
