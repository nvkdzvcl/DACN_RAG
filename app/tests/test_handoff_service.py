import unicodedata
import unittest

from app.services.handoff_service import COMPLAINT_TERMS, classify_message


class HandoffServiceTests(unittest.TestCase):
    def test_canonical_unicode_case_and_whitespace_preserve_handoff(self):
        for term in COMPLAINT_TERMS:
            for form in ('NFC', 'NFD'):
                for space in (' ', '\n', '\t', '\u00a0', '   '):
                    content = unicodedata.normalize(form, term.upper().replace(' ', space))
                    with self.subTest(term=term, form=form, space=space):
                        self.assertEqual(classify_message(f'({content})!'), ('negative', True))

    def test_words_containing_keywords_do_not_trigger_handoff(self):
        for content in ('Cách tải tệp PDF?', 'Tệp tin được lưu ở đâu?', 'Xin chào',
                        'tệpx', 'abcngười thật', 'người thậtx', ''):
            with self.subTest(content=content):
                self.assertEqual(classify_message(content), ('neutral', False))
        self.assertEqual(classify_message('Dịch vụ tệ!'), ('negative', True))

    def test_clear_neutral_context_does_not_request_handoff(self):
        for content in (
                'Cửa hàng hỗ trợ những loại tiền tệ nào?',
                'Điều kiện hoàn tiền theo chính sách cửa hàng là gì?',
                'Cho tôi hỏi chính sách hoàn tiền của cửa hàng như thế nào?',
                'Quy trình hoàn tiền ra sao?', 'Chính sách hoàn tiền?',
                'Không cần gặp nhân viên, chỉ kiểm tra trạng thái DH78216.',
                'Mình chưa muốn nói chuyện với người thật.',
                'Xin chào; tôi không muốn gặp người thật.'):
            for form in ('NFC', 'NFD'):
                with self.subTest(content=content, form=form):
                    variant = unicodedata.normalize(form, content.upper().replace(' ', '\n'))
                    self.assertEqual(classify_message(variant), ('neutral', False))

    def test_neutral_phrase_does_not_hide_another_request_or_complaint(self):
        for content in (
                'Tiền tệ được hỗ trợ ít quá, dịch vụ tệ!',
                'Điều kiện hoàn tiền là gì? Tôi muốn hoàn tiền đơn này.',
                'Chính sách hoàn tiền là gì và hoàn tiền cho tôi ngay.',
                'Chính sách hoàn tiền? Tôi cần gặp nhân viên.',
                'Không cần gặp nhân viên nhưng tôi rất bức xúc.',
                'Tôi không muốn gặp nhân viên, nhưng giờ tôi cần gặp nhân viên.',
                'Không cần người thật. Dịch vụ lừa đảo!',
                'Không phải tôi không muốn gặp nhân viên.',
                'Tôi không cần hỏi chính sách, hoàn tiền ngay.',
                'Chính sách hoàn tiền cho tôi ngay là gì?',
                'Tôi muốn hoàn tiền theo chính sách cửa hàng.',
                'Hoàn tiền', 'Gặp nhân viên', 'Người thật'):
            with self.subTest(content=content):
                self.assertEqual(classify_message(content), ('negative', True))


if __name__ == '__main__':
    unittest.main()
