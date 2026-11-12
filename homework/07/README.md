> **Note:** This README was **created by Claude** (an AI assistant by Anthropic) by summarizing the contents of the whole homework repository. Please verify technical details against the original files.

## Weekly Checklist
每週檢驗表格

每週檢驗表格
第幾週 |  習題內容 | 有上課且準時繳交 |  補交 | 且附上請假證明 | 作業連結
-------|----------|--------------------|-----|----------------|-------------
3          | 第 1, 2 章   |   是 |   | |[01](https://github.com/vionylele/_co_student/tree/main/homework/01), [02](https://github.com/vionylele/_co_student/tree/main/homework/02)
4          | 第3 章除 PC | 是 |   |  |[03](https://github.com/vionylele/_co_student/tree/main/homework/03) | 
5          | 第 4 章 | 是 |  |  |[04](https://github.com/vionylele/_co_student/tree/main/homework/04) | 
6          | HackCPU 電路圖 | 是 |  ||[HACKCPU](https://github.com/vionylele/_co_student/blob/main/homework/05/HACKCPU.jpg)| 
7          | 第 5 章 | 是 |  |  |[05](https://github.com/vionylele/_co_student/tree/main/homework/06) | 
8          | EDA 軟體報告 | 是 |  ||[06](https://github.com/vionylele/_co_student/tree/main/homework/06)| 

## Summary of All Homework

This repository contains six weekly assignments following the **Nand2Tetris** curriculum (*The Elements of Computing Systems*, Nisan & Schocken): building the Hack computer from a Nand gate, then studying Electronic Design Automation (EDA).

| HW | Topic | Contents | Folder |
|:--:|---|---|---|
| 01 | Elementary logic gates | Not, And, Or, Xor, Mux, DMux, 16-bit and multi-way versions | [`homework/01`](homework/01) |
| 02 | Boolean arithmetic | HalfAdder, FullAdder, Add16, Inc16, ALU | [`homework/02`](homework/02) |
| 03 | Memory (sequential) | Bit, Register, RAM8 → RAM16K, PC | [`homework/03`](homework/03) |
| 04 | Machine language | Assembly programs `Mult.asm` and `Fill.asm` | [`homework/04`](homework/04) |
| 05 | Computer architecture | Memory, CPU, Computer + `.hack` programs | [`homework/05`](homework/05) |
| 06 | EDA study notes | Physical Design Automation overview | [`homework/06`](homework/06) |

---

## Homework 01 — Elementary Logic Gates

Every chip is built from a single primitive: **Nand**.

- **Basic gates:** `Not`, `And`, `Or`, `Xor`
- **Routing:** `Mux`, `DMux`
- **16-bit bus versions:** `Not16`, `And16`, `Or16`, `Mux16`
- **Multi-way versions:** `Or8Way`, `Mux4Way16`, `Mux8Way16`, `DMux4Way`, `DMux8Way`

Each chip has an `.hdl` file (implementation), a `.tst` file (test script), and a `.cmp` file (expected output). Full explanations, truth tables, and design strategy are in [`implementation.md`](homework/01/implementation.md).

## Homework 02 — Boolean Arithmetic

- **`HalfAdder`** and **`FullAdder`**: 1-bit adders (the FullAdder is built from two HalfAdders and an Or gate).
- **`Add16`**: 16-bit adder using a *ripple-carry* architecture.
- **`Inc16`**: 16-bit incrementer (+1).
- **`ALU`**: the Hack Arithmetic Logic Unit, with control bits `zx, nx, zy, ny, f, no` and output flags `zr` and `ng`.

Documentation and test screenshots are in [`implementation.md`](homework/02/implementation.md), `week3_03.png`, `week3_04.png`, and `week3_05.png`.

## Homework 03 — Memory

Folder `a/` (small memories) and `b/` (large memories):

- **a/** — `Bit`, `Register`, `RAM8`, `RAM64`, `PC`
- **b/** — `RAM512`, `RAM4K`, `RAM16K`

The RAM hierarchy is built in layers: each larger RAM uses eight (or four) smaller RAMs, with a `DMux` selecting where to write and a `Mux` selecting which output to read.

> ⚠️ **Status to be aware of** (based on Claude's reading of the files in the repository):
> - `a/PC.hdl` is still empty (only the `PARTS:` skeleton, no implementation).
> - `a/Bit.hdl` contains code that looks like `RAM8` (it uses `DMux8Way`, `Register`, and `address`) rather than a 1-bit flip-flop built from `DFF`. The file contents may have been swapped and should be checked.

## Homework 04 — Machine Language

Two Hack assembly programs:

- **`mult/mult.asm`** — multiplies `R0` × `R1` and stores the result in `R2` by repeated addition: `R2 += R0`, repeated `R1` times.
- **`fill/Fill.asm`** — an infinite loop that reads the keyboard (`@KBD`). While a key is pressed the whole screen is blackened; otherwise the screen is cleared.

Test scripts and reference outputs (`Mult.tst`, `Mult.cmp`, `Fill.tst`, `FillAutomatic.tst`, etc.) are included.

## Homework 05 — Computer Architecture

- **`Memory.hdl`** — the full address space: RAM16K (`0x0000–0x3FFF`), Screen (`0x4000–0x5FFF`), and Keyboard (`0x6000`), with address decoding on bits 14 and 13.
- **`CPU.hdl`** — the Hack CPU: A/C instruction decoder, A and D registers, ALU, jump logic, and Program Counter.
- **`Computer.hdl`** — the complete computer: `ROM32K` + `CPU` + `Memory`.
- **`.hack` test programs:** `Add.hack`, `Max.hack`, `Rect.hack`, with `.tst`, `.cmp`, and `.out` files for `CPU`, `Memory`, `ComputerAdd`, `ComputerMax`, and `ComputerRect`.
- `HACKCPU.jpg` — Hack CPU architecture diagram.

## Homework 06 — EDA in IC Design

Study notes in an English [README](homework/06/README.md), based on the slides *ECE 5745 Complex Digital ASIC Design – Topic 13: Physical Design Automation Algorithms* (Christopher Batten, Cornell University). Topics covered:

- Where physical design fits in the CAD flow
- **Placement** — partitioning (Kernighan–Lin, min-cut) and analytical placement
- **Global routing** — channels, capacity, switchboxes, feedthroughs, Steiner trees
- **Detailed routing** — horizontal/vertical constraint graphs (HCG/VCG) and the *left-edge* algorithm

That document also states that it was written with Claude's help and links to a study conversation with Gemini.

---

## Repository Structure

```
.
├── README.md
└── homework/
    ├── 01/   logic gates (.hdl/.tst/.cmp) + implementation.md
    ├── 02/   adders & ALU + implementation.md + images
    ├── 03/
    │   ├── a/   Bit, Register, RAM8, RAM64, PC
    │   └── b/   RAM512, RAM4K, RAM16K
    ├── 04/
    │   ├── mult/   mult.asm
    │   └── fill/   Fill.asm
    ├── 05/   CPU, Memory, Computer, .hack programs
    └── 06/   README.md (EDA notes)
```

## How to Run

The `.hdl` chips and `.asm` programs are tested with the **Nand2Tetris Hardware Simulator** and **CPU Emulator**. Open the matching `.tst` file in the simulator; the output is compared against the `.cmp` file.

---

*This README was created by Claude (Anthropic).*
