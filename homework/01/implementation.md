# Project 01: Elementary Logic Gates Implementation Guide

## 1. Overview & Primitive Baseline

The objective of Project 01 is to construct the fundamental building blocks of digital computation starting from a single primitive: the **Nand gate**. 

In the Nand2Tetris curriculum, the `Nand` gate is provided as the baseline primitive. It is a "universal gate," meaning that any possible Boolean function can be implemented using only combinations of Nand gates. The logic of a Nand gate is defined as the negation of the logical conjunction: $\text{Nand}(a, b) = \neg(a \land b)$.

The progression of this project moves from basic single-bit gates to multi-bit bus operations and finally to routing logic (Multiplexers and Demultiplexers), establishing the hierarchical design pattern used throughout the rest of the hardware course.

---

## 2. Chip-by-Chip Implementation

### 2.1 Inverters (NOT)

#### Not
- **Interface**: `IN in`, `OUT out`
- **Boolean Logic**: $\text{Not}(a) = \neg a$.
- **Design Strategy**: Since $\text{Nand}(a, a) = \neg(a \land a) = \neg a$, we use a single Nand gate with both inputs tied to the signal.

**Truth Table:**
| in | out |
|:--:|:---:|
| 0  | 1   |
| 1  | 0   |

- **HDL**:
```hdl
CHIP Not {
    IN in;
    OUT out;

    PARTS:
    Nand(a=in, b=in, out=out);
}
```

#### Not16
- **Interface**: `IN in[16]`, `OUT out[16]`
- **Design Strategy**: A bitwise inversion of a 16-bit bus. This is implemented by instantiating 16 individual `Not` gates, each mapped to a corresponding index of the input and output buses.
- **HDL**:
```hdl
CHIP Not16 {
    IN in[16];
    OUT out[16];

    PARTS:
    Not(in=in[0], out=out[0]);
    Not(in=in[1], out=out[1]);
    Not(in=in[2], out=out[2]);
    Not(in=in[3], out=out[3]);
    Not(in=in[4], out=out[4]);
    Not(in=in[5], out=out[5]);
    Not(in=in[6], out=out[6]);
    Not(in=in[7], out=out[7]);
    Not(in=in[8], out=out[8]);
    Not(in=in[9], out=out[9]);
    Not(in=in[10], out=out[10]);
    Not(in=in[11], out=out[11]);
    Not(in=in[12], out=out[12]);
    Not(in=in[13], out=out[13]);
    Not(in=in[14], out=out[14]);
    Not(in=in[15], out=out[15]);
}
```

---

### 2.2 Conjunctions (AND)

#### And
- **Interface**: `IN a, b`, `OUT out`
- **Boolean Logic**: $\text{And}(a, b) = a \land b$.
- **Design Strategy**: Since $\text{Nand}(a, b) = \neg(a \land b)$, then $\text{And}(a, b) = \neg \text{Nand}(a, b)$.
- **HDL**:
```hdl
CHIP And {
    IN a, b;
    OUT out;

    PARTS:
    Nand(a=a, b=b, out=nandOut);
    Not(in=nandOut, out=out);
}
```

**Truth Table:**
| a | b | out |
|:-:|:-:|:---:|
| 0 | 0 | 0   |
| 0 | 1 | 0   |
| 1 | 0 | 0   |
| 1 | 1 | 1   |

#### And16
- **Interface**: `IN a[16], b[16]`, `OUT out[16]`
- **Design Strategy**: Bitwise conjunction. 16 `And` gates are wired in parallel to process the buses.
- **HDL**:
```hdl
CHIP And16 {
    IN a[16], b[16];
    OUT out[16];

    PARTS:
    And(a=a[0], b=b[0], out=out[0]);
    And(a=a[1], b=b[1], out=out[1]);
    And(a=a[2], b=b[2], out=out[2]);
    And(a=a[3], b=b[3], out=out[3]);
    And(a=a[4], b=b[4], out=out[4]);
    And(a=a[5], b=b[5], out=out[5]);
    And(a=a[6], b=b[6], out=out[6]);
    And(a=a[7], b=b[7], out=out[7]);
    And(a=a[8], b=b[8], out=out[8]);
    And(a=a[9], b=b[9], out=out[9]);
    And(a=a[10], b=b[10], out=out[10]);
    And(a=a[11], b=b[11], out=out[11]);
    And(a=a[12], b=b[12], out=out[12]);
    And(a=a[13], b=b[13], out=out[13]);
    And(a=a[14], b=b[14], out=out[14]);
    And(a=a[15], b=b[15], out=out[15]);
}
```

---

### 2.3 Disjunctions (OR)

#### Or
- **Interface**: `IN a, b`, `OUT out`
- **Boolean Logic**: $\text{Or}(a, b) = a \lor b$.
- **Design Strategy**: Based on De Morgan's Law: $a \lor b = \neg (\neg a \land \neg b)$. Thus, $\text{Or}(a, b) = \text{Nand}(\text{Not}(a), \text{Not}(b))$.
- **HDL**:
```hdl
CHIP Or {
    IN a, b;
    OUT out;

    PARTS:
    Not(in=a, out=notA);
    Not(in=b, out=notB);
    Nand(a=notA, b=notB, out=out);
}
```

**Truth Table:**
| a | b | out |
|:-:|:-:|:---:|
| 0 | 0 | 0   |
| 0 | 1 | 1   |
| 1 | 0 | 1   |
| 1 | 1 | 1   |

#### Or16
- **Interface**: `IN a[16], b[16]`, `OUT out[16]`
- **Design Strategy**: Bitwise disjunction. 16 `Or` gates are wired in parallel.
- **HDL**:
```hdl
CHIP Or16 {
    IN a[16], b[16];
    OUT out[16];

    PARTS:
    Or(a=a[0], b=b[0], out=out[0]);
    Or(a=a[1], b=b[1], out=out[1]);
    Or(a=a[2], b=b[2], out=out[2]);
    Or(a=a[3], b=b[3], out=out[3]);
    Or(a=a[4], b=b[4], out=out[4]);
    Or(a=a[5], b=b[5], out=out[5]);
    Or(a=a[6], b=b[6], out=out[6]);
    Or(a=a[7], b=b[7], out=out[7]);
    Or(a=a[8], b=b[8], out=out[8]);
    Or(a=a[9], b=b[9], out=out[9]);
    Or(a=a[10], b=b[10], out=out[10]);
    Or(a=a[11], b=b[11], out=out[11]);
    Or(a=a[12], b=b[12], out=out[12]);
    Or(a=a[13], b=b[13], out=out[13]);
    Or(a=a[14], b=b[14], out=out[14]);
    Or(a=a[15], b=b[15], out=out[15]);
}
```

#### Or8Way
- **Interface**: `IN in[8]`, `OUT out`
- **Design Strategy**: This chip computes the logical OR of 8 input bits. It is implemented as a linear chain (reduction) of `Or` gates.
- **HDL**:
```hdl
CHIP Or8Way {
    IN in[8];
    OUT out;

    PARTS:
    Or(a=in[0], b=in[1], out=o1);
    Or(a=o1, b=in[2], out=o2);
    Or(a=o2, b=in[3], out=o3);
    Or(a=o3, b=in[4], out=o4);
    Or(a=o4, b=in[5], out=o5);
    Or(a=o5, b=in[6], out=o6);
    Or(a=o6, b=in[7], out=out);
}
```

---

### 2.4 Exclusive OR (XOR)

#### Xor
- **Interface**: `IN a, b`, `OUT out`
- **Boolean Logic**: $\text{Xor}(a, b) = a \oplus b = (a \land \neg b) \lor (\neg a \land b)$.
- **Design Strategy**: We implement the canonical Sum-of-Products form using `Not`, `And`, and `Or` gates.
- **HDL**:
```hdl
CHIP Xor {
    IN a, b;
    OUT out;

    PARTS:
    Not(in=a, out=notA);
    Not(in=b, out=notB);
    And(a=a, b=notB, out=aAndNotB);
    And(a=notA, b=b, out=notAAndB);
    Or(a=aAndNotB, b=notAAndB, out=out);
}
```

**Truth Table:**
| a | b | out |
|:-:|:-:|:---:|
| 0 | 0 | 0   |
| 0 | 1 | 1   |
| 1 | 0 | 1   |
| 1 | 1 | 0   |

---

### 2.5 Multiplexers (MUX)

#### Mux
- **Interface**: `IN a, b, sel`, `OUT out`
- **Boolean Logic**: $\text{out} = (a \land \neg \text{sel}) \lor (b \land \text{sel})$.
- **Design Strategy**: The selector bit `sel` acts as a switch. When `sel=0`, the first term is active; when `sel=1`, the second term is active.
- **HDL**:
```hdl
CHIP Mux {
    IN a, b, sel;
    OUT out;

    PARTS:
    Not(in=sel, out=notSel);
    And(a=a, b=notSel, out=aSelected);
    And(a=b, b=sel, out=bSelected);
    Or(a=aSelected, b=bSelected, out=out);
}
```

**Truth Table:**
| a | b | sel | out |
|:-:|:-:|:---:|:---:|
| 0 | 0 | 0   | 0   |
| 0 | 0 | 1   | 0   |
| 0 | 1 | 0   | 0   |
| 0 | 1 | 1   | 1   |
| 1 | 0 | 0   | 1   |
| 1 | 0 | 1   | 0   |
| 1 | 1 | 0   | 1   |
| 1 | 1 | 1   | 1   |

#### Mux16
- **Interface**: `IN a[16], b[16], sel`, `OUT out[16]`
- **Design Strategy**: A multi-bit multiplexer that selects between two 16-bit buses using a single selector bit. 16 `Mux` gates are wired in parallel.
- **HDL**:
```hdl
CHIP Mux16 {
    IN a[16], b[16], sel;
    OUT out[16];

    PARTS:
    Mux(a=a[0], b=b[0], sel=sel, out=out[0]);
    Mux(a=a[1], b=b[1], sel=sel, out=out[1]);
    Mux(a=a[2], b=b[2], sel=sel, out=out[2]);
    Mux(a=a[3], b=b[3], sel=sel, out=out[3]);
    Mux(a=a[4], b=b[4], sel=sel, out=out[4]);
    Mux(a=a[5], b=b[5], sel=sel, out=out[5]);
    Mux(a=a[6], b=b[6], sel=sel, out=out[6]);
    Mux(a=a[7], b=b[7], sel=sel, out=out[7]);
    Mux(a=a[8], b=b[8], sel=sel, out=out[8]);
    Mux(a=a[9], b=b[9], sel=sel, out=out[9]);
    Mux(a=a[10], b=b[10], sel=sel, out=out[10]);
    Mux(a=a[11], b=b[11], sel=sel, out=out[11]);
    Mux(a=a[12], b=b[12], sel=sel, out=out[12]);
    Mux(a=a[13], b=b[13], sel=sel, out=out[13]);
    Mux(a=a[14], b=b[14], sel=sel, out=out[14]);
    Mux(a=a[15], b=b[15], sel=sel, out=out[15]);
}
```

#### Mux4Way16
- **Interface**: `IN a[16], b[16], c[16], d[16], sel[2]`, `OUT out[16]`
- **Design Strategy**: Implemented as a tree of `Mux16` gates. 
  - The first stage uses `sel[0]` to select between `(a, b)` and `(c, d)`.
  - The second stage uses `sel[1]` to select between the results of the first stage.
- **HDL**:
```hdl
CHIP Mux4Way16 {
    IN a[16], b[16], c[16], d[16], sel[2];
    OUT out[16];

    PARTS:
    Mux16(a=a, b=b, sel=sel[0], out=muxAB);
    Mux16(a=c, b=d, sel=sel[0], out=muxCD);
    Mux16(a=muxAB, b=muxCD, sel=sel[1], out=out);
}
```

#### Mux8Way16
- **Interface**: `IN a[16], b[16], c[16], d[16], e[16], f[16], g[16], h[16], sel[3]`, `OUT out[16]`
- **Design Strategy**: A hierarchical tree using `Mux4Way16` and `Mux16`.
  - Stage 1: Two `Mux4Way16` chips narrow the 8 inputs down to 2 candidates using `sel[0..1]`.
  - Stage 2: One `Mux16` chip selects the final output using `sel[2]`.
- **HDL**:
```hdl
CHIP Mux8Way16 {
    IN a[16], b[16], c[16], d[16], e[16], f[16], g[16], h[16], sel[3];
    OUT out[16];

    PARTS:
    Mux4Way16(a=a, b=b, c=c, d=d, sel=sel[0..1], out=muxABCD);
    Mux4Way16(a=e, b=f, c=g, d=h, sel=sel[0..1], out=muxEFGH);
    Mux16(a=muxABCD, b=muxEFGH, sel=sel[2], out=out);
}
```

---

### 2.6 Demultiplexers (DMUX)

#### DMux
- **Interface**: `IN in, sel`, `OUT a, b`
- **Boolean Logic**: $a = \text{in} \land \neg \text{sel}$; $b = \text{in} \land \text{sel}$.
- **Design Strategy**: The input `in` is gated by the selector. Only one output is "open" at a time, while the other is forced to 0.
- **HDL**:
```hdl
CHIP DMux {
    IN in, sel;
    OUT a, b;

    PARTS:
    Not(in=sel, out=notSel);
    And(a=in, b=notSel, out=a);
    And(a=in, b=sel, out=b);
}
```

**Truth Table:**
| in | sel | a | b |
|:--:|:---:|:-:|:-:|
| 0  | 0   | 0 | 0 |
| 0  | 1   | 0 | 0 |
| 1  | 0   | 1 | 0 |
| 1  | 1   | 0 | 1 |

#### DMux4Way
- **Interface**: `IN in, sel[2]`, `OUT a, b, c, d`
- **Design Strategy**: Implemented as a tree.
  - The first `DMux` uses `sel[1]` to route the input to either the `{a, b}` group or the `{c, d}` group.
  - Two subsequent `DMux` gates use `sel[0]` to finalize the routing to one of the four outputs.
- **HDL**:
```hdl
CHIP DMux4Way {
    IN in, sel[2];
    OUT a, b, c, d;

    PARTS:
    DMux(in=in, sel=sel[1], a=outAB, b=outCD);
    DMux(in=outAB, sel=sel[0], a=a, b=b);
    DMux(in=outCD, sel=sel[0], a=c, b=d);
}
```

#### DMux8Way
- **Interface**: `IN in, sel[3]`, `OUT a, b, c, d, e, f, g, h`
- **Design Strategy**: 
  - A primary `DMux` uses `sel[2]` to route the input to either the first 4 outputs (`DMux4Way`) or the last 4 outputs.
  - Two `DMux4Way` chips then route the signal to the specific output based on `sel[0..1]`.
- **HDL**:
```hdl
CHIP DMux8Way {
    IN in, sel[3];
    OUT a, b, c, d, e, f, g, h;

    PARTS:
    DMux(in=in, sel=sel[2], a=outABCD, b=outEFGH);
    DMux4Way(in=outABCD, sel=sel[0..1], a=a, b=b, c=c, d=d);
    DMux4Way(in=outEFGH, sel=sel[0..1], a=e, b=f, c=g, d=h);
}
```

---

## 3. Verification

To ensure the correctness of these implementations, each chip must be validated using the provided test scripts.

### Testing Workflow:
1. **Load HDL**: Open the `.hdl` file in the Nand2Tetris Hardware Simulator.
2. **Load Script**: Load the corresponding `.tst` file.
3. **Execute**: Run the simulation. The simulator will iterate through the truth table defined in the script.
4. **Comparison**: The simulator automatically compares the `out` signals produced by the HDL implementation against the expected values stored in the `.cmp` file.
5. **Success**: If the simulation completes without a "Mismatch" error, the chip is functionally correct.

### Common Pitfalls:
- **Bus Indexing**: Ensure that `in[0]` is the Least Significant Bit (LSB). In Nand2Tetris, `in[0]` is the rightmost bit.
- **Implicit Zeroes**: In `DMux` chips, remember that outputs not selected must be driven to 0. The `And` gate implementation naturally handles this.
- **Naming**: Ensure internal pins (e.g., `muxAB`) are uniquely named within the `PARTS` section to avoid signal collisions.
