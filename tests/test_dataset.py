"""
Unit tests for the fine-tuning dataset integrity and splits.
"""

import os
import json
import pytest
from pathlib import Path


def load_lines(filepath):
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def test_dataset_files_exist():
    base = Path("training/dataset")
    assert (base / "train.jsonl").exists()
    assert (base / "validation.jsonl").exists()
    assert (base / "test.jsonl").exists()
    assert (base / "dataset_manifest.json").exists()


def test_dataset_chatml_structure():
    base = Path("training/dataset")
    train_records = load_lines(base / "train.jsonl")
    assert len(train_records) > 0

    valid_roles = {"system", "user", "assistant"}
    for r in train_records:
        assert "messages" in r
        assert len(r["messages"]) >= 2
        for msg in r["messages"]:
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in valid_roles
            assert len(msg["content"].strip()) > 0


def test_dataset_no_leakage():
    base = Path("training/dataset")
    train = load_lines(base / "train.jsonl")
    val = load_lines(base / "validation.jsonl")
    test = load_lines(base / "test.jsonl")

    def get_queries(records):
        return {r["messages"][1]["content"].strip().lower() for r in records}

    train_q = get_queries(train)
    val_q = get_queries(val)
    test_q = get_queries(test)

    # Verify no query overlap between splits
    assert len(train_q.intersection(val_q)) == 0, "Train and validation sets share queries!"
    assert len(train_q.intersection(test_q)) == 0, "Train and test sets share queries!"
    assert len(val_q.intersection(test_q)) == 0, "Validation and test sets share queries!"
