import math
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
from io import StringIO

import Assembeler
from interpreter import VM, main


CASES = {
    "examples/vec_squares.csv":  (200, [0, 1, 4, 9, 16, 25, 36, 49]),
    "examples/vec_hundreds.csv": (300, [100, 400, 900, 1600, 2500, 3600, 4900, 6400]),
    "examples/vec_mixed.csv":    (400, [2, 10, 99, 1000, 65535, 1000000,
                                        16777216, 33554431]),
}
EXPECTED = {
    "examples/vec_squares.csv":  [0, 1, 2, 3, 4, 5, 6, 7],
    "examples/vec_hundreds.csv": [10, 20, 30, 40, 50, 60, 70, 80],
    "examples/vec_mixed.csv":    [1, 3, 9, 31, 255, 1000, 4096, 5792],
}


def load_vm(path):
    program = Assembeler.parse_source(path)
    return VM(Assembeler.assemble(program))


class VectorSqrtTests(unittest.TestCase):
    def test_expected_matches_isqrt(self):
        for path, (_, data) in CASES.items():
            self.assertEqual([math.isqrt(x) for x in data], EXPECTED[path])

    def test_vector_replaced_in_place(self):
        for path, (base, _) in CASES.items():
            with self.subTest(program=path):
                vm = load_vm(path)
                self.assertGreater(base, vm.code_size)
                vm.run()
                self.assertEqual(vm.memory[base:base + 8], EXPECTED[path])
                self.assertEqual(vm.executed, 40)
                self.assertEqual(vm.memory[base + 8], 0)

    def test_cli_dump(self):
        for path, (base, _) in CASES.items():
            with self.subTest(program=path), tempfile.TemporaryDirectory() as d:
                binary = os.path.join(d, "p.bin")
                dump = os.path.join(d, "dump.xml")
                with redirect_stdout(StringIO()):
                    Assembeler.main([path, binary])
                with redirect_stdout(StringIO()):
                    rc = main([binary, dump, f"{base}:{base + 8}"])
                self.assertEqual(rc, 0)
                cells = [(int(c.get("address")), int(c.get("value")))
                         for c in ET.parse(dump).getroot().iter("cell")]
                self.assertEqual(cells, list(zip(range(base, base + 8),
                                                 EXPECTED[path])))


if __name__ == "__main__":
    unittest.main()