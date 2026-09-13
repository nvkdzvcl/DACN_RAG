"""Run the frozen local RAG benchmark without touching application data."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.migrations import migrate
from app.rag.answer_service import answer_question
from app.rag.ollama import call, chat, chat_model, embedding_model
from app.rag.vector_store import VectorStore
from app.services.document_service import CHUNK_OVERLAP, CHUNK_SIZE, save_document

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evals/rag"


def normalize(value):
    return " ".join(value.lower().split())


def load_cases(path=DATASET / "cases.jsonl"):
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids, groups, queries = set(), {}, set()
    for case in cases:
        if case["id"] in ids or case["split"] not in {"dev", "test"} or not case["query"].strip():
            raise ValueError("Duplicate case ID, invalid split or blank query")
        ids.add(case["id"])
        if case["group"] in groups and groups[case["group"]] != case["split"]:
            raise ValueError("A fact group crosses dataset splits")
        groups[case["group"]] = case["split"]
        identity = (normalize(case["query"]), json.dumps(case["history"], ensure_ascii=False, sort_keys=True))
        if identity in queries:
            raise ValueError("Duplicate question and history")
        queries.add(identity)
        if type(case["should_answer"]) is not bool or not case["expected_answer"].strip():
            raise ValueError("Invalid gold answer")
        if case["should_answer"] and (not case["evidence"] or not case["required_patterns"]):
            raise ValueError("Answerable cases need gold evidence and fact patterns")
        for pattern in case["required_patterns"] + case["forbidden_patterns"]:
            re.compile(pattern)
        for evidence in case["evidence"]:
            name = evidence["source"]
            if Path(name).name != name or not name.startswith(case["split"] + "-"):
                raise ValueError("Evidence must stay in its split corpus")
            lines = (path.parent / "corpus" / name).read_text(encoding="utf-8").splitlines()
            line = int(evidence["location"].removeprefix("Dòng "))
            if line < 1 or line > len(lines) or evidence["quote"] != lines[line - 1]:
                raise ValueError("Gold evidence does not match corpus location")
    return cases


def ratio(numerator, denominator):
    return round(numerator / denominator, 6) if denominator else None


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lo, hi = math.floor(position), math.ceil(position)
    return round(ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo), 3)


def score_case(case, answer, error=None):
    hits = answer.get("results", []) if answer else []
    citations = answer.get("citations", []) if answer else []
    gold = case["evidence"]
    text = normalize(answer.get("answer", "")) if answer else ""
    grounded = bool(answer and answer.get("grounded"))
    valid_run = error is None and answer is not None
    def same_source(item, evidence):
        return item.get("source") == evidence["source"] and item.get("location") == evidence["location"]
    recalls = {str(k): ratio(sum(any(same_source(h, e) and normalize(e["quote"]) in normalize(h.get("content", ""))
                                         for h in hits[:k]) for e in gold), len(gold)) for k in (1, 3, 5)}
    valid_citations = sum(any(same_source(c, e) and normalize(c.get("quote", "")) and
                             normalize(c["quote"]) in normalize(e["quote"]) for e in gold) for c in citations)
    forbidden = any(re.search(p, text, re.IGNORECASE) for p in case["forbidden_patterns"])
    abstained = valid_run and not grounded and not citations
    patterns_ok = all(re.search(p, text, re.IGNORECASE) for p in case["required_patterns"])
    return {
        "recall": recalls, "citation_count": len(citations), "gold_citation_count": valid_citations,
        "decision_correct": valid_run and (grounded if case["should_answer"] else abstained),
        "abstained": abstained, "forbidden_text": forbidden,
        "fact_pattern_pass": bool(valid_run and not forbidden and
                                  (grounded and patterns_ok and valid_citations > 0 if case["should_answer"] else abstained)),
    }


def summarize(rows):
    supported = [r for r in rows if r["should_answer"]]
    unsupported = [r for r in rows if not r["should_answer"]]
    successful = [r for r in rows if r["error"] is None]
    recall_rows = [r for r in rows if r["scores"]["recall"]["5"] is not None]
    return {
        "cases": len(rows), "errors": len(rows) - len(successful),
        "answerable_cases": len(supported), "abstention_cases": len(unsupported),
        "retrieval_cases_with_gold": len(recall_rows),
        "recall_at_k": {str(k): ratio(sum(r["scores"]["recall"][str(k)] for r in recall_rows), len(recall_rows)) for k in (1, 3, 5)},
        "gold_source_citation_precision": ratio(sum(r["scores"]["gold_citation_count"] for r in rows), sum(r["scores"]["citation_count"] for r in rows)),
        "answerable_citation_coverage": ratio(sum(r["scores"]["gold_citation_count"] > 0 for r in supported), len(supported)),
        "correct_abstention_rate": ratio(sum(r["scores"]["abstained"] for r in unsupported), len(unsupported)),
        "false_abstention_rate": ratio(sum(r["scores"]["abstained"] for r in supported), len(supported)),
        "decision_accuracy": ratio(sum(r["scores"]["decision_correct"] for r in rows), len(rows)),
        "fact_pattern_pass_rate": ratio(sum(r["scores"]["fact_pattern_pass"] for r in rows), len(rows)),
        "forbidden_text_cases": sum(r["scores"]["forbidden_text"] for r in rows),
        "latency_seconds_successful": {"n": len(successful), "p50": percentile([r["seconds"] for r in successful], .5),
                                       "p95": percentile([r["seconds"] for r in successful], .95)},
        "human_reviewed_cases": 0,
    }


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(split, output):
    cases = [c for c in load_cases() if c["split"] == split]
    output.mkdir(parents=True, exist_ok=False)  # Never overwrite a previous baseline.
    files = [DATASET / "cases.jsonl", *sorted((DATASET / "corpus").glob("*.txt")), *sorted((ROOT / "app").rglob("*.py"))]
    models = call("/api/tags").get("models", [])
    selected_models = {m["name"]: m["digest"] for m in models if m["name"] in {chat_model(), embedding_model()}}
    if len(selected_models) != len({chat_model(), embedding_model()}):
        raise RuntimeError("Configured Ollama models must be downloaded before evaluation")
    manifest = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(), "status": "running", "split": split,
        "case_ids": [c["id"] for c in cases], "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        "models": selected_models, "top_k": 5, "min_score": float(os.getenv("RAG_MIN_SCORE", "0.35")),
        "chunk_words": CHUNK_SIZE, "overlap_words": CHUNK_OVERLAP,
        "temperature": 0, "num_ctx": 8192, "num_predict": 700, "keep_alive": 0,
        "answer_pipeline": "generate, exact citation validation, same-model review, source-version recheck",
        "chat_calls_per_question": "0-2; review only for candidates with valid citations; completions saved in call order",
        "packages": {p: importlib.metadata.version(p) for p in ("qdrant-client", "sqlalchemy", "httpx")},
        "label_status": "synthetic_agent_authored_pending_human_review",
        "timing": "Sequential end-to-end calls; includes query embedding and model load/unload, excludes ingestion. No deliberate warmup.",
    }
    write_json(output / "manifest.json", manifest)
    (output / "answer_service.py.txt").write_bytes((ROOT / "app/rag/answer_service.py").read_bytes())
    rows = []
    try:
        with tempfile.TemporaryDirectory(prefix="rag-eval-") as directory:
            root = Path(directory)
            engine = create_engine("sqlite:///" + str(root / "eval.db"))
            store = VectorStore(str(root / "vectors"))
            try:
                migrate(engine)
                with patch("app.services.document_service.vector_store", store), patch("app.rag.answer_service.vector_store", store), Session(engine) as db:
                    for path in sorted((DATASET / "corpus").glob(split + "-*.txt")):
                        result = save_document(db, path.name, path.read_bytes(), root / "files")
                        if result["status"] != "indexed":
                            raise RuntimeError(f"Ingestion failed: {path.name}: {result['error_message']}")
                    store.close()
                    for index, case in enumerate(cases, 1):
                        raw_completions = []
                        def capture_chat(*args):
                            response = chat(*args)
                            raw_completions.append(response)
                            return response
                        started = time.perf_counter()
                        answer, error = None, None
                        try:
                            with patch("app.rag.answer_service.chat", side_effect=capture_chat):
                                answer = answer_question(case["query"], history=case["history"], db=db)
                        except Exception as exc:
                            db.rollback()
                            error = {"type": type(exc).__name__, "message": str(exc)}
                        row = {**case, "seconds": round(time.perf_counter() - started, 3), "answer": answer,
                               "error": error, "raw_completions": raw_completions,
                               "scores": score_case(case, answer, error)}
                        rows.append(row)
                        with (output / "results.jsonl").open("a", encoding="utf-8") as stream:
                            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                        print(f"{split} {index}/{len(cases)} {case['id']} {row['seconds']}s pattern_pass={row['scores']['fact_pattern_pass']} error={bool(error)}", flush=True)
            finally:
                store.close()
                engine.dispose()
        summary = summarize(rows)
        summary["by_category"] = {category: summarize([r for r in rows if r["category"] == category]) for category in sorted({r["category"] for r in rows})}
        write_json(output / "summary.json", summary)
        with (output / "human-review.jsonl").open("w", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps({"id": row["id"], "gold_label_approved": None, "answer_correct": None,
                                         "all_claims_supported": None, "citation_entailment_correct": None,
                                         "abstention_correct": None, "reviewer": None, "notes": ""}) + "\n")
        manifest["status"] = "complete_with_errors" if summary["errors"] else "complete"
        return summary
    finally:
        if manifest["status"] == "running":
            manifest["status"] = "incomplete"
        manifest["completed_cases"] = len(rows)
        manifest["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(output / "manifest.json", manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", required=True, choices=["dev", "test"])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    summary = run(args.split, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
