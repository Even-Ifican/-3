import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

from Assembeler import (COMMANDS, Instruction, assemble, encode, format_bytes,
                       main, parse_source, translate)

SPEC_BYTES = bytes([
    0xD9, 0x29, 0x02, 0x00, 0x00,
    0xFA, 0x2B, 0xC0, 0x01,
    0xF0, 0x06,
    0xF2, 0x67, 0x02, 0x00,
])


def make(mnemonic, b, c):
    opcode, size, _ = COMMANDS[mnemonic]
    return Instruction(mnemonic, opcode, b, c, size)


class SpecTests(unittest.TestCase):
    def check(self, mnemonic, a, b, c, expected):
        instr = make(mnemonic, b, c)
        self.assertEqual((instr.a, instr.b, instr.c), (a, b, c))
        self.assertEqual(format_bytes(encode(instr)), expected)

    def test_load(self):
        self.check("LOAD", 25, 6, 553, "0xD9, 0x29, 0x02, 0x00, 0x00")

    def test_read(self):
        self.check("READ", 26, 351, 7, "0xFA, 0x2B, 0xC0, 0x01")

    def test_write(self):
        self.check("WRITE", 16, 7, 6, "0xF0, 0x06")

    def test_sqrt(self):
        self.check("SQRT", 18, 7, 615, "0xF2, 0x67, 0x02, 0x00")

    def test_parse_file(self):
        program = parse_source("examples/spec_tests.csv")
        got = [(i.a, i.b, i.c) for i in program]
        self.assertEqual(got, [(25, 6, 553), (26, 351, 7), (16, 7, 6), (18, 7, 615)])


class Stage2Tests(unittest.TestCase):
    def test_translate_per_command(self):
        program = parse_source("examples/spec_tests.csv")
        self.assertEqual([len(c) for c in translate(program)], [5, 4, 2, 4])

    def test_assemble_matches_spec(self):
        program = parse_source("examples/spec_tests.csv")
        self.assertEqual(assemble(program), SPEC_BYTES)

    def test_cli_writes_file_and_prints_count(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "out.bin")
            buf = StringIO()
            with redirect_stdout(buf):
                rc = main(["examples/spec_tests.csv", out, "--test"])
            self.assertEqual(rc, 0)
            with open(out, "rb") as f:
                self.assertEqual(f.read(), SPEC_BYTES)
            lines = buf.getvalue().splitlines()
            self.assertEqual(lines[0], "Ассемблировано команд: 4")
            self.assertEqual(lines[1], "0xD9, 0x29, 0x02, 0x00, 0x00")
            self.assertEqual(lines[4], "0xF2, 0x67, 0x02, 0x00")


if __name__ == "__main__":
    unittest.main()