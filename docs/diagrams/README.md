# Danh mục sơ đồ

Thư mục tập hợp sơ đồ và bản phác thảo giao diện để tìm theo loại, bổ sung ngày 16/10/2026. Các tệp được sao chép từ hồ sơ tuần 04, tuần 05 và tài liệu thiết kế; không thay đổi nội dung mô hình.

| Nhóm | Nội dung | Định dạng |
|---|---|---|
| [bfd](bfd/) | BFD tổng quan tuần 04; giữ thêm nguồn Mermaid cũ để đối chiếu | SVG, PNG, MMD |
| [bpmn](bpmn/) | Bốn quy trình nghiệp vụ có phân làn, nhánh và ngoại lệ | BPMN 2.0, SVG, PNG |
| [use-case](use-case/) | Use Case toàn hệ thống và sáu phân hệ | PlantUML, SVG, PNG |
| [sequence](sequence/) | Năm Sequence tuần 05; hai nguồn Mermaid cũ để đối chiếu | PlantUML, SVG, PNG, MMD |
| [erd](erd/) | ERD trong tài liệu thiết kế cũ | MMD |
| [architecture](architecture/) | Kiến trúc triển khai local | MMD |
| [state-machine](state-machine/) | Máy trạng thái hội thoại | MMD |
| [flowchart](flowchart/) | Luồng nghiệp vụ phân làn cũ, không phải BPMN 2.0 | MMD |
| [ui-mockup](ui-mockup/) | Các bản phác thảo giao diện đang có | SVG, PNG |

## BFD và BPMN

- [BFD tổng quan](bfd/BFD.svg).
- [BPMN01](bpmn/BPMN01.svg): tiếp nhận hỏi chính sách và chuyển giao.
- [BPMN02](bpmn/BPMN02.svg): xác minh và tra cứu đơn hàng.
- [BPMN03](bpmn/BPMN03.svg): nhân viên xử lý ticket và giao phản hồi.
- [BPMN04](bpmn/BPMN04.svg): quản lý và lập chỉ mục tri thức.

Mỗi BPMN có tệp `.bpmn` chỉnh sửa được và ảnh PNG cùng tên. BFD hiện có SVG/PNG; nguồn dựng nằm trong [công cụ tuần 04](../week04/build.py).

## Use Case

- [UC_ALL](use-case/UC_ALL.svg): toàn hệ thống.
- [UC_M01](use-case/UC_M01.svg): Unified Inbox và ticket.
- [UC_M02](use-case/UC_M02.svg): kho tri thức.
- [UC_M03](use-case/UC_M03.svg): hỏi đáp và tra đơn.
- [UC_M04](use-case/UC_M04.svg): chuyển giao nhân viên.
- [UC_S01](use-case/UC_S01.svg): truy cập và danh tính.
- [UC_S02](use-case/UC_S02.svg): quản lý, đánh giá và vận hành.

Mỗi hình có ảnh PNG và tệp PlantUML `.puml` cùng tên.

## Sequence Diagram

- [SD01](sequence/SD01.svg): hỏi chính sách và kiểm tra AI lỗi thời.
- [SD02](sequence/SD02.svg): cấp quyền và tra đơn chỉ đọc.
- [SD03](sequence/SD03.svg): tiếp nhận, phản hồi và hoàn tất ticket.
- [SD04](sequence/SD04.svg): Telegram nhận, giao và phục hồi tin.
- [SD05](sequence/SD05.svg): lập chỉ mục nguồn và xử lý lỗi liên kho.

Mỗi hình có ảnh PNG và tệp PlantUML `.puml` cùng tên. Hai tệp có hậu tố `-legacy.mmd` giữ mô hình Mermaid cũ; dùng bộ SD01–SD05 cho hồ sơ tuần 05.

## Các mô hình bổ sung

- [Kiến trúc local](architecture/local-architecture.mmd).
- [Trạng thái hội thoại](state-machine/conversation-states.mmd).
- [ERD cũ](erd/ERD-legacy.mmd).
- [Luồng nghiệp vụ cũ](flowchart/business-flow-legacy.mmd).
- Mockup: [SVG](ui-mockup/ui-mockup.svg), [bản v2](ui-mockup/ui-mockup-v2.png), [bản tham khảo Figma](ui-mockup/ui-mockup-figma.png).

Nguồn Mermaid được trích nguyên từ [DESIGN.md](../DESIGN.md), giữ nguyên mức độ hoàn thiện của bản gốc. ERD chưa cập nhật đủ schema hiện tại; việc tập hợp này không thay bước hoàn thiện ERD, từ điển dữ liệu hay duyệt thiết kế. Các mockup cũng cần đối chiếu với giao diện hiện tại. Tệp mang tên Figma là ảnh PNG, không phải dự án Figma có thể chỉnh sửa.

## Cập nhật và kiểm tra

Nguồn chính vẫn ở [tuần 04](../week04/README.md), [tuần 05](../week05/README.md), [DESIGN.md](../DESIGN.md) và các tệp mockup tại thư mục `docs`. Giữ đường dẫn gốc để hình trong báo cáo và công cụ dựng hoạt động bình thường.

Sau khi sửa hoặc dựng lại nguồn chính, cập nhật các bản sao bằng Python, không cần thư viện ngoài:

```powershell
python docs/diagrams/sync.py
python docs/diagrams/sync.py --check
```

Lệnh `--check` chỉ đọc: kiểm tra đủ 60 tệp trong chín nhóm, nội dung khớp nguồn và các liên kết trong danh mục hợp lệ. Khi cần chỉnh mô hình, sửa nguồn chính rồi đồng bộ; không sửa riêng bản sao trong thư mục này.
