#!/usr/bin/env python3
"""
test_jack.py -- tests for JackCompiler.py.

Each test compiles Jack sources to VM code, then *runs* that VM code on a small
VM interpreter (real stack / segments / call frames, 16-bit arithmetic). The Jack
OS is replaced by native Python stand-ins (Output, Math, Memory, Array, String,
Keyboard, Screen, Sys), so the compiler's output can be checked end to end
without the real OS.

Also checks: exact VM output for Seven, VM syntax validity (via VMTranslator if
it can be found), and that bad programs are rejected with line-numbered errors.

Usage:  python3 test_jack.py
"""

import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import JackCompiler as jc

for cand in (HERE, HERE.parent / "week11", Path("/home/claude/work")):
    if (cand / "VMTranslator.py").exists():
        sys.path.insert(0, str(cand))
        break
try:
    import VMTranslator as vmt
except ImportError:
    vmt = None
try:
    import run_tests as hack          # Hack assembler + CPU emulator from week 11
except ImportError:
    hack = None


# --------------------------------------------------------------------------
# VM interpreter
# --------------------------------------------------------------------------
def w16(x):
    x &= 0xFFFF
    return x - 0x10000 if x & 0x8000 else x


class VMRuntimeError(Exception):
    pass


class VM:
    HEAP = 2048

    def __init__(self, vm_texts, inputs=(), keys=()):
        self.ram = [0] * 32768
        self.ram[0] = 256
        self.statics = {}
        self.funcs = {}
        self.out = []
        self.inputs, self.keys = list(inputs), list(keys)
        self.heap, self.strings, self.screen_calls = self.HEAP, {}, []
        for text in vm_texts:
            self._load(text)

    def _load(self, text):
        fn = None
        for raw in text.splitlines():
            line = raw.split("//")[0].split()
            if not line:
                continue
            if line[0] == "function":
                fn = {"name": line[1], "nvars": int(line[2]), "code": [], "labels": {}}
                self.funcs[line[1]] = fn
            elif line[0] == "label":
                fn["labels"][line[1]] = len(fn["code"])
            else:
                fn["code"].append(tuple(line))

    # -- memory / stack ---------------------------------------------------
    def push(self, v):
        self.ram[self.ram[0]] = w16(v)
        self.ram[0] += 1

    def pop(self):
        self.ram[0] -= 1
        return self.ram[self.ram[0]]

    def alloc(self, n):
        addr, self.heap = self.heap, self.heap + max(n, 1)
        return addr

    def addr(self, seg, i, fn):
        if seg == "local": return self.ram[1] + i
        if seg == "argument": return self.ram[2] + i
        if seg == "this": return self.ram[3] + i
        if seg == "that": return self.ram[4] + i
        if seg == "pointer": return 3 + i
        if seg == "temp": return 5 + i
        raise VMRuntimeError(f"bad segment {seg}")

    # -- execution --------------------------------------------------------
    def run(self, entry, max_steps=3_000_000):
        frames = []
        fn, pc = None, 0

        def call(name, nargs):
            nonlocal fn, pc
            if name in self.funcs:
                frames.append((fn, pc))
                base = self.ram[0] - nargs
                for v in (0, self.ram[1], self.ram[2], self.ram[3], self.ram[4]):
                    self.push(v)
                self.ram[2], self.ram[1] = base, self.ram[0]
                fn, pc = self.funcs[name], 0
                for _ in range(fn["nvars"]):
                    self.push(0)
            elif name in NATIVE:
                args = [self.pop() for _ in range(nargs)][::-1]
                self.push(NATIVE[name](self, *args) or 0)
            else:
                raise VMRuntimeError(f"call to undefined function {name}")

        call(entry, 0)
        steps = 0
        while fn is not None:
            steps += 1
            if steps > max_steps:
                raise VMRuntimeError("step limit exceeded (infinite loop?)")
            if pc >= len(fn["code"]):
                raise VMRuntimeError(f"fell off the end of {fn['name']}")
            ins = fn["code"][pc]
            pc += 1
            op = ins[0]
            if op == "push":
                seg, i = ins[1], int(ins[2])
                if seg == "constant": self.push(i)
                elif seg == "static": self.push(self.statics.get((fn["name"].split(".")[0], i), 0))
                else: self.push(self.ram[self.addr(seg, i, fn)])
            elif op == "pop":
                seg, i = ins[1], int(ins[2])
                v = self.pop()
                if seg == "static": self.statics[(fn["name"].split(".")[0], i)] = v
                else: self.ram[self.addr(seg, i, fn)] = v
            elif op in ("add", "sub", "and", "or", "eq", "gt", "lt"):
                y, x = self.pop(), self.pop()
                self.push({"add": x + y, "sub": x - y, "and": x & y, "or": x | y,
                           "eq": -(x == y), "gt": -(x > y), "lt": -(x < y)}[op])
            elif op == "neg": self.push(-self.pop())
            elif op == "not": self.push(~self.pop())
            elif op == "label": pass
            elif op == "goto": pc = fn["labels"][ins[1]]
            elif op == "if-goto":
                if self.pop() != 0: pc = fn["labels"][ins[1]]
            elif op == "call": call(ins[1], int(ins[2]))
            elif op == "return":
                frame, ret = self.ram[1], self.pop()
                self.ram[self.ram[2]] = ret
                self.ram[0] = self.ram[2] + 1
                self.ram[4], self.ram[3] = self.ram[frame - 1], self.ram[frame - 2]
                self.ram[2], self.ram[1] = self.ram[frame - 3], self.ram[frame - 4]
                fn, pc = frames.pop()
            else:
                raise VMRuntimeError(f"unknown VM command {ins}")
        return self.ram[0]


# --------------------------------------------------------------------------
# Native OS stand-ins
# --------------------------------------------------------------------------
def _div(x, y):
    if y == 0:
        raise VMRuntimeError("division by zero")
    q = abs(x) // abs(y)
    return q if (x < 0) == (y < 0) else -q


def _new_string(vm, n):
    p = vm.alloc(2)
    vm.strings[p] = []
    return p


def _printstr(vm, s):
    vm.out.append("".join(chr(c) for c in vm.strings[s]))


def _key(vm):
    return vm.keys.pop(0) if vm.keys else 0  # no key pressed once the script runs out


def _read_int(vm, prompt):
    _printstr(vm, prompt)
    return vm.inputs.pop(0)


def _screen(vm, name):
    return lambda vm_, *a: vm.screen_calls.append((name, a))


def _set_int(vm, s, n):
    vm.strings[s] = [ord(c) for c in str(n)]


NATIVE = {
    "Math.multiply": lambda vm, x, y: x * y,
    "Math.divide": lambda vm, x, y: _div(x, y),
    "Math.abs": lambda vm, x: abs(x),
    "Math.min": lambda vm, x, y: min(x, y),
    "Math.max": lambda vm, x, y: max(x, y),
    "Math.sqrt": lambda vm, x: int(x ** 0.5),
    "Memory.alloc": lambda vm, n: vm.alloc(n),
    "Memory.deAlloc": lambda vm, p: 0,
    "Memory.peek": lambda vm, a: vm.ram[a],
    "Memory.poke": lambda vm, a, v: vm.ram.__setitem__(a, v),
    "Array.new": lambda vm, n: vm.alloc(n),
    "Array.dispose": lambda vm, p: 0,
    "String.new": _new_string,
    "String.appendChar": lambda vm, s, c: (vm.strings[s].append(c), s)[1],
    "String.length": lambda vm, s: len(vm.strings[s]),
    "String.charAt": lambda vm, s, i: vm.strings[s][i],
    "String.setInt": _set_int,
    "String.dispose": lambda vm, s: 0,
    "Output.printString": _printstr,
    "Output.printInt": lambda vm, n: vm.out.append(str(n)),
    "Output.printChar": lambda vm, c: vm.out.append(chr(c)),
    "Output.println": lambda vm: vm.out.append("\n"),
    "Keyboard.readInt": _read_int,
    "Keyboard.keyPressed": _key,
    "Sys.wait": lambda vm, n: 0,
    "Sys.halt": lambda vm: (_ for _ in ()).throw(VMRuntimeError("Sys.halt")),
}
for _n in ("setColor", "drawRectangle", "drawPixel", "drawLine", "drawCircle", "clearScreen"):
    NATIVE["Screen." + _n] = (lambda n: lambda vm, *a: vm.screen_calls.append((n, a)))(_n)


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------
def compile_dir(d):
    ok, written = jc.compile_path(d)
    if not ok:
        raise AssertionError(f"compilation of {d} failed")
    return written


def run_program(d, **kw):
    vm = VM([p.read_text() for p in compile_dir(d)], **kw)
    sp = vm.run("Main.main")
    return vm, sp


def t_seven():
    vm, _ = run_program(HERE / "tests/Seven")
    assert "".join(vm.out) == "7", vm.out
    ref = ["function Main.main 0", "push constant 1", "push constant 2", "push constant 3",
           "call Math.multiply 2", "add", "call Output.printInt 1", "pop temp 0",
           "push constant 0", "return"]
    got = (HERE / "tests/Seven/Main.vm").read_text().split("\n")[:-1]
    assert got == ref, got


def t_convert():
    d = HERE / "tests/ConvertToBin"
    vm = VM([p.read_text() for p in compile_dir(d)])
    vm.ram[8000] = 19  # 0b10011
    vm.run("Main.main")
    bits = [vm.ram[8001 + i] for i in range(16)]
    assert bits == [1, 1, 0, 0, 1] + [0] * 11, bits


def t_average():
    vm, _ = run_program(HERE / "tests/Average", inputs=[3, 10, 20, 33])
    want = "How many numbers? " + "Enter a number: " * 3 + "The average is 21\n"
    assert "".join(vm.out) == want, vm.out


def t_arrays():
    vm, _ = run_program(HERE / "tests/ComplexArrays")
    assert "".join(vm.out) == "5\n40\n0\n", vm.out


def t_features():
    vm, sp = run_program(HERE / "tests/Features")
    want = "6\n15\n21\n55\nHi!\n3\n-4\n3\n-1\n6\nyes\nnull is 0\nelse ok\n5050\n8\n18\n20\n"
    assert "".join(vm.out) == want, vm.out


def t_square():
    # keys: right (hold, release), down (hold, release), 'x' grow, 'z' shrink, 'q' quit, release
    vm, _ = run_program(HERE / "tests/Square", keys=[0, 132, 132, 0, 133, 133, 0, 88, 0, 90, 0, 81, 0])
    rects = [a for n, a in vm.screen_calls if n == "drawRectangle"]
    assert len(rects) >= 10, len(rects)
    rects = [tuple(r) for r in rects]
    assert rects[0] == (0, 0, 30, 30), rects[0]          # initial draw of Square.new(0,0,30)
    # moving right: erase the 1-px column at the old left edge, draw one at the new right edge
    assert rects[1:3] == [(0, 0, 1, 30), (31, 0, 32, 30)], rects[:3]
    # moving down afterwards: erase the old top row, draw a new bottom row
    assert (6, 0, 36, 1) in rects and (6, 31, 36, 32) in rects, rects[:10]


def t_stack_balanced():
    """After main returns, only main's return value should remain on the stack."""
    for name in ("Seven", "ConvertToBin", "Average", "ComplexArrays", "Features"):
        kw = {"inputs": [2, 4, 6]} if name == "Average" else {}
        vm, sp = run_program(HERE / "tests" / name, **kw)
        assert sp == 257, f"{name}: SP={sp} (expected 257: stack not balanced)"


def t_vm_syntax():
    if vmt is None:
        return "skipped (VMTranslator.py not found)"
    for d in (HERE / "tests").iterdir():
        files = compile_dir(d)
        vmt.translate(files, bootstrap=False)   # raises VMError on invalid VM code


def t_hack_end_to_end():
    """Jack -> VM -> asm -> Hack CPU, for a program that needs no OS routines."""
    if vmt is None or hack is None:
        return "skipped (week 11 VMTranslator.py / run_tests.py not found)"
    files = compile_dir(HERE / "tests/HackE2E")
    asm = vmt.translate(files)                       # Sys.init is defined -> bootstrap added
    ram = [0] * 32768
    hack.run(hack.assemble(asm), ram, 300_000)
    assert ram[16] == 5216, f"RAM[16] = {ram[16]} (expected 5216)"
    return f"RAM[16] = {ram[16]}, {len(asm)} asm lines"


BAD = {
    "undefined variable": ("class Main { function void main() { let x = 1; return; } }", "undefined variable 'x'"),
    "missing semicolon": ("class Main { function void main() { do Output.println() return; } }", "expected ';'"),
    "int too large": ("class Main { function void main() { var int a; let a = 40000; return; } }", "larger than 32767"),
    "field in function": ("class Main { field int a; function void main() { let a = 1; return; } }", "field 'a' cannot be used in a function"),
    "void returns value": ("class Main { function void main() { return 1; } }", "void subroutine cannot return a value"),
    "missing return value": ("class Main { function int f() { return; } }", "must return a value"),
    "duplicate variable": ("class Main { function void main() { var int a, a; return; } }", "already declared"),
    "unterminated comment": ("class Main { /* oops }", "unterminated comment"),
    "unterminated string": ('class Main { function void main() { do Output.printString("abc); return; } }', "unterminated string"),
    "bad statement": ("class Main { function void main() { 5; return; } }", "expected '}'"),
}


def t_errors():
    for name, (src, frag) in BAD.items():
        try:
            jc.compile_source(src, "Main.jack", "Main")
        except jc.JackError as e:
            assert frag in str(e) and str(e).startswith("Main.jack:1:"), f"{name}: {e}"
        else:
            raise AssertionError(f"{name}: expected a compile error")


def t_multiline_error_line():
    try:
        jc.compile_source("class Main {\n  function void main() {\n\n    let y = 2;\n    return;\n  }\n}", "Main.jack", "Main")
    except jc.JackError as e:
        assert str(e).startswith("Main.jack:4:"), e
    else:
        raise AssertionError("expected error")


TESTS = [t_seven, t_convert, t_average, t_arrays, t_features, t_square,
         t_stack_balanced, t_vm_syntax, t_hack_end_to_end, t_errors, t_multiline_error_line]


def main():
    failed = 0
    for t in TESTS:
        try:
            note = t()
            print(f"PASS  {t.__name__[2:]}" + (f"  ({note})" if note else ""))
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL  {t.__name__[2:]}: {type(e).__name__}: {e}")
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
