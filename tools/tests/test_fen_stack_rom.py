"""Check the ROM field-render scratch placement after `make`.

Run with: python3 -m unittest tools.tests.test_fen_stack_rom
The existing playthrough runner test covers the Heron Fen warden bout.
"""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class FenFieldStackRomTest(unittest.TestCase):
    def test_field_sprite_scratch_is_in_ewram(self):
        elf = ROOT / 'game.elf'
        if not elf.exists():
            self.skipTest('build the ROM first with make')
        output = subprocess.check_output(['arm-none-eabi-nm', '-S', str(elf)], text=True)
        symbols = {}
        for line in output.splitlines():
            parts = line.split()
            if len(parts) == 3:
                address, kind, name = parts
                size = 0
            elif len(parts) == 4:
                address, size, kind, name = parts
                size = int(size, 16)
            else:
                continue
            symbols[name] = (int(address, 16), size)
        for prefix, minimum_size in [('list.', 96 * 16), ('kins.', 400 * 4)]:
            matches = [(addr, size) for name, (addr, size) in symbols.items()
                       if name.startswith(prefix) and size >= minimum_size]
            self.assertEqual(len(matches), 1, f'missing or ambiguous {prefix} field scratch')
            address, size = matches[0]
            self.assertGreaterEqual(address, 0x02000000)
            self.assertLessEqual(address + size, 0x02040000)
        self.assertLess(symbols['__bss_end'][0], 0x03007D00)
        self.assertLessEqual(symbols['__sbss_end'][0], 0x02040000)


if __name__ == '__main__':
    unittest.main()
