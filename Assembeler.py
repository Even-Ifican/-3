import argparse
import csv
import sys
from dataclasses import dataclass


COMMANDS = {
    "LOAD":  (25, 5, {"B": (5, 3),  "C": (8, 25)}),
    "READ":  (26, 4, {"B": (5, 17), "C": (22, 3)}),
    "WRITE": (16, 2, {"B": (5, 3),  "C": (8, 3)}),
    "SQRT":  (18, 4, {"B": (5, 3),  "C": (8, 17)}),
}
A_FIELD = (0, 5)


class AsmError(Exception):



@dataclass
class Instruction:
    mnemonic: str
    a: int
    b: int
    c: int
    size: int


def parse_int(text: str, line_no: int) -> int:
    try:
        return int(text.strip(), 0)
    except ValueError:
        raise AsmError(f"строка {line_no}: '{text}' не является целым числом")


def check_range(name: str, value: int, width: int, line_no: int) -> None:
    if not 0 <= value < (1 << width):
        raise AsmError(
            f"строка {line_no}: поле {name}={value} вне диапазона 0..{(1 << width) - 1}")


def parse_source(path: str) -> list:
    program = []
    with open(path, newline="", encoding="utf-8") as f:
        for line_no, row in enumerate(csv.reader(f), start=1):
            row = [cell.strip() for cell in row]
            if not row or not row[0] or row[0].startswith("#"):
                continue  # пустая строка или комментарий
            mnemonic = row[0].upper()
            if mnemonic not in COMMANDS:
                raise AsmError(f"строка {line_no}: неизвестная команда '{row[0]}'")
            opcode, size, fields = COMMANDS[mnemonic]
            if len(row) != 3:
                raise AsmError(
                    f"строка {line_no}: команда {mnemonic} требует 2 операнда (B, C)")
            b = parse_int(row[1], line_no)
            c = parse_int(row[2], line_no)
            check_range("B", b, fields["B"][1], line_no)
            check_range("C", c, fields["C"][1], line_no)
            program.append(Instruction(mnemonic, opcode, b, c, size))
    return program


def encode(instr: Instruction) -> bytes:
    _, _, fields = COMMANDS[instr.mnemonic]
    word = instr.a << A_FIELD[0]
    word |= instr.b << fields["B"][0]
    word |= instr.c << fields["C"][0]
    return word.to_bytes(instr.size, "little")


def translate(program: list) -> list:
    return [encode(instr) for instr in program]


def assemble(program: list) -> bytes:
    return b"".join(translate(program))


def format_bytes(data: bytes) -> str:
    return ", ".join(f"0x{b:02X}" for b in data)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Ассемблер УВМ")
    parser.add_argument("source", help="путь к исходному файлу (CSV)")
    parser.add_argument("output", help="путь к двоичному файлу-результату")
    parser.add_argument("--test", action="store_true",
                        help="режим тестирования: вывести машинный код в байтовом формате")
    args = parser.parse_args(argv)

    try:
        program = parse_source(args.source)
        machine = translate(program)
        with open(args.output, "wb") as f:
            f.write(b"".join(machine))
    except (AsmError, OSError) as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1

    print(f"Ассемблировано команд: {len(machine)}")
    if args.test:
        for code in machine:
            print(format_bytes(code))
    return 0


if __name__ == "__main__":
    sys.exit(main())