#!/usr/bin/env python3
"""Hack assembler for Nand2Tetris (Project 6).

Usage: python assembler.py Prog.asm   ->  writes Prog.hack next to the input.
"""
import sys
from pathlib import Path

COMP = {
    "0": "0101010", "1": "0111111", "-1": "0111010",
    "D": "0001100", "A": "0110000", "!D": "0001101", "!A": "0110001",
    "-D": "0001111", "-A": "0110011", "D+1": "0011111", "A+1": "0110111",
    "D-1": "0001110", "A-1": "0110010", "D+A": "0000010", "D-A": "0010011",
    "A-D": "0000111", "D&A": "0000000", "D|A": "0010101",
    "M": "1110000", "!M": "1110001", "-M": "1110011", "M+1": "1110111",
    "M-1": "1110010", "D+M": "1000010", "D-M": "1010011", "M-D": "1000111",
    "D&M": "1000000", "D|M": "1010101",
}

DEST = {
    "": "000", "M": "001", "D": "010", "MD": "011",
    "A": "100", "AM": "101", "AD": "110", "AMD": "111",
}

JUMP = {
    "": "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111",
}

PREDEFINED = {
    "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
    "SCREEN": 16384, "KBD": 24576,
    **{f"R{i}": i for i in range(16)},
}


class AsmError(Exception):
    pass


def clean(line: str) -> str:
    """Strip comments and all whitespace."""
    return "".join(line.split("//")[0].split())


def assemble(source: str) -> list[str]:
    lines = [c for c in (clean(l) for l in source.splitlines()) if c]

    # Pass 1: record labels, collect real instructions.
    symbols = dict(PREDEFINED)
    instructions = []
    for line in lines:
        if line.startswith("(") and line.endswith(")"):
            label = line[1:-1]
            if label in symbols and label not in PREDEFINED:
                raise AsmError(f"Duplicate label: {label}")
            symbols[label] = len(instructions)
        else:
            instructions.append(line)

    # Pass 2: translate.
    next_var = 16
    out = []
    for line in instructions:
        if line.startswith("@"):
            sym = line[1:]
            if sym.isdigit():
                value = int(sym)
            else:
                if sym not in symbols:
                    symbols[sym] = next_var
                    next_var += 1
                value = symbols[sym]
            if not 0 <= value < 2 ** 15:
                raise AsmError(f"Address out of range: {line}")
            out.append(format(value, "016b"))
        else:
            dest, comp, jump = "", line, ""
            if "=" in comp:
                dest, comp = comp.split("=", 1)
            if ";" in comp:
                comp, jump = comp.split(";", 1)
            if dest not in DEST or comp not in COMP or jump not in JUMP:
                raise AsmError(f"Invalid instruction: {line}")
            out.append("111" + COMP[comp] + DEST[dest] + JUMP[jump])
    return out


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python assembler.py Prog.asm")
    src = Path(sys.argv[1])
    try:
        result = assemble(src.read_text())
    except AsmError as e:
        sys.exit(f"Error: {e}")
    dst = src.with_suffix(".hack")
    dst.write_text("\n".join(result) + "\n")
    print(f"Wrote {len(result)} instructions to {dst}")


if __name__ == "__main__":
    main()
