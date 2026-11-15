"""Language-level safety filters and structural source checks.

Nothing here depends on how a particular question is phrased: these rules look at instruction-like
text, role tags, labelled numbers and the shape of policy clauses only.
"""
import re
import unicodedata

INSTRUCTION = re.compile(
    r"(?i)(?:<\s*/?\s*(?:system|developer|assistant)\b|"
    r"&lt;\s*/?\s*(?:system|developer|assistant)\b|"
    r"\[/?INST\]|<\|(?:im_start|im_end|start_header_id|end_header_id)\|>|"
    r"system\s+(?:update|override)|dữ liệu không đáng tin|"
    r"\b(?:bỏ qua|phớt lờ|ignore|disregard)\b[^.!?\n]{0,160}"
    r"\b(?:chỉ dẫn|hướng dẫn|quy tắc|hệ thống|câu hỏi|instructions?|rules?|system|prompts?|questions?)\b|"
    r"\b(?:trợ lý|chatbot|assistant|AI)\b[^.!?\n]{0,100}\b(?:phải|hãy|must|should)\b|"
    r"bỏ nguồn|(?:luôn|mọi)\s+(?:trả lời|đáp án)|chế độ quản trị)"
)
ROLE_BLOCK = re.compile(
    r"(?is)(?:<\s*(system|developer|assistant)\b[^>]*>.*?(?:<\s*/\s*\1\s*>|$)|"
    r"&lt;\s*(system|developer|assistant)\b.*?&gt;.*?(?:&lt;\s*/\s*\2\s*&gt;|$)|"
    r"\[INST\].*?(?:\[/INST\]|$)|<\|im_start\|>.*?(?:<\|im_end\|>|$)|"
    r"<\|start_header_id\|>.*?(?:<\|eot_id\|>|$))"
)
# A customer asking for a phone/account number must receive one printed next to its label, never generic advice.
CONTACT_NUMBERS = [
    (re.compile(r"số điện thoại|hotline|phone number", re.IGNORECASE),
     re.compile(r"(?:điện thoại|hotline|phone)[^.!?\n\d]{0,60}\d(?:[ .()-]?\d){5,}", re.IGNORECASE)),
    (re.compile(r"số tài khoản|account number", re.IGNORECASE),
     re.compile(r"(?:tài khoản|account)[^.!?\n\d]{0,60}\d(?:[ -]?\d){5,}", re.IGNORECASE)),
]


def nfc(text):
    return unicodedata.normalize("NFC", text)


def has_instruction(text):
    return INSTRUCTION.search(nfc(text)) is not None


def clean_history(history, turns=4, characters=300):
    """Keep the last turns, truncated, dropping any message that carries instructions."""
    return [{"role": m["role"], "content": m["content"][:characters]} for m in (history or [])[-turns:]
            if not has_instruction(m["content"])]


def required_contact_number(question):
    """Pattern the evidence must match when the customer asks for a phone/account number, else None."""
    return next((labelled for request, labelled in CONTACT_NUMBERS if request.search(question)), None)


def unresolved_notices(text):
    # ponytail: two numbered notices with different values and no stated precedence.
    text = nfc(text).casefold()
    notices = set(re.findall(r"(?:thông báo|chính sách|văn bản)\s+([a-z0-9]+)\b", text))
    if len(notices) < 2 or not re.search(
            r"không (?:ghi|có|nêu|xác định)[^.!?]{0,100}(?:hiệu lực|phiên bản|ưu tiên|thay thế)", text):
        return False
    values = {}
    for number, unit in re.findall(r"\b(\d[\d.,]*)\s*(đồng|tháng|ngày|giờ)\b", text):
        values.setdefault(unit, set()).add(number)
    return any(len(numbers) > 1 for numbers in values.values())


def opposing_policy(evidence, texts):
    # ponytail: the same scoped clause appearing both permitted and negated across retrieved sources.
    def clauses(text):
        for sentence in re.split(r"(?<=[.!?])\s+", nfc(text).casefold()):
            sentence = re.sub(r"\[\d+\]\s*", "", sentence).strip().rstrip(".!?")
            if ":" not in sentence or re.search(r"thay thế|ưu tiên|ngoại lệ|trước ngày|từ ngày", sentence):
                continue
            positive = re.sub(r"\bkhông\s+(?=được\b|cho phép\b|bao gồm\b|áp dụng\b)", "", sentence)
            yield " ".join(positive.split()), positive != sentence
    selected = {clause for item in evidence for clause in clauses(item.quote)}
    return any((key, not negative) in selected for text in texts for key, negative in clauses(text))
