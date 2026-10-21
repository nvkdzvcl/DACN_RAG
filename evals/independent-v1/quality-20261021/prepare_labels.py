from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from app.evaluate_rag import load_cases


def main():
    root = Path.cwd()
    source = root / 'evals/independent-v1/customer-v1'
    destination = root / 'evals/independent-v1/customer-v2'
    destination.mkdir(exist_ok=False)
    changes = {
        'customer-024': {'should_answer': True,
                         'required_patterns': ['không cam kết', 'khôi phục', 'chưa sao lưu']},
        'customer-048': {'should_answer': True,
                         'required_patterns': ['chưa có xác nhận', 'không chứng minh', 'thành công']},
        'customer-051': {'required_patterns': ['không phải cung cấp', 'đặt lịch']},
    }
    reasons = {
        'customer-024': 'Câu hỏi có đáp án phủ định trực tiếp trong nguồn: không cam kết khôi phục dữ liệu chưa sao lưu. Không đồng nhất thiếu dữ liệu cá nhân với không được trả lời phủ định theo chính sách.',
        'customer-048': 'Nguồn nói rõ hồ sơ chưa xác nhận hoàn tiền. Trả lời phủ định trạng thái thành công theo chính văn là hợp lệ; phải bỏ chỉ dẫn giả và không tuyên bố đã hoàn.',
        'customer-051': 'Câu hỏi tập trung giấy chứng nhận khi nhận ở sảnh trệt; yêu cầu lặp lại tầng trệt trong regex là không cần thiết. Vẫn yêu cầu không phải cung cấp giấy tờ và đăng ký khi đặt lịch.',
    }
    log = []
    for partition in ('main', 'reserve'):
        target = destination / partition
        target.mkdir()
        shutil.copytree(source / partition / 'corpus', target / 'corpus')
        rows = load_cases(source / partition / 'cases.jsonl')
        for row in rows:
            if row['id'] in changes:
                update = changes[row['id']]
                log.append({'id': row['id'], 'partition': partition,
                            'before': {key: row[key] for key in update}, 'after': update,
                            'reason': reasons[row['id']], 'evidence': row['evidence'],
                            'proposal_author': 'AI assistant', 'human_reviewer': None, 'human_approved': False})
                row.update(update)
        (target / 'cases.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
        assert len(load_cases(target / 'cases.jsonl')) == len(rows)
    manifest = {'version': 'customer-v2', 'parent_version': 'customer-v1',
                'created_at_utc': datetime.now(timezone.utc).isoformat(),
                'status': 'ai_proposed_label_revision_pending_human_approval',
                'human_approved': False, 'corpus_changed': False, 'questions_changed': False,
                'changes': log,
                'sha256': {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in sorted(destination.rglob('*')) if path.is_file()}}
    (destination / 'dataset-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = ['# customer-v2 — đề xuất sửa ba nhãn', '',
             '**AI đề xuất sau khi đã xem kết quả v1; chưa có người duyệt độc lập.** Không gọi v2 là tập kín mới hoặc lấy thay điểm lịch sử v1.', '',
             'Giữ nguyên 60 câu, lịch sử và toàn bộ corpus. Chỉ sửa các trường trong bảng; không thay kỳ vọng ngữ nghĩa để hợp thức hóa câu trả lời sai.', '',
             '| Ca | Trước | Sau | Lý do |', '|---|---|---|---|']
    for item in log:
        lines.append(f"| {item['id']} | {json.dumps(item['before'], ensure_ascii=False)} | {json.dumps(item['after'], ensure_ascii=False)} | {item['reason']} |")
    lines += ['', 'Chạy kiểm tra cấu trúc và phạm vi thay đổi:', '',
              '```powershell', 'python -m evals.independent-v1.quality-20261021.validate_labels', '```', '',
              'Chấm lại cùng đáp án v1 theo v2 chỉ đo tác động sửa nhãn, không phải một lượt Ollama mới. Báo cáo sẽ tách rõ điểm theo v1/v2 và giữ cả trước/sau runtime trên cùng v2. Phiếu người duyệt không được tự điền.']
    (destination / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('Created customer-v2; three AI-proposed label revisions, no question/corpus changes.')


if __name__ == '__main__':
    main()
