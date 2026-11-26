import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
from io import StringIO

import Assembeler
from intepretator import MEM_SIZE, VM, VMError, main, parse_range


def build(rows):
    """Собрать программу из списка (мнемоника, B, C) в машинный код."""
    program = []
    for name, b, c in rows:
        opcode, size, _ = Assembeler.COMMANDS[name]
        program.append(Assembeler.Instruction(name, opcode, b, c, size))
    return Assembeler.assemble(program)


class VMTests(unittest.TestCase):
    def test_load(self):
        vm = VM(build([("LOAD", 6, 553)]))
        vm.run()
        self.assertEqual(vm.registers[6], 553)

    def test_write_then_read(self):
        vm = VM(build([
            ("LOAD", 0, 1000),
            ("LOAD", 1, 42),
            ("WRITE", 1, 0),
            ("READ", 1000, 5),
        ]))
        vm.run()
        self.assertEqual(vm.memory[1000], 42)
        self.assertEqual(vm.registers[5], 42)

    def test_decode_spec_commands(self):
        vm = VM(bytes([0xD9, 0x29, 0x02, 0x00, 0x00]))
        ins = vm.fetch()
        self.assertEqual((ins.mnemonic, ins.a, ins.b, ins.c), ("LOAD", 25, 6, 553))
        vm = VM(bytes([0xFA, 0x2B, 0xC0, 0x01]))
        ins = vm.fetch()
        self.assertEqual((ins.mnemonic, ins.a, ins.b, ins.c), ("READ", 26, 351, 7))
        vm = VM(bytes([0xF0, 0x06]))
        ins = vm.fetch()
        self.assertEqual((ins.mnemonic, ins.a, ins.b, ins.c), ("WRITE", 16, 7, 6))

    def test_code_in_shared_memory(self):
        code = build([("LOAD", 0, 1)])
        vm = VM(code)
        self.assertEqual(bytes(vm.memory[:len(code)]), code)

    def test_unknown_opcode(self):
        with self.assertRaises(VMError):
            VM(bytes([0x01])).run()

    def test_address_out_of_memory(self):
        vm = VM(build([("LOAD", 0, MEM_SIZE), ("WRITE", 0, 0)]))
        with self.assertRaises(VMError):
            vm.run()

    def test_truncated_command(self):
        with self.assertRaises(VMError):
            VM(bytes([0xD9, 0x29])).run()

    def test_parse_range(self):
        self.assertEqual(parse_range("300:305"), (300, 305))
        with self.assertRaises(VMError):
            parse_range("305:300")
        with self.assertRaises(VMError):
            parse_range("abc")


class CopyArrayTest(unittest.TestCase):
    def run_copy(self):
        program = Assembeler.parse_source("examples/copy_array.csv")
        vm = VM(Assembeler.assemble(program))
        vm.run()
        return vm

    def test_array_copied(self):
        vm = self.run_copy()
        expected = [11, 22, 33, 44, 55]
        self.assertEqual(vm.memory[200:205], expected)
        self.assertEqual(vm.memory[300:305], expected)
        self.assertEqual(vm.memory[305], 0)

    def test_cli_xml_dump(self):
        with tempfile.TemporaryDirectory() as d:
            binary = os.path.join(d, "copy.bin")
            dump = os.path.join(d, "dump.xml")
            with redirect_stdout(StringIO()):
                Assembeler.main(["examples/copy_array.csv", binary])
            buf = StringIO()
            with redirect_stdout(buf):
                rc = main([binary, dump, "300:305"])
            self.assertEqual(rc, 0)
            self.assertIn("Выполнено команд: 25", buf.getvalue())
            root = ET.parse(dump).getroot()
            cells = [(int(c.get("address")), int(c.get("value")))
                     for c in root.iter("cell")]
            self.assertEqual(cells, [(300, 11), (301, 22), (302, 33),
                                     (303, 44), (304, 55)])


class SqrtTests(unittest.TestCase):
    def test_decode_spec_sqrt(self):
        vm = VM(bytes([0xF2, 0x67, 0x02, 0x00]))
        ins = vm.fetch()
        self.assertEqual((ins.mnemonic, ins.a, ins.b, ins.c), ("SQRT", 18, 7, 615))

    def test_sqrt_to_memory(self):
        vm = VM(build([("LOAD", 7, 81), ("SQRT", 7, 300)]))
        vm.run()
        self.assertEqual(vm.memory[300], 9)
        self.assertEqual(vm.registers[7], 81)     # операнд не изменился

    def test_sqrt_floor(self):
        vm = VM(build([("LOAD", 0, 99), ("SQRT", 0, 300)]))
        vm.run()
        self.assertEqual(vm.memory[300], 9)

    def test_sqrt_program_file(self):
        program = Assembeler.parse_source("examples/sqrt_test.csv")
        vm = VM(Assembeler.assemble(program))
        vm.run()
        self.assertEqual(vm.memory[200:206], [12, 1000, 25, 0, 1, 5792])
        self.assertEqual(vm.executed, 12)

    def test_cli_sqrt_dump(self):
        with tempfile.TemporaryDirectory() as d:
            binary = os.path.join(d, "sqrt.bin")
            dump = os.path.join(d, "dump.xml")
            with redirect_stdout(StringIO()):
                Assembeler.main(["examples/sqrt_test.csv", binary])
            with redirect_stdout(StringIO()):
                rc = main([binary, dump, "200:206"])
            self.assertEqual(rc, 0)
            values = [int(c.get("value")) for c in ET.parse(dump).getroot().iter("cell")]
            self.assertEqual(values, [12, 1000, 25, 0, 1, 5792])


if __name__ == "__main__":
    unittest.main()