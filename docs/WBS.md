# CẤU TRÚC PHÂN RÃ CÔNG VIỆC (WORK BREAKDOWN STRUCTURE - WBS)
## DỰ ÁN: MULTIMODAL AGENTIC CHATBOT GIÁM SÁT & QUẢN TRỊ VẬN HÀNH DOANH NGHIỆP
### (Smart Warehouse & Store Operations Agent)

---

## TỔNG QUAN CÁC GÓI CÔNG VIỆC (WORK PACKAGES)

```
                              DỰ ÁN AGENTIC CCTV
                                      │
    ┌──────────────────┬──────────────┴─────┬──────────────────┐
    ▼                  ▼                    ▼                  ▼
[WBS 1: CV ENGINE] [WBS 2: AGENTIC AI]  [WBS 3: BACKEND]  [WBS 4: FRONTEND UI]
 (Thị giác máy)     (Bộ não LangGraph)    (FastAPI API)     (Dual-Mode Web)
```

---

## CHI TIẾT TỪNG GÓI CÔNG VIỆC

### GÓI 1: COMPUTER VISION (CV) ENGINE - "ĐÔI MẮT THỊ GIÁC"
*Mục tiêu: Đọc video theo mốc thời gian, chạy mô hình AI phát hiện vi phạm, xuất ảnh bằng chứng và tính toán số giây cần tua lại.*

- [ ] **WBS 1.1: Quản lý & Trích xuất Video (Video Reader & Frame Sampler)**
  - *Công nghệ*: OpenCV / Decord, Python.
  - *Mô tả*: Viết module mở video từ thư mục lưu trữ, áp dụng kỹ thuật lấy mẫu frame (1 fps) để tăng tốc độ phân tích lên 15–20 lần.
  - *Đầu ra*: Generator trả về từng frame ảnh kèm mốc giây (`second_timestamp`).

- [ ] **WBS 1.2: Mô hình Nhận diện An toàn Bảo hộ (PPE Detector)**
  - *Công nghệ*: Ultralytics YOLOv8 (pretrained PPE / person + helmet/vest).
  - *Mô tả*: Quét người trong frame, kiểm tra xem người có đội mũ cứng bảo hộ / mặc áo phản quang không.
  - *Đầu ra*: Tọa độ bounding box người vi phạm, độ tin cậy (confidence).

- [ ] **WBS 1.3: Mô hình Phát hiện Vật cản Lối đi / Thoát hiểm (Zone Obstruction)**
  - *Công nghệ*: YOLO-World + Supervision PolygonZone + ByteTrack.
  - *Mô tả*: Xác định vật thể (hộp carton, pallet) nằm trong vùng đa giác (lối thoát hiểm) vượt quá thời gian quy định.
  - *Đầu ra*: Thời gian vật thể chiếm chỗ (phút), cảnh báo tắc nghẽn.

- [ ] **WBS 1.4: Mô hình Giám sát Mật độ & Đếm người (Crowd Density)**
  - *Công nghệ*: YOLOv8 `person` + Supervision ZoneCounter.
  - *Mô tả*: Đếm số lượng người theo từng mốc thời gian tại khu vực chỉ định, tìm mốc thời gian đông nhất.
  - *Đầu ra*: Số lượng người lúc cao điểm, cảnh báo quá tải (`overcrowded`).

- [ ] **WBS 1.5: Xuất Bằng chứng & Đóng gói Hàm Tool (Annotator & Tool Packaging)**
  - *Mô tả*: Vẽ khung đỏ/xanh lên frame vi phạm, lưu ảnh vào thư mục `storage/evidence/`.
  - *Đầu ra*: Hàm Python trả về JSON chuẩn: `{ "found": true, "seek_seconds": 1390, "evidence_img": "violation.jpg", "summary": "..." }`.

---

### GÓI 2: AGENTIC AI ORCHESTRATOR - "BỘ NÃO ĐIỀU PHỐI LANGGRAPH"
*Mục tiêu: Tiếp nhận câu hỏi tự nhiên của người dùng, phân tích ý định, kích hoạt đúng Tool CV và tổng hợp báo cáo bằng chứng.*

- [ ] **WBS 2.1: Thiết lập Trạng thái & Bộ nhớ Hội thoại (AgentState)**
  - *Công nghệ*: `langgraph`, `typing.Annotated`, `add_messages`.
  - *Mô tả*: Khởi tạo `AgentState` quản lý danh sách `messages` (hỗ trợ hỏi đáp nối tiếp multi-turn).

- [ ] **WBS 2.2: Đóng gói Tools cho LLM (LangChain `@tool` & `ToolNode`)**
  - *Công nghệ*: `@tool`, `langgraph.prebuilt.ToolNode`, `bind_tools`.
  - *Mô tả*: Gắn decorator `@tool` cho các hàm ở Gói 1, khai báo docstring chi tiết để LLM hiểu khi nào cần gọi tool nào.

- [ ] **WBS 2.3: Xây dựng System Prompt Hướng dẫn Suy luận (Persona & Instructions)**
  - *Mô tả*: Viết prompt đóng vai Quản lý Kho bãi thông minh: tự động phân loại camera/xưởng, bắt buộc trích dẫn bằng chứng ảnh, từ chối câu hỏi ngoài phạm vi.

- [ ] **WBS 2.4: Xây dựng Đồ thị LangGraph (StateGraph Workflow)**
  - *Công nghệ*: `StateGraph`, `should_continue`, `conditional_edges`.
  - *Mô tả*: Nối luồng `agent` $\rightarrow$ `should_continue` (kiểm tra `tool_calls`) $\rightarrow$ `tools` $\rightarrow$ quay lại `agent` $\rightarrow$ `END`.

---

### GÓI 3: BACKEND API GATEWAY & DATA STORAGE
*Mục tiêu: Dựng server trung gian kết nối giữa Web và Agent, quản lý file video camera và cấp phát ảnh bằng chứng.*

- [ ] **WBS 3.1: Khởi tạo FastAPI Server & Cấu hình CORS**
  - *Công nghệ*: FastAPI, Uvicorn, Pydantic Settings.
  - *Đầu ra*: Server chạy tại `http://localhost:8000`, có Swagger UI `/docs`.

- [ ] **WBS 3.2: Dịch vụ Lưu trữ & Bản đồ Camera (Camera Registry)**
  - *Mô tả*: Đọc file `config/cameras.json` chứa danh sách camera, tên xưởng và tọa độ vùng ROI.
  - *API*: `GET /api/v1/cameras` (trả về danh sách camera cho giao diện web hiển thị).

- [ ] **WBS 3.3: Endpoint Xử lý Chatbot (Chat Endpoint)**
  - *API*: `POST /api/v1/chat`.
  - *Mô tả*: Hứng câu hỏi từ web $\rightarrow$ đưa vào LangGraph $\rightarrow$ trả về kết quả gồm: câu trả lời text, link ảnh bằng chứng, video URL và số giây cần tua (`seek_seconds`).

- [ ] **WBS 3.4: Static File Server phục vụ Video & Ảnh bằng chứng**
  - *Mô tả*: Cấu hình FastAPI mount thư mục `storage/cctv_videos` và `storage/evidence` để Web có thể stream video và tải ảnh.

---

### GÓI 4: FRONTEND WEB CHAT - "GIAO DIỆN DUAL-MODE HIỆN ĐẠI"
*Mục tiêu: Xây dựng giao diện web gồm 2 nửa: nửa trái xem camera chuyển trạng thái Live <-> Replay, nửa phải chat với AI.*

- [ ] **WBS 4.1: Khởi tạo Dự án Web & Layout 2 Cột (Split-Screen Layout)**
  - *Công nghệ*: Next.js / React, Tailwind CSS, Lucide Icons.
  - *Mô tả*: Nửa trái chiếm 55% (khung camera), nửa phải chiếm 45% (khung chat).

- [ ] **WBS 4.2: Trình phát Camera Dual-Mode (Nửa màn hình trái)**
  - *Mô tả*:
    - Trạng thái 1: Nhãn `[🔴 LIVE]` (chấm đỏ nhấp nháy, đồng hồ đếm giây OSD).
    - Trạng thái 2: Khi nhận kết quả từ Bot $\rightarrow$ tự động đổi nhãn sang `[⏪ PLAYBACK - 14:23:10]`, tua video đến đúng giây vi phạm (`video.currentTime = seek_seconds`).
    - Nút bấm `[🔴 Quay lại LIVE]` để trở về trạng thái trực tiếp.

- [ ] **WBS 4.3: Thanh chọn Camera & Nạp Video Mới**
  - *Mô tả*: Các tab chọn nhanh: `[Cam 01 - Bốc Dỡ]`, `[Cam 02 - Lối Đi]`, và nút `[+ Tải video mới]`.

- [ ] **WBS 4.4: Khung Chatbot & Evidence Card (Nửa màn hình phải)**
  - *Mô tả*:
    - Danh sách tin nhắn User và Bot.
    - Component **Evidence Card**: Hiển thị ảnh chụp vi phạm có khoanh đỏ, bấm vào để phóng to xem chi tiết.
    - Trạng thái Agent suy nghĩ (Status loading badge).

---

### GÓI 5: TÍCH HỢP HỆ THỐNG & KỊCH BẢN DEMO BÁO CÁO
*Mục tiêu: Kiểm thử toàn bộ hệ thống từ đầu đến cuối và chuẩn bị kịch bản hoàn hảo cho ngày thuyết trình.*

- [ ] **WBS 5.1: Chuẩn bị 3 Video Demo Kịch bản Thực tế**
  - Clip 1: Khu bốc dỡ có người không đội mũ bảo hộ.
  - Clip 2: Lối thoát hiểm có thùng hàng đặt chắn > 15 phút.
  - Clip 3: Khu đóng gói dồn ứ đông người.

- [ ] **WBS 5.2: Kiểm thử Tích hợp End-to-End (Integration Testing)**
  - Gõ thử câu hỏi trên Web $\rightarrow$ Kiểm tra camera tự động nhảy mốc giờ và Bot trả lời đúng ảnh.

- [ ] **WBS 5.3: Soạn Kịch bản Thuyết trình & Đo độ trễ (Dry Run)**
  - Bộ 3 câu hỏi demo chính và 2 câu hỏi bẫy (hỏi nội quy, hỏi ngoài phạm vi).
  - Tối ưu thời gian phản hồi dưới 3–5 giây.
