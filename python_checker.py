"""
PYTHON CHECKER - EASY READ VERSION (v2)

Finds problems in a Python file. For every problem it tells you:
  - WHERE it is (line number and the code itself)
  - WHY it's a problem, in plain English
  - HOW to fix it

Run from your Codespaces terminal (in the repo folder):
    python python_checker.py                               (it will ask for a file)
    python python_checker.py task_2_summer.py
    python python_checker.py task_2_summer.py --run --expected expected.txt

What it checks:
  1. Syntax check  - finds every syntax error it can, not just the first one
  2. Bug checks    - 30+ built-in checks for common mistakes (no install needed)
  3. Extra tools   - Ruff, Pylint, Mypy and Bandit, if they're installed
  4. Test run      - (optional) runs your program to catch crashes
  5. Output check  - (optional) compares what it prints with what it SHOULD print

Install the extra tools once (recommended):
    python -m pip install -r requirements.txt

Options:
    --run              run the program after checking it
    --no-run           don't run it (and don't ask)
    --expected FILE    text file with the exact output the program should print
    --inputs FILE      text file of answers to type into input(), one per line
    --timeout SECONDS  how long the test run is allowed to take
    --details          also show each tool's original message
    --save             save the report next to your file as <name>_report.txt
    --no-color         plain text, no colours
"""

from __future__ import annotations

import argparse
import ast
import builtins
import difflib
import importlib.util
import json
import keyword
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import tokenize
import warnings
from dataclasses import dataclass, field
from pathlib import Path

SEVERITIES = ["ERROR", "SECURITY", "WARNING", "STYLE", "INFO"]
WIDTH = 76


# ----------------------------------------------------------------------------
# Data + output helpers
# ----------------------------------------------------------------------------

@dataclass
class Finding:
    tool: str
    severity: str
    line: int | None
    title: str
    explanation: str
    fix: str
    original: str = ""
    family: str = ""
    col: int | None = None
    also: list[str] = field(default_factory=list)


class Report:
    COLOURS = {"ERROR": "91", "SECURITY": "95", "WARNING": "93", "STYLE": "96",
               "INFO": "37", "ok": "92", "bold": "1", "dim": "90", "head": "1;96"}

    def __init__(self, colour: bool):
        self.colour = colour
        self.lines: list[str] = []

    def say(self, text: str = "", style: str | None = None) -> None:
        self.lines.append(text)
        if self.colour and style:
            text = f"\033[{self.COLOURS.get(style, style)}m{text}\033[0m"
        print(text)

    def wrapped(self, label: str, text: str, style: str | None = None) -> None:
        prefix = f"    {label:<6}"
        body = textwrap.fill(text, WIDTH, initial_indent=prefix,
                             subsequent_indent=" " * len(prefix))
        self.say(body, style)

    def banner(self, text: str) -> None:
        self.say("")
        self.say("=" * WIDTH, "head")
        self.say(text.center(WIDTH), "head")
        self.say("=" * WIDTH, "head")

    def section(self, text: str) -> None:
        self.say("")
        self.say(text, "bold")
        self.say("-" * WIDTH, "dim")


def strip_comment(text: str) -> str:
    """Remove a trailing # comment (good enough for patching lines)."""
    if "#" not in text:
        return text
    in_quote = None
    for i, ch in enumerate(text):
        if in_quote:
            if ch == in_quote:
                in_quote = None
        elif ch in "'\"":
            in_quote = ch
        elif ch == "#":
            return text[:i]
    return text


# ----------------------------------------------------------------------------
# 1. Syntax check - finds several syntax errors by patching each one in memory
# ----------------------------------------------------------------------------

SYNTAX_HELP = [
    (r"expected ':'", "Missing colon",
     "Lines that start a block (if, elif, else, for, while, def, class, try, except, with) "
     "must end with a colon. Without it Python doesn't know the block is starting.",
     "Add a : to the end of this line."),
    (r"was never closed", "Bracket not closed",
     "A bracket ( [ or { was opened on this line but never closed, so Python thinks the "
     "line carries on forever.",
     "Add the matching ) ] or }. Count the opening and closing brackets on this line."),
    (r"unmatched '", "Extra closing bracket",
     "There's a closing bracket with no opening bracket to match it.",
     "Remove the extra bracket, or add the missing opening one."),
    (r"does not match opening parenthesis", "Brackets don't match",
     "A bracket was closed with the wrong type, e.g. ( closed with ].",
     "Make each closing bracket the same type as its opening bracket."),
    (r"unterminated string literal|EOL while scanning", "Text (string) not closed",
     "A piece of text was started with a quote, but the closing quote is missing.",
     "Add the missing ' or \" at the end of the text. Use the same type of quote at both ends."),
    (r"unterminated triple-quoted string|EOF while scanning triple", "Triple-quoted text not closed",
     "A \"\"\" or ''' block was opened but never closed, so the rest of the file is treated as text.",
     "Add the closing \"\"\" or ''' where the text should end."),
    (r"expected an indented block", "Missing indented code",
     "After a line ending in a colon, Python needs at least one indented line that belongs to it.",
     "Indent the code that belongs inside the block by 4 spaces, or write pass as a placeholder."),
    (r"unexpected indent", "Line indented too far",
     "This line is indented more than the lines around it, but it isn't inside a new block.",
     "Line it up with the code above it."),
    (r"unindent does not match", "Indentation doesn't line up",
     "This line's indentation doesn't match any of the lines above it.",
     "Use exactly 4 spaces per level and line it up with the block it belongs to."),
    (r"inconsistent use of tabs", "Tabs and spaces mixed",
     "The file mixes tab characters and spaces for indentation. They look the same but Python "
     "treats them differently.",
     "Use spaces only. In VS Code: Command Palette > 'Convert Indentation to Spaces'."),
    (r"Maybe you meant '==' or ':='|invalid syntax. Maybe you meant '=='", "Used = instead of ==",
     "A single = STORES a value. To COMPARE two values you need ==.",
     "Change = to == in this condition."),
    (r"Perhaps you forgot a comma", "Missing comma",
     "Python found two values next to each other with nothing between them.",
     "Add a comma between the items."),
    (r"Missing parentheses in call to 'print'", "print needs brackets",
     "In Python 3, print is a function, so it needs brackets.",
     "Write print(\"text\") instead of print \"text\"."),
    (r"invalid character", "Strange character",
     "The line has a character Python doesn't understand. Often it's a curly quote “ ” ‘ ’ or a "
     "long dash copied from Word or a website.",
     "Retype the quotes and symbols on this line in the code editor."),
    (r"invalid decimal literal", "Number in the wrong place",
     "A name starts with a digit, or a number is touching a name, e.g. 2nd_place or 5x.",
     "Names can't start with a number. Rename it, or add the missing operator, e.g. 5 * x."),
    (r"'return' outside function", "return outside a function",
     "return can only be used inside a def.",
     "Indent it into the function it belongs to, or remove it."),
    (r"'break' outside loop|'continue' not properly in loop", "break/continue outside a loop",
     "break and continue only work inside a for or while loop.",
     "Check the indentation so it's inside the loop, or remove it."),
    (r"cannot assign to", "Can't store a value there",
     "The left side of = must be a variable name, not a value or a calculation.",
     "Put the variable on the left: total = a + b (not a + b = total)."),
    (r"f-string", "Problem inside an f-string",
     "Something inside the { } of an f-string is wrong.",
     "Check the brackets and quotes inside the { }. Use different quotes inside the { } than "
     "around the whole string."),
    (r"invalid syntax", "Invalid syntax",
     "Python couldn't understand this line.",
     "Look for a missing bracket, quote, colon, comma or operator on this line or the line before."),
]

BLOCK_START = re.compile(
    r"^\s*(async\s+)?(def|class|if|elif|else|for|while|try|except|finally|with|match|case)\b")


def explain_syntax(exc: SyntaxError) -> Finding:
    msg = exc.msg or "invalid syntax"
    for pattern, title, why, fix in SYNTAX_HELP:
        if re.search(pattern, msg):
            break
    else:
        title, why, fix = "Syntax error", "Python couldn't understand this line.", \
            "Check brackets, quotes, colons and indentation on this line and the one before."
    return Finding("Python", "ERROR", exc.lineno, title, f'{why} (Python says: "{msg}")', fix,
                   original=f"SyntaxError: {msg}", family="syntax", col=exc.offset)


def patch_line(lines: list[str], lineno: int, msg: str) -> None:
    """Change one line (in memory only) so checking can carry on past it."""
    i = lineno - 1
    text = lines[i]
    indent = text[: len(text) - len(text.lstrip())]
    if "expected ':'" in msg and BLOCK_START.match(text):
        lines[i] = strip_comment(text).rstrip() + ":"
        return
    m = re.search(r"on line (\d+)", msg)
    if "expected an indented block" in msg and m:
        j = int(m.group(1)) - 1
        lines[j] = strip_comment(lines[j]).rstrip() + " pass"
        return
    if "unexpected indent" in msg or "unindent" in msg:
        current = len(indent)
        best = 0
        for prev in reversed(lines[:i]):
            if prev.strip() and not prev.lstrip().startswith("#"):
                width = len(prev) - len(prev.lstrip())
                if width <= current:
                    best = width
                    break
        lines[i] = " " * best + text.lstrip()
        return
    if strip_comment(text).rstrip().endswith(":") or BLOCK_START.match(text):
        lines[i] = indent + "if True:"   # keeps the indented block below it valid
    else:
        lines[i] = indent + "pass"


def find_syntax_errors(source: str, filename: str) -> tuple[list[Finding], str | None]:
    """Return (syntax findings, source that parses or None)."""
    lines = source.splitlines()
    findings: list[Finding] = []
    tried: set[tuple[int, str]] = set()
    for _ in range(30):
        text = "\n".join(lines) + "\n"
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                compile(text, filename, "exec", dont_inherit=True)
            return findings, text
        except SyntaxError as exc:
            lineno = exc.lineno or 1
            finding = explain_syntax(exc)
            if findings:
                finding.explanation += (" Note: this might be a knock-on effect of an earlier "
                                        "error - fix the first one, then check again.")
            key = (lineno, exc.msg)
            if key in tried or not 1 <= lineno <= len(lines):
                return findings, None
            findings.append(finding)
            tried.add(key)
            patch_line(lines, lineno, exc.msg or "")
    return findings, None


# ----------------------------------------------------------------------------
# 2. Built-in bug checks (plain-English explanations for common mistakes)
# ----------------------------------------------------------------------------

BUILTIN_NAMES = set(dir(builtins)) | {
    "__name__", "__file__", "__doc__", "__builtins__", "__spec__", "__loader__",
    "__package__", "__annotations__", "__dict__", "__class__", "__qualname__", "__module__"}
SHADOW_RISK = {"list", "dict", "str", "int", "float", "bool", "set", "tuple", "input", "print",
               "len", "sum", "max", "min", "sorted", "range", "open", "type", "round", "abs",
               "any", "all", "map", "filter", "zip", "format", "next", "iter", "object"}
TEXT_METHODS = {"strip", "lower", "upper", "title", "capitalize", "lstrip", "rstrip", "casefold"}
NUMBER_FUNCS = {"len", "sum", "int", "float", "round", "abs"}
IN_PLACE_METHODS = {"sort", "append", "extend", "insert", "reverse", "clear"}
THROWAWAY_METHODS = {"upper", "lower", "strip", "lstrip", "rstrip", "title", "capitalize",
                     "casefold", "split", "join", "zfill", "center", "ljust", "rjust"}
FIELD_RE = re.compile(r"(?<!\{)\{\s*([A-Za-z_]\w*)(?:[.\[][^{}]*)?\s*(?:![rsa])?(?::[^{}]*)?\}(?!\})")
EXTERNAL_DATA_MODULES = {"json", "csv", "requests", "sqlite3", "flask", "pandas", "yaml",
                         "tomllib", "configparser", "urllib", "http", "django", "pymongo"}
STOP_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)


def is_num(node: ast.AST) -> bool:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        node = node.operand
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
        and not isinstance(node.value, bool)


def is_text(node: ast.AST) -> bool:
    return isinstance(node, ast.JoinedStr) or (
        isinstance(node, ast.Constant) and isinstance(node.value, str))


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


class Analyzer:
    def __init__(self, tree: ast.Module, source: str):
        self.tree = tree
        self.source = source
        self.findings: list[Finding] = []
        self.parents: dict[ast.AST, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                self.parents[child] = node
        self.all_nodes = list(ast.walk(tree))
        self._collect_names()

    # ---- helpers ---------------------------------------------------------
    def add(self, severity, where, title, why, fix, family=""):
        line = where if isinstance(where, int) or where is None else getattr(where, "lineno", None)
        self.findings.append(Finding("Bug check", severity, line, title, why, fix, family=family))

    def src(self, node: ast.AST) -> str:
        text = ast.get_source_segment(self.source, node) or "..."
        text = " ".join(text.split())
        return text if len(text) <= 50 else text[:47] + "..."

    @staticmethod
    def walk_body(stmts):
        """Walk statements without going into nested functions/classes."""
        stack = list(stmts)
        while stack:
            node = stack.pop()
            yield node
            for child in ast.iter_child_nodes(node):
                if not isinstance(child, STOP_NODES):
                    stack.append(child)

    def is_input_call(self, node) -> bool:
        while (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and node.func.attr in TEXT_METHODS):
            node = node.func.value
        return call_name(node) == "input"

    def is_input_value(self, node) -> bool:
        return self.is_input_call(node) or (
            isinstance(node, ast.Name) and node.id in self.input_names)

    def is_number_value(self, node) -> bool:
        return is_num(node) or call_name(node) in NUMBER_FUNCS or (
            isinstance(node, ast.Name) and node.id in self.number_names)

    def kind_of(self, value) -> str:
        if self.is_input_call(value):
            return "input"
        if self.is_number_value(value) and not isinstance(value, ast.Name):
            return "num"
        return "other"

    def _collect_names(self) -> None:
        self.defined = set(BUILTIN_NAMES)
        self.star_import = False
        self.imports: set[str] = set()
        store_count: dict[str, int] = {}
        kinds: dict[str, list[str]] = {}
        self.format_receivers: set[str] = set()
        self.referenced: set[str] = set()
        self.input_names: set[str] = set()
        self.number_names: set[str] = set()

        for node in self.all_nodes:
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, (ast.Store, ast.Del)):
                    self.defined.add(node.id)
                    store_count[node.id] = store_count.get(node.id, 0) + 1
                else:
                    self.referenced.add(node.id)
            elif isinstance(node, ast.arg):
                self.defined.add(node.arg)
                store_count[node.arg] = store_count.get(node.arg, 0) + 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.defined.add(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom) and node.module:
                    self.imports.add(node.module.split(".")[0])
                for alias in node.names:
                    if alias.name == "*":
                        self.star_import = True
                    else:
                        self.defined.add(alias.asname or alias.name.split(".")[0])
                        if isinstance(node, ast.Import):
                            self.imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ExceptHandler) and node.name:
                self.defined.add(node.name)
            elif isinstance(node, (ast.Global, ast.Nonlocal)):
                self.defined.update(node.names)
            elif isinstance(node, ast.Attribute):
                self.referenced.add(node.attr)
                if node.attr in ("format", "format_map") and isinstance(node.value, ast.Name):
                    self.format_receivers.add(node.value.id)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                self.referenced.add(node.value)
            for attr in ("name", "rest"):  # match/case patterns
                if type(node).__name__ in ("MatchAs", "MatchStar", "MatchMapping"):
                    value = getattr(node, attr, None)
                    if isinstance(value, str):
                        self.defined.add(value)

            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        if isinstance(node, ast.AugAssign):
                            kind = "num" if self.kind_of(node.value) == "num" else "other"
                        elif node.value is None:
                            kind = "other"
                        else:
                            kind = self.kind_of(node.value) if is_num(node.value) or \
                                self.is_input_call(node.value) or call_name(node.value) in NUMBER_FUNCS \
                                else "other"
                        kinds.setdefault(target.id, []).append(kind)

        self.input_names = {n for n, k in kinds.items()
                            if len(k) == store_count.get(n, 0) and set(k) == {"input"}}
        self.number_names = {n for n, k in kinds.items()
                             if len(k) == store_count.get(n, 0) and set(k) == {"num"}}
        self.user_defined = self.defined - BUILTIN_NAMES

        self.module_funcs: dict[str, ast.FunctionDef] = {}
        for node in self.tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in self.module_funcs:
                    first = self.module_funcs[node.name].lineno
                    self.add("WARNING", node, f"Function '{node.name}' is defined twice",
                             f"'{node.name}' was already defined on line {first}. The second "
                             "definition silently replaces the first, so the first one never runs.",
                             "Rename one of them, or delete the one you don't need.", "redefined")
                self.module_funcs[node.name] = node
        self.funcs = {n: f for n, f in self.module_funcs.items() if n not in store_count}
        self.returns_value = {}
        for name, fn in self.funcs.items():
            self.returns_value[name] = any(
                (isinstance(n, ast.Return) and n.value is not None
                 and not (isinstance(n.value, ast.Constant) and n.value.value is None))
                or isinstance(n, (ast.Yield, ast.YieldFrom))
                for n in self.walk_body(fn.body))

    # ---- run all checks --------------------------------------------------
    def run(self) -> list[Finding]:
        checks = [self.check_undefined, self.check_compares, self.check_uncalled_functions,
                  self.check_missing_f, self.check_loops, self.check_unreachable,
                  self.check_running_totals, self.check_while_loops, self.check_arguments,
                  self.check_no_return, self.check_in_place_methods, self.check_indexes,
                  self.check_dict_keys, self.check_shadowing, self.check_exceptions,
                  self.check_defaults, self.check_statements, self.check_or_conditions,
                  self.check_text_and_numbers, self.check_input_conversion,
                  self.check_unused_functions]
        for check in checks:
            try:
                check()
            except Exception as exc:  # one broken check shouldn't stop the others
                self.add("INFO", None, f"Internal check '{check.__name__}' skipped",
                         f"The checker hit a problem of its own: {exc}", "Nothing to fix in your code.")
        return self.findings

    # ---- individual checks -----------------------------------------------
    def check_undefined(self):
        if self.star_import:
            return
        seen: dict[str, list[int]] = {}
        for node in self.all_nodes:
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) \
                    and node.id not in self.defined:
                seen.setdefault(node.id, []).append(node.lineno)
        candidates = list(self.user_defined) + ["print", "input", "len", "range", "int", "str",
                                                "float", "list", "dict", "round", "sum", "max",
                                                "min", "sorted", "open", "append"]
        for name, lines in seen.items():
            fixed = {"true": "True", "false": "False", "none": "None", "null": "None"}
            guess = fixed.get(name.lower()) or next(iter(difflib.get_close_matches(
                name, candidates, n=1, cutoff=0.75)), None)
            others = f" It's also used on line(s) {', '.join(map(str, lines[1:]))}." \
                if len(lines) > 1 else ""
            hint = f" Did you mean '{guess}'?" if guess else ""
            self.add("ERROR", lines[0], f"'{name}' is not defined",
                     f"Python doesn't know anything called '{name}'. It's never created in this "
                     f"file, so this line will crash with a NameError.{others}",
                     f"Check the spelling (capitals matter).{hint} If it's a variable, give it a "
                     "value before this line. If it's from a module, import it at the top.",
                     "undefined")

    def check_compares(self):
        for node in self.all_nodes:
            if not isinstance(node, ast.Compare):
                continue
            left = node.left
            for op, right in zip(node.ops, node.comparators):
                if isinstance(op, (ast.Eq, ast.NotEq)):
                    for side in (left, right):
                        if isinstance(side, ast.Constant) and side.value is None:
                            word = "is" if isinstance(op, ast.Eq) else "is not"
                            self.add("STYLE", node, "Use 'is None' to check for None",
                                     "None is a special single value, so Python style is to "
                                     "check it with 'is' rather than ==.",
                                     f"Write '{word} None' instead.", "none-compare")
                        elif isinstance(side, ast.Constant) and isinstance(side.value, bool):
                            self.add("STYLE", node, "No need to compare with True/False",
                                     "'if x == True:' does the same thing as 'if x:'.",
                                     "Write 'if x:' or 'if not x:' instead.", "bool-compare")
                if isinstance(op, (ast.Is, ast.IsNot)):
                    for side in (left, right):
                        if isinstance(side, ast.Constant) and isinstance(
                                side.value, (str, int, float, bytes)) and not isinstance(side.value, bool):
                            self.add("WARNING", node, "Using 'is' to compare values",
                                     "'is' checks whether two things are the exact same object in "
                                     "memory, not whether they're equal. It can give False even "
                                     "when the values match.",
                                     "Use == (or !=) to compare values.", "is-literal")
                if (self.is_input_value(left) and self.is_number_value(right)) or \
                        (self.is_input_value(right) and self.is_number_value(left)):
                    text_side = left if self.is_input_value(left) else right
                    name = self.src(text_side)
                    if isinstance(op, (ast.Lt, ast.Gt, ast.LtE, ast.GtE)):
                        self.add("ERROR", node, "Comparing text from input() with a number",
                                 f"input() always gives back text (a string), so {name} is text "
                                 "like \"5\", not the number 5. Python can't tell if text is "
                                 "bigger or smaller than a number, so this crashes with a TypeError.",
                                 f"Convert it to a number when you read it, e.g. "
                                 f"{name} = int(input(...)) - or float(...) for decimals.", "type-mix")
                    elif isinstance(op, (ast.Eq, ast.NotEq)):
                        self.add("ERROR", node, "Text from input() will never equal a number",
                                 f"input() gives back text, so {name} could be \"5\" but never the "
                                 "number 5. This comparison is always False (or always True with !=).",
                                 "Convert with int(...) first, or compare with text, e.g. == \"5\".",
                                 "type-mix")
                left = right

    def check_uncalled_functions(self):
        for node in self.all_nodes:
            if not (isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
                    and node.id in self.funcs):
                continue
            parent = self.parents.get(node)
            name = node.id
            problem = None
            if isinstance(parent, (ast.BinOp, ast.UnaryOp)):
                problem = "calc"
            elif isinstance(parent, ast.Compare) and not all(
                    isinstance(o, (ast.Is, ast.IsNot)) for o in parent.ops):
                problem = "calc"
            elif isinstance(parent, ast.FormattedValue):
                problem = "show"
            elif isinstance(parent, ast.Call) and node in parent.args and call_name(parent) in (
                    "print", "str", "int", "float", "len", "round"):
                problem = "show"
            elif isinstance(parent, (ast.If, ast.While, ast.IfExp)) and parent.test is node:
                problem = "test"
            elif isinstance(parent, ast.Subscript) and parent.value is node:
                problem = "calc"
            elif isinstance(parent, ast.Expr):
                problem = "statement"
            if problem is None:
                continue
            why = {
                "calc": f"'{name}' is a function. Without () Python uses the function itself, not "
                        "the answer it works out, so this calculation will crash with a TypeError.",
                "show": f"'{name}' is a function. Without () Python shows something like "
                        f"<function {name} at 0x...> instead of the answer.",
                "test": f"'{name}' is a function. A function on its own always counts as True, so "
                        "this condition is always True and never actually runs the function.",
                "statement": f"This line names the function '{name}' but doesn't run it, so "
                             "nothing happens.",
            }[problem]
            family = {"test": "constant-test", "statement": "pointless"}.get(problem, "uncalled")
            self.add("ERROR" if problem in ("calc", "statement") else "WARNING", node,
                     f"Function '{name}' used without brackets ()", why,
                     f"Add brackets to run it: {name}()", family)

    def check_missing_f(self):
        for node in self.all_nodes:
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            parent = self.parents.get(node)
            if isinstance(parent, (ast.JoinedStr, ast.Expr)):
                continue
            if isinstance(parent, ast.Attribute) and parent.attr in ("format", "format_map"):
                continue
            if isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Mod):
                continue
            if isinstance(parent, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id in self.format_receivers for t in parent.targets):
                continue
            match = FIELD_RE.search(node.value)
            if match and match.group(1) in self.user_defined and not keyword.iskeyword(match.group(1)):
                self.add("WARNING", node, "Missing f before the string",
                         f"This text contains {{{match.group(1)}}}, which looks like it should "
                         f"show the value of {match.group(1)}. Without an f in front of the "
                         "opening quote, Python prints the curly brackets and the name exactly "
                         "as typed.",
                         "Put an f straight before the opening quote, e.g. f\"Total: {total}\".",
                         "missing-f")

    def check_loops(self):
        for node in self.all_nodes:
            if not isinstance(node, (ast.For, ast.AsyncFor, ast.While)) or not node.body:
                continue
            last = node.body[-1]
            if not isinstance(last, (ast.Return, ast.Break)):
                continue
            if any(isinstance(n, ast.Continue) for n in self.walk_body(node.body)):
                continue
            word = "return" if isinstance(last, ast.Return) else "break"
            loop = "for" if isinstance(node, (ast.For, ast.AsyncFor)) else "while"
            extra = ""
            if isinstance(last, ast.Return) and any(
                    isinstance(n, ast.If) and any(isinstance(m, ast.Return) for m in ast.walk(n))
                    for n in node.body[:-1]):
                extra = (" This usually happens when a 'return' that should come AFTER the loop "
                         "has been indented one level too far.")
            self.add("WARNING", last, "Loop stops after the first time round",
                     f"The {word} on line {last.lineno} is part of the loop body, so it runs on the "
                     f"very first pass. The loop never gets to the second item.{extra}",
                     f"If it should only happen once the loop has finished, un-indent line "
                     f"{last.lineno} so it lines up with the '{loop}' on line {node.lineno}.",
                     "loop-once")

    def check_unreachable(self):
        for node in self.all_nodes:
            for name in ("body", "orelse", "finalbody"):
                stmts = getattr(node, name, None)
                if not isinstance(stmts, list):
                    continue
                for first, second in zip(stmts, stmts[1:]):
                    if isinstance(first, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                        word = type(first).__name__.lower()
                        self.add("WARNING", second, "Code that can never run",
                                 f"Line {first.lineno} uses '{word}', which leaves this block "
                                 "straight away, so this line is never reached.",
                                 f"Move this code above line {first.lineno}, or check its "
                                 "indentation. Delete it if it isn't needed.", "unreachable")
                        break

    def _inside_if_about(self, node, name, stop) -> bool:
        current = self.parents.get(node)
        while current is not None and current is not stop:
            if isinstance(current, ast.If) and any(
                    isinstance(n, ast.Name) and n.id == name for n in ast.walk(current.test)):
                return True
            current = self.parents.get(current)
        return False

    def check_running_totals(self):
        reported = set()
        for node in self.all_nodes:
            for fieldname in ("body", "orelse", "finalbody"):
                stmts = getattr(node, fieldname, None)
                if not isinstance(stmts, list):
                    continue
                starts: dict[str, tuple[int, str]] = {}
                for stmt in stmts:
                    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                            and isinstance(stmt.targets[0], ast.Name):
                        value = stmt.value
                        if (isinstance(value, ast.Constant) and value.value in (0, "")
                                and not isinstance(value.value, bool)) or (
                                isinstance(value, ast.List) and not value.elts):
                            starts[stmt.targets[0].id] = (stmt.lineno, self.src(value))
                    elif isinstance(stmt, (ast.For, ast.While)):
                        for inner in self.walk_body(stmt.body):
                            if not (isinstance(inner, ast.Assign) and len(inner.targets) == 1
                                    and isinstance(inner.targets[0], ast.Name)):
                                continue
                            name = inner.targets[0].id
                            if name not in starts or (name, inner.lineno) in reported:
                                continue
                            if any(isinstance(n, ast.Name) and n.id == name
                                   for n in ast.walk(inner.value)):
                                continue
                            if self._inside_if_about(inner, name, stmt):
                                continue
                            siblings = next((getattr(p, f) for p in [self.parents.get(inner)]
                                             for f in ("body", "orelse")
                                             if inner in (getattr(p, f, None) or [])), [])
                            if any(isinstance(n, ast.Break) for n in siblings):
                                continue
                            reported.add((name, inner.lineno))
                            line, start = starts[name]
                            if start == "[]":
                                fix = f"To add to the list use {name}.append(...) instead."
                            else:
                                fix = (f"To keep a running total use {name} += ... instead "
                                       f"of {name} = ...")
                            self.add("WARNING", inner, f"'{name}' is replaced instead of added to",
                                     f"'{name}' starts as {start} on line {line}, but inside the "
                                     f"loop this line replaces it with '=' each time round. After "
                                     "the loop it will only hold the LAST value, not the total.",
                                     fix, "overwrite")

    def _is_exit_call(self, node) -> bool:
        if call_name(node) in ("exit", "quit"):
            return True
        return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr in ("exit", "_exit")

    def check_while_loops(self):
        for node in self.all_nodes:
            if not isinstance(node, ast.While):
                continue
            body = list(self.walk_body(node.body))
            leaves = any(isinstance(n, (ast.Break, ast.Return, ast.Raise)) or self._is_exit_call(n)
                         for n in body)
            if leaves:
                continue
            if isinstance(node.test, ast.Constant) and node.test.value:
                self.add("WARNING", node, "Loop never ends",
                         "'while True' keeps going forever unless something inside it uses "
                         "break, return or exits the program - and nothing in this loop does.",
                         "Add a break (usually inside an if) for when the loop should stop.",
                         "infinite")
                continue
            names = {n.id for n in ast.walk(node.test)
                     if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
            if not names or any(isinstance(n, (ast.Call, ast.Attribute, ast.Subscript))
                                for n in ast.walk(node.test)):
                continue
            changed = any(
                (isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id in names)
                or (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                    and n.value.id in names)
                or (isinstance(n, (ast.Global, ast.Nonlocal)))
                for n in body)
            if not changed:
                shown = ", ".join(sorted(names))
                example = sorted(names)[0]
                self.add("WARNING", node, "Loop condition never changes",
                         f"The loop keeps going while '{self.src(node.test)}' is true, but nothing "
                         f"inside the loop changes {shown}. If it's true once, it stays true "
                         "forever and the program freezes.",
                         f"Update {example} inside the loop (e.g. {example} += 1 or a new "
                         "input()), or add a break.", "infinite")

    def check_arguments(self):
        for node in self.all_nodes:
            name = call_name(node)
            if name not in self.funcs:
                continue
            fn = self.funcs[name]
            if fn.decorator_list or any(isinstance(a, ast.Starred) for a in node.args) \
                    or any(k.arg is None for k in node.keywords):
                continue
            a = fn.args
            params = [p.arg for p in a.posonlyargs + a.args]
            kwonly = [p.arg for p in a.kwonlyargs]
            required = params[: len(params) - len(a.defaults)]
            given_pos = len(node.args)
            given_kw = [k.arg for k in node.keywords]
            problems = []
            if a.vararg is None and given_pos > len(params):
                problems.append(f"it's given {given_pos} value(s) but only takes {len(params)}")
            given = set(params[:given_pos]) | set(given_kw)
            missing = [p for p in required if p not in given]
            missing += [p.arg for p, d in zip(a.kwonlyargs, a.kw_defaults)
                        if d is None and p.arg not in given_kw]
            if missing:
                problems.append("it's missing a value for " + ", ".join(missing))
            if a.kwarg is None:
                unknown = [k for k in given_kw if k not in params and k not in kwonly]
                if unknown:
                    problems.append("it doesn't have a parameter called " + ", ".join(unknown))
            if problems:
                self.add("ERROR", node, f"Wrong values passed to {name}()",
                         f"{name}() is defined on line {fn.lineno} as {name}({', '.join(params + kwonly)}), "
                         f"but here {' and '.join(problems)}. This crashes with a TypeError.",
                         "Pass one value for each parameter, in the same order as the def line "
                         "- or change the def line if it needs different parameters.", "args")

    def check_no_return(self):
        for node in self.all_nodes:
            name = call_name(node)
            if name not in self.funcs or self.returns_value.get(name, True) \
                    or self.funcs[name].decorator_list:
                continue
            parent = self.parents.get(node)
            used = (isinstance(parent, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Return))
                    and parent.value is node) or isinstance(
                parent, (ast.BinOp, ast.Compare, ast.FormattedValue)) or (
                isinstance(parent, ast.Call) and call_name(parent) == "print" and node in parent.args)
            if used:
                self.add("WARNING", node, f"Using the answer from {name}(), which doesn't return one",
                         f"{name}() has no 'return <value>' line, so it gives back None. Using its "
                         "result here gives None (it might print 'None', or crash in a calculation). "
                         "A common cause is a function that print()s its answer instead of "
                         "returning it.",
                         f"Add 'return <value>' at the end of {name}(), or just call {name}() on "
                         "its own line.", "no-return")

    def check_in_place_methods(self):
        for node in self.all_nodes:
            if not isinstance(node, (ast.Assign, ast.Return)) or node.value is None:
                continue
            value = node.value
            if call_name(value) == "print":
                self.add("WARNING", node, "Storing the result of print()",
                         "print() shows text on screen but gives back None, so this stores None.",
                         "Store the text in the variable first, then print the variable.",
                         "no-return")
                continue
            if not (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)):
                continue
            method = value.func.attr
            obj = self.src(value.func.value)
            if method in IN_PLACE_METHODS or (method == "shuffle" and obj == "random"):
                fix = f"Call it on its own line ({self.src(value)}), then use the list itself."
                if method == "sort":
                    fix += f" For a sorted copy instead, use sorted({obj})."
                self.add("WARNING", node, f".{method}() gives back None",
                         f".{method}() changes the list in place and gives back None. So this "
                         "line stores (or returns) None, not the list.", fix, "no-return")

    def check_indexes(self):
        for node in self.all_nodes:
            if isinstance(node, ast.Subscript):
                index = node.slice
                if call_name(index) == "len" and len(index.args) == 1 and \
                        ast.dump(index.args[0]) == ast.dump(node.value):
                    obj = self.src(node.value)
                    self.add("ERROR", node, "Index is one too big",
                             f"Positions start at 0, so the last item of {obj} is at "
                             f"len({obj}) - 1. Using len({obj}) goes past the end and crashes "
                             "with an IndexError.",
                             f"Use {obj}[-1] for the last item, or {obj}[len({obj}) - 1].", "index")
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) \
                    and isinstance(node.right, ast.Constant) and node.right.value == 0:
                self.add("ERROR", node, "Dividing by zero",
                         "Dividing by 0 is impossible, so this crashes with a ZeroDivisionError.",
                         "Check the number you're dividing by.", "zero")
            if isinstance(node, ast.For) and isinstance(node.target, ast.Name) \
                    and call_name(node.iter) == "range":
                var = node.target.id
                args = node.iter.args
                indexed = {ast.dump(n.value): n for n in self.walk_body(node.body)
                           if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Name)
                           and n.slice.id == var}
                if len(args) == 1 and isinstance(args[0], ast.BinOp) and isinstance(args[0].op, ast.Add) \
                        and call_name(args[0].left) == "len" and is_num(args[0].right) \
                        and args[0].left.args and ast.dump(args[0].left.args[0]) in indexed:
                    obj = self.src(args[0].left.args[0])
                    self.add("ERROR", node, "Loop goes one past the end of the list",
                             f"range(len({obj}) + 1) goes up to len({obj}), but the last position "
                             f"is len({obj}) - 1. The final {obj}[{var}] crashes with an IndexError.",
                             f"Use range(len({obj})).", "index")
                if len(args) >= 2 and is_num(args[0]) and args[0].value == 1 \
                        and call_name(args[1]) == "len" and args[1].args \
                        and ast.dump(args[1].args[0]) in indexed:
                    obj = self.src(args[1].args[0])
                    self.add("WARNING", node, "Loop skips the first item",
                             f"range(1, len({obj})) starts at 1, but the first item in a list is "
                             f"at position 0, so {obj}[0] is never looked at.",
                             f"Use range(len({obj})), or better: for item in {obj}:", "index")

    def check_dict_keys(self):
        if self.imports & EXTERNAL_DATA_MODULES:
            return
        writes, reads, dynamic = set(), {}, False
        for node in self.all_nodes:
            if isinstance(node, ast.Dict):
                writes.update(k.value for k in node.keys
                              if isinstance(k, ast.Constant) and isinstance(k.value, str))
            elif isinstance(node, ast.Subscript):
                key = node.slice
                if isinstance(node.ctx, (ast.Store, ast.Del)):
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        writes.add(key.value)
                    else:
                        dynamic = True
                elif isinstance(key, ast.Constant) and isinstance(key.value, str):
                    if isinstance(node.value, ast.Attribute) and node.value.attr in ("environ", "modules"):
                        continue
                    reads.setdefault(key.value, []).append(node.lineno)
            elif isinstance(node, ast.Call):
                if call_name(node) == "dict":
                    writes.update(k.arg for k in node.keywords if k.arg)
                if isinstance(node.func, ast.Attribute) and node.func.attr in ("setdefault", "update"):
                    writes.update(k.arg for k in node.keywords if k.arg)
                    if node.args and isinstance(node.args[0], ast.Constant):
                        writes.add(node.args[0].value)
                    if node.args and not isinstance(node.args[0], (ast.Constant, ast.Dict)):
                        dynamic = True
                if call_name(node) in ("zip", "fromkeys"):
                    dynamic = True
        if not writes or dynamic:
            return
        for key, lines in reads.items():
            if key in writes:
                continue
            guess = difflib.get_close_matches(key, list(writes), n=1, cutoff=0.3)
            hint = f" The closest key that does exist is '{guess[0]}' - is one of them a typo?" \
                if guess else ""
            where = f" (line {', '.join(map(str, sorted(set(lines))))})"
            self.add("ERROR", lines[0], f"Dictionary key '{key}' is never created",
                     f"The code looks up ['{key}']{where}, but no dictionary in this file is "
                     f"ever given a '{key}' key, so this will crash with a KeyError.{hint}",
                     "Use exactly the same key name (spelling and capitals) everywhere: where the "
                     "dictionary is made and where it's read.", "key")

    def check_shadowing(self):
        seen = set()
        for node in self.all_nodes:
            name = None
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                name = node.id
            elif isinstance(node, ast.arg):
                name = node.arg
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                name = node.name
            if name in SHADOW_RISK and name not in seen:
                seen.add(name)
                self.add("WARNING", node, f"'{name}' hides a built-in Python function",
                         f"'{name}' is already a built-in Python function. Using it as your own "
                         f"name means the real {name}() stops working in this part of the code, "
                         "which causes confusing errors later.",
                         f"Rename it to something more descriptive, e.g. my_{name} or "
                         f"{name}_value.", "shadow")

    def check_exceptions(self):
        for node in self.all_nodes:
            if not isinstance(node, ast.ExceptHandler):
                continue
            if node.type is None:
                self.add("WARNING", node, "Bare 'except:' catches every error",
                         "This catches almost every error - including typos in your own code and "
                         "even Ctrl+C - so real bugs get hidden.",
                         "Catch the specific error you expect, e.g. 'except ValueError:'.",
                         "bare-except")
            if all(isinstance(s, (ast.Pass, ast.Continue)) or (
                    isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)) for s in node.body):
                self.add("WARNING", node, "Errors are silently ignored",
                         "When an error happens here, the program carries on without telling "
                         "anyone, which makes bugs very hard to find.",
                         "At least print a message, e.g. print(\"Please enter a number\").",
                         "swallow")

    def check_defaults(self):
        for node in self.all_nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                    isinstance(d, (ast.List, ast.Dict, ast.Set)) for d in node.args.defaults):
                self.add("WARNING", node, f"'{node.name}' has a list/dict as a default value",
                         "The default list or dictionary is created ONCE and shared by every "
                         "call, so items from one call leak into the next.",
                         "Use None as the default, then inside: if items is None: items = []",
                         "mutable-default")

    def check_statements(self):
        for node in self.all_nodes:
            if not isinstance(node, ast.Expr):
                continue
            value = node.value
            if isinstance(value, ast.Compare) and isinstance(value.ops[0], ast.Eq):
                self.add("ERROR", node, "Comparison that does nothing",
                         "This line checks whether two things are equal, then throws the answer "
                         "away. You probably meant to STORE a value, which uses a single =.",
                         f"Use = to store a value: {self.src(value.left)} = "
                         f"{self.src(value.comparators[0])}", "pointless")
            elif isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute) \
                    and value.func.attr in THROWAWAY_METHODS:
                obj = self.src(value.func.value)
                self.add("WARNING", node, f"Result of .{value.func.attr}() is thrown away",
                         "Text (strings) can't be changed in place. "
                         f".{value.func.attr}() gives back a NEW value, but this line doesn't "
                         f"store it, so {obj} is unchanged.",
                         f"Store the result, e.g. {obj} = {self.src(value)}", "pointless")
            elif call_name(value) == "sorted":
                self.add("WARNING", node, "Result of sorted() is thrown away",
                         "sorted() gives back a NEW sorted list but this line doesn't store it, so "
                         "the original list is unchanged.",
                         "Store it (my_list = sorted(my_list)) or sort in place (my_list.sort()).",
                         "pointless")

    def check_or_conditions(self):
        for node in self.all_nodes:
            if not (isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or)):
                continue
            compares = [v for v in node.values if isinstance(v, ast.Compare)
                        and isinstance(v.ops[0], (ast.Eq, ast.NotEq))]
            constants = [v for v in node.values if isinstance(v, ast.Constant) and v.value]
            if compares and constants:
                var = self.src(compares[0].left)
                values = [self.src(compares[0].comparators[0])] + [self.src(c) for c in constants]
                self.add("ERROR", node, "Condition is always True",
                         f"Python reads this as ({self.src(compares[0])}) or ({values[1]}). A "
                         f"non-empty value like {values[1]} on its own always counts as True, so "
                         f"this doesn't check {var} against it at all.",
                         f"Repeat the comparison: {var} == {values[0]} or {var} == {values[1]} - "
                         f"or use: {var} in ({', '.join(values)})", "constant-test")

    def check_text_and_numbers(self):
        for node in self.all_nodes:
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                pairs = [(node.left, node.right), (node.right, node.left)]
                for text_side, num_side in pairs:
                    if is_text(text_side) and self.is_number_value(num_side):
                        self.add("ERROR", node, "Joining text and a number with +",
                                 f"+ can add two numbers or join two pieces of text, but not "
                                 f"both at once. {self.src(num_side)} is a number, so this crashes "
                                 "with a TypeError.",
                                 f"Convert it: str({self.src(num_side)}), or use an f-string: "
                                 f"f\"... {{{self.src(num_side)}}}\"", "type-mix")
                        break
            if isinstance(node, ast.BinOp) and not isinstance(node.op, (ast.Mult, ast.Mod)):
                if (self.is_input_value(node.left) and self.is_number_value(node.right)) or \
                        (self.is_input_value(node.right) and self.is_number_value(node.left)):
                    side = node.left if self.is_input_value(node.left) else node.right
                    self.add("ERROR", node, "Doing maths with text from input()",
                             f"input() always gives back text, so {self.src(side)} is text like "
                             "\"5\", not a number. Maths with text and numbers crashes with a "
                             "TypeError.",
                             f"Convert when you read it: {self.src(side)} = int(input(...))", "type-mix")
            if call_name(node) == "range" and any(self.is_input_value(a) for a in node.args):
                self.add("ERROR", node, "range() given text from input()",
                         "range() needs whole numbers, but input() gives back text.",
                         "Convert first: int(input(...))", "type-mix")

    def check_input_conversion(self):
        for node in self.all_nodes:
            if call_name(node) not in ("int", "float") or not node.args \
                    or not self.is_input_call(node.args[0]):
                continue
            current, protected = self.parents.get(node), False
            while current is not None:
                if isinstance(current, ast.Try) and current.handlers:
                    protected = True
                    break
                current = self.parents.get(current)
            if not protected:
                self.add("INFO", node, "Crashes if the user types something that isn't a number",
                         f"{call_name(node)}(input(...)) will crash with a ValueError if the user "
                         "types letters or leaves it blank.",
                         "Wrap it in try / except ValueError and ask again (input validation).",
                         "robust")

    def check_unused_functions(self):
        for name, fn in self.module_funcs.items():
            if name in self.referenced or fn.decorator_list or name.startswith("__"):
                continue
            if name == "main":
                self.add("WARNING", fn, "main() is never called",
                         "main() is defined but nothing ever runs it, so the program does nothing.",
                         "Add main() at the bottom of the file, or:  if __name__ == \"__main__\": main()",
                         "unused-func")
            else:
                self.add("INFO", fn, f"Function '{name}' is never used",
                         f"{name}() is defined but never called anywhere in this file.",
                         "Call it where it's needed, or delete it if it's left over.", "unused-func")


# ----------------------------------------------------------------------------
# 3. External tools (Ruff, Pylint, Mypy, Bandit), translated into plain English
# ----------------------------------------------------------------------------

# code: (severity, title, why, fix, family)
RUFF_HELP = {
    "F821": ("ERROR", "Name is not defined",
             "Python doesn't know this name. It might be a typo, or it's used before it's created.",
             "Check the spelling, and make sure it gets a value before this line.", "undefined"),
    "F841": ("WARNING", "Variable is never used",
             "This variable gets a value but is never used afterwards - often a typo or a "
             "forgotten step.", "Use the variable, or remove the line if it isn't needed.",
             "unused-var"),
    "F401": ("WARNING", "Import is never used", "This module is imported but never used.",
             "Remove the import if you don't need it.", "unused-import"),
    "F811": ("WARNING", "Name defined twice",
             "This was already defined earlier; the new one replaces the old one.",
             "Rename one of them, or remove the duplicate.", "redefined"),
    "F632": ("WARNING", "Using 'is' to compare values",
             "'is' checks for the same object, not equal values.", "Use == or != instead.",
             "is-literal"),
    "E711": ("STYLE", "Use 'is None' to check for None",
             "Python style is to check for None with 'is'.", "Write 'is None' / 'is not None'.",
             "none-compare"),
    "E712": ("STYLE", "No need to compare with True/False",
             "'if x == True:' does the same as 'if x:'.", "Write 'if x:' or 'if not x:'.",
             "bool-compare"),
    "E722": ("WARNING", "Bare 'except:' catches every error",
             "This hides real bugs as well as the error you expected.",
             "Catch a specific error, e.g. 'except ValueError:'.", "bare-except"),
    "B006": ("WARNING", "Function has a list/dict as a default value",
             "The default is shared between every call.", "Use None as the default instead.",
             "mutable-default"),
    "B015": ("ERROR", "Comparison that does nothing",
             "The answer of this comparison is thrown away. You probably meant = (store).",
             "Use = to store a value, or put the comparison in an if.", "pointless"),
    "B018": ("WARNING", "Line that does nothing",
             "This line works something out but doesn't use or store it.",
             "Did you forget brackets to call a function, or = to store the result?", "pointless"),
    "F541": ("STYLE", "f-string with nothing to fill in",
             "This string starts with f but has no {placeholders}.",
             "Remove the f, or add the {variable} you meant to show.", "fstring-empty"),
    "F823": ("ERROR", "Variable used before it gets a value",
             "Inside this function the variable is used before it's assigned, so Python crashes "
             "with UnboundLocalError.", "Give it a value first, or pass it in as a parameter.",
             "unbound"),
    "F601": ("WARNING", "Same dictionary key used twice",
             "The second value silently replaces the first.", "Use different keys.", "dup-key"),
    "B007": ("STYLE", "Loop variable not used", "The loop variable is never used inside the loop.",
             "Rename it to _ if you don't need it.", "loop-var"),
    "E741": ("STYLE", "Confusing variable name", "Names like l, O and I look like 1 and 0.",
             "Use a more descriptive name.", "name"),
    "PLW0602": ("STYLE", "Uses 'global'", "global makes code harder to follow and test.",
                "Pass values in as parameters and return results instead.", "global"),
    "PLW0603": ("STYLE", "Uses 'global'", "global makes code harder to follow and test.",
                "Pass values in as parameters and return results instead.", "global"),
    "PLW2901": ("WARNING", "Loop variable overwritten inside the loop",
                "Changing the loop variable inside the loop doesn't change the list and is "
                "easy to get confused by.", "Use a new variable name for the changed value.",
                "loop-var"),
    "E701": ("STYLE", "Two statements on one line", "This is harder to read.",
             "Put the code after the colon on its own indented line.", "oneline"),
    "E702": ("STYLE", "Two statements on one line", "Semicolons make code harder to read.",
             "Put each statement on its own line.", "oneline"),
}

PYLINT_HELP = {
    "undefined-variable": RUFF_HELP["F821"],
    "used-before-assignment": RUFF_HELP["F823"],
    "possibly-used-before-assignment": (
        "WARNING", "Variable might not have a value yet",
        "On some paths through the code (e.g. when an if is False) this variable never gets a "
        "value, so it could crash.", "Give it a starting value before the if or loop.", "unbound"),
    "unused-variable": RUFF_HELP["F841"],
    "unused-import": RUFF_HELP["F401"],
    "unreachable": ("WARNING", "Code that can never run",
                    "A return, break or raise before this line means it's never reached.",
                    "Move it earlier, fix the indentation, or delete it.", "unreachable"),
    "no-value-for-parameter": ("ERROR", "Missing value when calling a function",
                               "The function needs more values than it's given here.",
                               "Pass a value for each parameter on its def line.", "args"),
    "too-many-function-args": ("ERROR", "Too many values passed to a function",
                               "The function is given more values than it accepts.",
                               "Check the def line for how many it takes.", "args"),
    "unexpected-keyword-arg": ("ERROR", "Unknown named value passed to a function",
                               "The function has no parameter with that name.",
                               "Check the spelling against the def line.", "args"),
    "comparison-with-callable": ("ERROR", "Comparing a function instead of its result",
                                 "A function name without () is the function itself, not its answer.",
                                 "Add () to call it.", "uncalled"),
    "using-constant-test": ("WARNING", "Condition is always the same",
                            "This if/while condition is always True (or always False), so it "
                            "doesn't really check anything.",
                            "Compare a variable, e.g. 'if answer == \"yes\":', or call the "
                            "function with ().", "constant-test"),
    "singleton-comparison": RUFF_HELP["E711"],
    "redefined-builtin": ("WARNING", "Name hides a built-in Python function",
                          "Using a built-in name (like list or input) for your own variable "
                          "breaks the built-in in that part of the code.",
                          "Rename your variable.", "shadow"),
    "dangerous-default-value": RUFF_HELP["B006"],
    "bare-except": RUFF_HELP["E722"],
    "broad-exception-caught": ("STYLE", "Catches every kind of error",
                               "'except Exception' can hide bugs you didn't expect.",
                               "Catch the specific error you expect, e.g. 'except ValueError:'.",
                               "broad-except"),
    "assignment-from-no-return": ("WARNING", "Storing the answer of a function that doesn't return one",
                                  "This function has no return <value>, so this stores None.",
                                  "Add a return to the function.", "no-return"),
    "assignment-from-none": ("WARNING", "Storing None",
                             "This function always gives back None.",
                             "Add a return to the function, or don't store its result.", "no-return"),
    "pointless-statement": ("WARNING", "Line that does nothing",
                            "This line works something out but doesn't use or store it.",
                            "Did you forget () to call a function, or = to store a value?", "pointless"),
    "expression-not-assigned": ("WARNING", "Line that does nothing",
                                "The result of this line is thrown away.",
                                "Store it with =, or use it in an if.", "pointless"),
    "inconsistent-return-statements": (
        "WARNING", "Function doesn't always return a value",
        "Some paths through this function return a value and some don't (those give back None).",
        "Make sure every path ends with a return, e.g. add 'return None' or 'return False' at the end.",
        "inconsistent-return"),
    "redefined-outer-name": ("STYLE", "A variable name is reused",
                             "This name is also used outside the function. Reusing it can be confusing.",
                             "Use a different name inside the function.", "outer-name"),
    "missing-function-docstring": ("STYLE", "Function has no description (docstring)",
                                   "A short description makes the code easier to understand and mark.",
                                   "Add a one-line \"\"\"docstring\"\"\" as the first line inside the function.",
                                   "docstring"),
    "missing-class-docstring": ("STYLE", "Class has no description (docstring)",
                                "A short description makes the code easier to understand.",
                                "Add a one-line \"\"\"docstring\"\"\" inside the class.", "docstring"),
    "missing-module-docstring": ("STYLE", "File has no description at the top",
                                 "A comment at the top explaining the program helps readers.",
                                 "Add a \"\"\"docstring\"\"\" on the first line of the file.", "docstring"),
    "invalid-name": ("STYLE", "Name doesn't follow Python naming style",
                     "Python style uses snake_case for variables/functions, UPPER_CASE for "
                     "constants and CapWords for classes.", "Rename to match the style.", "name"),
    "consider-using-enumerate": ("STYLE", "Could use enumerate()",
                                 "for i in range(len(x)) is harder to read than enumerate.",
                                 "Use: for i, item in enumerate(x):", "enumerate"),
    "no-else-return": ("STYLE", "Unnecessary 'else' after 'return'",
                       "The return already leaves the function, so else isn't needed.",
                       "Remove the else and un-indent its code.", "else-return"),
    "global-statement": RUFF_HELP["PLW0603"],
    "consider-using-with": ("STYLE", "Use 'with' to open files",
                            "If the program crashes, the file might be left open.",
                            "Use: with open(filename) as file:", "with"),
    "unspecified-encoding": ("STYLE", "open() without an encoding",
                             "Files can read differently on Windows and Linux without one.",
                             "Add encoding=\"utf-8\" to open().", "encoding"),
    "no-member": ("ERROR", "That thing has no such attribute or method",
                  "Often a typo, or the variable holds a different type than you think.",
                  "Check the spelling; print(type(x)) shows what it really is.", "attr"),
    "not-callable": ("ERROR", "Trying to call something that isn't a function",
                     "There are () after something that's a value, not a function.",
                     "Remove the (), or check you haven't reused a function's name for a variable.",
                     "callable"),
    "duplicate-key": RUFF_HELP["F601"],
    "function-redefined": RUFF_HELP["F811"],
    "f-string-without-interpolation": RUFF_HELP["F541"],
    "condition-evals-to-constant": ("ERROR", "Condition is always the same",
                                    "Part of this condition is a value on its own, which always "
                                    "counts as True, so the condition doesn't check what you think.",
                                    "Repeat the comparison on both sides of or/and, e.g. "
                                    "x == \"a\" or x == \"b\".", "constant-test"),
    "self-assigning-variable": ("WARNING", "Variable assigned to itself",
                                "x = x does nothing.", "Check what you meant to store.", "pointless"),
    "unsubscriptable-object": ("ERROR", "Using [ ] on something that can't be indexed",
                               "You can only use [ ] on lists, strings, dictionaries and similar.",
                               "Check what type the variable really is.", "index"),
}

# (pattern, severity, title, why, fix, family) - first match wins
MYPY_HELP = [
    (r"Unsupported operand types.*Callable|\"Callable\[.*has no attribute", "ERROR",
     "Function used without brackets ()",
     "A function name without () is the function itself, not the answer it works out.",
     "Add () after the function name to call it.", "uncalled"),
    (r"could always be true in boolean context", "WARNING", "Function used as a condition",
     "A function on its own always counts as True.", "Add () to call it.", "constant-test"),
    (r'\("str" and "(int|float)"\)|\("(int|float)" and "str"\)', "ERROR",
     "Mixing text and numbers",
     "This does maths or a comparison with text (str) and a number. Python can't, so it crashes "
     "with a TypeError. Remember input() always gives text.",
     "Convert text with int(...) or float(...), or turn the number into text with str(...).",
     "type-mix"),
    (r'Name "\w+" is not defined', *RUFF_HELP["F821"]),
    (r'expression has type "None"', "WARNING", "Storing None by mistake",
     "The value being stored here is None, e.g. from .sort() or a function with no return.",
     "Store the list or value itself, not the result of a method that changes it in place.",
     "no-return"),
    (r"Too many arguments|Missing positional argument|Unexpected keyword argument|Too few arguments",
     "ERROR", "Wrong values passed to a function",
     "The function is given a different number of values than its def line asks for.",
     "Match the values to the parameters on the def line.", "args"),
    (r"does not return a value", "WARNING", "Using the answer of a function that doesn't return one",
     "This function gives back None, so using its result won't work.",
     "Add 'return <value>' to the function.", "no-return"),
    (r'Item "None" of|"None" has no attribute|"None" not callable|"None"', "WARNING",
     "Value might be None",
     "Something here could be None (no value), e.g. a search that found nothing or a function "
     "with no return.", "Check first: if x is not None:", "maybe-none"),
    (r"has no attribute", "ERROR", "That thing has no such attribute or method",
     "Often a typo, or the variable holds a different type than you expect.",
     "Check the spelling and what type the variable is.", "attr"),
    (r"Incompatible types in assignment", "WARNING", "Variable changes type",
     "This variable first held one type of value (e.g. a number) and now gets another (e.g. "
     "text). That often causes bugs later.", "Use a separate variable, or convert the value.",
     "type-change"),
    (r"Argument \d+ to .* has incompatible type", "ERROR", "Wrong type of value passed to a function",
     "The function expects a different type of value here (e.g. a number, not text).",
     "Convert the value before passing it.", "arg-type"),
    (r"not callable", "ERROR", "Trying to call something that isn't a function",
     "There are () after a value that isn't a function.", "Remove the () or fix the name.",
     "callable"),
    (r"not indexable", "ERROR", "Using [ ] on something that can't be indexed",
     "You can only use [ ] on lists, strings, dictionaries and similar.",
     "Check what type the variable is.", "index"),
    (r"Unsupported operand types", "ERROR", "These values can't be combined like this",
     "The two sides of this operator are types that don't work together.",
     "Check both values are the type you expect (print(type(x))).", "type-mix"),
]

BANDIT_HELP = {
    "B307": ("SECURITY", "eval() can run any code",
             "If the text comes from a user, they could type Python code and eval() will run it.",
             "For numbers use int() or float(). For other values use ast.literal_eval()."),
    "B102": ("SECURITY", "exec() can run any code", "exec() runs whatever text it's given.",
             "Avoid exec(); write the code normally instead."),
    "B608": ("SECURITY", "SQL built by joining text (SQL injection risk)",
             "If user input goes straight into an SQL string, a user can change what the query does.",
             "Use ? placeholders: cursor.execute(\"SELECT * FROM users WHERE name = ?\", (name,))"),
    "B105": ("SECURITY", "Password written in the code",
             "Anyone who can see the code (e.g. on GitHub) can see the password.",
             "Load it from an environment variable or a file that isn't committed."),
    "B106": ("SECURITY", "Password written in the code",
             "Anyone who can see the code can see the password.",
             "Load it from an environment variable instead."),
    "B311": ("INFO", "random isn't secure for passwords or codes",
             "Fine for games, but the numbers can be predicted.",
             "For passwords, tokens or PINs use the secrets module."),
    "B101": ("INFO", "assert is skipped in optimised mode",
             "Python can be run with asserts turned off.",
             "Use an if and raise an error for real checks."),
    "B110": ("WARNING", "Errors are silently ignored",
             "try/except/pass hides every error.", "At least print a message in the except."),
    "B602": ("SECURITY", "Running a shell command", "shell=True with user input can run any command.",
             "Pass a list of arguments and leave shell=False."),
    "B605": ("SECURITY", "Running a shell command", "os.system with user input can run any command.",
             "Use subprocess.run([...]) with a list of arguments."),
    "B301": ("SECURITY", "pickle can run code when loading",
             "Loading a pickle file from someone else can run their code.", "Use json instead."),
    "B404": ("INFO", "Uses the subprocess module", "subprocess can run other programs.",
             "Fine if you control the commands. Never build them from user input."),
    "B603": ("INFO", "Runs another program", "This starts another program.",
             "Fine if you control the command. Never build it from user input."),
    "B607": ("INFO", "Runs a program by name only", "The program is found using PATH.",
             "Use the full path if security matters."),
    "B113": ("WARNING", "Web request without a timeout",
             "If the website doesn't answer, the program waits forever.",
             "Add timeout=10 to the request."),
}


def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def run_command(cmd: list[str], timeout: int = 120) -> tuple[str, str]:
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=timeout)
    return result.stdout or "", result.stderr or ""


def tool_finding(tool, help_entry, line, original, fallback_severity, col=None) -> Finding:
    if help_entry:
        severity, title, why, fix, family = help_entry
        return Finding(tool, severity, line, title, why, fix, original, family, col)
    return Finding(tool, fallback_severity, line, original.split(" (")[0][:70],
                   f"{tool} reported: {original}",
                   "Look closely at this line and the one before. Search the message online if "
                   "it doesn't make sense.", original, "", col)


def run_ruff(path: Path) -> list[Finding]:
    out, _ = run_command([sys.executable, "-m", "ruff", "check", "--output-format", "json",
                            "--no-cache", "--exit-zero", "--select", "E,F,W,B,PLE,PLW",
                            "--ignore", "E501,W291,W293,W292,B905,PLW1510", str(path)])
    findings = []
    for item in json.loads(out or "[]"):
        code = item.get("code") or ""
        message = item.get("message", "")
        line = (item.get("location") or {}).get("row")
        if not code or "SyntaxError" in message:
            findings.append(Finding("Ruff", "ERROR", line, "Syntax error", message,
                                    "See the Python syntax error for this line.", message, "syntax"))
            continue
        if code.startswith(("F", "E9", "PLE")):
            fallback = "ERROR"
        elif code.startswith(("B", "PLW")):
            fallback = "WARNING"
        else:
            fallback = "STYLE"
        findings.append(tool_finding("Ruff", RUFF_HELP.get(code), line, f"{code} {message}", fallback))
    return findings


def run_pylint(path: Path) -> list[Finding]:
    out, _ = run_command([sys.executable, "-m", "pylint", "--output-format=json", "--score=n",
                            "--reports=n", "--disable=line-too-long,trailing-whitespace,"
                            "missing-final-newline,too-few-public-methods,subprocess-run-check", str(path)])
    findings = []
    for item in json.loads(out or "[]"):
        symbol = item.get("symbol", "")
        kind = item.get("type", "")
        message = item.get("message", "")
        line = item.get("line")
        if symbol == "syntax-error":
            findings.append(Finding("Pylint", "ERROR", line, "Syntax error", message,
                                    "See the Python syntax error for this line.", message, "syntax"))
            continue
        fallback = {"fatal": "ERROR", "error": "ERROR", "warning": "WARNING"}.get(kind, "STYLE")
        help_entry = PYLINT_HELP.get(symbol)
        # Pylint uses 'singleton-comparison' for None AND for True/False comparisons,
        # so pick the matching tip from the message text.
        if symbol == "singleton-comparison" and not re.search(r"\bNone\b", message):
            help_entry = RUFF_HELP["E712"]
        findings.append(tool_finding("Pylint", help_entry, line,
                                     f"{item.get('message-id', '')} {message} ({symbol})", fallback))
    return findings


def run_mypy(path: Path) -> list[Finding]:
    cache = Path(tempfile.gettempdir()) / "python_checker_mypy_cache"
    out, err = run_command([sys.executable, "-m", "mypy", "--no-pretty", "--show-error-codes",
                            "--no-error-summary", "--ignore-missing-imports", "--check-untyped-defs",
                            "--no-color-output", "--follow-imports", "silent",
                            "--disable-error-code", "var-annotated",
                            "--disable-error-code", "annotation-unchecked",
                            "--cache-dir", str(cache), str(path)])
    findings = []
    for raw in (out + "\n" + err).splitlines():
        m = re.match(r"^(.*?):(\d+):(?:\d+:)?\s*(error|warning):\s*(.*?)(?:\s+\[([\w-]+)\])?$", raw)
        if not m:
            continue
        filename, line, kind, message, code = m.groups()
        try:
            if Path(filename).resolve() != path:
                continue
        except OSError:
            continue
        if "syntax" in (code or "") or "invalid syntax" in message:
            findings.append(Finding("Mypy", "ERROR", int(line), "Syntax error", message,
                                    "See the Python syntax error for this line.", raw, "syntax"))
            continue
        entry = next(((sev, t, w, f, fam) for pat, sev, t, w, f, fam in MYPY_HELP
                      if re.search(pat, message)), None)
        findings.append(tool_finding("Mypy", entry, int(line), message, "ERROR" if kind == "error"
                                     else "WARNING"))
    return findings


def run_bandit(path: Path) -> list[Finding]:
    out, _ = run_command([sys.executable, "-m", "bandit", "-q", "-f", "json", str(path)])
    findings = []
    try:
        data = json.loads(out or "{}")
    except json.JSONDecodeError:
        return findings
    for item in data.get("results", []):
        test_id = item.get("test_id", "")
        text = item.get("issue_text", "")
        line = item.get("line_number")
        if test_id in BANDIT_HELP:
            severity, title, why, fix = BANDIT_HELP[test_id]
        else:
            severity, title, why = "SECURITY", "Possible security risk", text
            fix = "Check whether this could expose data, run unsafe commands or trust user input."
        findings.append(Finding("Bandit", severity, line, title, why, fix, f"{test_id} {text}",
                                "swallow" if test_id == "B110" else f"bandit-{test_id}"))
    return findings


TOOLS = [("Ruff", "ruff", run_ruff), ("Pylint", "pylint", run_pylint),
         ("Mypy", "mypy", run_mypy), ("Bandit", "bandit", run_bandit)]


# ----------------------------------------------------------------------------
# 4 + 5. Test run and output check
# ----------------------------------------------------------------------------

EXCEPTION_HELP = {
    "NameError": ("Used a name Python doesn't know",
                  "A variable or function was used before it was created, or it's spelt "
                  "differently somewhere else.",
                  "Check the spelling (capitals matter) and that it gets a value before this line.",
                  "undefined"),
    "TypeError": ("Wrong type of value",
                  "An operation was used on the wrong kind of value - e.g. adding text to a "
                  "number, or calling a function with the wrong number of values.",
                  "Read Python's message below. Convert with int()/str(), or check the () and "
                  "the values passed in.", "type-mix"),
    "ValueError": ("The value can't be used",
                   "The type was right but the value wasn't, e.g. int(\"hello\").",
                   "Check the value. Put int(input(...)) inside try / except ValueError.", "value"),
    "KeyError": ("Dictionary key doesn't exist",
                 "The code looked up a key that the dictionary doesn't have.",
                 "Use exactly the same key name (spelling and capitals) as where the dictionary "
                 "was made, or use .get(key).", "key"),
    "IndexError": ("Position is past the end of the list",
                   "Positions start at 0, so the last item is at len(list) - 1. The list might "
                   "also be empty.", "Check your range() and index numbers.", "index"),
    "ZeroDivisionError": ("Divided by zero", "Dividing by 0 is impossible.",
                          "Check the number isn't 0 before dividing.", "zero"),
    "AttributeError": ("That thing doesn't have that attribute or method",
                       "Often a typo, or the variable holds None or a different type than expected.",
                       "Check the spelling; print(type(x)) shows what it really is.", "attr"),
    "UnboundLocalError": ("Variable used before it gets a value",
                          "Inside a function, a variable was used before it was assigned. If you "
                          "assign to it anywhere in a function, Python treats it as local.",
                          "Give it a value first, pass it in as a parameter, or return it.", "unbound"),
    "RecursionError": ("Function keeps calling itself forever",
                       "A function calls itself with no point where it stops.",
                       "Add a base case (an if that returns without calling itself).", "recursion"),
    "FileNotFoundError": ("File not found",
                          "The program tried to open a file that isn't there. The test run starts "
                          "in the same folder as your program.",
                          "Check the filename, spelling and folder.", "file"),
    "ModuleNotFoundError": ("Module not installed or misspelt", "Python can't find that module.",
                            "Check the spelling, or install it: python -m pip install <name>", "import"),
    "ImportError": ("Couldn't import that", "The module exists but doesn't have that name in it.",
                    "Check the spelling of what you're importing.", "import"),
    "EOFError": ("The program wanted input but didn't get any",
                 "input() was called but there was nothing to read.",
                 "Give answers with --inputs answers.txt (one per line), or run without "
                 "--expected so you can type them yourself.", "eof"),
    "AssertionError": ("An assert check failed", "An assert condition was False.",
                       "Check the values just before this line.", "assert"),
    "PermissionError": ("Not allowed to open that file", "The file is locked or protected.",
                        "Close it in other programs, or check the folder.", "file"),
}


# More specific help for common crash messages: (exception, pattern, title, why, fix)
SPECIFIC_CRASHES = [
    ("ValueError", r"remove\(x\): x not in list", "Removing something that isn't in the list",
     ".remove() looks for an item EQUAL to the value you give it, and nothing in the list matches. "
     "A common cause is giving it a name (text) when the list holds dictionaries or other objects.",
     "Remove the actual item from the list (e.g. the dictionary you found), or check with "
     "'if x in my_list:' first."),
    ("ValueError", r"invalid literal for int\(\)|could not convert string to float",
     "Text couldn't be turned into a number",
     "int() or float() was given text that isn't a number, e.g. \"ten\" or an empty answer.",
     "Put the conversion inside try / except ValueError and ask again if it fails."),
    ("ValueError", r"not enough values to unpack|too many values to unpack",
     "Wrong number of variables when unpacking",
     "The number of variables on the left of = doesn't match the number of values on the right.",
     "Make the number of variables match the number of values."),
    ("TypeError", r"unsupported operand.*'function'|'function' object",
     "Function used without brackets ()",
     "A function name was used in a calculation without (), so Python used the function itself.",
     "Add () after the function name to call it."),
    ("TypeError", r"can only concatenate str|must be str, not|unsupported operand.*'str'",
     "Mixing text and numbers",
     "Text and a number were joined or calculated together. Remember input() always gives text.",
     "Convert with int()/float() for maths, or str() / an f-string for joining text."),
    ("TypeError", r"missing \d+ required positional argument|takes \d+ positional argument",
     "Wrong number of values passed to a function",
     "A function was called with more or fewer values than its def line asks for.",
     "Match the values in the call to the parameters on the def line."),
    ("TypeError", r"'NoneType' object", "Using None as if it were a value",
     "Something here is None - often from a function with no return, or from .sort()/.append().",
     "Find where the variable got None. Add a return, or don't store the result of .sort()."),
    ("TypeError", r"'(int|float)' object is not (subscriptable|iterable)",
     "Using [ ] or a loop on a number",
     "You can only use [ ] or a for loop on things like lists and strings, not numbers.",
     "Check the variable holds what you think. Use range(n) to loop n times."),
    ("AttributeError", r"'NoneType' object has no attribute", "Using None as if it were a value",
     "The variable is None, so it has no methods. Often a function with no return, or a "
     "search that found nothing.", "Check for None first (if x is not None:), or add a return."),
    ("IndexError", r"out of range", "Position is past the end of the list",
     "Positions start at 0, so the last item is at len(list) - 1. The list might also be empty.",
     "Check range() and index numbers; use list[-1] for the last item."),
]


def exception_family(name: str, message: str) -> str:
    if name == "TypeError":
        if "function" in message or "not subscriptable" in message and "function" in message:
            return "uncalled"
        if "positional argument" in message or "keyword argument" in message:
            return "args"
        if "NoneType" in message:
            return "maybe-none"
    return EXCEPTION_HELP.get(name, ("", "", "", "runtime"))[3]


def parse_traceback(stderr: str, path: Path) -> Finding | None:
    text = stderr.strip()
    if "Traceback (most recent call last)" not in text and not re.search(r"^\w+Error", text, re.M):
        return None
    line = None
    for filename, lineno in re.findall(r'File "(.+?)", line (\d+)', text):
        try:
            if Path(filename).resolve() == path:
                line = int(lineno)
        except OSError:
            pass
    last = [l for l in text.splitlines() if l.strip()][-1].strip()
    name, _, message = last.partition(":")
    name = name.split(".")[-1].strip()
    message = message.strip()
    title, why, fix, family = EXCEPTION_HELP.get(
        name, (f"The program crashed with {name}", "The program stopped with an error.",
               "Read Python's message below and look at this line.", "runtime"))
    for exc_name, pattern, t, w, f in SPECIFIC_CRASHES:
        if exc_name == name and re.search(pattern, message):
            title, why, fix = t, w, f
            break
    family = exception_family(name, message)
    detail = f' Python says: "{last}".'
    return Finding("Test run", "ERROR", line, f"Crash: {title}", why + detail, fix, original=last,
                   family=family)


def run_program(path: Path, capture: bool, inputs: str | None, timeout: float):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    cmd = [sys.executable, str(path)]
    try:
        if capture:
            r = subprocess.run(cmd, cwd=path.parent, input=inputs or "", capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
            return r.returncode, r.stdout, r.stderr, False
        r = subprocess.run(cmd, cwd=path.parent, stderr=subprocess.PIPE, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=env)
        return r.returncode, None, r.stderr, False
    except subprocess.TimeoutExpired as exc:
        def text(value):
            if isinstance(value, bytes):
                return value.decode("utf-8", "replace")
            return value or ""
        return None, text(exc.stdout), text(exc.stderr), True
    except KeyboardInterrupt:
        return None, "", "", False


def group_diffs(diffs):
    """Squash runs of missing lines into one entry so a crash doesn't flood the report."""
    grouped, i = [], 0
    while i < len(diffs):
        j = i
        while j < len(diffs) and diffs[j][2] is None and diffs[j][1] is not None:
            j += 1
        if j - i >= 3:
            grouped.append((diffs[i][0], f"{j - i} more line(s), starting: {diffs[i][1]!r}",
                            None, "missing"))
            i = j
        else:
            grouped.append((*diffs[i], ""))
            i += 1
    return grouped


def compare_output(expected: str, actual: str) -> list[tuple[int, str | None, str | None]]:
    exp = [l.rstrip() for l in expected.rstrip("\n").splitlines()]
    act = [l.rstrip() for l in actual.rstrip("\n").splitlines()]
    diffs = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, exp, act, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        length = max(i2 - i1, j2 - j1)
        for k in range(length):
            e = exp[i1 + k] if i1 + k < i2 else None
            a = act[j1 + k] if j1 + k < j2 else None
            diffs.append((i1 + k + 1, e, a))
    return diffs


# ----------------------------------------------------------------------------
# Putting it together
# ----------------------------------------------------------------------------

def merge_findings(findings: list[Finding]) -> list[Finding]:
    """Combine reports of the same problem from different tools."""
    result, by_family, by_title = [], {}, set()
    for f in findings:
        if f.family:
            key = (f.line, f.family)
            if key in by_family:
                keep = by_family[key]
                if f.tool != keep.tool and f.tool not in keep.also:
                    keep.also.append(f.tool)
                if SEVERITIES.index(f.severity) < SEVERITIES.index(keep.severity):
                    keep.severity = f.severity
                continue
            by_family[key] = f
        exact = (f.line, f.title, f.explanation)
        if exact in by_title:
            continue
        by_title.add(exact)
        result.append(f)
    return result


def find_file(raw: str) -> Path | None:
    raw = raw.strip().strip('"').strip("'")
    if not raw:
        print("\nYou didn't enter a filename.")
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    if not path.is_file():
        matches = [p for p in Path.cwd().rglob(Path(raw).name)
                   if p.is_file() and ".git" not in p.parts][:10]
        if len(matches) == 1:
            print(f"\nI couldn't find {raw} here, but found it at: {matches[0]}")
            path = matches[0].resolve()
        else:
            print(f"\nI couldn't find this file:\n  {path}")
            print(f"\nYour current folder is:\n  {Path.cwd()}")
            if matches:
                print("\nDid you mean one of these?")
                for m in matches:
                    print(f"  {m.relative_to(Path.cwd())}")
            else:
                print("Tip: include its folder, for example: python/task_2_summer.py")
            return None
    if path.suffix.lower() != ".py":
        print("\nPlease choose a file ending in .py")
        return None
    return path


def ask(question: str, default: bool) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"{question} {hint} ").strip().lower()
    except EOFError:
        return default
    return default if not answer else answer.startswith("y")


def print_finding(rep: Report, number: int, f: Finding, source_lines: list[str], details: bool):
    where = f"line {f.line}" if f.line else ""
    title = f"{number}. [{f.severity}] {f.title}"
    rep.say("")
    gap = WIDTH - len(title) - len(where)
    rep.say(title + (" " * gap if gap >= 2 else "  ") + where, f.severity)
    if f.line and 1 <= f.line <= len(source_lines):
        code = source_lines[f.line - 1].expandtabs(4)
        stripped = code.lstrip()
        rep.say(f"    {f.line:>4} | {stripped}", "bold")
        if f.col and f.family == "syntax":
            caret = max(0, f.col - 1 - (len(code) - len(stripped)))
            if caret <= len(stripped):
                rep.say(f"         | {' ' * caret}^", f.severity)
    rep.wrapped("Why:", f.explanation)
    rep.wrapped("Fix:", f.fix, "ok")
    tools = [f.tool] + f.also
    if "Test run" in f.also:
        rep.say("    Found by: " + ", ".join(t for t in tools if t != "Test run")
                + " - and CONFIRMED when the program ran", "dim")
    else:
        rep.say("    Found by: " + ", ".join(tools), "dim")
    if details and f.original:
        rep.say(f"    Tool message: {f.original}", "dim")


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Find problems in a Python file and explain them.")
    parser.add_argument("file", nargs="?", help="the .py file to check")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--run", action="store_true", help="run the program after checking it")
    group.add_argument("--no-run", action="store_true", help="don't run the program")
    parser.add_argument("--expected", help="text file with the output the program should print")
    parser.add_argument("--inputs", help="text file of answers for input(), one per line")
    parser.add_argument("--timeout", type=float, help="seconds the test run may take")
    parser.add_argument("--details", action="store_true", help="show each tool's original message")
    parser.add_argument("--save", action="store_true", help="save the report as <name>_report.txt")
    parser.add_argument("--no-color", action="store_true", help="plain output without colours")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if sys.platform == "win32":
        os.system("")  # turns on colours in the Windows terminal
    colour = not args.no_color and sys.stdout.isatty() and "NO_COLOR" not in os.environ
    rep = Report(colour)
    rep.banner("PYTHON CHECKER - EASY READ")
    rep.say("I'll find problems, explain WHY each one is a problem, and HOW to fix it.")

    interactive = args.file is None
    raw = args.file
    if interactive:
        try:
            raw = input("\nPython file to check (example: task_2_summer.py): ")
        except EOFError:
            raw = ""
    path = find_file(raw or "")
    if path is None:
        return 1

    try:
        with tokenize.open(path) as file:
            source = file.read()
    except (OSError, UnicodeError, SyntaxError) as exc:
        print(f"\nI couldn't read that file: {exc}")
        return 1
    source_lines = source.splitlines()
    rep.say(f"\nChecking: {path}  ({len(source_lines)} lines)")
    findings: list[Finding] = []

    # 1. Syntax
    rep.section("1. Syntax check")
    syntax, analysable = find_syntax_errors(source, str(path))
    findings += syntax
    if not syntax:
        rep.say("  [OK] Python can read the whole file.", "ok")
    else:
        rep.say(f"  [!] {len(syntax)} syntax error(s) found.", "ERROR")
        if analysable:
            rep.say("      I patched them in memory (your file is NOT changed) so I could keep "
                    "checking the rest.")

    # 2. Built-in checks
    rep.section("2. Bug checks")
    if analysable:
        tree = ast.parse(analysable, filename=str(path))
        bug_findings = Analyzer(tree, analysable).run()
        findings += bug_findings
        rep.say(f"  [DONE] {len(bug_findings)} thing(s) found.")
    else:
        rep.say("  [SKIPPED] Fix the syntax error(s) first, then check again.")

    # 3. Tools
    rep.section("3. Extra tools")
    used, missing = [], []
    tool_path, temp_dir = path, None
    if syntax and analysable:
        # Tools can't read a file with syntax errors, so give them the patched copy
        # (same line numbers). Your real file is never changed.
        temp_dir = tempfile.TemporaryDirectory()
        tool_path = Path(temp_dir.name) / path.name
        tool_path.write_text(analysable, encoding="utf-8")
        rep.say("  (Checking the patched copy, so the tools can see past the syntax errors.)", "dim")
    for name, module, runner in TOOLS:
        if not module_available(module):
            missing.append(name)
            rep.say(f"  [SKIPPED] {name} isn't installed.", "dim")
            continue
        try:
            tool_findings = runner(tool_path.resolve())
            used.append(name)
            findings += tool_findings
            rep.say(f"  [DONE] {name}: {len(tool_findings)} thing(s) reported.")
        except subprocess.TimeoutExpired:
            rep.say(f"  [NOTE] {name} took too long and was stopped.", "WARNING")
        except Exception as exc:  # a tool problem should never stop the report
            rep.say(f"  [NOTE] {name} couldn't run: {exc}", "WARNING")

    if temp_dir is not None:
        temp_dir.cleanup()

    # 4 + 5. Test run
    rep.section("4. Test run")
    output_diffs = None
    crashed = False
    expected_text = None
    inputs_text = None
    if args.expected:
        try:
            expected_text = Path(args.expected).read_text(encoding="utf-8")
        except OSError as exc:
            rep.say(f"  [NOTE] Couldn't read the expected output file: {exc}", "WARNING")
    if args.inputs:
        try:
            inputs_text = Path(args.inputs).read_text(encoding="utf-8")
        except OSError as exc:
            rep.say(f"  [NOTE] Couldn't read the inputs file: {exc}", "WARNING")

    if syntax:
        rep.say("  [SKIPPED] Python can't run a file with syntax errors. Fix them first.", "dim")
    else:
        should_run = args.run or bool(expected_text)
        if interactive and not args.run and not args.no_run and not expected_text:
            rep.say("  Running your program finds crashes the checks above can't see.")
            rep.say("  Only run code you trust - it runs for real.")
            should_run = ask("  Run it now?", True)
        if args.no_run:
            should_run = False
        if not should_run:
            rep.say("  [SKIPPED] Not run. Add --run to run it, or --expected FILE to check "
                    "its output.", "dim")
        else:
            capture = expected_text is not None or inputs_text is not None
            timeout = args.timeout or (20 if capture else 300)
            if capture:
                source_of_answers = "your inputs file" if inputs_text is not None else \
                    "nowhere - add --inputs FILE if it asks questions"
                rep.say(f"  Running {path.name} (answers to input() come from {source_of_answers})...")
            else:
                rep.say(f"  Running {path.name}. If it asks you anything, type your answer.")
                rep.say("  ---------------- program output ----------------", "dim")
            code, stdout, stderr, timed_out = run_program(path, capture, inputs_text, timeout)
            if not capture:
                rep.say("  ---------------- end of output -----------------", "dim")
            crash = parse_traceback(stderr, path) if stderr else None
            if timed_out:
                findings.append(Finding(
                    "Test run", "ERROR", None, "Program didn't finish",
                    f"It was still running after {timeout:g} seconds. This usually means a loop "
                    "that never ends, or it's waiting for input that never comes.",
                    "Check every while loop changes its condition or has a break. Look at the "
                    "Loop warnings above.", family="infinite"))
                rep.say("  [!] Stopped - it took too long.", "ERROR")
            elif crash:
                crashed = True
                findings.append(crash)
                rep.say(f"  [!] It crashed: {crash.original}", "ERROR")
            elif code not in (0, None):
                rep.say(f"  [NOTE] It finished with exit code {code}.", "WARNING")
            else:
                rep.say("  [OK] It ran to the end without crashing.", "ok")
            if expected_text is not None and stdout is not None:
                output_diffs = compare_output(expected_text, stdout)
                if output_diffs:
                    rep.say(f"  [!] The output is different from what's expected in "
                            f"{len(output_diffs)} line(s).", "ERROR")
                else:
                    rep.say("  [OK] The output matches the expected output exactly!", "ok")
            if args.details and stdout:
                rep.say("\n  Program output:", "dim")
                for line in stdout.splitlines():
                    rep.say("    " + line, "dim")

    # Results
    findings = merge_findings(findings)
    groups = {s: sorted([f for f in findings if f.severity == s], key=lambda f: f.line or 0)
              for s in SEVERITIES}

    rep.banner("YOUR RESULTS")
    rep.say(f"  Errors (crash or wrong results):  {len(groups['ERROR'])}", "ERROR" if groups["ERROR"] else "ok")
    rep.say(f"  Security alerts:                  {len(groups['SECURITY'])}")
    rep.say(f"  Warnings (probably bugs):         {len(groups['WARNING'])}")
    rep.say(f"  Style tips (optional):            {len(groups['STYLE'])}")
    rep.say(f"  Notes:                            {len(groups['INFO'])}")
    if output_diffs is not None:
        rep.say(f"  Output lines that don't match:    {len(output_diffs)}",
                "ERROR" if output_diffs else "ok")

    number = 0
    serious = groups["ERROR"] + groups["SECURITY"]
    if serious:
        rep.section("MUST FIX - these will crash or give wrong results")
        for f in serious:
            number += 1
            print_finding(rep, number, f, source_lines, args.details)
    if groups["WARNING"]:
        rep.section("SHOULD CHECK - these are probably bugs")
        for f in groups["WARNING"]:
            number += 1
            print_finding(rep, number, f, source_lines, args.details)

    if output_diffs:
        rep.section("OUTPUT CHECK - what it printed vs what it should print")
        rep.say("  These are LOGIC errors: the code runs, but gives the wrong answer.")
        rep.say("  Find the code that prints each line and check the calculation or condition.")
        shown = group_diffs(output_diffs)
        for out_line, exp, got, kind in shown[:12]:
            rep.say("")
            rep.say(f"  Output line {out_line}:", "bold")
            if kind == "missing":
                rep.say(f"    Expected: {exp}", "ok")
                reason = " because the program crashed (see above)" if crashed else ""
                rep.say(f"    Got:      nothing - the output stops here{reason}", "ERROR")
                continue
            rep.say(f"    Expected: {exp if exp is not None else '(nothing - this line is extra)'}", "ok")
            rep.say(f"    Got:      {got if got is not None else '(nothing - this line is missing)'}",
                    "ERROR")
        if len(shown) > 12:
            rep.say(f"\n  ...and {len(shown) - 12} more difference(s).")

    for severity, heading in (("STYLE", "STYLE TIPS - optional, but make your code tidier"),
                              ("INFO", "NOTES")):
        if not groups[severity]:
            continue
        rep.section(heading)
        grouped: dict[str, list[Finding]] = {}
        for f in groups[severity]:
            grouped.setdefault(f.title, []).append(f)
        for title, items in grouped.items():
            lines = sorted({f.line for f in items if f.line})
            where = f" (line {', '.join(map(str, lines))})" if lines else ""
            rep.say(f"  - {title}{where}", severity)
            rep.say(textwrap.fill(f"Why: {items[0].explanation}", WIDTH, initial_indent="      ",
                                  subsequent_indent="           "))
            rep.say(textwrap.fill(f"Fix: {items[0].fix}", WIDTH, initial_indent="      ",
                                  subsequent_indent="           "), "ok")

    if not findings and not output_diffs:
        rep.say("\n  GREAT! No problems were found by the checks that ran.", "ok")

    rep.section("CHECKER SETUP")
    rep.say("Tools used: Python syntax check, built-in bug checks"
            + (", " + ", ".join(used) if used else ""))
    if missing:
        rep.say("Not installed: " + ", ".join(missing) + "  (they find extra problems)")
        rep.say("Install them once with:  python -m pip install -r requirements.txt")

    rep.section("REMEMBER")
    rep.say("No checker can find every bug. The hardest ones are LOGIC errors, where the")
    rep.say("program runs but follows the wrong rule (e.g. > instead of >=).")
    rep.say("To catch those: save what the program SHOULD print in a text file and run")
    rep.say(f"  python {sys.argv[0]} {raw} --expected expected.txt")
    rep.say("and test with boundary values (0, 1, the exact limit, one over the limit).")
    rep.say("=" * WIDTH, "head")

    if args.save:
        report_path = path.with_name(path.stem + "_report.txt")
        report_path.write_text("\n".join(rep.lines) + "\n", encoding="utf-8")
        print(f"\nReport saved to: {report_path}")

    return 1 if groups["ERROR"] or groups["SECURITY"] or output_diffs else 0


if __name__ == "__main__":
    raise SystemExit(main())
