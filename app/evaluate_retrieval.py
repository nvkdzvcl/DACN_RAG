"""Retrieval-only benchmark on a pooled knowledge base (embeddings only, no chat model).

Every eval corpus is ingested into one temporary index, so other shops' similar policies act as
distractors, as in a growing real knowledge base. Each case with gold evidence is queried once per
retrieval mode; gate variants are scored offline from the same ranked lists.

Follow-up queries use the no-model fallback (customer turns + question), not the model rewrite.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unicodedata
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.migrations import migrate
from app.evaluate_rag import ROOT, load_cases, normalize, ratio
from app.rag import vector_store as vector_module
from app.rag.lexical import fuse
from app.rag.ollama import embed
from app.rag.vector_store import VectorStore
from app.services.document_service import ALLOWED_EXTENSIONS, save_document

DATASETS = {"rag": "evals/rag", "bt20": "evals/bt20", "context": "evals/rag-context", "documents": "evals/rag-documents",
            "policy": "evals/rag-policy", "customer": "evals/independent-v1/customer-v2/main",
            "reserve": "evals/independent-v1/customer-v2/reserve", "heldout": "evals/heldout-v1"}
HELD_OUT = {"heldout"}
CANDIDATES = 20  # production pool size for top_k=5 (max(top_k, min(top_k * 4, 40)))
WEIGHTS = (1.0, 0.5, 0.3, 0.15)
MODES = ("legacy", "dense", *(f"rrf{w}" for w in WEIGHTS))
TOP_K = 5  # same as production answer_question
GATES = {"cos0.35": (0.35, 0, 1.0), "cos0.30": (0.30, 0, 1.0), "cos0.35+lex2@0.25": (0.35, 2, 0.25),
         "cos0.35+lex3@0.25": (0.35, 3, 0.25), "cos0.35+lex2@0.20": (0.35, 2, 0.20), "cos0.30+lex2@0.20": (0.30, 2, 0.20)}


def passes_gate(result, settings):
    """Cosine threshold, optionally also admitting top lexical ranks above a lower cosine (benchmark only)."""
    min_cosine, lexical_rank, lexical_min_cosine = settings
    rank = result.get("lexical_rank")
    return result["score"] >= min_cosine or (rank is not None and rank <= lexical_rank and result["score"] >= lexical_min_cosine)


def legacy_rank(query, results, top_k):
    """The pre-hybrid ranking (dense candidates plus a capped bigram bonus), kept only for comparison."""
    def phrases(text):
        words = re.findall(r"\w+", unicodedata.normalize("NFC", text).casefold())
        return set(zip(words, words[1:]))
    query_phrases = phrases(query)
    source_phrases = [phrases(result["content"]) for result in results]
    counts = Counter(phrase for item in source_phrases for phrase in item)
    weighted = [(result["score"] + min(0.12, sum(0.04 / counts[p] for p in query_phrases & terms)), index, result)
                for index, (result, terms) in enumerate(zip(results, source_phrases))]
    return [result for _, _, result in sorted(weighted, key=lambda item: (-item[0], item[1]))[:top_k]]


def query_text(case):
    turns = [m["content"][:240] for m in case["history"] if m["role"] == "user"]
    return "\n".join([*turns, case["query"]])


def found(hits, evidence, names):
    return any(h["source"] == names[evidence["source"]] and h.get("location") == evidence["location"] and
               ("page" not in evidence or h.get("page") == evidence["page"]) and
               normalize(evidence["quote"]) in normalize(h["content"]) for h in hits)


def score(rows, mode, gate):
    gold = [r for r in rows if r["evidence"]]
    quotes = [(r, e) for r in gold for e in r["evidence"]]
    gated = {r["id"]: [h for h in r[mode] if passes_gate(h, GATES[gate])][:5] for r in rows}
    negatives = [r for r in rows if not r["should_answer"]]
    return {
        "gold_cases": len(gold), "gold_quotes": len(quotes),
        "recall_at": {k: ratio(sum(found(r[mode][:k], e, r["names"]) for r, e in quotes), len(quotes)) for k in (1, 3, 5)},
        "gate_quote_recall": ratio(sum(found(gated[r["id"]], e, r["names"]) for r, e in quotes), len(quotes)),
        "gate_case_hit": ratio(sum(any(found(gated[r["id"]], e, r["names"]) for e in r["evidence"]) for r in gold), len(gold)),
        "gate_empty_on_answerable": sum(not gated[r["id"]] for r in rows if r["should_answer"]),
        "mean_gated_on_negatives": ratio(sum(len(gated[r["id"]]) for r in negatives), len(negatives)),
    }


def run(output, datasets=DATASETS):
    output.mkdir(parents=True, exist_ok=False)
    cases, names_by_dataset, files = [], {}, []
    for key, folder in datasets.items():
        directory = ROOT / folder
        cases += [{**case, "dataset": key} for case in load_cases(directory / "cases.jsonl")]
        files += [(key, path) for path in sorted((directory / "corpus").iterdir()) if path.suffix.lower() in ALLOWED_EXTENSIONS]
    rows = []
    with tempfile.TemporaryDirectory(prefix="retrieval-eval-") as tmp:
        root = Path(tmp)
        engine = create_engine("sqlite:///" + str(root / "eval.db"))
        store = VectorStore(str(root / "vectors"))
        migrate(engine)
        cache = {}
        def cached_embed(texts):
            missing = [t for t in texts if t not in cache]
            if missing:
                cache.update(zip(missing, embed(missing)))
            return [cache[t] for t in texts]
        try:
            with patch("app.services.document_service.vector_store", store), Session(engine) as db:
                pooled = {}
                for key, path in files:
                    content = path.read_bytes()
                    digest = hashlib.sha256(content).hexdigest()
                    if digest not in pooled:  # identical files across datasets are ingested once
                        name = f"{key}__{path.name}"
                        result = save_document(db, name, content, root / "files")
                        if result["status"] != "indexed":
                            raise RuntimeError(f"Ingestion failed: {name}: {result['error_message']}")
                        pooled[digest] = name
                    names_by_dataset.setdefault(key, {})[path.name] = pooled[digest]
                with patch.object(vector_module, "embed", side_effect=cached_embed):
                    store.search("khởi tạo", TOP_K, db)  # builds the lexical cache for the pooled versions
                    key, chunks = store.lexical.key, store.lexical.chunks
                    for index, case in enumerate(cases, 1):
                        query = query_text(case)
                        with patch.object(store.lexical, "search", return_value=[]):
                            ranked = store.search(query, 400, db)  # cosine for every chunk, dense order
                        cosine = {item["chunk_id"]: item["score"] for item in ranked}
                        lexical = [(chunk | {"score": cosine[chunk["chunk_id"]]}, value) for chunk, value in
                                   store.lexical.search(query, CANDIDATES, key, lambda: chunks) if chunk["chunk_id"] in cosine]
                        dense = ranked[:CANDIDATES]
                        row = {k: case[k] for k in ("id", "dataset", "category", "query", "history", "should_answer", "evidence")}
                        row |= {"names": names_by_dataset[case["dataset"]], "legacy": legacy_rank(query, dense, TOP_K),
                                "dense": dense[:TOP_K], **{f"rrf{w}": fuse(dense, lexical, TOP_K, w) for w in WEIGHTS}}
                        rows.append(row)
                        if index % 50 == 0:
                            print(f"{index}/{len(cases)}", flush=True)
        finally:
            store.close()
            engine.dispose()
    with (output / "results.jsonl").open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    groups = {"dev": [r for r in rows if r["dataset"] not in HELD_OUT], "heldout": [r for r in rows if r["dataset"] in HELD_OUT]}
    summary = {"finished_at_utc": datetime.now(timezone.utc).isoformat(), "pooled_files": len(set(pooled.values())),
               "cases": len(rows), "query": "customer turns + question (no model rewrite)",
               "gates": {name: list(values) for name, values in GATES.items()},
               "results": {group: {mode: {gate: score(items, mode, gate) for gate in GATES} for mode in MODES}
                           for group, items in groups.items() if items}}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    summary = run(args.output)
    for group, modes in summary["results"].items():
        for mode, gates in modes.items():
            first = next(iter(gates.values()))
            print(f"{group:8s} {mode:7s} n={first['gold_cases']} R@1={first['recall_at'][1]} R@5={first['recall_at'][5]}")
            for gate, values in gates.items():
                print(f"{'':17s} {gate:20s} gate_hit={values['gate_case_hit']} empty={values['gate_empty_on_answerable']} "
                      f"noise_neg={values['mean_gated_on_negatives']}")


if __name__ == "__main__":
    main()
