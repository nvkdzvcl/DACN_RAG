COMPLAINT_TERMS = ("khiếu nại", "bức xúc", "tệ", "lừa đảo", "hoàn tiền", "gặp nhân viên", "người thật")

def classify_message(content: str) -> tuple[str, bool]:
    normalized = content.casefold()
    matched = [term for term in COMPLAINT_TERMS if term in normalized]
    if matched:
        return "negative", True
    return "neutral", False
