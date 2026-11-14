# Nguồn và thay đổi Kho tri thức: chính sách FPT Shop (15/11/2026)

## Nguyên tắc

- Nội dung lấy từ trang chính thức fptshop.com.vn, **diễn đạt lại bằng lời của nhóm**, giữ dữ kiện (thời hạn, phí, điều kiện), không chép nguyên văn. Lý do: Quy chế hoạt động của FPT Shop (fptshop.com.vn/tos) giữ bản quyền nội dung website và cấm sao chép, phổ biến khi chưa được đồng ý, còn repo này công khai.
- Mỗi file mở đầu bằng dòng nguồn: URL, ngày hiệu lực, ngày truy cập và lưu ý "không phải văn bản chính thức của FPT Shop".
- Định dạng theo cách pipeline đọc: mỗi dòng là một quy định tự đủ nghĩa, mở đầu bằng tiền tố phạm vi `**Nhóm – trường hợp:**`, điều kiện và ngoại lệ nằm cùng dòng. Kiểm tra máy: dòng dài nhất 79 từ (một chunk tối đa 180 từ), không dòng nào bị bộ lọc chỉ dẫn chặn.
- Chỉ dùng để demo đồ án; chatbot không phải kênh chính thức của FPT Shop.

## Danh sách nguồn

Truy cập ngày 15/11/2026.

| File trong `knowledge/fptshop/` | Trang nguồn | Hiệu lực ghi trên nguồn |
|---|---|---|
| `doi-tra.md` | /ho-tro/chinh-sach-doi-san-pham | 01/7/2024 |
| `bao-hanh.md` | /ho-tro/chinh-sach-bao-hanh | 01/7/2024 |
| `kiem-hang.md` | /ho-tro/chinh-sach-kiem-hang-khui-hop-san-pham | 01/7/2024 |
| `giao-hang.md` | /ho-tro/chinh-sach-giao-hang; /ho-tro/cac-dieu-kien-hoac-han-che-trong-viec-cung-cap-hang-hoa-dich-vu | 01/7/2024 |
| `thanh-toan.md` | /ho-tro/chinh-sach-thanh-toan; /ho-tro/chinh-sach-gia | 01/7/2024 |
| `tra-gop.md` | /ho-tro/chinh-sach-tra-gop | 01/7/2024 |
| `khach-hang-than-thiet.md` | /ho-tro/chinh-sach-chuong-trinh-khach-hang-than-thiet-tai-fpt-shop | 05/01/2024; quy đổi điểm từ 01/11/2024 |
| `bao-mat.md` | /ho-tro/chinh-sach-thu-thap-va-xu-ly-du-lieu-ca-nhan (chỉ các phần khách hay hỏi) | 01/01/2026 |
| `khieu-nai.md` | /ho-tro/quy-trinh-giai-quyet-phan-anh-yeu-cau-khieu-nai-cua-nguoi-tieu-dung | không ghi |
| `ho-tro-ky-thuat.md` | /ho-tro/quy-dinh-ho-tro-ky-thuat-va-sao-luu-du-lieu | không ghi |
| `thu-cu-doi-moi.md` | /ctkm/thu-cu-doi-moi (trang khuyến mãi, không phải văn bản chính sách) | không ghi |
| `lien-he-va-mua-hang.md` | chân trang fptshop.com.vn; /ho-tro/huong-dan-mua-hang | không ghi |

Tất cả URL có tiền tố `https://fptshop.com.vn`.

## Bảng thay đổi so với Kho tri thức hiện tại

Kho tri thức trước cập nhật chỉ có một tài liệu giả lập: `chinh-sach-mau-binh-giu-nhiet-BT20.md` (khoảng 1.560 từ, "Cửa hàng mẫu RAG").

| Thao tác | Nội dung | Lý do |
|---|---|---|
| **Xóa** | Toàn bộ `chinh-sach-mau-binh-giu-nhiet-BT20.md`: sản phẩm BT20, đặt hàng/hủy đơn, giao hàng, đổi trả 7 ngày, bảo hành 12 tháng, hoàn tiền, quyền tra cứu đơn | Chính sách giả lập; để lẫn với chính sách mới sẽ bị coi là mâu thuẫn (ví dụ đổi trả 7 ngày so với 30 ngày) và hệ thống sẽ từ chối trả lời |
| **Thêm** | 12 file `knowledge/fptshop/*.md`, 201 dòng quy định | Thay bằng chính sách có nguồn |
| **Sửa** | Không có, vì thay toàn bộ | |

Bộ eval cũ (`evals/rag`, `evals/heldout-v1`, ...) dùng corpus riêng trong từng thư mục, không phụ thuộc Kho tri thức runtime, nên không bị ảnh hưởng.

## Nội dung không đưa vào

| Nội dung nguồn | Lý do |
|---|---|
| Chính sách mạng di động và gói cước FPT | Ngoài phạm vi cửa hàng bán lẻ của đề tài |
| Chính sách ưu tiên hiển thị, đại lý ủy quyền Apple, giới thiệu máy đổi trả | Không phải câu hỏi chính sách thường gặp |
| Phần chương trình tích điểm tại Long Châu | Không thuộc FPT Shop |
| Chi tiết cookie, chuyển dữ liệu ra nước ngoài, định nghĩa pháp lý trong chính sách bảo mật | Quá dài và pháp lý; khách ít hỏi |
| Mức trợ giá thu cũ "đến 5 triệu trong tháng 11" | Ưu đãi theo đợt, nhanh lỗi thời |
| Ảnh minh họa lỗi ngoại quan, bảng giá sửa chữa | Không trích xuất được dạng chữ |

## Điểm cần lưu ý khi duyệt

1. **Hai tổng đài khác nhau, không mâu thuẫn:** 1800 6601 là tư vấn mua hàng (nhánh 1), hỗ trợ kỹ thuật (nhánh 2), đổi trả và hoàn tiền, khách hàng thân thiết; 1800 6616 là góp ý, khiếu nại, chăm sóc khách hàng và dữ liệu cá nhân (nhánh 3). Câu hỏi chung "số tổng đài là gì" có thể khiến chatbot hỏi lại.
2. **Hóa đơn VAT:** nguồn không có trang riêng; chỉ có hai dữ kiện (giá đã gồm thuế; phí 10% khi trả hàng đơn xuất hóa đơn công ty không có biên bản điều chỉnh). Câu hỏi về thủ tục xuất hóa đơn công ty sẽ bị từ chối là đúng.
3. **Đổi 1-1 điện máy tại nhà:** áp dụng cho Casper (tủ lạnh, máy giặt, máy sấy, máy lạnh) và máy lạnh Midea; các hãng khác chỉ bảo hành tại nhà.
4. **Khi FPT Shop đổi chính sách:** cần cập nhật file, đổi ngày truy cập và lập chỉ mục lại; chatbot không tự biết chính sách đã thay đổi.
