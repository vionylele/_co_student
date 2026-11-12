# Hack Assembler (Nand2Tetris Project 6)

A two-pass assembler for the Hack assembly language from the Nand2Tetris course. It translates `.asm` files into `.hack` files of 16-bit binary machine code.

**Author:** Written by Claude, an AI assistant made by Anthropic.

## Requirements

- Python 3.9 or newer
- No third-party packages
- For the windowed version: tkinter, which is included with the standard Python installer for Windows and macOS

## Files

| File | Purpose |
|------|---------|
| `assembler.py` | Command-line version |
| `assembler_gui.py` | Windowed version (no terminal needed) |
| `Add.asm` | Small example program (computes R0 = 2 + 3) |
| `README.md` | This file |

The two versions are independent, and each contains the full assembler. You only need the one you plan to use.

## How to run

### Option 1: Command line

1. Put `assembler.py` and your assembly file in the same folder.
2. Open a terminal in that folder and run:

   ```
   python assembler.py Add.asm
   ```

   Replace `Add.asm` with the exact name of your own file. On some systems you may need `python3` instead of `python`.

3. The assembler writes `Add.hack` in the same folder and prints:

   ```
   Wrote 8 instructions to Add.hack
   ```

If you see `FileNotFoundError`, the file name is wrong or the file is not in the folder you are running the command from.

### Option 2: Window app

1. Double-click `assembler_gui.py`, or run `python assembler_gui.py`.
2. Click **Open .asm...** and choose your file. It assembles immediately, with the assembly on the left and the machine code on the right.
3. Click **Save .hack...** to save the result.

You can also paste or edit assembly in the left pane and click **Assemble**. Errors appear in red at the bottom of the window.

## Example

`Add.asm`:

```
// Computes R0 = 2 + 3
@2
D=A
@3
D=D+A
@0
M=D
(END)
@END
0;JMP
```

Running `python assembler.py Add.asm` produces `Add.hack`:

```
0000000000000010
1110110000010000
0000000000000011
1110000010010000
0000000000000000
1110001100001000
0000000000000110
1110101010000111
```

The `.hack` file has one 16-character binary instruction per line, ready to load into the Nand2Tetris CPU Emulator.

## How it works

1. **Pass 1:** Removes comments and whitespace, then records the address of every `(LABEL)` in the symbol table. Labels are not emitted as instructions.
2. **Pass 2:** Translates each remaining instruction.
   - **A-instructions** (`@value` or `@symbol`) become `0` followed by a 15-bit address. Unknown symbols are treated as variables and assigned RAM addresses starting at 16.
   - **C-instructions** (`dest=comp;jump`) become `111` followed by the comp, dest, and jump bits from lookup tables.

Predefined symbols are supported: `R0`-`R15`, `SP`, `LCL`, `ARG`, `THIS`, `THAT`, `SCREEN`, and `KBD`.

## Error handling

The assembler reports an error if it finds:

- an invalid instruction (unknown dest, comp, or jump)
- a duplicate label
- an address outside the 15-bit range
