#!/usr/bin/env python3
"""Hack Assembler (Nand2Tetris Project 6) - windowed version.

Double-click this file (or run `python assembler_gui.py`) to open the app.
Self-contained: only needs Python 3.9+ (tkinter ships with the Windows installer).
"""
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

# ---------------------------------------------------------------- assembler
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


def clean(line):
    return "".join(line.split("//")[0].split())


def assemble(source):
    lines = [c for c in (clean(l) for l in source.splitlines()) if c]

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


# ---------------------------------------------------------------------- GUI
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hack Assembler")
        self.geometry("900x520")
        self.asm_path = None
        self.result = []

        bar = tk.Frame(self)
        bar.pack(fill="x", padx=8, pady=8)
        tk.Button(bar, text="Open .asm...", command=self.open_file).pack(side="left")
        tk.Button(bar, text="Assemble", command=self.run_assemble).pack(side="left", padx=6)
        self.save_btn = tk.Button(bar, text="Save .hack...", command=self.save_file,
                                  state="disabled")
        self.save_btn.pack(side="left")
        self.path_label = tk.Label(bar, text="No file opened", anchor="w")
        self.path_label.pack(side="left", padx=12)

        panes = tk.PanedWindow(self, orient="horizontal", sashrelief="raised")
        panes.pack(fill="both", expand=True, padx=8)
        self.src = self._pane(panes, "Assembly (.asm) - you can edit or paste here")
        self.dst = self._pane(panes, "Machine code (.hack)", readonly=True)

        self.status = tk.Label(self, text="Open a file or paste code, then press Assemble.",
                               anchor="w")
        self.status.pack(fill="x", padx=8, pady=6)

    def _pane(self, parent, title, readonly=False):
        frame = tk.Frame(parent)
        tk.Label(frame, text=title, anchor="w").pack(fill="x")
        inner = tk.Frame(frame)
        inner.pack(fill="both", expand=True)
        text = tk.Text(inner, wrap="none", font=("Consolas", 11), undo=not readonly)
        sb = tk.Scrollbar(inner, command=text.yview)
        text.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        parent.add(frame, stretch="always")
        return text

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Open assembly file",
            filetypes=[("Hack assembly", "*.asm"), ("All files", "*.*")])
        if not path:
            return
        try:
            content = Path(path).read_text()
        except OSError as e:
            messagebox.showerror("Error", str(e))
            return
        self.asm_path = Path(path)
        self.path_label.config(text=str(self.asm_path))
        self.src.delete("1.0", "end")
        self.src.insert("1.0", content)
        self.run_assemble()

    def run_assemble(self):
        try:
            self.result = assemble(self.src.get("1.0", "end"))
        except AsmError as e:
            self.result = []
            self._set_output("")
            self.save_btn.config(state="disabled")
            self.status.config(text=f"Error: {e}", fg="red")
            return
        self._set_output("\n".join(self.result))
        self.save_btn.config(state="normal" if self.result else "disabled")
        self.status.config(text=f"Assembled {len(self.result)} instructions.", fg="green")

    def _set_output(self, text):
        self.dst.config(state="normal")
        self.dst.delete("1.0", "end")
        self.dst.insert("1.0", text)
        self.dst.config(state="disabled")

    def save_file(self):
        initial = self.asm_path.with_suffix(".hack").name if self.asm_path else "out.hack"
        initdir = str(self.asm_path.parent) if self.asm_path else None
        path = filedialog.asksaveasfilename(
            title="Save machine code", defaultextension=".hack", initialfile=initial,
            initialdir=initdir, filetypes=[("Hack machine code", "*.hack")])
        if not path:
            return
        Path(path).write_text("\n".join(self.result) + "\n")
        self.status.config(text=f"Saved to {path}", fg="green")


if __name__ == "__main__":
    App().mainloop()
