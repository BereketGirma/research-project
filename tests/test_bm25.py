import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from retrieval.bm25 import candidate_chunks, evaluate_ranking, rank_files, tokenize


class BM25Edit2RippleTests(unittest.TestCase):
    def test_tokenize_splits_camel_snake_and_alphanumeric_terms(self):
        self.assertEqual(
            tokenize("HTTPServer anchor_file fooBar v2-beta"),
            ["http", "server", "anchor", "file", "foo", "bar", "v2", "beta"],
        )

    def test_candidate_chunks_excludes_all_anchor_file_chunks(self):
        sample = {"query": {"anchor_file": "src/anchor.py"}}
        chunks = [
            {"path": "src/anchor.py", "chunk_id": "a"},
            {"path": "src/other.py", "chunk_id": "b"},
            {"path": "src/anchor.py", "chunk_id": "c"},
        ]
        self.assertEqual([chunk["chunk_id"] for chunk in candidate_chunks(sample, chunks)], ["b"])

    def test_rank_files_deduplicates_chunks_by_path(self):
        sample = {
            "query": {
                "anchor_file": "anchor.py",
                "intent": "target symbol",
                "anchor_diff": "targetSymbol()",
            }
        }
        chunks = [
            {"path": "anchor.py", "symbol": "targetSymbol", "text": "target", "chunk_id": "given"},
            {"path": "best.py", "symbol": "targetSymbol", "text": "target symbol", "chunk_id": "best-1"},
            {"path": "best.py", "symbol": "other", "text": "target", "chunk_id": "best-2"},
            {"path": "second.py", "symbol": "other", "text": "unrelated", "chunk_id": "second"},
        ]
        results = rank_files(sample, chunks, top_k=10)
        self.assertEqual([result.path for result in results], ["best.py", "second.py"])
        self.assertNotIn("anchor.py", [result.path for result in results])

    def test_evaluate_ranking_uses_file_recall_and_first_gold_rank(self):
        metrics = evaluate_ranking(["gold-a.py", "gold-b.py"], ["x.py", "gold-b.py", "y.py"])
        self.assertEqual(metrics.recall_at_5, 0.5)
        self.assertEqual(metrics.recall_at_10, 0.5)
        self.assertEqual(metrics.reciprocal_rank, 0.5)


if __name__ == "__main__":
    unittest.main()
