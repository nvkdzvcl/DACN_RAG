from app.rag.vector_store import vector_store


def answer_question(query: str, top_k: int = 5) -> dict:
    results = vector_store.search(query, top_k)
    useful = [item for item in results if item["score"] >= 0.18]
    if not useful:
        return {"answer": "Tôi chưa tìm thấy thông tin phù hợp trong tài liệu hiện có.", "grounded": False, "citations": [], "results": results}
    best = useful[0]
    return {
        "answer": f"Theo tài liệu {best['source']}: {best['content']}",
        "grounded": True,
        "citations": [{"chunk_id": item["chunk_id"], "source": item["source"], "score": item["score"]} for item in useful],
        "results": results,
    }
