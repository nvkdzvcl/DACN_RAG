"""Ask 10 fixed fptshop-v1 questions against the application's real knowledge base (not a temporary index).

Used once before and once after replacing the knowledge base, to show the effect of the update.
Reads only the non-secret RAG settings from the env file. The API must be stopped (embedded Qdrant).
Run from the repository root: python evals/fptshop-v1/before_after.py --label before --env-file .env
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CASE_IDS = ["fpt-001", "fpt-007", "fpt-010", "fpt-011", "fpt-015", "fpt-016", "fpt-018", "fpt-020", "fpt-022", "fpt-023"]
SETTINGS = ("DATABASE_URL", "QDRANT_PATH", "LLM_MODEL", "EMBEDDING_MODEL", "RAG_MIN_SCORE", "OLLAMA_HOST")


def load_settings(env_file):
    for line in Path(env_file).read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition("=")
        if key.strip() in SETTINGS and value.strip():
            os.environ.setdefault(key.strip(), value.strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True, choices=["before", "after"])
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()
    output = HERE / "before-after" / f"{args.label}.json"
    if output.exists():
        raise SystemExit(f"{output} already exists; results are never overwritten.")
    load_settings(args.env_file)
    sys.path.insert(0, str(ROOT))
    from app.db.session import SessionLocal
    from app.models.support import KnowledgeDocument
    from app.rag.answer_service import answer_question

    cases = {case["id"]: case for case in map(json.loads, (HERE / "cases.jsonl").read_text(encoding="utf-8").splitlines())}
    rows = []
    with SessionLocal() as db:
        documents = sorted(d.filename for d in db.query(KnowledgeDocument).filter_by(status="indexed"))
        db.commit()
        for case_id in CASE_IDS:
            case = cases[case_id]
            started = time.perf_counter()
            result = answer_question(case["query"], history=case["history"], db=db)
            rows.append({"id": case_id, "query": case["query"], "expected": case["expected_answer"],
                         "answer": result["answer"], "grounded": result["grounded"],
                         "sources": sorted({f"{c['source']} {c.get('location') or ''}".strip() for c in result["citations"]}),
                         "seconds": round(time.perf_counter() - started, 2)})
            print(f"{case_id} grounded={result['grounded']} {rows[-1]['seconds']}s", flush=True)
    from app.rag.vector_store import vector_store
    vector_store.close()
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps({"label": args.label, "run_at_utc": datetime.now(timezone.utc).isoformat(),
                                  "indexed_documents": documents, "results": rows}, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")


if __name__ == "__main__":
    main()
