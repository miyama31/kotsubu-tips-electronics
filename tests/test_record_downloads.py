import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from scripts import record_downloads
from datetime import datetime
from scripts.record_downloads import JST, merge_rows


class RecordingTests(unittest.TestCase):
    def test_first_and_same_day_replacement_and_next_day(self):
        first = merge_rows([], [("tag", "file.zip", 10)], datetime(2026, 10, 29, 7, tzinfo=JST))
        self.assertEqual(first[0]["increase"], "")
        repeated = merge_rows(first, [("tag", "file.zip", 12)], datetime(2026, 10, 29, 8, tzinfo=JST))
        self.assertEqual(len(repeated), 1)
        next_day = merge_rows(repeated, [("tag", "file.zip", 15)], datetime(2026, 10, 30, 7, tzinfo=JST))
        self.assertEqual(next_day[1]["increase"], "3")

    def test_new_target_has_no_invented_baseline(self):
        rows = merge_rows([], [("02", "a.zip", 4), ("03", "b.zip", 8)], datetime(2026, 10, 29, tzinfo=JST))
        self.assertTrue(all(row["increase"] == "" for row in rows))

    def test_decrease_and_invalid_counter_fail(self):
        rows = merge_rows([], [("tag", "a", 4)], datetime(2026, 10, 29, tzinfo=JST))
        with self.assertRaises(ValueError):
            merge_rows(rows, [("tag", "a", 3)], datetime(2026, 10, 30, tzinfo=JST))
        with self.assertRaises(ValueError):
            merge_rows([], [("tag", "a", None)], datetime(2026, 10, 29, tzinfo=JST))
        with self.assertRaises(ValueError):
            merge_rows(rows, [("tag", "a", 3)], datetime(2026, 10, 29, 8, tzinfo=JST))

    def test_api_failure_preserves_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config/download-targets.json").write_text('[{"release_tag":"tag","asset_name":"a"}]')
            (root / "data").mkdir()
            csv_path = root / "data/download-history.csv"
            csv_path.write_bytes(b"existing history")
            with patch.object(record_downloads, "ROOT", root), patch.object(record_downloads, "urlopen", side_effect=OSError("API unavailable")):
                with self.assertRaises(OSError):
                    record_downloads.main()
            self.assertEqual(csv_path.read_bytes(), b"existing history")
