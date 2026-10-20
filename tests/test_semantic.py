import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from retrieval.semantic import encode_chunks, rank_files


class FakeEncoder:
    def encode(self, sentences, **kwargs):
        values = [sentences] if isinstance(sentences, str) else sentences
        vectors = []
        for value in values:
            text = value.lower()
            vector = np.array(
                [float("target" in text), float("secondary" in text)], dtype=np.float32
            )
            norm = np.linalg.norm(vector)
            vectors.append(vector / norm if norm else vector)
        result = np.stack(vectors)
        return result[0] if isinstance(sentences, str) else result


class SemanticEdit2RippleTests(unittest.TestCase):
    def test_rank_files_excludes_anchor_and_deduplicates_paths(self):
        sample = {
            "query": {
                "anchor_file": "anchor.py",
                "intent": "target",
                "anchor_diff": "",
            }
        }
        chunks = [
            {"path": "anchor.py", "symbol": "target", "text": "target", "chunk_id": "a"},
            {"path": "best.py", "symbol": "target", "text": "target", "chunk_id": "b1"},
            {"path": "best.py", "symbol": "target", "text": "", "chunk_id": "b2"},
            {"path": "other.py", "symbol": "secondary", "text": "secondary", "chunk_id": "c"},
        ]
        model = FakeEncoder()
        embeddings = encode_chunks(chunks, model)
        results = rank_files(sample, chunks, model, chunk_embeddings=embeddings)
        self.assertEqual([result.path for result in results], ["best.py", "other.py"])
        self.assertNotIn("anchor.py", [result.path for result in results])

    def test_embedding_count_must_match_chunks(self):
        sample = {"query": {"anchor_file": "anchor.py", "intent": "target"}}
        with self.assertRaises(ValueError):
            rank_files(
                sample,
                [{"path": "x.py"}],
                FakeEncoder(),
                chunk_embeddings=np.zeros((2, 2), dtype=np.float32),
            )


if __name__ == "__main__":
    unittest.main()
