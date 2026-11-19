#!/usr/bin/env python3
"""
VMTranslator.py -- nand2tetris VM translator (projects 7 and 8).

Translates Hack VM code (.vm) into Hack assembly (.asm).

Usage:
    python3 VMTranslator.py <Prog.vm | ProgDir> [-o OUT.asm] [--bootstrap | --no-bootstrap]

Input / output:
    * Prog.vm   ->  Prog.asm              (next to the input file)
    * ProgDir/  ->  ProgDir/ProgDir.asm   (all *.vm files in the directory)

Bootstrap code (SP = 256; call Sys.init) is emitted automatically when the
input defines a `Sys.init` function; --bootstrap / --no-bootstrap override
that. (The book runs NestedCall without bootstrap; its test script fakes the
frame bootstrap would build, so it passes either way.)

Comparisons: eq is inlined. gt/lt are shared subroutines (emitted once, at the
end of the output, only if used) that check the operands' signs first, so they
stay correct even when x - y would overflow 16 bits (e.g. -20000 < 20000).
The program always ends in an infinite loop so execution never runs into them.

Conventions:
    static i          ->  <FileName>.i        (per-file, e.g. Class1.0)
    label L           ->  <function>$L        (just L outside any function)
    return address    ->  <function>$ret.<n>  (n is a global counter)
"""

import argparse
import re
import sys
from pathlib import Path


class VMError(Exception):
    """Raised for malformed VM code; carries file/line information."""


# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------

ARITHMETIC = {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}
SEGMENTS = {"argument", "local", "static", "constant", "this", "that", "pointer", "temp"}
SYMBOL = re.compile(r"^[A-Za-z_.$:][A-Za-z0-9_.$:]*$")

# command -> (command kind, number of operands)
SHAPES = {
    "push": ("push", 2), "pop": ("pop", 2),
    "label": ("label", 1), "goto": ("goto", 1), "if-goto": ("if-goto", 1),
    "function": ("function", 2), "call": ("call", 2), "return": ("return", 0),
}
SHAPES.update({name: ("arithmetic", 0) for name in ARITHMETIC})


class Command:
    __slots__ = ("kind", "name", "arg1", "arg2", "line_no", "text")

    def __init__(self, kind, name, arg1, arg2, line_no, text):
        self.kind, self.name = kind, name
        self.arg1, self.arg2 = arg1, arg2
        self.line_no, self.text = line_no, text


def parse(source: str, filename: str):
    """Yield a Command for every VM command in `source`."""
    for line_no, raw in enumerate(source.splitlines(), start=1):
        text = raw.split("//", 1)[0].strip()
        if not text:
            continue

        def fail(msg):
            raise VMError(f"{filename}:{line_no}: {msg}: '{text}'")

        tokens = text.split()
        name, operands = tokens[0], tokens[1:]
        if name not in SHAPES:
            fail(f"unknown command '{name}'")
        kind, arity = SHAPES[name]
        if len(operands) != arity:
            fail(f"'{name}' takes {arity} operand(s), got {len(operands)}")

        arg1 = operands[0] if arity >= 1 else None
        arg2 = None

        if kind in ("push", "pop"):
            if arg1 not in SEGMENTS:
                fail(f"unknown segment '{arg1}'")
            if not operands[1].isdigit():
                fail("index must be a non-negative integer")
            arg2 = int(operands[1])
            if arg1 == "constant" and (kind == "pop" or arg2 > 32767):
                fail("invalid constant access (pop, or value > 32767)")
            if arg1 == "temp" and arg2 > 7:
                fail("temp index must be 0..7")
            if arg1 == "pointer" and arg2 > 1:
                fail("pointer index must be 0 or 1")
        elif kind in ("label", "goto", "if-goto", "function", "call"):
            if not SYMBOL.match(arg1):
                fail(f"invalid symbol '{arg1}'")
            if kind in ("function", "call"):
                if not operands[1].isdigit():
                    fail("argument count must be a non-negative integer")
                arg2 = int(operands[1])

        yield Command(kind, name, arg1, arg2, line_no, text)


# --------------------------------------------------------------------------
# Code writer
# --------------------------------------------------------------------------

BINARY_OPS = {"add": "M=D+M", "sub": "M=M-D", "and": "M=D&M", "or": "M=D|M"}
UNARY_OPS = {"neg": "M=-M", "not": "M=!M"}
BASES = {"local": "LCL", "argument": "ARG", "this": "THIS", "that": "THAT"}
FIXED = {"temp": lambda i: f"R{5 + i}", "pointer": lambda i: ("THIS", "THAT")[i]}

PUSH_D = ["@SP", "A=M", "M=D", "@SP", "M=M+1"]
POP_TO_D = ["@SP", "AM=M-1", "D=M"]


def _compare_routine(op):
    """
    Shared routine for `gt` / `lt`. Entry: y on top of stack, x below it,
    return address in R13. Exit: x replaced by true (-1) / false (0), SP -= 1.

    If x and y have different signs the answer is decided by the signs alone;
    otherwise x - y cannot overflow and its sign decides.
    """
    n = f"__{op.upper()}"
    # result when (x >= 0, y < 0) and when (x < 0, y >= 0)
    pos_neg, neg_pos = (n + ".TRUE", n + ".FALSE") if op == "gt" else (n + ".FALSE", n + ".TRUE")
    same_jump = "JGT" if op == "gt" else "JLT"
    return [
        f"({n})",
        "@SP", "AM=M-1", "D=M", "@R14", "M=D",           # R14 = y
        "@SP", "A=M-1", "D=M",                           # D = x
        f"@{n}.XNEG", "D;JLT",
        "@R14", "D=M", f"@{pos_neg}", "D;JLT",           # x >= 0, y < 0
        f"@{n}.SUB", "0;JMP",
        f"({n}.XNEG)",
        "@R14", "D=M", f"@{neg_pos}", "D;JGE",           # x < 0, y >= 0
        f"({n}.SUB)",                                    # same sign: x - y is safe
        "@SP", "A=M-1", "D=M", "@R14", "D=D-M",
        f"@{n}.TRUE", f"D;{same_jump}",
        f"({n}.FALSE)",
        "@SP", "A=M-1", "M=0", "@R13", "A=M", "0;JMP",
        f"({n}.TRUE)",
        "@SP", "A=M-1", "M=-1", "@R13", "A=M", "0;JMP",
    ]


class CodeWriter:
    def __init__(self):
        self.out = []
        self.file = ""        # current .vm file stem, used for static variables
        self.function = ""    # current VM function, used for label scoping
        self._labels = 0      # unique ids for comparison labels
        self._returns = 0     # unique ids for return addresses
        self._routines = set()  # shared comparison routines that were used

    # -- public ----------------------------------------------------------
    def set_file(self, stem):
        self.file = stem
        self.function = ""

    def bootstrap(self):
        self.out.append("// bootstrap: SP = 256; call Sys.init")
        self.out += ["@256", "D=A", "@SP", "M=D"]
        self._emit_call("Sys.init", 0, caller="$bootstrap")

    def finish(self):
        """Terminate the program with an infinite loop, then emit shared routines."""
        self.out += ["// end of program: loop forever", "(__END)", "@__END", "0;JMP"]
        for op in sorted(self._routines):
            self.out += _compare_routine(op)

    def write(self, c: Command):
        self.out.append(f"// {c.text}")
        getattr(self, "_" + c.kind.replace("-", "_"))(c)

    # -- helpers ---------------------------------------------------------
    def _scoped(self, label):
        return f"{self.function}${label}" if self.function else label

    # -- arithmetic / logic ---------------------------------------------
    def _arithmetic(self, c):
        op = c.name
        if op in BINARY_OPS:
            # y -> D, x stays in memory at the new stack top
            self.out += POP_TO_D + ["A=A-1", BINARY_OPS[op]]
        elif op in UNARY_OPS:
            self.out += ["@SP", "A=M-1", UNARY_OPS[op]]
        elif op == "eq":
            end = f"__EQ_END.{self._labels}"
            self._labels += 1
            # D = x - y (exact for equality even if it wraps); optimistically
            # store true (-1), fall through to false.
            self.out += POP_TO_D + [
                "A=A-1", "D=M-D", "M=-1",
                f"@{end}", "D;JEQ",
                "@SP", "A=M-1", "M=0",
                f"({end})",
            ]
        else:
            # gt / lt: call the shared routine; return address passed in R13
            ret = f"__CMP_RET.{self._labels}"
            self._labels += 1
            self._routines.add(op)
            self.out += [f"@{ret}", "D=A", "@R13", "M=D",
                         f"@__{op.upper()}", "0;JMP", f"({ret})"]

    # -- push / pop ------------------------------------------------------
    def _push(self, c):
        seg, i = c.arg1, c.arg2
        if seg == "constant":
            self.out += [f"@{i}", "D=A"]
        elif seg in BASES:
            if i == 0:
                self.out += [f"@{BASES[seg]}", "A=M", "D=M"]
            else:
                self.out += [f"@{i}", "D=A", f"@{BASES[seg]}", "A=D+M", "D=M"]
        elif seg in FIXED:
            self.out += [f"@{FIXED[seg](i)}", "D=M"]
        else:  # static
            self.out += [f"@{self.file}.{i}", "D=M"]
        self.out += PUSH_D

    def _pop(self, c):
        seg, i = c.arg1, c.arg2
        if seg in BASES:
            # compute target address first and park it in R13
            self.out += [f"@{BASES[seg]}", "D=M"]
            if i:
                self.out += [f"@{i}", "D=D+A"]
            self.out += ["@R13", "M=D"] + POP_TO_D + ["@R13", "A=M", "M=D"]
        else:
            target = FIXED[seg](i) if seg in FIXED else f"{self.file}.{i}"
            self.out += POP_TO_D + [f"@{target}", "M=D"]

    # -- program flow ----------------------------------------------------
    def _label(self, c):
        self.out.append(f"({self._scoped(c.arg1)})")

    def _goto(self, c):
        self.out += [f"@{self._scoped(c.arg1)}", "0;JMP"]

    def _if_goto(self, c):
        self.out += POP_TO_D + [f"@{self._scoped(c.arg1)}", "D;JNE"]

    # -- functions -------------------------------------------------------
    def _function(self, c):
        self.function = c.arg1
        self.out.append(f"({c.arg1})")
        if c.arg2:
            # zero k locals directly above SP, then bump SP once
            self.out += ["@SP", "A=M"]
            for _ in range(c.arg2):
                self.out += ["M=0", "A=A+1"]
            self.out += ["D=A", "@SP", "M=D"]

    def _call(self, c):
        self._emit_call(c.arg1, c.arg2, caller=self.function or "_")

    def _emit_call(self, name, nargs, caller):
        ret = f"{caller}$ret.{self._returns}"
        self._returns += 1

        self.out += [f"@{ret}", "D=A"] + PUSH_D               # push return address
        for reg in ("LCL", "ARG", "THIS", "THAT"):             # save caller frame
            self.out += [f"@{reg}", "D=M"] + PUSH_D
        self.out += ["@SP", "D=M", f"@{nargs + 5}", "D=D-A",   # ARG = SP - n - 5
                     "@ARG", "M=D"]
        self.out += ["@SP", "D=M", "@LCL", "M=D"]              # LCL = SP
        self.out += [f"@{name}", "0;JMP", f"({ret})"]

    def _return(self, c):
        self.out += [
            "@LCL", "D=M", "@R13", "M=D",          # R13 = FRAME = LCL
            "@5", "A=D-A", "D=M", "@R14", "M=D",   # R14 = RET = *(FRAME-5)
        ]
        self.out += POP_TO_D + ["@ARG", "A=M", "M=D"]          # *ARG = pop()
        self.out += ["@ARG", "D=M+1", "@SP", "M=D"]            # SP = ARG + 1
        for reg in ("THAT", "THIS", "ARG", "LCL"):             # restore caller
            self.out += ["@R13", "AM=M-1", "D=M", f"@{reg}", "M=D"]
        self.out += ["@R14", "A=M", "0;JMP"]                   # goto RET


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def collect_inputs(path: Path):
    """Return (list of .vm files, default output path)."""
    if path.is_dir():
        files = sorted(path.glob("*.vm"))
        if not files:
            raise VMError(f"no .vm files found in directory '{path}'")
        return files, path / f"{path.resolve().name}.asm"
    if path.suffix != ".vm":
        raise VMError(f"input must be a .vm file or a directory: '{path}'")
    if not path.is_file():
        raise VMError(f"no such file: '{path}'")
    return [path], path.with_suffix(".asm")


def translate(files, bootstrap=None):
    """Translate VM files into a single list of assembly lines."""
    sources = [(f, f.read_text()) for f in files]
    if bootstrap is None:
        bootstrap = any(re.search(r"^\s*function\s+Sys\.init\b", text, re.M)
                        for _, text in sources)
    writer = CodeWriter()
    if bootstrap:
        writer.bootstrap()
    for f, text in sources:
        writer.set_file(f.stem)
        for command in parse(text, f.name):
            writer.write(command)
    writer.finish()
    return writer.out


def main(argv=None):
    ap = argparse.ArgumentParser(description="nand2tetris VM translator")
    ap.add_argument("input", type=Path, help="a .vm file or a directory of .vm files")
    ap.add_argument("-o", "--output", type=Path, help="output .asm path")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--bootstrap", dest="bootstrap", action="store_true", default=None,
                       help="always emit bootstrap code")
    group.add_argument("--no-bootstrap", dest="bootstrap", action="store_false",
                       help="never emit bootstrap code")
    args = ap.parse_args(argv)

    try:
        files, default_out = collect_inputs(args.input)
        asm = translate(files, args.bootstrap)
    except VMError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    out = args.output or default_out
    out.write_text("\n".join(asm) + "\n")
    n = sum(1 for l in asm if not l.startswith(("//", "(")))
    print(f"wrote {out} ({n} instructions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
