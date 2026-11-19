#!/usr/bin/env python3
"""
run_tests.py -- verifies VMTranslator.py against the nand2tetris test suites.

For every test directory under the given root(s) it:
  1. translates the directory's .vm files with VMTranslator,
  2. assembles the result with a built-in Hack assembler,
  3. runs it on a built-in Hack CPU emulator, following the directory's .tst
     script (set RAM[..], repeat N { ticktock }, output-list ...),
  4. compares the output-list values with the directory's .cmp file.

Usage:  python3 run_tests.py [root ...]        (default: 07 08 next to this file)
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import VMTranslator as vm

# --------------------------------------------------------------------------
# Hack assembler
# --------------------------------------------------------------------------
COMP = {
    "0": "101010", "1": "111111", "-1": "111010", "D": "001100", "A": "110000",
    "!D": "001101", "!A": "110001", "-D": "001111", "-A": "110011",
    "D+1": "011111", "A+1": "110111", "D-1": "001110", "A-1": "110010",
    "D+A": "000010", "D-A": "010011", "A-D": "000111", "D&A": "000000", "D|A": "010101",
}
DEST = {"": 0, "M": 1, "D": 2, "MD": 3, "A": 4, "AM": 5, "AD": 6, "AMD": 7}
JUMP = {"": 0, "JGT": 1, "JEQ": 2, "JGE": 3, "JLT": 4, "JNE": 5, "JLE": 6, "JMP": 7}
PREDEF = {"SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4, "SCREEN": 16384, "KBD": 24576,
          **{f"R{i}": i for i in range(16)}}


def comp_bits(expr):
    a = "1" if "M" in expr else "0"
    e = expr.replace("M", "A")
    if e not in COMP:                       # commutative operators: try swapped
        for op in "+&|":
            if op in e:
                l, r = e.split(op)
                e = r + op + l
                break
    if e not in COMP:
        raise ValueError(f"bad comp '{expr}'")
    return a + COMP[e]


def assemble(lines):
    code, symbols, pc = [], dict(PREDEF), 0
    for raw in lines:
        s = re.sub(r"//.*", "", raw).replace(" ", "").strip()
        if not s:
            continue
        if s.startswith("("):
            if s[1:-1] in symbols and s[1:-1] not in PREDEF:
                raise ValueError(f"duplicate label {s}")
            symbols[s[1:-1]] = pc
        else:
            code.append(s)
            pc += 1
    nxt, rom = 16, []
    for s in code:
        if s[0] == "@":
            v = s[1:]
            if v.isdigit():
                n = int(v)
            else:
                if v not in symbols:
                    symbols[v] = nxt
                    nxt += 1
                n = symbols[v]
            rom.append(n)
        else:
            dest, _, rest = s.partition("=") if "=" in s else ("", "", s)
            comp, _, jump = rest.partition(";")
            rom.append(int("111" + comp_bits(comp) + format(DEST[dest], "03b")
                           + format(JUMP[jump], "03b"), 2))
    return rom


# --------------------------------------------------------------------------
# Hack CPU emulator
# --------------------------------------------------------------------------
def to_signed(x):
    x &= 0xFFFF
    return x - 0x10000 if x & 0x8000 else x


def alu(c, x, y):
    if c & 0b100000: x = 0
    if c & 0b010000: x = ~x & 0xFFFF
    if c & 0b001000: y = 0
    if c & 0b000100: y = ~y & 0xFFFF
    out = (x + y) if c & 0b000010 else (x & y)
    if c & 0b000001: out = ~out
    return out & 0xFFFF


def run(rom, ram, ticks):
    rom = rom + [0] * (32768 - len(rom))
    a = d = pc = 0
    for _ in range(ticks):
        ins = rom[pc]
        if not ins & 0x8000:
            a, pc = ins, pc + 1
            continue
        y = ram[a] if ins & 0x1000 else a
        out = alu((ins >> 6) & 0x3F, d, y)
        dest, jmp, s = (ins >> 3) & 7, ins & 7, to_signed(out)
        take = ((jmp & 1 and s > 0) or (jmp & 2 and s == 0) or (jmp & 4 and s < 0))
        pc = a if take else pc + 1           # jump target is the *old* A
        if dest & 1: ram[a] = out            # M is written at the *old* A
        if dest & 2: d = out
        if dest & 4: a = out
        pc &= 0x7FFF
    return ram


# --------------------------------------------------------------------------
# .tst / .cmp handling
# --------------------------------------------------------------------------
def read_tst(path):
    text = re.sub(r"//.*", "", path.read_text())
    sets = [(int(a), int(v)) for a, v in re.findall(r"set\s+RAM\[(\d+)\]\s+(-?\d+)", text)]
    ticks = sum(int(n) for n in re.findall(r"repeat\s+(\d+)", text))
    out = re.search(r"output-list\s+(.*?);", text, re.S).group(1)
    cells = [int(a) for a in re.findall(r"RAM\[(\d+)\]", out)]
    return sets, ticks, cells


def read_cmp(path):
    rows = [r for r in path.read_text().splitlines() if r.strip()]
    return [int(x) for x in rows[1].strip("|").split("|")]


# Tests whose .tst builds its own stack frame (the book says: no bootstrap).
NO_BOOTSTRAP = {"NestedCall"}


def run_test(d: Path):
    name = d.name
    tst = d / f"{name}.tst"
    files, _ = vm.collect_inputs(d)
    boot = False if name in NO_BOOTSTRAP else None     # None = auto-detect
    asm = vm.translate(files, boot)
    (d / f"{name}.asm").write_text("\n".join(asm) + "\n")

    sets, ticks, cells = read_tst(tst)
    ram = [0] * 32768
    for a, v in sets:
        ram[a] = v & 0xFFFF
    run(assemble(asm), ram, ticks)
    got = [to_signed(ram[c]) for c in cells]
    want = read_cmp(d / f"{name}.cmp")
    return got == want, got, want, cells


def extra_compare_test():
    """Every eq/gt/lt over extreme values, checked against Python (overflow cases!)."""
    import tempfile
    vals = [-32768, -32767, -20000, -1, 0, 1, 20000, 32767]

    def push(v):
        if v >= 0:
            return [f"push constant {v}"]
        if v == -32768:
            return ["push constant 32767", "neg", "push constant 1", "sub"]
        return [f"push constant {-v}", "neg"]

    prog, want = [], []
    for x in vals:
        for y in vals:
            for op, f in (("eq", x == y), ("gt", x > y), ("lt", x < y)):
                prog += push(x) + push(y) + [op]
                want.append(-1 if f else 0)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "Cmp.vm"
        src.write_text("\n".join(prog) + "\n")
        asm = vm.translate([src])
    ram = [0] * 32768
    ram[0] = 256
    run(assemble(asm), ram, 400_000)
    got = [to_signed(v) for v in ram[256:256 + len(want)]]
    ok = got == want and ram[0] == 256 + len(want)
    bad = [(i, g, w) for i, (g, w) in enumerate(zip(got, want)) if g != w][:5]
    return ok, len(want), bad


def main(roots):
    dirs = sorted({t.parent for r in roots for t in Path(r).rglob("*.tst")
                   if not t.name.endswith("VME.tst")})
    failed = 0
    for d in dirs:
        try:
            ok, got, want, cells = run_test(d)
        except Exception as e:                      # noqa: BLE001
            ok, got, want, cells = False, repr(e), "-", []
        print(f"{'PASS' if ok else 'FAIL'}  {d.parent.name}/{d.name}")
        if not ok:
            failed += 1
            print(f"      cells={cells}\n      got ={got}\n      want={want}")
    ok, n, bad = extra_compare_test()
    print(f"{'PASS' if ok else 'FAIL'}  extra/comparison edge cases ({n} comparisons)")
    if not ok:
        failed += 1
        print(f"      first mismatches (index, got, want): {bad}")
    total = len(dirs) + 1
    print(f"\n{total - failed}/{total} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    here = Path(__file__).parent
    sys.exit(main(sys.argv[1:] or [here / "07", here / "08"]))
