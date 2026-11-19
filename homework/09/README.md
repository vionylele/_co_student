# Week 11 – nand2tetris VM Translator (Projects 7 & 8)

> **Note:** This document was created with the help of **Claude** (an AI assistant by Anthropic). It is based on the lecture slides *ECE 5745 Complex Digital ASIC Design – Topic 13: Physical Design Automation Algorithms* (Christopher Batten, Cornell University). Please verify technical details against the original source material.

---

A VM translator that converts Hack VM code (`.vm`) into Hack assembly (`.asm`),
a test runner, and a browser-based VM/CPU emulator.

## Contents

| File | Purpose |
|---|---|
| `VMTranslator.py` | The VM translator (command line, Python 3, no dependencies) |
| `run_tests.py` | Self-contained test runner: assembler + CPU emulator + `.tst`/`.cmp` checker |
| `vm_emulator.html` | Visual emulator: VM code → assembly → CPU, with ROM / RAM / stack views |
| `07-08_translated.zip` | Your `07/` and `08/` test folders with the generated `.asm` files |

## 1. VM Translator

```
python3 VMTranslator.py <Prog.vm | ProgDir> [-o OUT.asm] [--bootstrap | --no-bootstrap]
```

| Input | Output |
|---|---|
| `Prog.vm` | `Prog.asm` next to the input |
| `ProgDir/` | `ProgDir/ProgDir.asm` (all `*.vm` files combined) |

Examples:

```
python3 VMTranslator.py 07/StackArithmetic/SimpleAdd/SimpleAdd.vm
python3 VMTranslator.py 08/FunctionCalls/FibonacciElement
```

**Bootstrap.** The startup code (`SP = 256; call Sys.init`) is added automatically
when the input defines `Sys.init`. Use `--bootstrap` / `--no-bootstrap` to override.
(The book runs NestedCall without bootstrap; its test script fakes the frame that
bootstrap would build, so it passes either way.)

**Errors** are reported with file and line, e.g.
`bad.vm:2: unknown segment 'foo': 'push foo 2'`, and the exit code is 1.

### Translation conventions

| VM | Assembly |
|---|---|
| `static i` | variable `<FileName>.i` (e.g. `Class1.0`) |
| `label L` inside function `f` | `(f$L)` (just `(L)` outside any function) |
| return address | `(f$ret.N)`, `N` is a global counter |
| `temp i` / `pointer i` | `R(5+i)` / `THIS`, `THAT` |
| `eq` | inline, 12 instructions |
| `gt`, `lt` | shared subroutines `__GT` / `__LT`, emitted once and only if used |

`gt`/`lt` check the operands' signs before subtracting, so they stay correct when
`x - y` would overflow 16 bits (e.g. `-20000 < 20000`). The textbook approach gets
those cases wrong. The program always ends in an infinite loop (`__END`) so
execution never runs into the shared routines.

## 2. Tests

Place `VMTranslator.py` and `run_tests.py` next to your `07/` and `08/` folders:

```
python3 run_tests.py
```

For each test folder it translates the `.vm` files, assembles the result, runs it
on a built-in Hack CPU emulator following the folder's `.tst` script, and compares
the output-list values with the `.cmp` file. It also runs 192 extra comparison
cases (`eq`/`gt`/`lt` over values including -32768 and 32767) checked against Python.

Expected result: `12/12 tests passed`.

This does not replace the official CPU Emulator. To double-check there, load the
matching `.tst` file; it picks up the generated `.asm` next to it.

## 3. Browser emulator (`vm_emulator.html`)

Open the file in any browser (double-click it). No internet or installation needed.

1. Pick an example from the dropdown, paste your own VM code, or choose one or
   more `.vm` files (select several to load a whole program directory).
2. Click **Load**. The VM code is translated and assembled, RAM is reset, and `SP` is set to 256.
3. Click **Step** to run one instruction, or **Run** with a speed from Slow to Max.
   **Stop** pauses, **Reset** restarts the program.

What you see:

- **Registers:** PC, A, D, cycle count, and SP, LCL, ARG, THIS, THAT.
- **ROM:** instructions around the current PC, highlighted, with the VM command it came from.
- **Stack:** values from the top down, with the SP marker.
- **RAM:** a 24-cell window. Change the start address or use the quick buttons
  (0, 16, 256, LCL, ARG, THIS, THAT). Recently written cells are highlighted.
- **Show generated assembly:** the full `.asm` text.

**Editing RAM.** Click any RAM cell to set its value, like `set RAM[n] v` in a
`.tst` script. For example, BasicTest needs RAM[1..4] = 300, 400, 3000, 3010; the
built-in BasicTest example sets these for you. Values you set are kept when you press Reset.

Execution stops automatically at `__END`. A loop you wrote yourself (such as
`label END` / `goto END` in `Sys.init`) is not detected, so press **Stop**.

When loading several files, the page joins them with `//@file Name.vm` marker
lines. You can write these markers yourself to build a multi-file program in the
text box. The file name (without `.vm`) is used as the prefix for `static` variables.

## Requirements

- Translator and tests: Python 3.8+
- Emulator: any modern browser
