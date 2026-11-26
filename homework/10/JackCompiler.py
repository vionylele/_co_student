#!/usr/bin/env python3
"""
JackCompiler.py -- nand2tetris Jack compiler (projects 10 and 11).

Compiles Jack source (.jack) into Hack VM code (.vm).

Usage:
    python3 JackCompiler.py <File.jack | Dir>

    File.jack -> File.vm (next to the source)
    Dir/      -> one .vm per .jack file in the directory

Pipeline: tokenizer -> recursive-descent parser that emits VM code directly,
with a two-level symbol table (class scope: static/field, subroutine scope:
argument/local). Errors are reported as `File.jack:LINE: message` (exit code 1).
"""

import argparse
import re
import sys
from pathlib import Path


class JackError(Exception):
    pass


# --------------------------------------------------------------------------
# Tokenizer
# --------------------------------------------------------------------------

KEYWORDS = {
    "class", "constructor", "function", "method", "field", "static", "var",
    "int", "char", "boolean", "void", "true", "false", "null", "this",
    "let", "do", "if", "else", "while", "return",
}
TOKEN_RE = re.compile(r"""
    (?P<ws>\s+)
  | (?P<lc>//[^\n]*)
  | (?P<bc>/\*.*?\*/)
  | (?P<int>\d+)
  | (?P<str>"[^"\n]*")
  | (?P<id>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<sym>[{}()\[\].,;+\-*/&|<>=~])
""", re.X | re.S)


class Tok:
    __slots__ = ("kind", "val", "line")

    def __init__(self, kind, val, line):
        self.kind, self.val, self.line = kind, val, line


def tokenize(src, fname):
    toks, pos, line = [], 0, 1
    while pos < len(src):
        if src.startswith("/*", pos) and src.find("*/", pos + 2) < 0:
            raise JackError(f"{fname}:{line}: unterminated comment")
        m = TOKEN_RE.match(src, pos)
        if not m:
            what = "unterminated string constant" if src[pos] == '"' else f"unexpected character {src[pos]!r}"
            raise JackError(f"{fname}:{line}: {what}")
        text, k = m.group(), m.lastgroup
        if k == "int":
            if int(text) > 32767:
                raise JackError(f"{fname}:{line}: integer constant {text} is larger than 32767")
            toks.append(Tok("int", int(text), line))
        elif k == "str":
            toks.append(Tok("str", text[1:-1], line))
        elif k == "id":
            toks.append(Tok("keyword" if text in KEYWORDS else "id", text, line))
        elif k == "sym":
            toks.append(Tok("sym", text, line))
        line += text.count("\n")
        pos = m.end()
    toks.append(Tok("eof", "<end of file>", line))
    return toks


# --------------------------------------------------------------------------
# Compiler (parser + code generator)
# --------------------------------------------------------------------------

SEGMENT = {"static": "static", "field": "this", "arg": "argument", "var": "local"}
OPS = {"+": "add", "-": "sub", "*": "call Math.multiply 2", "/": "call Math.divide 2",
       "&": "and", "|": "or", "<": "lt", ">": "gt", "=": "eq"}
KEYWORD_CONSTANTS = {"true", "false", "null", "this"}


class Compiler:
    def __init__(self, src, fname, stem):
        self.f, self.stem = fname, stem
        self.t = tokenize(src, fname)
        self.i = 0
        self.out = []
        self.cls = ""
        self.class_syms, self.sub_syms = {}, {}
        self.counts = {"static": 0, "field": 0, "arg": 0, "var": 0}

    # -- token helpers ----------------------------------------------------
    @property
    def tok(self):
        return self.t[self.i]

    def peek(self, offset=0):
        return self.t[min(self.i + offset, len(self.t) - 1)]

    def err(self, msg, tok=None):
        raise JackError(f"{self.f}:{(tok or self.tok).line}: {msg}")

    def next(self):
        tok = self.tok
        self.i += 1
        return tok

    def is_(self, val):
        return self.tok.kind in ("sym", "keyword") and self.tok.val == val

    def expect(self, val):
        if not self.is_(val):
            self.err(f"expected '{val}' but found '{self.tok.val}'")
        return self.next()

    def ident(self, what="identifier"):
        if self.tok.kind != "id":
            self.err(f"expected {what} but found '{self.tok.val}'")
        return self.next().val

    def type_(self, allow_void=False):
        t = self.tok
        if t.kind == "keyword" and (t.val in ("int", "char", "boolean") or (allow_void and t.val == "void")):
            return self.next().val
        if t.kind == "id":
            return self.next().val
        self.err(f"expected a type but found '{t.val}'")

    # -- symbol table -----------------------------------------------------
    def define(self, name, typ, kind, tok):
        table = self.class_syms if kind in ("static", "field") else self.sub_syms
        if name in table:
            self.err(f"'{name}' is already declared in this scope", tok)
        table[name] = (typ, kind, self.counts[kind])
        self.counts[kind] += 1

    def lookup(self, name, tok):
        sym = self.sub_syms.get(name) or self.class_syms.get(name)
        if sym and sym[1] == "field" and self.sub_kind == "function":
            self.err(f"field '{name}' cannot be used in a function", tok)
        return sym

    def emit(self, *lines):
        self.out.extend(lines)

    # -- declarations -----------------------------------------------------
    def compile_class(self):
        self.expect("class")
        name_tok = self.tok
        self.cls = self.ident("class name")
        if self.cls != self.stem:
            print(f"warning: {self.f}:{name_tok.line}: class '{self.cls}' should be in {self.cls}.jack",
                  file=sys.stderr)
        self.expect("{")
        while self.is_("static") or self.is_("field"):
            self.class_var_dec()
        while self.tok.val in ("constructor", "function", "method") and self.tok.kind == "keyword":
            self.subroutine()
        self.expect("}")
        if self.tok.kind != "eof":
            self.err(f"unexpected '{self.tok.val}' after end of class")
        return self.out

    def class_var_dec(self):
        kind = self.next().val
        typ = self.type_()
        while True:
            tok = self.tok
            self.define(self.ident("variable name"), typ, kind, tok)
            if not self.is_(","):
                break
            self.next()
        self.expect(";")

    def subroutine(self):
        self.sub_kind = self.next().val
        self.ret_void = self.is_("void")
        self.type_(allow_void=True)
        name = self.ident("subroutine name")
        self.sub_syms = {}
        self.counts["arg"] = self.counts["var"] = 0
        self.if_n = self.while_n = 0
        if self.sub_kind == "method":
            self.define("this", self.cls, "arg", self.tok)
        self.expect("(")
        if not self.is_(")"):
            while True:
                typ = self.type_()
                tok = self.tok
                self.define(self.ident("parameter name"), typ, "arg", tok)
                if not self.is_(","):
                    break
                self.next()
        self.expect(")")
        self.expect("{")
        while self.is_("var"):
            self.next()
            typ = self.type_()
            while True:
                tok = self.tok
                self.define(self.ident("variable name"), typ, "var", tok)
                if not self.is_(","):
                    break
                self.next()
            self.expect(";")
        self.emit(f"function {self.cls}.{name} {self.counts['var']}")
        if self.sub_kind == "constructor":
            self.emit(f"push constant {self.counts['field']}", "call Memory.alloc 1", "pop pointer 0")
        elif self.sub_kind == "method":
            self.emit("push argument 0", "pop pointer 0")
        self.statements()
        self.expect("}")

    # -- statements -------------------------------------------------------
    def statements(self):
        while self.tok.kind == "keyword" and self.tok.val in ("let", "if", "while", "do", "return"):
            getattr(self, "st_" + self.tok.val)()

    def push_var(self, name, tok):
        sym = self.lookup(name, tok)
        if not sym:
            self.err(f"undefined variable '{name}'", tok)
        self.emit(f"push {SEGMENT[sym[1]]} {sym[2]}")

    def st_let(self):
        self.next()
        tok = self.tok
        name = self.ident("variable name")
        sym = self.lookup(name, tok)
        if not sym:
            self.err(f"undefined variable '{name}'", tok)
        is_array = self.is_("[")
        if is_array:
            self.next()
            self.emit(f"push {SEGMENT[sym[1]]} {sym[2]}")
            self.expression()
            self.expect("]")
            self.emit("add")
        self.expect("=")
        self.expression()
        self.expect(";")
        if is_array:
            self.emit("pop temp 0", "pop pointer 1", "push temp 0", "pop that 0")
        else:
            self.emit(f"pop {SEGMENT[sym[1]]} {sym[2]}")

    def st_if(self):
        self.next()
        n, self.if_n = self.if_n, self.if_n + 1
        self.expect("(")
        self.expression()
        self.expect(")")
        self.emit(f"if-goto IF_TRUE{n}", f"goto IF_FALSE{n}", f"label IF_TRUE{n}")
        self.expect("{")
        self.statements()
        self.expect("}")
        if self.is_("else"):
            self.next()
            self.emit(f"goto IF_END{n}", f"label IF_FALSE{n}")
            self.expect("{")
            self.statements()
            self.expect("}")
            self.emit(f"label IF_END{n}")
        else:
            self.emit(f"label IF_FALSE{n}")

    def st_while(self):
        self.next()
        n, self.while_n = self.while_n, self.while_n + 1
        self.emit(f"label WHILE_EXP{n}")
        self.expect("(")
        self.expression()
        self.expect(")")
        self.emit("not", f"if-goto WHILE_END{n}")
        self.expect("{")
        self.statements()
        self.expect("}")
        self.emit(f"goto WHILE_EXP{n}", f"label WHILE_END{n}")

    def st_do(self):
        self.next()
        tok = self.tok
        name = self.ident("subroutine or variable name")
        self.call(name, tok)
        self.expect(";")
        self.emit("pop temp 0")

    def st_return(self):
        tok = self.next()
        if self.is_(";"):
            if not self.ret_void:
                self.err("a non-void subroutine must return a value", tok)
            self.emit("push constant 0")
        else:
            if self.ret_void:
                self.err("a void subroutine cannot return a value", tok)
            self.expression()
        self.expect(";")
        self.emit("return")

    # -- expressions ------------------------------------------------------
    def expression(self):
        self.term()
        while self.tok.kind == "sym" and self.tok.val in OPS:
            op = self.next().val
            self.term()
            self.emit(OPS[op])

    def expression_list(self):
        n = 0
        if not self.is_(")"):
            while True:
                self.expression()
                n += 1
                if not self.is_(","):
                    break
                self.next()
        return n

    def call(self, name, tok):
        """Compile a subroutine call whose first identifier was already consumed."""
        if self.is_("."):
            self.next()
            sub = self.ident("subroutine name")
            sym = self.lookup(name, tok)
            if sym:
                self.emit(f"push {SEGMENT[sym[1]]} {sym[2]}")
                cls, extra = sym[0], 1
            else:
                cls, extra = name, 0
        else:
            if self.sub_kind == "function":
                self.err(f"cannot call method '{name}' without an object inside a function", tok)
            sub, cls, extra = name, self.cls, 1
            self.emit("push pointer 0")
        self.expect("(")
        n = self.expression_list()
        self.expect(")")
        self.emit(f"call {cls}.{sub} {n + extra}")

    def term(self):
        t = self.tok
        if t.kind == "int":
            self.next()
            self.emit(f"push constant {t.val}")
        elif t.kind == "str":
            self.next()
            self.emit(f"push constant {len(t.val)}", "call String.new 1")
            for ch in t.val:
                self.emit(f"push constant {ord(ch)}", "call String.appendChar 2")
        elif t.kind == "keyword" and t.val in KEYWORD_CONSTANTS:
            self.next()
            if t.val == "true":
                self.emit("push constant 0", "not")
            elif t.val == "this":
                if self.sub_kind == "function":
                    self.err("'this' cannot be used in a function", t)
                self.emit("push pointer 0")
            else:
                self.emit("push constant 0")
        elif t.kind == "sym" and t.val == "(":
            self.next()
            self.expression()
            self.expect(")")
        elif t.kind == "sym" and t.val in "-~":
            self.next()
            self.term()
            self.emit("neg" if t.val == "-" else "not")
        elif t.kind == "id":
            self.next()
            if self.is_("["):
                self.next()
                self.push_var(t.val, t)
                self.expression()
                self.expect("]")
                self.emit("add", "pop pointer 1", "push that 0")
            elif self.is_("(") or self.is_("."):
                self.call(t.val, t)
            else:
                self.push_var(t.val, t)
        else:
            self.err(f"expected an expression but found '{t.val}'")


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def compile_source(src, fname="<input>", stem=None):
    """Compile Jack source text; returns a list of VM lines."""
    return Compiler(src, fname, stem or Path(fname).stem).compile_class()


def compile_path(path: Path):
    """Compile a .jack file or every .jack file in a directory. Returns (ok, written)."""
    if path.is_dir():
        files = sorted(path.glob("*.jack"))
        if not files:
            print(f"error: no .jack files found in '{path}'", file=sys.stderr)
            return False, []
    elif path.suffix == ".jack" and path.is_file():
        files = [path]
    else:
        print(f"error: expected a .jack file or a directory: '{path}'", file=sys.stderr)
        return False, []
    ok, written = True, []
    for f in files:
        try:
            vm = compile_source(f.read_text(), f.name, f.stem)
        except JackError as e:
            print(f"error: {e}", file=sys.stderr)
            ok = False
            continue
        out = f.with_suffix(".vm")
        out.write_text("\n".join(vm) + "\n")
        written.append(out)
    return ok, written


def main(argv=None):
    ap = argparse.ArgumentParser(description="nand2tetris Jack compiler")
    ap.add_argument("input", type=Path, help="a .jack file or a directory of .jack files")
    args = ap.parse_args(argv)
    ok, written = compile_path(args.input)
    for w in written:
        print(f"wrote {w}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
