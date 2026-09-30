#!/usr/bin/env python3

import argparse
import json
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


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
class Component:
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {"name": self.name, "properties": self.properties}


@dataclass
class Entity:
    id: str
    name: str
    state: Dict[str, Any] = field(default_factory=dict)
    components: Dict[str, Component] = field(default_factory=dict)
    active: bool = True

    def add_component(self, component: Component):
        self.components[component.name] = component

    def get_component(self, name: str):
        return self.components.get(name)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "active": self.active,
            "components": {name: comp.to_dict() for name, comp in self.components.items()},
            "state": self.state,
        }


@dataclass
class GameEvent:
    id: str
    event_type: str
    entity_id: str
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp,
            "data": self.data,
        }


class GameState:
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.events: List[GameEvent] = []
        self.global_state: Dict[str, Any] = {}

    def create_entity(self, name: str, initial_state: Optional[Dict[str, Any]] = None) -> Entity:
        entity_id = str(uuid.uuid4())
        entity = Entity(id=entity_id, name=name, state=initial_state or {})
        self.entities[entity_id] = entity
        self.events.append(
            GameEvent(
                id=str(uuid.uuid4()),
                event_type="entity_created",
                entity_id=entity_id,
                timestamp=datetime.now().timestamp(),
                data={"name": name},
            )
        )
        return entity

    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        for entity in self.entities.values():
            if entity.name == name:
                return entity
        return None

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)

    def add_component(self, entity_id: str, component_name: str, properties: Dict[str, Any]):
        entity = self.get_entity(entity_id)
        if entity is None:
            raise TrishulError(f"Entity '{entity_id}' not found")
        entity.add_component(Component(component_name, properties))
        self.events.append(
            GameEvent(
                id=str(uuid.uuid4()),
                event_type="component_added",
                entity_id=entity_id,
                timestamp=datetime.now().timestamp(),
                data={"component": component_name, "properties": properties},
            )
        )

    def update_state(self, entity_id: str, state_update: Dict[str, Any]):
        entity = self.get_entity(entity_id)
        if entity is None:
            raise TrishulError(f"Entity '{entity_id}' not found")
        entity.state.update(state_update)
        self.events.append(
            GameEvent(
                id=str(uuid.uuid4()),
                event_type="state_changed",
                entity_id=entity_id,
                timestamp=datetime.now().timestamp(),
                data=state_update,
            )
        )

    def trigger_action(self, entity_id: str, action_name: str, params: Dict[str, Any]):
        entity = self.get_entity(entity_id)
        if entity is None:
            raise TrishulError(f"Entity '{entity_id}' not found")
        self.events.append(
            GameEvent(
                id=str(uuid.uuid4()),
                event_type="action_triggered",
                entity_id=entity_id,
                timestamp=datetime.now().timestamp(),
                data={"action": action_name, "params": params},
            )
        )

    def export_json(self, out_path: str):
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "entities": {entity_id: entity.to_dict() for entity_id, entity in self.entities.items()},
                    "events": [event.to_dict() for event in self.events],
                    "global_state": self.global_state,
                },
                f,
                indent=2,
            )


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
class EntityCreate:
    name: Any
    initial_state: Optional[Dict[str, Any]]


@dataclass
class ComponentAdd:
    entity_ref: Any
    component_name: Any
    properties: Optional[Dict[str, Any]]


@dataclass
class StateUpdate:
    entity_ref: Any
    state_changes: Any


@dataclass
class ActionTrigger:
    entity_ref: Any
    action_name: Any
    params: Any


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
    "kaam": "KAAM",
    "khatam": "KHATAM",
    "wapis": "WAPIS",
    "sahi": "TRUE",
    "galat": "FALSE",
    "aur": "AND",
    "ya": "OR",
    "tod_do": "BREAK",
    "agle": "CONTINUE",
    "entity": "ENTITY",
    "banao": "CREATE",
    "component": "COMPONENT",
    "add_karo": "ADD_COMPONENT",
    "state_badlo": "UPDATE_STATE",
    "action": "ACTION",
    "trigger_karo": "TRIGGER_ACTION",
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
                        raise TrishulError("Dangling escape in string literal")
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
                raise TrishulError("Unterminated string literal")
            tokens.append(Token("STRING", value))
            continue

        if ch.isdigit() or (ch == '.' and i + 1 < len(source) and source[i + 1].isdigit()):
            start = i
            has_dot = False
            while i < len(source) and (source[i].isdigit() or source[i] == '.'):
                if source[i] == '.':
                    if has_dot:
                        break
                    has_dot = True
                i += 1
            text = source[start:i]
            try:
                value = int(text)
            except ValueError:
                value = float(text)
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

        if ch in "{}(),;:":
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
                raise TrishulError("Assignment uses 'ko ... rakho', not '='")
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

    def match(self, *types: str) -> Optional[Token]:
        if self.current().type in types:
            return self.advance()
        return None

    def expect(self, token_type: str) -> Token:
        token = self.current()
        if token.type != token_type:
            raise TrishulError(f"Expected {token_type!r}, found {token.type!r}")
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
        stmts: List[Stmt] = []
        while self.current().type != "}":
            if self.current().type == "EOF":
                raise TrishulError("Missing closing '}'")
            stmts.append(self.parse_statement())
        self.expect("}")
        return stmts

    def parse_object_literal(self) -> Dict[str, Any]:
        obj: Dict[str, Any] = {}
        self.expect("{")
        while self.current().type != "}":
            key = self.expect("IDENT").value
            self.expect(":")
            value = self.parse_expression()
            obj[key] = value
            if not self.match(","):
                break
        self.expect("}")
        return obj

    def parse_statement(self) -> Stmt:
        token = self.current()

        if token.type == "ENTITY":
            self.advance()
            self.expect("CREATE")
            name_expr = self.parse_expression()
            init_state = None
            if self.current().type == "{":
                init_state = self.parse_object_literal()
            return EntityCreate(name_expr, init_state)

        if token.type == "COMPONENT":
            self.advance()
            self.expect("ADD_COMPONENT")
            entity_ref = self.parse_expression()
            self.expect(":")
            comp_name = self.expect("IDENT").value
            props = self.parse_object_literal() if self.current().type == "{" else {}
            return ComponentAdd(entity_ref, comp_name, props)

        if token.type == "ACTION":
            self.advance()
            self.expect("TRIGGER_ACTION")
            entity_ref = self.parse_expression()
            self.expect(":")
            action_name = self.expect("IDENT").value
            params = self.parse_object_literal() if self.current().type == "{" else {}
            return ActionTrigger(entity_ref, action_name, params)

        if token.type == "UPDATE_STATE":
            self.advance()
            entity_ref = self.parse_expression()
            if self.current().type == "{":
                state_changes = self.parse_object_literal()
            else:
                state_changes = {}
            return StateUpdate(entity_ref, state_changes)

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
        if self.match("{"):
            obj: Dict[str, Any] = {}
            while self.current().type != "}":
                key = self.expect("IDENT").value
                self.expect(":")
                obj[key] = self.parse_expression()
                if not self.match(","):
                    break
            self.expect("}")
            return obj
        if self.match("("):
            expr = self.parse_expression()
            self.expect(")")
            return expr

        raise TrishulError(f"Unexpected token in expression: {token.type!r}")


class FunctionValue:
    def __init__(self, name: str, params: List[str], body: List[Stmt], closure: Dict[str, Any]):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure


class Interpreter:
    def __init__(self, game_state: GameState, max_loop_iterations: int = 10000):
        self.game_state = game_state
        self.globals: Dict[str, Any] = {}
        self.max_loop_iterations = max_loop_iterations

    def execute_program(self, program: Program):
        env = dict(self.globals)
        for stmt in program.statements:
            self.execute_statement(stmt, env)
        return env

    def execute_block(self, statements: List[Stmt], env: Dict[str, Any]):
        for stmt in statements:
            self.execute_statement(stmt, env)

    def resolve_entity_ref(self, expr: Any, env: Dict[str, Any]) -> str:
        value = self.eval_expr(expr, env)
        if isinstance(value, Entity):
            return value.id
        if isinstance(value, str):
            entity = self.game_state.get_entity_by_name(value)
            if entity:
                return entity.id
            return value
        raise TrishulError(f"Unsupported entity reference: {value!r}")

    def execute_statement(self, stmt: Stmt, env: Dict[str, Any]):
        if isinstance(stmt, EntityCreate):
            name = self.eval_expr(stmt.name, env)
            initial_state = self.eval_expr(stmt.initial_state, env) if stmt.initial_state is not None else {}
            entity = self.game_state.create_entity(name, initial_state)
            env[name] = entity
            return None

        if isinstance(stmt, ComponentAdd):
            entity_id = self.resolve_entity_ref(stmt.entity_ref, env)
            comp_name = self.eval_expr(stmt.component_name, env) if isinstance(stmt.component_name, Name) else stmt.component_name
            props = self.eval_expr(stmt.properties, env) if stmt.properties is not None else {}
            self.game_state.add_component(entity_id, comp_name, props)
            return None

        if isinstance(stmt, StateUpdate):
            entity_id = self.resolve_entity_ref(stmt.entity_ref, env)
            state_changes = self.eval_expr(stmt.state_changes, env) if stmt.state_changes is not None else {}
            self.game_state.update_state(entity_id, state_changes)
            return None

        if isinstance(stmt, ActionTrigger):
            entity_id = self.resolve_entity_ref(stmt.entity_ref, env)
            action_name = self.eval_expr(stmt.action_name, env) if isinstance(stmt.action_name, Name) else stmt.action_name
            params = self.eval_expr(stmt.params, env) if stmt.params is not None else {}
            self.game_state.trigger_action(entity_id, action_name, params)
            return None

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
                    raise LoopLimitExceeded(f"While loop exceeded maximum iterations ({self.max_loop_iterations})")
                try:
                    self.execute_block(stmt.body, env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return None

        if isinstance(stmt, FunctionDef):
            env[stmt.name] = FunctionValue(stmt.name, stmt.params, stmt.body, dict(env))
            return None

        if isinstance(stmt, ExprStmt):
            self.eval_expr(stmt.expr, env)
            return None

        raise TrishulError(f"Unsupported statement type: {type(stmt).__name__}")

    def eval_expr(self, expr: Any, env: Dict[str, Any]):
        if expr is None:
            return None

        if isinstance(expr, dict):
            return {key: self.eval_expr(value, env) for key, value in expr.items()}

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
                    raise TrishulError("Division by zero")
                return left / right
            if op == '%':
                if right == 0:
                    raise TrishulError("Modulo by zero")
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
                raise TrishulError("Only Trishul functions can be called")
            if len(expr.args) != len(callee.params):
                raise TrishulError(f"Function {callee.name} expected {len(callee.params)} args, got {len(expr.args)}")
            local_env = dict(callee.closure)
            for param, arg in zip(callee.params, expr.args):
                local_env[param] = self.eval_expr(arg, env)
            try:
                for stmt in callee.body:
                    self.execute_statement(stmt, local_env)
            except ReturnSignal as sig:
                return sig.value
            return None

        return expr

    @staticmethod
    def is_truthy(value):
        return bool(value)


def parse_source(source: str) -> Program:
    tokens = tokenize(source)
    parser = Parser(tokens)
    program = parser.parse_program()
    if parser.current().type != "EOF":
        raise TrishulError(f"Unexpected trailing tokens: {parser.current().type!r}")
    return program


def run_script(path: str, output_path: Optional[str] = None, max_iterations: int = 10000):
    with open(path, "r", encoding="utf-8") as fh:
        source = fh.read()
    program = parse_source(source)
    game_state = GameState()
    interpreter = Interpreter(game_state, max_loop_iterations=max_iterations)
    interpreter.execute_program(program)
    if output_path:
        game_state.export_json(output_path)
    return game_state


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Trishul game backend language")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Execute a Trishul game script")
    run_parser.add_argument("file", help="Path to the Trishul script")
    run_parser.add_argument("-o", "--output", help="Optional output JSON path")
    run_parser.add_argument("--max-iterations", type=int, default=10000, help="Maximum loop iterations")

    return parser


def main(argv=None):
    args = build_cli().parse_args(argv)
    try:
        if args.command == "run":
            state = run_script(args.file, args.output, args.max_iterations)
            if not args.output:
                print(json.dumps({"entities": {k: v.to_dict() for k, v in state.entities.items()}, "events": [e.to_dict() for e in state.events]}, indent=2))
        else:
            raise TrishulError(f"Unknown command: {args.command}")
    except TrishulError as exc:
        print(f"Trishul error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Trishul error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
