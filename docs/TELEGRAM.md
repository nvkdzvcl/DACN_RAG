# Telegram: nhận và gửi qua polling

Ngày kiểm chứng local: 01/10/2026. Adapter và giao diện đã có; chưa kiểm chứng bot/tài khoản Telegram thật, chưa nghiệm thu M6. Mặc định tắt, không thay `.env` của người dùng.

## Cấu hình bot thử nghiệm

1. Tạo bot thử nghiệm riêng qua BotFather chính thức trong Telegram. Giữ token trong `.env` local; không gửi token vào chat, ảnh chụp, log hoặc Git.
2. Thêm `TELEGRAM_ENABLED=true` và `TELEGRAM_BOT_TOKEN=<token của bot>` vào `.env` hiện có. Không ghi đè các cấu hình DB/model.
3. Dừng tiến trình API cũ rồi chạy `python -m uvicorn app.main:app --env-file .env` từ root repo. Chỉ chạy một API worker và một tiến trình dùng bot này. Không dùng `--workers` nhiều hơn 1.
4. Mở Cài đặt để xem trạng thái Telegram. Worker kiểm tra `getMe` và `getWebhookInfo`, sau đó gọi `getUpdates`. Không cần URL công khai. Nếu bot đang có webhook, worker dừng với `telegram_webhook_active`; hệ thống không tự xóa webhook.
5. Nhắn riêng `/start` cho bot, hỏi chính sách đã có trong Kho tri thức, rồi `/human`. Tiếp nhận trong Inbox và trả lời; đối chiếu tin thật trên Telegram. Sau khi đóng hội thoại, tin khách tiếp theo phải tạo hội thoại mới.

Khởi động lại API sau khi đổi cấu hình. Tắt bằng `TELEGRAM_ENABLED=false` và khởi động lại. `connected` chỉ xác nhận vòng nhận gần nhất thành công, không chứng minh mọi tin đã gửi hoặc khách đã đọc. Khi kiểm tra `getMe`/`getWebhookInfo`, lỗi mạng hoặc HTTP 5xx tự thử lại sau 5 giây; trạng thái giữ `error` trong lúc chờ. Dừng API ngắt được thời gian chờ. Token sai, bot không hợp lệ, webhook đang hoạt động và lỗi khởi động khác cần xử lý rồi khởi động lại; chưa tự retry HTTP 429 theo Retry-After. Chỉ phục hồi hàng gửi sau khi xác minh bot và webhook thành công. Lỗi trong vòng polling vẫn thử lại sau 5 giây. Token không trả về API Cài đặt.

## Phạm vi xử lý

- Chỉ nhận tin mới trong chat riêng giữa người dùng và bot; bỏ qua nhóm, bot gửi tin và chỉnh sửa tin. `/start` trả hướng dẫn, `/human` chuyển nhân viên. Nội dung không phải văn bản hoặc quá 4000 ký tự được chuyển nhân viên; chưa tải/xử lý file Telegram.
- Danh tính gắn với bot ID và user/chat ID do Telegram cung cấp. Không gộp với khách widget hoặc khách cùng tên/email. Tên Telegram là tên hiển thị, không chứng minh chủ đơn; mã truy cập đơn widget không áp dụng cho Telegram.
- Tin khách được lưu bền cùng con trỏ update trước khi lần polling sau xác nhận đã nhận. Khóa `bot_id:update_id` chặn nhận trùng. Sau gián đoạn, không gọi lại AI nếu tin khách đã lưu mà kết quả chưa rõ; chuyển nhân viên để xử lý.
- Dùng chung RAG, chọn tool và handoff. Tin AI đang chờ bị bỏ nếu hội thoại không còn open, có tin khách mới hơn hoặc còn update khách chưa xử lý. Tin đã gửi lên mạng không thể thu hồi bằng kiểm tra này.
- Thông báo chuyển nhân viên được lưu cùng transaction với trạng thái và ticket, kể cả handoff do lỗi gửi/phục hồi. Worker dừng sau commit không làm mất thông báo; rollback hủy cả ba, nhận lại update hoặc khách nhắn thêm khi đang chờ không tạo thông báo trùng. Yêu cầu mới sau giải quyết tạo thông báo lượt mới. Tin này vẫn tuân thủ hàng chờ gửi; lỗi trước đó cần người phụ trách xử lý trước. Không tự bù thông báo đã thiếu trong dữ liệu cũ.
- Chỉ gửi nội dung trả lời và tối đa ba nhãn nguồn/vị trí; không gửi `tool_trace`, ghi chú nội bộ hoặc bản ghi ticket. Nội dung dài lấy tối đa 4000 ký tự, thêm nguồn nếu tổng không quá 4096. Khi bật bot, nội dung này được truyền tới Telegram.

## Trạng thái gửi và xử lý lỗi

| Trạng thái | Ý nghĩa |
|---|---|
| pending | Đã lưu, chờ worker gửi; chưa chắc đã rời máy |
| sending | Đang gửi; chưa có kết quả cuối |
| sent | Telegram trả thành công và message ID; không phải xác nhận khách đọc |
| failed | Lỗi gửi đã biết, ví dụ Telegram trả HTTP 403 |
| uncertain | Timeout, phản hồi không hợp lệ hoặc gián đoạn khi đang gửi; Telegram có thể đã nhận |
| skipped | Nhân viên bỏ qua hoặc AI đã lỗi thời; giữ lịch sử, không gửi nữa |

Lỗi/không rõ kết quả chặn các tin sau tới cùng người dùng trên cùng bot, kể cả hội thoại mới. Hội thoại đang open được chuyển sang hàng chờ nhân viên. Người phụ trách chọn **Gửi lại Telegram** hoặc **Bỏ qua gửi** ngay dưới tin trong Inbox. Tin uncertain cần đánh dấu xác nhận nguy cơ trùng trước khi gửi lại. Bỏ qua không xóa lịch sử hoặc thu hồi tin có thể đã tới Telegram. Quyền xử lý còn áp dụng cho người phụ trách hội thoại đã đóng; nếu tin cũ chặn hội thoại mới, mở hội thoại cũ để xử lý.

Không tự thử lại sendMessage sau lỗi mạng. Khi khởi động lại, sending chuyển uncertain; tránh mặc định gửi trùng. API gửi tin nhân viên nhận UUID, giữ UUID khi thử lại cùng nội dung trong cùng trang. Tải lại trang có thể mất UUID/bản nháp; đọc lịch sử trước khi gửi lại bằng yêu cầu mới.

SLA phản hồi đầu của Telegram tính lúc Telegram xác nhận gửi thành công (`sent_at`), không tính lúc lưu tin nhân viên vào DB. Ticket đã kết thúc giữ snapshot SLA; tin gửi thành công muộn không sửa SLA lịch sử. Website vẫn tính theo thời điểm lưu tin nhân viên.

## Kiểm chứng và giới hạn

Ngày 01/10/2026 sửa worker dừng hẳn khi mất mạng ở bước khởi động. Hai test mới tái hiện trước sửa; 23 test Telegram đạt sau sửa, gồm lỗi mạng rồi 503 rồi kết nối thành công, chưa chạm DB trước xác minh, dừng khi đang chờ và không tự retry lỗi cấu hình. Model/transport giả lập; chưa phải nghiệm thu bot thật. Cơ chế thử lại chỉ áp dụng probe đọc, không áp dụng sendMessage có kết quả chưa rõ.

Ngày 01/10/2026 bổ sung xử lý lỗi giao thức HTTP (`IncompleteRead`, `BadStatusLine`): nếu đang gửi thì ghi `uncertain` ngay, không để kẹt `sending` đến khi khởi động lại. Không lưu lỗi transport thô/token; không tự gửi lại, khách khác vẫn tiếp tục gửi theo hàng chờ riêng. Lỗi nhận được chuyển thành TelegramError để dùng nhánh phục hồi polling hiện có. Test tái hiện trước sửa; 21 test Telegram đạt sau sửa với transport/model giả lập, chưa kiểm chứng bot thật.

Ngày 01/10/2026 sửa hàng chờ bị phụ thuộc vào lần nhận tin tiếp theo. Sau khi khởi động/xác minh bot thành công, lỗi `getUpdates` hoặc danh sách update sai vẫn cho xử lý một update đã commit mỗi vòng và thử gửi theo quy tắc hiện có. Trạng thái kết nối giữ `error`, chờ 5 giây sau vòng lỗi; chỉ lần nhận hợp lệ mới báo `connected`. Không tăng con trỏ khi response sai, không tự gửi lại tin `failed/uncertain`. Lỗi DB hoặc cấu hình khởi động vẫn dừng vòng xử lý tương ứng; chưa tách worker nhận/xử lý/gửi.

Test mới tái hiện lỗi trước sửa; 20 test Telegram đạt sau sửa, gồm backlog pending/processing, mất mạng, response sai, giữ con trỏ và không trùng tin/ticket. Model và transport giả lập, chưa là bằng chứng bot thật.

`python -m unittest app.tests.test_telegram -v` kiểm tra danh tính, nhận trùng, con trỏ bền, phục hồi sau gián đoạn, tranh chấp đóng, AI lỗi thời, gửi thất bại/không rõ, quyền gửi lại/bỏ qua, UUID, SLA, webhook đang tồn tại và che token trong lỗi. Transport Telegram và model được mock trong nhóm test này; không dùng kết quả giả lập để tuyên bố kết nối thật.

Một luồng polling xử lý tuần tự trong một API worker. Lời gọi model làm chậm nhận tin mới, `/human` và phản hồi nhân viên; chưa có giới hạn backlog, điều phối nhiều worker, webhook, retry tự động theo Retry-After hoặc kiểm thử tải. Cần worker có lease/queue trước khi mở rộng. SQLite chưa bật cưỡng chế khóa ngoại; dữ liệu cũ giữ nguyên qua migration v7.

Trước nghiệm thu M6 còn cần bot thật, gửi/nhận từ hai người dùng độc lập, RAG có nguồn, handoff, nhân viên trả lời, khởi động lại và thử lỗi mạng có kiểm soát. Ghi rõ thời điểm và bằng chứng; không chụp token hoặc dữ liệu khách thật.

QA trình duyệt trên DB/vector riêng xác nhận cảnh báo nguy cơ trùng, gửi lại chuyển pending, bỏ qua giữ lịch sử, phản hồi nhân viên chờ gửi khi bot tắt và Cài đặt báo chưa kết nối. Desktop và khung mobile 390 pixel đã kiểm tra trực quan, không tràn ngang; không gửi tin ra Telegram thật.
