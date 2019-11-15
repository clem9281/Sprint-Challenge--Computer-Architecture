"""CPU functionality."""

import sys

# ALU ops
ADD = 0b10100000
SUB = 0b10100001
MUL = 0b10100010
DIV = 0b10100011
MOD = 0b10100100

INC = 0b01100101
DEC = 0b01100110

CMP = 0b10100111

AND = 0b10101000
NOT = 0b01101001
OR = 0b10101010
XOR = 0b10101011
SHL = 0b10101100
SHR = 0b10101101

# PC mutators
CALL = 0b01010000
RET = 0b00010001

INT = 0b01010010
IRET = 0b00010011

JMP = 0b01010100
JEQ = 0b01010101
JNE = 0b01010110
JGT = 0b01010111
JLT = 0b01011000
JLE = 0b01011001
JGE = 0b01011010

# Other
NOP = 0b00000000

HLT = 0b00000001

LDI = 0b10000010

LD = 0b10000011
ST = 0b10000100

PUSH = 0b01000101
POP = 0b01000110

PRN = 0b01000111
PRA = 0b01001000


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.register = bytearray(8)
        self.ram = [0] * 256
        self.pc = 0
        self.SP = 7
        self.flags = 0b00000000
        self.register[self.SP] = 0xF4
        self.branchtable = {}
        self.branchtable[HLT] = self.handle_HTL
        self.branchtable[LDI] = self.handle_LDI
        self.branchtable[PRN] = self.handle_PRN
        self.branchtable[PUSH] = self.handle_PUSH
        self.branchtable[POP] = self.handle_POP
        self.branchtable[CALL] = self.handle_CALL
        self.branchtable[RET] = self.handle_RET
        self.branchtable[JEQ] = self.handle_JEQ
        self.branchtable[LD] = self.handle_LD
        self.branchtable[PRA] = self.handle_PRA
        self.branchtable[JMP] = self.handle_JMP
        self.branchtable[JNE] = self.handle_JNE
        # debug flag for fun
        self.debug = False

    def load(self):
        """Load a program into memory."""
        # I thought I'd try argparse out, I wanted to be able to run this code with optional debug output. argparse gives us an easy way to do that, and gives us friendly -h output
        # run python ls8.py -h, you'll see we have nice instructions on how to run ls8
        import argparse

        # initialize parser
        parser = argparse.ArgumentParser(description="Run a file in ls8")
        # create a required command line arg called file_dir with type string
        parser.add_argument(
            "file_dir", type=str, help="Directory of file to run with ls8"
        )
        # the -- lets the parser know this next argument is optional, and its action means debug=false when -d or --debug isn't supplied, and debug=true when ls8.py is run with -d or --debug. Since our arguments have different types (boolean and string) we can supply them in any order in the command line
        # either python `python ls8.py file_dir -d` or `python ls8.py -d file_dir` works now, or you can omit the flag altogether
        parser.add_argument(
            "-d",
            "--debug",
            help="Run with --debug to run code with debug output",
            action="store_true",
        )

        args = parser.parse_args()

        if args.debug:
            self.debug = True

        # parse the file
        f = open(args.file_dir)
        program = []
        for line in f:
            if line[0] != "#" and len(line) > 0 and line != "\n":
                program.append(int(line[:8], 2))
        f.close()

        # load the program array into ram
        address = 0
        # For now, we've just hardcoded a program:
        for instruction in program:
            self.ram[address] = instruction
            address += 1

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""
        # print(reg_a, reg_b)
        if self.debug:
            # x and y just clean up our debug output here: reg_b is getting passed in whether we want it or not, so if we aren't using it (like in DEC and INC) don't show it in our debug output
            x = f"and {self.register[reg_b]}" if len(self.register) >= reg_b else ""
            y = f"and storing in register[{reg_a}]" if x != "" else ""
            print(
                f"ALU {op} {self.register[reg_a]} {x} {y}"
            )
        if op == "CMP":
            a = self.register[reg_a]
            b = self.register[reg_b]
            if a < b:
                self.flags = 0b00000100
            elif a > b:
                self.flags = 0b00000010
            else:
                self.flags = 0b00000001
        # MATH
        elif op == "ADD":
            self.register[reg_a] += self.register[reg_b]
        elif op == "SUB":
            self.reg[reg_a] -= self.reg[reg_b]
        elif op == "MOD":
            self.reg[reg_a] = self.reg[reg_a] % self.reg[reg_b]
        elif op == "MUL":
            self.register[reg_a] = (self.register[reg_a] * self.register[reg_b]) & 0xFF
        elif op == "DIV":
            dividend = self.register[reg_b]
            divisor = self.register[reg_a]
            if dividend == 0:
                print("Error")
                raise
            self.register[reg_a] = dividend // divisor
        # BITWISE OPS
        elif op == "AND":
            self.register[reg_a] = self.register[reg_a] & self.register[reg_b]
        elif op == "NOT":
            self.register[reg_a] = ~self.register[reg_a]
        elif op == "OR":
            self.register[reg_a] = self.register[reg_a] | self.register[reg_b]
        elif op == "XOR":
            self.register[reg_a] = self.register[reg_a] ^ self.register[reg_b]
        elif op == "SHR":
            self.register[reg_a] = self.register[reg_a] >> self.register[reg_b]
        elif op == "SHL":
            self.register[reg_a] = self.register[reg_a] << self.register[reg_b]
        # +1 & -1
        elif op == "DEC":
            self.register[reg_a] -= 1
        elif op == "INC":
            self.register[reg_a] += 1

        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(
            f"TRACE: %02X | %02X %02X %02X |"
            % (
                self.pc,
                # self.fl,
                # self.ie,
                self.ram_read(self.pc),
                self.ram_read(self.pc + 1),
                self.ram_read(self.pc + 2),
            ),
            end="",
        )

        for i in range(8):
            print(" %02X" % self.reg[i], end="")

        print()

    def ram_read(self, mar):
        return self.ram[mar]

    def ram_write(self, mar, mdr):
        self.ram[mar] = mdr

    def run(self):
        """Run the CPU."""
        ops = {
            MUL: "MUL",
            ADD: "ADD",
            SUB: "SUB",
            MUL: "MUL",
            DIV: "DIV",
            MOD: "MOD",
            INC: "INC",
            DEC: "DEC",
            CMP: "CMP",
            AND: "AND",
            NOT: "NOT",
            OR: "OR",
            XOR: "XOR",
            SHL: "SHL",
            SHR: "SHR",
        }
        while True:
            command = self.ram[self.pc]
            is_alu_command = command & 0b00100000
            is_pc_mutator = (command >> 4) & 0b0001
            instruction_length = command >> 6
            if self.debug:
                print("------------------------------------")
                print(
                    f"RUN: {command}, isALU: {is_alu_command > 0}, isMutator: {is_pc_mutator > 0}"
                )
            if is_pc_mutator > 0:
                if command in self.branchtable:
                    self.branchtable[command]()
                else:
                    print("We haven't implemented that command")
                    raise
            elif is_alu_command > 0:
                operation = self.ram[self.pc]
                operand_a = self.ram[self.pc + 1]
                operand_b = self.ram[self.pc + 2]
                self.alu(ops[operation], operand_a, operand_b)
                self.pc += instruction_length + 1
            elif command in self.branchtable:
                self.branchtable[command]()
                self.pc += instruction_length + 1
            else:
                print(f"Unknown command at {self.pc}")
                sys.exit(1)

    # OP HANDLERS FOR BRANCHTABLE
    def handle_HTL(self):
        if self.debug:
            print(f"HTL: Exiting program at {self.pc}")
        sys.exit()

    def handle_LDI(self):
        operand_a = self.ram[self.pc + 1]
        operand_b = self.ram[self.pc + 2]
        if self.debug:
            print(f"LDI: Storing {operand_b} at register[{operand_a}]")
        self.register[operand_a] = operand_b

    def handle_PRN(self):
        operand = self.ram[self.pc + 1]
        if self.debug:
            print(f"PRN: Printing from register[{operand}]")
        print(self.register[operand])

    def handle_PUSH(self):
        self.register[self.SP] -= 1
        operand = self.register[self.ram[self.pc + 1]]
        self.ram[self.register[self.SP]] = operand
        if self.debug:
            print(
                f"PUSH: Storing {operand} from register[{self.ram[self.pc + 1]}] at Stack[{0xf4 - self.register[self.SP] - 1}]->ram[{self.register[self.SP] }]"
            )

    def handle_POP(self):
        operand = self.ram[self.register[self.SP]]
        self.register[self.ram[self.pc + 1]] = operand
        if self.debug:
            print(
                f"POP: Popped {operand} from Stack[{0xf4 - self.register[self.SP] - 1}]->ram[{self.register[self.SP]}], storing in register[{self.ram[self.pc+1]}]"
            )
        self.register[self.SP] += 1

    # PC MUTATORS
    def handle_CALL(self):
        self.register[self.SP] -= 1
        self.ram[self.register[self.SP]] = self.pc + 2
        if self.debug:
            print(
                f"CALL: Storing {self.pc + 2} on Stack[{0xf4 - self.register[self.SP] - 1}]->ram[{self.register[self.SP]}] to return to"
            )
        reg = self.ram[self.pc + 1]
        self.pc = self.register[reg]
        if self.debug:
            print(f"CALL: Calling subroutine {self.register[reg]} stored at register[{reg}]")

    def handle_RET(self):
        self.pc = self.ram[self.register[self.SP]]
        if self.debug:
            print(f"RET: Returning to {self.ram[self.register[self.SP]]}")
        self.register[self.SP] += 1

    def handle_JEQ(self):
        oldPC = self.pc
        if self.flags & 0b00000001 > 0:
            self.pc = self.register[self.ram[self.pc + 1]]
        else:
            self.pc += 2
        if self.debug:
            print(f'JEQ: Equal flag set to {self.flags & 0b00000001 > 0}, pc moves from {oldPC} to {self.pc}')
            
    def handle_LD(self):
        operand_a = self.ram[self.pc + 1]
        operand_b = self.ram[self.pc + 2]
        self.register[operand_a] = self.ram[self.register[operand_b]]
        if self.debug:
            print(f"LD: storing {self.ram[self.register[operand_b]]} from ram[{self.register[operand_b]}] in register{[operand_a]}")
            
    def handle_PRA(self):
        operand_a = self.ram[self.pc + 1]
        if self.debug:
            print(f"PRA: printing ///{chr(self.register[operand_a])}/// from register[{operand_a}]")
        print(f"{chr(self.register[operand_a])}")
        
    def handle_JMP(self):
        oldPC = self.pc
        operand_a = self.ram[self.pc + 1]
        self.pc = self.register[operand_a]
        if self.debug:
            print(f"JMP: jumping to {self.register[operand_a]} from {oldPC}")
    def handle_JNE(self):
        oldPC = self.pc
        if self.flags & 0b00000001 == 0:
            self.pc = self.register[self.ram[self.pc + 1]]
        else:
            self.pc += 2
        if self.debug:
            print(f'JNE: Equal flag set to {self.flags & 0b00000001 > 0}, pc moves from {oldPC} to {self.pc}')