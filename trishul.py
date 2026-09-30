#!/usr/bin/env python3

import argparse
import sys
from dataclasses import dataclass, field
from typing import Any, List, Optional


class TrishulError(Exception):
    pass


class LoopLimitExceeded(TrishulError):
    pass


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


@dataclass
class Token:
    type: str
    value: Any = None


@dataclass
class Program:
    statements: List["Stmt"]


@dataclass
class Literal:
    value: Any


@dataclass
class Name:
    name: str


@dataclass
class Binary:
    op: str
    left: Any
    right: Any


@dataclass
class Unary:
    op: str
    operand: Any


@dataclass
class Call:
    callee: Any
    args: List[Any]


@dataclass
class Assign:
    name: str
    value: Any


@dataclass
class Print:
    expr: Any


@dataclass
class Return:
    expr: Any


@dataclass
class If:
    condition: Any
    then_body: List["Stmt"]
    else_body: Optional[List["Stmt"]] = None


@dataclass
class While:
    condition: Any
    body: List["Stmt"]
    max_iterations: int = 10000


@dataclass
class For:
    var: str
    start: Any
    end: Any
    step: Any
    body: List["Stmt"]
    max_iterations: int = 10000


@dataclass
class Break:
    pass


@dataclass
class Continue:
    pass


@dataclass
class FunctionDef:
    name: str
    params: List[str]
    body: List["Stmt"]


@dataclass
class ExprStmt:
    expr: Any


Stmt = Any


KEYWORDS = {
    "ko": "KO",
    "rakho": "RAKHO",
    "likho": "LIKHO",
    "agar": "AGAR",
    "to": "TO",
    "warna": "WARNA",
    "jabtak": "JABTAK",
    "ke_liye": "FOR",
    "se": "FROM",
    "tak": "UNTIL",
    "tak_badhte_hue": "UNTIL_STEP",
    "kaam": "KAAM",
    "khatam": "KHATAM",
    "wapis": "WAPIS",
    "sahi": "TRUE",
    "galat": "FALSE",
    "aur": "AND",
    "ya": "OR",
    "tod_do": "BREAK",
    "agle": "CONTINUE",
}


def tokenize(source: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    while i < len(source):
        ch = source[i]

        if ch.isspace():
            i += 1
            continue

        if ch == '#':
            while i < len(source) and source[i] != '\n':
                i += 1
            continue

        if ch == '"':
            i += 1
            value = ""
            while i < len(source):
                if source[i] == '\\':
                    i += 1
                    if i >= len(source):
                        raise TrishulError("Dangling escape in string.")
                    esc = source[i]
                    mapping = {'n': '\n', 't': '\t', '"': '"', "'": "'", '\\': '\\'}
                    value += mapping.get(esc, esc)
                    i += 1
                    continue
                if source[i] == '"':
                    i += 1
                    break
                value += source[i]
                i += 1
            else:
                raise TrishulError("Unterminated string literal.")
            tokens.append(Token("STRING", value))
            continue

        if ch.isdigit() or (ch == '.' and i + 1 < len(source) and source[i + 1].isdigit()):
            start = i
            dot_count = 0
            while i < len(source) and (source[i].isdigit() or source[i] == '.'):
                if source[i] == '.':
                    dot_count += 1
                    if dot_count > 1:
                        break
                i += 1
            num_text = source[start:i]
            try:
                value = int(num_text)
            except ValueError:
                value = float(num_text)
            tokens.append(Token("NUMBER", value))
            continue

        if ch.isalpha() or ch == '_':
            start = i
            i += 1
            while i < len(source) and (source[i].isalnum() or source[i] == '_'):
                i += 1
            word = source[start:i]
            token_type = KEYWORDS.get(word.lower(), "IDENT")
            tokens.append(Token(token_type, word))
            continue

        if ch in "{}(),;":
            tokens.append(Token(ch, ch))
            i += 1
            continue

        if ch in "+-*/%":
            tokens.append(Token(ch, ch))
            i += 1
            continue

        if ch in "<>!=":
            if i + 1 < len(source) and source[i + 1] == '=':
                tokens.append(Token(source[i] + "=", source[i] + "="))
                i += 2
                continue
            if ch == '=':
                raise TrishulError("Assignment uses 'ko ... rakho', not '='.")
            tokens.append(Token(ch, ch))
            i += 1
            continue

        raise TrishulError(f"Unexpected character: {ch!r}")

    tokens.append(Token("EOF", None))
    return tokens


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.index = 0

    def current(self) -> Token:
        return self.tokens[self.index]

    def peek(self, offset: int = 1) -> Token:
        idx = self.index + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def advance(self) -> Token:
        token = self.current()
        if token.type != "EOF":
            self.index += 1
        return token

    def match(self, *token_types: str) -> Optional[Token]:
        if self.current().type in token_types:
            return self.advance()
        return None

    def expect(self, token_type: str) -> Token:
        token = self.current()
        if token.type != token_type:
            raise TrishulError(f"Expected {token_type!r}, found {token.type!r}.")
        self.index += 1
        return token

    def parse_program(self) -> Program:
        statements: List[Stmt] = []
        while self.current().type != "EOF":
            if self.current().type == "}":
                break
            statements.append(self.parse_statement())
        return Program(statements)

    def parse_block(self) -> List[Stmt]:
        self.expect("{")
        statements: List[Stmt] = []
        while self.current().type != "}":
            if self.current().type == "EOF":
                raise TrishulError("Missing closing '}' for block.")
            statements.append(self.parse_statement())
        self.expect("}")
        return statements

    def parse_statement(self) -> Stmt:
        token = self.current()

        if token.type == "AGAR":
            self.advance()
            condition = self.parse_expression()
            self.expect("TO")
            then_body = self.parse_block()
            else_body = None
            if self.match("WARNA"):
                else_body = self.parse_block()
            return If(condition, then_body, else_body)

        if token.type == "JABTAK":
            self.advance()
            condition = self.parse_expression()
            self.expect("TO")
            body = self.parse_block()
            return While(condition, body, max_iterations=10000)

        if token.type == "FOR":
            self.advance()
            var = self.expect("IDENT").value
            self.expect("FROM")
            start = self.parse_expression()
            self.expect("UNTIL")
            end = self.parse_expression()
            step = Literal(1)
            if self.match("UNTIL_STEP"):
                step = self.parse_expression()
            self.expect("TO")
            body = self.parse_block()
            return For(var, start, end, step, body, max_iterations=10000)

        if token.type == "BREAK":
            self.advance()
            return Break()

        if token.type == "CONTINUE":
            self.advance()
            return Continue()

        if token.type == "KAAM":
            self.advance()
            name = self.expect("IDENT").value
            self.expect("(")
            params: List[str] = []
            if self.current().type != ")":
                while True:
                    params.append(self.expect("IDENT").value)
                    if not self.match(","):
                        break
            self.expect(")")
            body = self.parse_block()
            self.expect("KHATAM")
            return FunctionDef(name, params, body)

        if token.type == "IDENT" and self.peek().type == "KO":
            name = self.advance().value
            self.expect("KO")
            value = self.parse_expression()
            self.expect("RAKHO")
            return Assign(name, value)

        expr = self.parse_expression()

        if self.match("LIKHO"):
            return Print(expr)
        if self.match("WAPIS"):
            return Return(expr)

        return ExprStmt(expr)

    def parse_expression(self) -> Any:
        return self.parse_or()

    def parse_or(self) -> Any:
        left = self.parse_and()
        while self.match("OR"):
            right = self.parse_and()
            left = Binary("or", left, right)
        return left

    def parse_and(self) -> Any:
        left = self.parse_equality()
        while self.match("AND"):
            right = self.parse_equality()
            left = Binary("and", left, right)
        return left

    def parse_equality(self) -> Any:
        left = self.parse_relational()
        while self.current().type in {"==", "!="}:
            op = self.advance().type
            right = self.parse_relational()
            left = Binary(op, left, right)
        return left

    def parse_relational(self) -> Any:
        left = self.parse_additive()
        while self.current().type in {"<", ">", "<=", ">="}:
            op = self.advance().type
            right = self.parse_additive()
            left = Binary(op, left, right)
        return left

    def parse_additive(self) -> Any:
        left = self.parse_multiplicative()
        while self.current().type in {"+", "-"}:
            op = self.advance().type
            right = self.parse_multiplicative()
            left = Binary(op, left, right)
        return left

    def parse_multiplicative(self) -> Any:
        left = self.parse_unary()
        while self.current().type in {"*", "/", "%"}:
            op = self.advance().type
            right = self.parse_unary()
            left = Binary(op, left, right)
        return left

    def parse_unary(self) -> Any:
        if self.current().type in {"+", "-"}:
            op = self.advance().type
            return Unary(op, self.parse_unary())
        return self.parse_primary()

    def parse_primary(self) -> Any:
        token = self.current()

        if token.type == "NUMBER":
            self.advance()
            return Literal(token.value)

        if token.type == "STRING":
            self.advance()
            return Literal(token.value)

        if token.type == "TRUE":
            self.advance()
            return Literal(True)

        if token.type == "FALSE":
            self.advance()
            return Literal(False)

        if token.type == "IDENT":
            name = self.advance().value
            if self.match("("):
                args: List[Any] = []
                if self.current().type != ")":
                    while True:
                        args.append(self.parse_expression())
                        if not self.match(","):
                            break
                self.expect(")")
                return Call(Name(name), args)
            return Name(name)

        if self.match("("):
            expr = self.parse_expression()
            self.expect(")")
            return expr

        raise TrishulError(f"Unexpected token in expression: {token.type!r}")


class FunctionValue:
    def __init__(self, name: str, params: List[str], body: List[Stmt], closure: dict):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure


class Interpreter:
    def __init__(self, max_loop_iterations: int = 10000):
        self.globals = {}
        self.max_loop_iterations = max_loop_iterations

    def execute_program(self, program: Program):
        env = dict(self.globals)
        for stmt in program.statements:
            self.execute_statement(stmt, env)
        return env

    def execute_block(self, statements: List[Stmt], env: dict):
        for stmt in statements:
            self.execute_statement(stmt, env)

    def execute_statement(self, stmt: Stmt, env: dict):
        if isinstance(stmt, Assign):
            env[stmt.name] = self.eval_expr(stmt.value, env)
            return None

        if isinstance(stmt, Print):
            print(self.eval_expr(stmt.expr, env))
            return None

        if isinstance(stmt, Return):
            raise ReturnSignal(self.eval_expr(stmt.expr, env))

        if isinstance(stmt, Break):
            raise BreakSignal()

        if isinstance(stmt, Continue):
            raise ContinueSignal()

        if isinstance(stmt, If):
            if self.is_truthy(self.eval_expr(stmt.condition, env)):
                self.execute_block(stmt.then_body, env)
            elif stmt.else_body is not None:
                self.execute_block(stmt.else_body, env)
            return None

        if isinstance(stmt, While):
            iterations = 0
            while self.is_truthy(self.eval_expr(stmt.condition, env)):
                iterations += 1
                if iterations > self.max_loop_iterations:
                    raise LoopLimitExceeded(
                        f"While loop exceeded maximum iterations ({self.max_loop_iterations})"
                    )
                try:
                    self.execute_block(stmt.body, env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return None

        if isinstance(stmt, For):
            start_val = self.eval_expr(stmt.start, env)
            end_val = self.eval_expr(stmt.end, env)
            step_val = self.eval_expr(stmt.step, env)

            if step_val == 0:
                raise TrishulError("For loop step cannot be zero (anant loop ka khatra)")
            
            iterations = 0
            current = start_val
            
            while (step_val > 0 and current < end_val) or (step_val < 0 and current > end_val):
                iterations += 1
                if iterations > self.max_loop_iterations:
                    raise LoopLimitExceeded(
                        f"For loop exceeded maximum iterations ({self.max_loop_iterations})"
                    )
                env[stmt.var] = current
                try:
                    self.execute_block(stmt.body, env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    pass
                current += step_val
            
            return None

        if isinstance(stmt, FunctionDef):
            env[stmt.name] = FunctionValue(stmt.name, stmt.params, stmt.body, dict(env))
            return None

        if isinstance(stmt, ExprStmt):
            self.eval_expr(stmt.expr, env)
            return None

        raise TrishulError(f"Unsupported statement type: {type(stmt).__name__}")

    def eval_expr(self, expr: Any, env: dict):
        if isinstance(expr, Literal):
            return expr.value

        if isinstance(expr, Name):
            if expr.name not in env:
                raise TrishulError(f"Undefined variable: {expr.name}")
            return env[expr.name]

        if isinstance(expr, Unary):
            value = self.eval_expr(expr.operand, env)
            if expr.op == '-':
                return -value
            if expr.op == '+':
                return +value
            raise TrishulError(f"Unsupported unary op: {expr.op}")

        if isinstance(expr, Binary):
            left = self.eval_expr(expr.left, env)
            right = self.eval_expr(expr.right, env)
            op = expr.op

            if op == 'and':
                return bool(left) and bool(right)
            if op == 'or':
                return bool(left) or bool(right)
            if op == '+':
                return left + right
            if op == '-':
                return left - right
            if op == '*':
                return left * right
            if op == '/':
                if right == 0:
                    raise TrishulError("Division by zero (shunya se bhag nahi hota)")
                return left / right
            if op == '%':
                if right == 0:
                    raise TrishulError("Modulo by zero (shunya se bhag nahi hota)")
                return left % right
            if op == '==':
                return left == right
            if op == '!=':
                return left != right
            if op == '<':
                return left < right
            if op == '>':
                return left > right
            if op == '<=':
                return left <= right
            if op == '>=':
                return left >= right
            raise TrishulError(f"Unsupported binary op: {op}")

        if isinstance(expr, Call):
            callee = self.eval_expr(expr.callee, env)
            if not isinstance(callee, FunctionValue):
                raise TrishulError("Only Trishul functions can be called.")
            if len(expr.args) != len(callee.params):
                raise TrishulError(f"Function {callee.name} expected {len(callee.params)} args, got {len(expr.args)}.")

            local_env = dict(callee.closure)
            for param, arg in zip(callee.params, expr.args):
                local_env[param] = self.eval_expr(arg, env)

            try:
                for stmt in callee.body:
                    self.execute_statement(stmt, local_env)
            except ReturnSignal as sig:
                return sig.value
            return None

        raise TrishulError(f"Unsupported expression node: {type(expr).__name__}")

    @staticmethod
    def is_truthy(value):
        return bool(value)


class PythonCompiler:
    def __init__(self):
        self.op_map = {
            '+': '+',
            '-': '-',
            '*': '*',
            '/': '/',
            '%': '%',
            '==': '==',
            '!=': '!=',
            '<': '<',
            '>': '>',
            '<=': '<=',
            '>=': '>=',
            'and': 'and',
            'or': 'or',
        }

    def compile_program(self, program: Program) -> str:
        lines: List[str] = []
        for stmt in program.statements:
            lines.extend(self.compile_statement(stmt, 0))
        return '\n'.join(lines) + ('\n' if lines else '')

    def compile_statement(self, stmt: Stmt, indent: int) -> List[str]:
        pad = ' ' * indent

        if isinstance(stmt, Assign):
            return [f"{pad}{stmt.name} = {self.compile_expr(stmt.value)}"]

        if isinstance(stmt, Print):
            return [f"{pad}print({self.compile_expr(stmt.expr)})"]

        if isinstance(stmt, Return):
            return [f"{pad}return {self.compile_expr(stmt.expr)}"]

        if isinstance(stmt, Break):
            return [f"{pad}break"]

        if isinstance(stmt, Continue):
            return [f"{pad}continue"]

        if isinstance(stmt, If):
            lines = [f"{pad}if {self.compile_expr(stmt.condition)}:"]
            for inner in stmt.then_body:
                lines.extend(self.compile_statement(inner, indent + 4))
            if stmt.else_body is not None:
                lines.append(f"{pad}else:")
                for inner in stmt.else_body:
                    lines.extend(self.compile_statement(inner, indent + 4))
            return lines

        if isinstance(stmt, While):
            lines = [f"{pad}while {self.compile_expr(stmt.condition)}:"]
            for inner in stmt.body:
                lines.extend(self.compile_statement(inner, indent + 4))
            return lines

        if isinstance(stmt, For):
            lines = [f"{pad}for {stmt.var} in range({self.compile_expr(stmt.start)}, {self.compile_expr(stmt.end)}, {self.compile_expr(stmt.step)}):"]
            for inner in stmt.body:
                lines.extend(self.compile_statement(inner, indent + 4))
            return lines

        if isinstance(stmt, FunctionDef):
            params = ', '.join(stmt.params)
            lines = [f"{pad}def {stmt.name}({params}):"]
            for inner in stmt.body:
                lines.extend(self.compile_statement(inner, indent + 4))
            return lines

        if isinstance(stmt, ExprStmt):
            return [f"{pad}{self.compile_expr(stmt.expr)}"]

        raise TrishulError(f"Unsupported statement for compiler: {type(stmt).__name__}")

    def compile_expr(self, expr: Any) -> str:
        if isinstance(expr, Literal):
            if expr.value is True:
                return 'True'
            if expr.value is False:
                return 'False'
            if expr.value is None:
                return 'None'
            if isinstance(expr.value, str):
                return repr(expr.value)
            return str(expr.value)

        if isinstance(expr, Name):
            return expr.name

        if isinstance(expr, Call):
            args = ', '.join(self.compile_expr(arg) for arg in expr.args)
            return f"{self.compile_expr(expr.callee)}({args})"

        if isinstance(expr, Binary):
            op = self.op_map.get(expr.op, expr.op)
            return f"({self.compile_expr(expr.left)} {op} {self.compile_expr(expr.right)})"

        if isinstance(expr, Unary):
            return f"({expr.op}{self.compile_expr(expr.operand)})"

        raise TrishulError(f"Unsupported expression for compiler: {type(expr).__name__}")


def parse_source(source: str) -> Program:
    tokens = tokenize(source)
    parser = Parser(tokens)
    program = parser.parse_program()
    if parser.current().type != "EOF":
        raise TrishulError(f"Unexpected trailing tokens: {parser.current().type}")
    return program


def run_file(path: str, max_iterations: int = 10000):
    with open(path, 'r', encoding='utf-8') as fh:
        source = fh.read()
    program = parse_source(source)
    interpreter = Interpreter(max_loop_iterations=max_iterations)
    result = interpreter.execute_program(program)
    return result


def compile_file(input_path: str, output_path: Optional[str] = None):
    with open(input_path, 'r', encoding='utf-8') as fh:
        source = fh.read()
    program = parse_source(source)
    compiled = PythonCompiler().compile_program(program)
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as fh:
            fh.write(compiled)
        return output_path
    return compiled


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Trishul — Hindi-inspired programming language with English script.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    run_parser = subparsers.add_parser('run', help='Execute a Trishul source file.')
    run_parser.add_argument('file', help='Path to the Trishul source file.')
    run_parser.add_argument('--max-iterations', type=int, default=10000, help='Maximum loop iterations (default: 10000)')

    compile_parser = subparsers.add_parser('compile', help='Compile Trishul source to Python.')
    compile_parser.add_argument('file', help='Path to the Trishul source file.')
    compile_parser.add_argument('-o', '--output', help='Optional output path for generated Python file.')

    return parser


def main(argv=None):
    args = build_cli().parse_args(argv)

    try:
        if args.command == 'run':
            run_file(args.file, max_iterations=args.max_iterations)
        elif args.command == 'compile':
            out = compile_file(args.file, args.output)
            if args.output is None:
                print(out, end='')
        else:
            raise TrishulError(f"Unknown command: {args.command}")
    except TrishulError as exc:
        print(f"Trishul error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Trishul error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
