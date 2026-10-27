import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from retrieval.hybrid import reciprocal_rank_fusion


class ReciprocalRankFusionTests(unittest.TestCase):
    def test_shared_files_receive_two_rank_contributions(self):
        results = reciprocal_rank_fusion(
            ["lexical.py", "shared.py", "anchor.py"],
            ["semantic.py", "shared.py", "anchor.py"],
            anchor_file="anchor.py",
        )
        self.assertEqual(results[0].path, "shared.py")
        self.assertEqual(results[0].bm25_rank, 2)
        self.assertEqual(results[0].semantic_rank, 2)
        self.assertNotIn("anchor.py", [result.path for result in results])

    def test_results_are_unique_and_limited(self):
        results = reciprocal_rank_fusion(
            ["a.py", "a.py", "b.py"],
            ["b.py", "c.py"],
            top_k=2,
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(len({result.path for result in results}), 2)

    def test_invalid_parameters_are_rejected(self):
        with self.assertRaises(ValueError):
            reciprocal_rank_fusion([], [], top_k=-1)
        with self.assertRaises(ValueError):
            reciprocal_rank_fusion([], [], rrf_k=-1)


if __name__ == "__main__":
    unittest.main()
