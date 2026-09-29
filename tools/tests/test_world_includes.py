"""Safe, ordered expansion of region-local C include fragments."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from world_includes import read_world_source


class WorldSourceTests(unittest.TestCase):
    def test_order_comments_and_repeated_noncyclic_includes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "extra.inc").write_text("MAP_NEW,\n")
            (root / "ids.inc").write_text('MAP_OLD,\n/* #include "missing.inc" */\n'
                                          '#include "extra.inc"\nMAP_LAST,\n#include "extra.inc"\n')
            source = read_world_source(root / "ids.inc", root)
            self.assertLess(source.index("MAP_OLD"), source.index("MAP_NEW"))
            self.assertLess(source.index("MAP_NEW"), source.index("MAP_LAST"))
            self.assertEqual(source.count("MAP_NEW"), 2)
            self.assertNotIn("missing", source)

    def test_cycle_is_descriptive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.inc").write_text('#include "b.inc"')
            (root / "b.inc").write_text('#include "a.inc"')
            with self.assertRaisesRegex(ValueError, "include cycle"):
                read_world_source(root / "a.inc", root)

    def test_include_cannot_escape_world_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "world"
            root.mkdir()
            (root / "a.inc").write_text('#include "../outside.inc"')
            with self.assertRaisesRegex(ValueError, "escapes its root"):
                read_world_source(root / "a.inc", root)

    def test_missing_include_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.inc").write_text('#include "missing.inc"')
            with self.assertRaises(FileNotFoundError):
                read_world_source(root / "a.inc", root)


if __name__ == "__main__":
    unittest.main()
