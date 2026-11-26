# Week 12 – nand2tetris Jack Compiler (Projects 10 & 11)

> **Note:** This document was created with the help of **Claude** (an AI assistant by Anthropic). It is based on the lecture slides *ECE 5745 Complex Digital ASIC Design – Topic 13: Physical Design Automation Algorithms* (Christopher Batten, Cornell University). Please verify technical details against the original source material.

Compiles Jack (`.jack`) into Hack VM code (`.vm`). Pairs with the Week 11 VM translator
to take a Jack program all the way to Hack assembly.

## Contents

| File | Purpose |
|---|---|
| `JackCompiler.py` | The compiler (Python 3, no dependencies) |
| `test_jack.py` | Test suite (compiles, then *runs* the generated VM code) |
| `jack_vm_simulator.html` | Browser VM simulator: paste Jack or VM code, compile, step/run, inspect stack, segments, call stack, screen, output |
| `tests/` | Jack test programs (and the `.vm` files generated from them) |

## Usage

```
python3 JackCompiler.py Prog.jack      # -> Prog.vm
python3 JackCompiler.py ProgDir/       # -> one .vm per .jack file in the directory
```

To continue to assembly (with `../week11/VMTranslator.py`): copy the Jack OS `.vm` files
into the same directory, then `python3 VMTranslator.py ProgDir`.
Or load the directory in the official VM Emulator, which has the OS built in.

Errors are printed as `File.jack:LINE: message` and the exit code is 1, e.g.
`Main.jack:4: undefined variable 'y'`.

## How it works

Tokenizer → recursive-descent parser that emits VM code directly → symbol table with a
class scope (`static`, `field`) and a subroutine scope (`argument`, `local`).

| Jack | VM code |
|---|---|
| `constructor` | `push constant <fields>; call Memory.alloc 1; pop pointer 0` |
| `method` | `this` is `argument 0` (declared parameters start at 1); `push argument 0; pop pointer 0` |
| `let a[i] = e` | `push a; <i>; add; <e>; pop temp 0; pop pointer 1; push temp 0; pop that 0` |
| `if` / `while` | labels `IF_TRUE/IF_FALSE/IF_END n`, `WHILE_EXP/WHILE_END n` (counted per subroutine) |
| `do f()` | call, then `pop temp 0` |
| `return;` | `push constant 0; return` |
| `*`, `/` | `call Math.multiply 2`, `call Math.divide 2` |
| string constant | `String.new`, then `String.appendChar` per character |
| `true`, `false`/`null`, `this` | `push constant 0; not`, `push constant 0`, `push pointer 0` |
| `f(x)` / `obj.f(x)` / `Class.f(x)` | method on `this` / method on `obj` (receiver pushed first) / function |

Semantic checks: undefined or duplicate variables, fields or `this` used in a function,
`return` value vs. `void`, integer constants above 32767, unterminated comments and strings.
Expressions evaluate strictly left to right (Jack has no operator precedence).

## Tests

```
python3 test_jack.py        # expected: 11/11 tests passed
```

The suite compiles each program and executes the VM code on a small interpreter with
native stand-ins for the OS (Output, Math, Memory, Array, String, Keyboard, Screen, Sys).

| Test | What it checks |
|---|---|
| `seven` | Prints 7; VM output is identical to the reference translation of Seven |
| `convert` | ConvertToBin unpacks 19 into 16 bits in RAM[8001..8016] |
| `average` | Strings, `Array.new`, `a[i]`, `while`, integer division |
| `arrays` | Nested array indexing on both sides of `let` |
| `features` | Classes, constructors, methods (with parameters), static/field, recursion, operators, `null`, if/else |
| `square` | Square/SquareGame: object graph, method calls, drawing calls from a scripted key sequence |
| `stack_balanced` | The stack is balanced after `Main.main` returns |
| `vm_syntax` | Every generated `.vm` is accepted by the Week 11 translator |
| `hack_end_to_end` | Jack → VM → asm → Hack CPU for an OS-free program (`RAM[16] = 5216`) |
| `errors` | 10 kinds of bad programs are rejected with a line-numbered message |

Note: the Seven, ConvertToBin, Average and Square programs here are recreations of the
standard Chapter 11 programs, written without access to the official files. To test against
the official Chapter 11 project, compile each of its directories and run the supplied
test scripts in the official VM Emulator.

## Browser simulator (`jack_vm_simulator.html`)

Open the file in any browser (double-click it). No internet or installation needed.

1. Pick an example, or paste Jack classes (several classes can go in one box) or raw VM code.
2. Click **Compile & load**, then **Step** (one VM command) or **Run** (speed selectable).
3. Panels: VM code with the next command highlighted, call stack, stack, segments
   (local / argument / this / that / pointer / temp / static), screen canvas and text output.

The compiler is a JavaScript port of `JackCompiler.py`; the Jack OS (Output, Math, Memory,
Array, String, Screen, Keyboard, Sys) is built in. Entry point is `Sys.init` if defined,
otherwise `Main.main`. Click the screen and use the keyboard for programs that read keys.
