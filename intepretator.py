import argparse
import sys
import xml.etree.ElementTree as ET

from Assembeler import A_FIELD, COMMANDS, Instruction

MEM_SIZE = 1 << 17
REG_COUNT = 8
WORD_MASK = 0xFFFFFFFF


OPCODES = {opcode: name for name, (opcode, _, _) in COMMANDS.items()}


class VMError(Exception):



class VM:
    def __init__(self, code: bytes):
        if len(code) > MEM_SIZE:
            raise VMError("программа не помещается в память")
        self.memory = [0] * MEM_SIZE
        for i, byte in enumerate(code):
            self.memory[i] = byte
        self.code_size = len(code)
        self.registers = [0] * REG_COUNT
        self.pc = 0
        self.executed = 0


    def _check_addr(self, addr: int) -> None:
        if not 0 <= addr < MEM_SIZE:
            raise VMError(f"адрес {addr} вне памяти (0..{MEM_SIZE - 1})")

    def read_mem(self, addr: int) -> int:
        self._check_addr(addr)
        return self.memory[addr]

    def write_mem(self, addr: int, value: int) -> None:
        self._check_addr(addr)
        self.memory[addr] = value & WORD_MASK


    def fetch(self) -> Instruction:

        a = self.memory[self.pc] & ((1 << A_FIELD[1]) - 1)
        if a not in OPCODES:
            raise VMError(f"адрес {self.pc}: неизвестный код операции A={a}")
        mnemonic = OPCODES[a]
        _, size, fields = COMMANDS[mnemonic]
        if self.pc + size > self.code_size:
            raise VMError(f"адрес {self.pc}: команда {mnemonic} обрезана")
        word = 0
        for i in range(size):
            word |= (self.memory[self.pc + i] & 0xFF) << (8 * i)
        b_off, b_w = fields["B"]
        c_off, c_w = fields["C"]
        b = (word >> b_off) & ((1 << b_w) - 1)
        c = (word >> c_off) & ((1 << c_w) - 1)
        return Instruction(mnemonic, a, b, c, size)


    def execute(self, ins: Instruction) -> None:
        if ins.mnemonic == "LOAD":
            self.registers[ins.b] = ins.c
        elif ins.mnemonic == "READ":
            self.registers[ins.c] = self.read_mem(ins.b)
        elif ins.mnemonic == "WRITE":
            self.write_mem(self.registers[ins.c], self.registers[ins.b])
        else:
            raise VMError(f"команда {ins.mnemonic} пока не реализована")

    def run(self) -> None:
        while self.pc < self.code_size:
            ins = self.fetch()
            self.pc += ins.size
            self.execute(ins)
            self.executed += 1


def parse_range(text: str) -> tuple:

    try:
        start_s, end_s = text.split(":")
        start, end = int(start_s, 0), int(end_s, 0)
    except ValueError:
        raise VMError(f"диапазон '{text}' должен иметь вид начало:конец")
    if not 0 <= start <= end <= MEM_SIZE:
        raise VMError(f"диапазон {start}:{end} вне памяти (0..{MEM_SIZE})")
    return start, end


def dump_xml(vm: VM, start: int, end: int, path: str) -> None:
    root = ET.Element("memory", start=str(start), end=str(end))
    for addr in range(start, end):
        ET.SubElement(root, "cell", address=str(addr), value=str(vm.memory[addr]))
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Интерпретатор УВМ")
    parser.add_argument("program", help="путь к бинарному файлу программы")
    parser.add_argument("dump", help="путь к XML-файлу с дампом памяти")
    parser.add_argument("range", help="диапазон адресов дампа: начало:конец (конец не включается)")
    args = parser.parse_args(argv)

    try:
        start, end = parse_range(args.range)
        with open(args.program, "rb") as f:
            code = f.read()
        vm = VM(code)
        vm.run()
        dump_xml(vm, start, end, args.dump)
    except (VMError, OSError) as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1

    print(f"Выполнено команд: {vm.executed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())