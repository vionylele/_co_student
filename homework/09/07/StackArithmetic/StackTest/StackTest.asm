// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
AM=M-1
D=M
A=A-1
D=M-D
M=-1
@__EQ_END.0
D;JEQ
@SP
A=M-1
M=0
(__EQ_END.0)
// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 16
@16
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
AM=M-1
D=M
A=A-1
D=M-D
M=-1
@__EQ_END.1
D;JEQ
@SP
A=M-1
M=0
(__EQ_END.1)
// push constant 16
@16
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
AM=M-1
D=M
A=A-1
D=M-D
M=-1
@__EQ_END.2
D;JEQ
@SP
A=M-1
M=0
(__EQ_END.2)
// push constant 892
@892
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@__CMP_RET.3
D=A
@R13
M=D
@__LT
0;JMP
(__CMP_RET.3)
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 892
@892
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@__CMP_RET.4
D=A
@R13
M=D
@__LT
0;JMP
(__CMP_RET.4)
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@__CMP_RET.5
D=A
@R13
M=D
@__LT
0;JMP
(__CMP_RET.5)
// push constant 32767
@32767
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@__CMP_RET.6
D=A
@R13
M=D
@__GT
0;JMP
(__CMP_RET.6)
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 32767
@32767
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@__CMP_RET.7
D=A
@R13
M=D
@__GT
0;JMP
(__CMP_RET.7)
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@__CMP_RET.8
D=A
@R13
M=D
@__GT
0;JMP
(__CMP_RET.8)
// push constant 57
@57
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 31
@31
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 53
@53
D=A
@SP
A=M
M=D
@SP
M=M+1
// add
@SP
AM=M-1
D=M
A=A-1
M=D+M
// push constant 112
@112
D=A
@SP
A=M
M=D
@SP
M=M+1
// sub
@SP
AM=M-1
D=M
A=A-1
M=M-D
// neg
@SP
A=M-1
M=-M
// and
@SP
AM=M-1
D=M
A=A-1
M=D&M
// push constant 82
@82
D=A
@SP
A=M
M=D
@SP
M=M+1
// or
@SP
AM=M-1
D=M
A=A-1
M=D|M
// not
@SP
A=M-1
M=!M
// end of program: loop forever
(__END)
@__END
0;JMP
(__GT)
@SP
AM=M-1
D=M
@R14
M=D
@SP
A=M-1
D=M
@__GT.XNEG
D;JLT
@R14
D=M
@__GT.TRUE
D;JLT
@__GT.SUB
0;JMP
(__GT.XNEG)
@R14
D=M
@__GT.FALSE
D;JGE
(__GT.SUB)
@SP
A=M-1
D=M
@R14
D=D-M
@__GT.TRUE
D;JGT
(__GT.FALSE)
@SP
A=M-1
M=0
@R13
A=M
0;JMP
(__GT.TRUE)
@SP
A=M-1
M=-1
@R13
A=M
0;JMP
(__LT)
@SP
AM=M-1
D=M
@R14
M=D
@SP
A=M-1
D=M
@__LT.XNEG
D;JLT
@R14
D=M
@__LT.FALSE
D;JLT
@__LT.SUB
0;JMP
(__LT.XNEG)
@R14
D=M
@__LT.TRUE
D;JGE
(__LT.SUB)
@SP
A=M-1
D=M
@R14
D=D-M
@__LT.TRUE
D;JLT
(__LT.FALSE)
@SP
A=M-1
M=0
@R13
A=M
0;JMP
(__LT.TRUE)
@SP
A=M-1
M=-1
@R13
A=M
0;JMP
