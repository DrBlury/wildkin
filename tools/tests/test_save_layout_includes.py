"""The save manifest must count region-owned content split into include files."""
import importlib.util
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
spec = importlib.util.spec_from_file_location("save_layout_generator", ROOT / "tools/gen_save_layout.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class RegionIncludeTests(unittest.TestCase):
    def fixture(self, root, kind, base, extra):
        region = root / "east"
        (region / "biomes").mkdir(parents=True, exist_ok=True)
        (region / f"{kind}.inc").write_text(base + '\n#include "biomes/' + kind + '.inc"\n')
        (region / "biomes" / f"{kind}.inc").write_text(extra)

    def test_ids_keep_compiler_include_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, "ids", "MAP_EXISTING,", "MAP_MISTFALL_GORGE, MAP_MISTBELL,")
            with patch.object(generator, "WORLD", root):
                self.assertEqual(generator.ids("east", "ids", "MAP_"),
                                 ["MAP_EXISTING", "MAP_MISTFALL_GORGE", "MAP_MISTBELL"])

    def test_satchel_indices_include_new_items_without_reordering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, "satchels", "{ MAP_EXISTING, 2, 3, ITEM_TONIC, 1 },",
                         "/* { MAP_FAKE, ignored } */\n{ MAP_MISTBELL, 4, 5, ITEM_TONIC, 1 },")
            with patch.object(generator, "WORLD", root):
                self.assertEqual(generator.ids("east", "satchels", ""), ["east:0", "east:1"])

    def test_include_cycle_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, "ids", "MAP_EXISTING,", '#include "../ids.inc"')
            with patch.object(generator, "WORLD", root):
                with self.assertRaisesRegex(ValueError, "cycle"):
                    generator.ids("east", "ids", "MAP_")


if __name__ == "__main__":
    unittest.main()
