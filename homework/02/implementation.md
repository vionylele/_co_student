# Project 02: Boolean Arithmetic Implementation

## 1. Overview
Boolean arithmetic forms the foundation of digital computation, enabling the processor to perform mathematical operations using only binary signals (0 and 1). This project focuses on the construction of additive circuits and the Arithmetic Logic Unit (ALU).

### Two's Complement Representation
To handle signed integers, the Hack architecture utilizes **Two's Complement** representation. In this system, the most significant bit (MSB) serves as the sign bit. The value of a negative number is found by inverting all bits of its positive counterpart and adding one. This allows the hardware to use the same addition logic for both addition and subtraction.

### The ALU's Role
The ALU is the "engine" of the CPU. It takes two 16-bit inputs and a set of control bits to perform a wide array of operations (addition, AND, OR, negation, etc.). By manipulating the inputs and the final output via control signals, the ALU implements the functional requirements of the Hack instruction set.

---

## 2. Per-Chip Implementation Details

### HalfAdder
The `HalfAdder` is the simplest additive unit, summing two single-bit inputs.

- **Chip Interface**: 
  - `IN a, b`
  - `OUT sum, carry`
- **Boolean Logic**:
  - `sum = a XOR b`
  - `carry = a AND b`
- **HDL Implementation**:
```hdl
CHIP HalfAdder {
    IN a, b;
    OUT sum, carry;

    PARTS:
    Xor(a=a, b=b, out=sum);
    And(a=a, b=b, out=carry);
}
```
- **Design Considerations**: The `HalfAdder` cannot accept a carry-in from a previous stage, limiting its use to the least significant bit (LSB) of a larger adder.

### FullAdder
The `FullAdder` extends the `HalfAdder` by incorporating a carry-in bit, allowing it to be cascaded.

- **Chip Interface**:
  - `IN a, b, c` (where `c` is carry-in)
  - `OUT sum, carry`
- **Boolean Logic**:
  - `sum = (a XOR b) XOR c`
  - `carry = (a AND b) OR (c AND (a XOR b))`
- **HDL Implementation**:
```hdl
CHIP FullAdder {
    IN a, b, c;
    OUT sum, carry;

    PARTS:
    HalfAdder(a=a, b=b, sum=s1, carry=c1);
    HalfAdder(a=s1, b=c, sum=sum, carry=c2);
    Or(a=c1, b=c2, out=carry);
}
```
- **Design Considerations**: Structurally, a `FullAdder` is composed of two `HalfAdders` and an `Or` gate to combine the carry signals.

### Add16
The `Add16` chip implements 16-bit unsigned/signed addition using a **Ripple-Carry** architecture.

- **Chip Interface**:
  - `IN a[16], b[16]`
  - `OUT out[16]`
- **Architecture**: 
  - A chain of 16 `FullAdder`s (or one `HalfAdder` for the LSB and 15 `FullAdder`s).
  - The `carry` output of bit $i$ becomes the `c` (carry-in) input of bit $i+1$.
- **HDL Implementation**:
```hdl
CHIP Add16 {
    IN a[16], b[16];
    OUT out[16];

    PARTS:
    HalfAdder(a=a[0], b=b[0], sum=out[0], carry=c0);
    FullAdder(a=a[1], b=b[1], c=c0, sum=out[1], carry=c1);
    FullAdder(a=a[2], b=b[2], c=c1, sum=out[2], carry=c2);
    FullAdder(a=a[3], b=b[3], c=c2, sum=out[3], carry=c3);
    FullAdder(a=a[4], b=b[4], c=c3, sum=out[4], carry=c4);
    FullAdder(a=a[5], b=b[5], c=c4, sum=out[5], carry=c5);
    FullAdder(a=a[6], b=b[6], c=c5, sum=out[6], carry=c6);
    FullAdder(a=a[7], b=b[7], c=c6, sum=out[7], carry=c7);
    FullAdder(a=a[8], b=b[8], c=c7, sum=out[8], carry=c8);
    FullAdder(a=a[9], b=b[9], c=c8, sum=out[9], carry=c9);
    FullAdder(a=a[10], b=b[10], c=c9, sum=out[10], carry=c10);
    FullAdder(a=a[11], b=b[11], c=c10, sum=out[11], carry=c11);
    FullAdder(a=a[12], b=b[12], c=c11, sum=out[12], carry=c12);
    FullAdder(a=a[13], b=b[13], c=c12, sum=out[13], carry=c13);
    FullAdder(a=a[14], b=b[14], c=c13, sum=out[14], carry=c14);
    FullAdder(a=a[15], b=b[15], c=c14, sum=out[15], carry=c15);
}
```
- **Design Considerations**: In 16-bit addition, the final carry-out (`c15`) is discarded. This is consistent with standard fixed-width integer overflow behavior in computer architecture.

### Inc16
The `Inc16` chip increments a 16-bit number by one.

- **Chip Interface**:
  - `IN in[16]`
  - `OUT out[16]`
- **Architecture**:
  - This is a specialized version of `Add16` where the second operand is the constant `1`.
- **HDL Implementation**:
```hdl
CHIP Inc16 {
    IN in[16];
    OUT out[16];

    PARTS:
    // Use Add16: add 'in' and a constant 1
    // We simulate the constant 1 by setting b[0]=true and all other b[i]=false
    Add16(a=in, b[0]=true, b[1]=false, b[2]=false, b[3]=false, b[4]=false, 
          b[5]=false, b[6]=false, b[7]=false, b[8]=false, b[9]=false, 
          b[10]=false, b[11]=false, b[12]=false, b[13]=false, b[14]=false, 
          b[15]=false, out=out);
}
```
- **Design Considerations**: Pinning `b[0]=true` effectively adds the binary value `0000000000000001` to the input.

### ALU (Arithmetic Logic Unit)
The ALU is the most complex chip in Project 02, implementing 18 different functions based on 6 control bits.

- **Chip Interface**:
  - `IN x[16], y[16], zx, nx, zy, ny, f, no`
  - `OUT out[16], zr, ng`
- **Logic Architecture**:
  1. **Input Pre-processing**:
     - `zx`: Zero the x-input (`x = 0`).
     - `nx`: Negate the x-input (`x = !x`).
     - `zy`: Zero the y-input (`y = 0`).
     - `ny`: Negate the y-input (`y = !y`).
  2. **Function Execution**:
     - `f`: Compute `x + y` if `f=1`, else compute `x AND y` if `f=0`.
  3. **Output Post-processing**:
     - `no`: Negate the result (`out = !out`).
  4. **Flag Generation**:
     - `zr`: Set to 1 if `out == 0`.
     - `ng`: Set to 1 if `out < 0` (i.e., `out[15] == 1`).

- **HDL Implementation**:
```hdl
CHIP ALU {
    IN  x[16], y[16],  zx, nx, zy, ny, f, no;
    OUT out[16], zr, ng;

    PARTS:
    // x-input processing
    Mux16(a=x, b=false, sel=zx, out=x1);
    Not16(in=x1, out=notx1);
    Mux16(a=x1, b=notx1, sel=nx, out=x2);

    // y-input processing
    Mux16(a=y, b=false, sel=zy, out=y1);
    Not16(in=y1, out=noty1);
    Mux16(a=y1, b=noty1, sel=ny, out=y2);

    // Function selection
    Add16(a=x2, b=y2, out=addxy);
    And16(a=x2, b=y2, out=andxy);
    Mux16(a=andxy, b=addxy, sel=f, out=fout);

    // Final output negation and flags
    Not16(in=fout, out=notfout);
    Mux16(a=fout, b=notfout, sel=no, out=out);

    // ng flag: simply the MSB of the result
    // We use a temporary wire to access out[15]
    // (Note: In Hardware Simulator, we can use internal pins)
    
    // To implement zr, we check if any bit is 1
    // Or8Way is used on the lower and upper bytes
    // Since out is the final output, we must use a internal pin
    // because out is an output and cannot be used as an input.
    // (In actual implementation, we use 'out=out, out[0..7]=low, out[8..15]=high')
}
```
*(Note: Due to HDL constraints, the flags `zr` and `ng` are typically implemented by splitting the output of the final Mux16 into two 8-bit segments, passing them through `Or8Way`, and then `Nor`-ing the results.)*

- **Design Considerations & Pitfalls**:
  - **The `zr` Flag**: Since `out` is an output pin, you cannot feed it back into another gate. The solution is to name the final output using multiple internal pins: `Mux16(..., out=out, out[0..7]=outLow, out[8..15]=outHigh)`. Then, `Or8Way(in=outLow, out=lowOr)`, `Or8Way(in=outHigh, out=highOr)`, and `Or(a=lowOr, b=highOr, out=notZr)`. Finally, `Not(in=notZr, out=zr)`.
  - **The `ng` Flag**: This is simply the MSB (`out[15]`).

---

## 3. Verification
To ensure correctness, each chip must be validated using the **Hardware Simulator**:

1. **Load HDL**: Load the `.hdl` file into the simulator.
2. **Load Script**: Load the corresponding `.tst` file.
3. **Execute**: Run the simulation. The simulator will automatically compare the chip's outputs against the expected values stored in the `.cmp` file.
4. **Debug**: If a "Comparison failure" occurs, use the simulator's visualizer to trace signals through the chip's internal parts to identify the logic error.
