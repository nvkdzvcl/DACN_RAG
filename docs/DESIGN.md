# Thiết kế hệ thống hỗ trợ khách hàng

Ngày đối chiếu: 15/09/2026. Tài liệu mô tả chức năng đang có trên FastAPI/SQLite, React/Vite, Qdrant embedded và Ollama local. Đây là hồ sơ kỹ thuật để người dùng/GVHD duyệt sau; chưa phải xác nhận nghiệm thu. M3 còn chờ người duyệt chất lượng, M4 mới kiểm chứng chức năng local. API chi tiết tại [API.md](API.md), bằng chứng tại [M4_ACCEPTANCE.md](M4_ACCEPTANCE.md).

## Phân rã chức năng BFD

```mermaid
flowchart TD
    S[Hỗ trợ khách hàng] --> A[Quản lý truy cập]
    S --> K[Kho tri thức]
    S --> C[Hội thoại]
    S --> T[Xử lý yêu cầu]
    S --> E[Đánh giá RAG]
    A --> A1[Cấp tài khoản và đăng nhập nhân viên]
    A --> A2[Tạo và thu hồi phiên khách]
    K --> K1[Tải tài liệu và lập chỉ mục]
    K --> K2[Xem nguồn, lập chỉ mục lại, xóa]
    C --> C1[Lưu tin, truy xuất và trả lời có nguồn]
    C --> C2[Tra cứu đơn theo khách trong hệ thống]
    C --> C3[Khôi phục lịch sử và polling]
    T --> T1[Chuyển hàng chờ và tiếp nhận]
    T --> T2[Trả lời, giải quyết và đóng]
    T --> T3[SLA phản hồi đầu và tiếp nhận lại]
    E --> E1[Đo dev và regression]
    E --> E2[Tổng hợp phiếu người duyệt]
```

LLM tool calling, kênh xã hội thứ hai, push realtime, OCR và SLA giải quyết thuộc phạm vi dự kiến, không nằm trong các nút đã thực hiện.

## Luồng nghiệp vụ mức 0

Sơ đồ phân làn dưới đây diễn tả nhiệm vụ, điều kiện rẽ nhánh và trao đổi giữa khách, hệ thống, nhân viên. Đây là biểu diễn luồng nghiệp vụ bằng Mermaid để rà soát; chưa phải file BPMN 2.0 có thể nhập vào công cụ mô hình hóa hoặc thực thi.

```mermaid
flowchart TD
    subgraph KH[Khách hàng]
        Start([Bắt đầu]) --> Session[Tạo hoặc khôi phục phiên]
        Send[Gửi yêu cầu]
        Read[Đọc phản hồi và nguồn]
        More{Cần hỗ trợ thêm?}
        EndSession[Kết thúc phiên]
    end
    subgraph HT[Hệ thống]
        Valid{Phiên và dữ liệu hợp lệ?}
        Error[Báo lỗi và giữ bản nháp tại trang]
        Save[Lưu tin khách, kiểm tra UUID]
        Route{Trạng thái và yêu cầu}
        Rag[Truy xuất, chọn câu và kiểm định]
        Guard{Trạng thái, tin cuối, nguồn còn đúng?}
        Answer[Trả lời có nguồn hoặc từ chối]
        Queue[Tạo ticket và đưa vào hàng chờ]
        Keep[Lưu tin, không gọi AI]
        Close[Đóng ticket hoạt động và thu hồi phiên]
    end
    subgraph NV[Nhân viên]
        Accept[Tiếp nhận độc quyền]
        Reply[Đọc và trả lời]
        Finish{Kết quả xử lý}
        Resolve[Giải quyết với ghi chú nội bộ]
        Closed[Đóng với ghi chú nội bộ]
    end
    Session --> Send --> Valid
    Valid -->|Không| Error --> Send
    Valid -->|Có| Save --> Route
    Route -->|Đang mở, hỏi chính sách| Rag --> Guard
    Guard -->|Có| Answer --> Read
    Guard -->|Không| Keep
    Route -->|Yêu cầu người thật hoặc nhắn sau giải quyết| Queue
    Route -->|Đang chờ hoặc đã tiếp nhận| Keep
    Route -->|Đã đóng| Error
    Queue --> Accept --> Reply --> Finish
    Keep --> Reply
    Reply --> Read --> More
    More -->|Có| Send
    More -->|Không| EndSession --> Close
    Finish -->|Đã xử lý| Resolve --> More
    Finish -->|Kết thúc hội thoại| Closed --> EndSession
```

Khi hội thoại còn mở và có mã đơn, backend dùng hàm tra cứu theo customer_id của hội thoại. Không tìm thấy đơn thuộc khách sẽ chuyển nhân viên; không gọi LLM để tự quyết định tool. Phiên widget tự tạo khách mới, nên tên giống người mua không cấp quyền đơn có sẵn. Handoff là nhận diện theo quy tắc; tóm tắt ticket là trích tối đa tám tin gần nhất, không phải tóm tắt bằng LLM.

## Use Case và quyền

| ID | Tác nhân | Mục tiêu | Điều kiện và kết quả |
|---|---|---|---|
| UC01 | Admin | Cấp tài khoản | Đã đăng nhập; username duy nhất, mật khẩu ít nhất 12 ký tự |
| UC02 | Admin, agent | Đăng nhập, đăng xuất | Tài khoản hoạt động; phiên nhân viên tối đa 8 giờ |
| UC03 | Khách | Bắt đầu, khôi phục, kết thúc chat | Phiên khách tối đa 24 giờ, chỉ một hội thoại; không xác minh chủ đơn |
| UC04 | Khách | Hỏi chính sách có nguồn | Hội thoại open; tin lưu trước model; thiếu bằng chứng trả từ chối |
| UC05 | Admin | Quản lý tài liệu | Tải/lập chỉ mục lại/xóa; staff được xem tài liệu, đoạn nguồn và hỏi thử |
| UC06 | Khách, staff | Chuyển nhân viên | Ticket hoạt động được tái sử dụng; AI ngừng trả lời |
| UC07 | Admin, agent | Tiếp nhận | Hội thoại đang chờ, chưa có người phụ trách; tranh chấp chỉ một người thắng |
| UC08 | Người phụ trách | Trả lời | Hội thoại assigned và assigned_agent_id khớp người đăng nhập |
| UC09 | Người phụ trách | Giải quyết hoặc đóng | Ghi chú bắt buộc, tin khách cuối không đổi; chốt SLA và ghi người/thời điểm |
| UC10 | Khách | Nhắn sau giải quyết | Giữ lịch sử, tạo ticket mới, bỏ phân công cũ và chờ tiếp nhận lại |
| UC11 | Admin, agent | Xem Inbox và SLA | Thấy tất cả hội thoại nội bộ; chưa có tenant/team isolation |
| UC12 | Người duyệt | Chấm chất lượng | Điền bản sao phiếu; CLI chỉ tính nhãn đã duyệt và câu thực chấm |

UC09 dùng kết quả UC07; UC10 phát sinh UC06 mới và không bật lại UC04. Admin có quyền quản lý nhưng UC08/UC09 vẫn yêu cầu phụ trách. Khách không được gọi API nội bộ, không xem ghi chú ticket hoặc retrieval thô. Giao diện dùng luồng trên, backend kiểm tra quyền độc lập.

## Kiến trúc triển khai local

```mermaid
flowchart LR
    W[Widget iframe và trang chat] --> F[Origin frontend và proxy API]
    I[Inbox và Kho tri thức] --> F
    F --> A[FastAPI một worker]
    A --> S[(SQLite)]
    A --> D[File tài liệu]
    A --> Q[(Qdrant embedded)]
    A --> O[Ollama local]
    O --> L[qwen3:4b]
    O --> E[embeddinggemma:300m]
```

Frontend cần SPA fallback cho /chat và proxy /api cùng origin. Bản Vite build chỉ là tài nguyên tĩnh; backend không tự phục vụ frontend. Cookie SameSite Strict/HttpOnly tách khách và nhân viên, bật Secure ngoài development. Không giữ SQL transaction trong lúc gọi Ollama. Qdrant và giới hạn trong bộ nhớ hiện chỉ hỗ trợ một API worker. Triển khai cloud, sao lưu/khôi phục, tải đồng thời và HTTPS thực tế chưa được nghiệm thu.

## ERD

```mermaid
erDiagram
    users ||--o{ auth_sessions : owns
    users o|--o{ conversations : assigned
    users o|--o{ messages : sends
    users o|--o{ tickets : completes
    customers ||--o{ conversations : starts
    customers ||--o{ orders : owns
    conversations ||--o| widget_sessions : has
    conversations ||--o{ messages : contains
    conversations ||--o{ tickets : tracks
    knowledge_documents ||--o{ document_chunks : contains
    users {
        string id PK
        string username UK
        string role
        boolean active
        string password_hash
    }
    auth_sessions {
        string token_hash PK
        string user_id FK
        int expires_at
    }
    customers {
        string id PK
        string display_name
        string email
    }
    conversations {
        string id PK
        string customer_id FK
        string assigned_agent_id FK
        string last_customer_message_id
        string channel
        string status
        string priority
        datetime created_at
    }
    widget_sessions {
        string token_hash PK
        string conversation_id FK,UK
        int expires_at
    }
    messages {
        string id PK
        string conversation_id FK
        string agent_id FK
        string sender_type
        string external_message_id
        text content
        json citations
        datetime created_at
    }
    tickets {
        string id PK
        string conversation_id FK
        string status
        string priority
        text summary
        datetime created_at
        datetime completed_at
        string completed_by_id FK
        text completion_note
        datetime first_response_at
    }
    orders {
        string id PK
        string customer_id FK
        string status
        string tracking_code
    }
    knowledge_documents {
        string id PK
        string filename
        string status
        string file_hash UK
        string index_version
        string embedding_model
        text error_message
        datetime created_at
    }
    document_chunks {
        string id PK
        string document_id FK
        int chunk_index
        text content
        string source
        int page
        string location
    }
```

ERD phản ánh liên kết khai báo trong SQLAlchemy và migration v4. SQLite hiện chưa bật PRAGMA foreign_keys trong cấu hình kết nối; không coi ký hiệu FK là bằng chứng DB cưỡng chế toàn bộ quan hệ. last_customer_message_id là con trỏ logic, không có FK. UUID tin ngoài không có UNIQUE index; chống trùng trong process_message dựa trên khóa ghi hội thoại và tra UUID theo hội thoại. Các state/priority là chuỗi, chưa có CHECK constraint. schema_migrations là bảng hạ tầng với version làm khóa chính.

Citation là snapshot JSON trong Message, không có FK tới chunk; quote lịch sử được giữ khi tài liệu bị xóa, mở nguồn có thể trả 404/409. Hash file có unique index; vector dùng ID chunk và phiên bản chỉ mục để đối chiếu với SQL. Không đồng nhất file, chunk và lịch sử hội thoại thành một nguồn dữ liệu.

## Trạng thái hội thoại

```mermaid
stateDiagram-v2
    [*] --> open: Tạo hội thoại
    open --> open: Hỏi đáp hoặc tra đơn
    open --> handoff_requested: Yêu cầu nhân viên
    handoff_requested --> assigned: Tiếp nhận thành công
    assigned --> resolved: Người phụ trách giải quyết
    assigned --> closed: Người phụ trách đóng
    resolved --> handoff_requested: Tin khách mới tạo lượt hỗ trợ
    open --> closed: Khách kết thúc phiên
    handoff_requested --> closed: Khách kết thúc phiên
    assigned --> closed: Khách kết thúc phiên
    resolved --> closed: Khách kết thúc phiên
    closed --> [*]: Chỉ xem lịch sử hoặc bắt đầu phiên mới
```

Ticket hoạt động đi từ open sang assigned rồi resolved/closed. Khách kết thúc trước tiếp nhận có thể chuyển trực tiếp open sang closed. Lượt sau tạo ticket mới, không đổi trạng thái ticket cũ. Resolved giữ thông tin phân công cho tới khi tin khách mới bỏ phân công; closed không mở lại. Retry tin cũ sau resolved không làm phát sinh chuyển trạng thái.

## Sequence hỏi đáp và chống AI muộn

```mermaid
sequenceDiagram
    participant K as Khách
    participant A as API
    participant D as SQLite
    participant R as RAG và Ollama
    K->>A: Tin nhắn và UUID
    A->>D: Khóa hội thoại, kiểm tra UUID và trạng thái
    A->>D: Lưu tin khách, cập nhật tin cuối, commit
    A->>R: Truy xuất, chọn câu, kiểm định khi còn open
    Note over A,D: Không giữ transaction trong lúc model chạy
    opt Khách chuyển nhân viên khi model chờ
        K->>A: Handoff
        A->>D: Khóa, tạo ticket, đổi trạng thái, commit
    end
    R-->>A: Kết quả hoặc lỗi provider
    A->>D: Khóa lại, kiểm tra trạng thái, tin cuối và nguồn
    alt Còn open, đúng tin cuối, nguồn hợp lệ
        A->>D: Lưu AI và citation, commit
    else Trạng thái hoặc dữ liệu đã đổi
        A->>D: Không lưu AI muộn
    end
    A-->>K: Snapshot riêng của phiên hoặc lỗi phiên hết hạn
```

## Sequence hoàn tất và tiếp nhận lại

```mermaid
sequenceDiagram
    participant N as Nhân viên
    participant A as API
    participant D as SQLite
    participant K as Khách
    N->>A: finish với ticket và tin khách cuối đã xem
    A->>D: Khóa hội thoại
    alt Cùng ticket, người, trạng thái và ghi chú đã hoàn tất
        A-->>N: 200 duplicate, không ghi thêm
    else Chưa hoàn tất
        A->>D: Kiểm tra phụ trách và tin khách cuối
        alt Có tin mới hoặc sai người phụ trách
            A-->>N: 409, đọc lại trước khi hoàn tất
        else Hợp lệ
            A->>D: Chốt phản hồi, lưu kết quả và ghi chú nội bộ
            A->>D: Đổi trạng thái, thêm thông báo chung, commit
            A-->>N: 200
        end
    end
    K->>A: Tin mới sau resolved
    A->>D: Khóa, lưu tin, tạo ticket, bỏ phân công, commit
    A-->>K: handoff_requested, AI vẫn dừng
    N->>A: Tiếp nhận lượt mới
    A->>D: UPDATE có điều kiện, chỉ một người thắng
```

Tin mới thắng khóa trước finish khiến finish bị 409; finish resolved thắng trước khiến tin mới vào lượt mới. Ghi chú không được đưa vào thông báo công khai. Ticket kết thúc chốt first_response_at, kể cả null; phản hồi lượt sau không biến cancelled thành met. Hạn phản hồi cố định urgent/high/normal/low là 5/15/60/240 phút, 24/7 từ tạo ticket, chưa lưu phiên bản chính sách/deadline.

## Giao diện và phần còn thiếu

Màn hình hiện có gồm đăng nhập, Inbox ba vùng, Kho tri thức, trang chat và widget iframe. Inbox polling mỗi ba giây khi hiển thị, giữ bản nháp/lựa chọn, dừng khi tab ẩn hoặc thao tác ghi. Form hoàn tất chỉ hiện cho người phụ trách có ticket hoạt động; xác nhận giải thích hành vi nhắn tiếp. Widget sau resolved cho gửi, sau closed khóa composer và hướng dẫn bắt đầu phiên mới.

QA giao diện ngày 14/09 đã kiểm tra desktop/mobile 390px; các ảnh trong data/runtime là bằng chứng local, không thuộc gói nguồn bắt buộc. Các mockup do người dùng tạo chưa được duyệt hoặc chỉnh sửa trong đợt này. Cần chốt mẫu thiết kế với GVHD, bổ sung BPMN chuẩn nếu biểu mẫu yêu cầu, nghiệm thu người dùng và đo tải trước tuyên bố hoàn tất toàn bộ M2/M4.
