import unittest

from Assembeler import Instruction, COMMANDS, encode, format_bytes, parse_source


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


if __name__ == "__main__":
    unittest.main()