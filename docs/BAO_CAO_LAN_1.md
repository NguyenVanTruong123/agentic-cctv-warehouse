# BÁO CÁO TIẾN ĐỘ THỰC TẬP / NGHIÊN CỨU KHOA HỌC (LẦN 1 - TUẦN 7)

**TÊN ĐỀ TÀI:**  
# MULTIMODAL AGENTIC CHATBOT GIÁM SÁT & QUẢN TRỊ VẬN HÀNH DOANH NGHIỆP
**(Smart Warehouse & Store Operations Agent)**

---

## PHẦN 1: CƠ SỞ LÝ THUYẾT VỀ CHỦ ĐỀ NGHIÊN CỨU (HƯỚNG NGHIÊN CỨU)

### 1.1. Đặt vấn đề và Bài toán thực tiễn
Trong kỷ nguyên công nghiệp 4.0 và chuỗi cung ứng hiện đại, các doanh nghiệp vận hành kho bãi (Warehouse), trung tâm logistics và sàn sản xuất đều trang bị hệ thống camera an ninh (CCTV/NVR) hoạt động 24/7. Tuy nhiên, phương thức quản trị truyền thống đang bộc lộ những hạn chế nghiêm trọng:
- **Giám sát thụ động:** Đội ngũ an ninh không thể quan sát cùng lúc hàng chục màn hình camera liên tục nhiều giờ liền, dẫn đến bỏ sót các sự cố vi phạm an toàn lao động (EHS) như công nhân đi vào làn xe nâng nguy hiểm, không trang bị đồ bảo hộ (PPE), hoặc vật cản chắn lối thoát hiểm.
- **Rà soát dữ liệu thủ công, chậm trễ:** Khi xảy ra sự cố, người quản lý phải mất hàng giờ tua lại băng ghi hình (playback) một cách mò mẫm.
- **Khoảng cách giữa Chatbot AI và Dữ liệu Thị giác:** Các chatbot AI phổ biến hiện nay (RAG truyền thống) chỉ xử lý được văn bản hoặc tài liệu tĩnh, hoàn toàn "mù" trước luồng dữ liệu video thị giác thời gian thực tại hiện trường.

👉 **Bài toán đặt ra:** Xây dựng một **Tác nhân AI Đa phương thức (Multimodal Agentic AI)** có khả năng tự động phân tích luồng video camera an ninh, chủ động phát hiện và lập chỉ mục các sự kiện vi phạm an toàn, đồng thời đóng vai trò một "Trợ lý Điều hành Thông minh" cho phép cấp quản lý truy vấn thông tin bằng ngôn ngữ tự nhiên và lập tức trích xuất hình ảnh/khoảnh khắc video làm bằng chứng.

---

### 1.2. Các Khái niệm Cốt lõi
1. **Multimodal AI (Trí tuệ nhân tạo Đa phương thức):** Là hệ thống AI có khả năng tiếp nhận, xử lý và liên kết đồng thời nhiều loại dữ liệu khác nhau (Văn bản - Ngôn ngữ tự nhiên và Thị giác - Video/Hình ảnh camera).
2. **Agentic AI (AI Tác nhân / Agent):** Khác với mô hình ngôn ngữ thông thường (chỉ hỏi-đáp văn bản tĩnh), AI Agent có "não bộ điều phối" (Orchestrator), sở hữu khả năng tự lên kế hoạch (Planning), gọi các công cụ chuyên biệt (Tool Calling) để tương tác với thế giới bên ngoài (mô hình Computer Vision, cơ sở dữ liệu), và kiểm chứng lại kết quả (Reflection).
3. **CCTV Video Analytics (Phân tích Video Camera Giám sát):** Việc áp dụng các thuật toán học sâu (Deep Learning) vào luồng video từ đầu ghi camera (NVR/RTSP) để tự động nhận diện người, phương tiện, hành vi và các điều kiện bất thường.
4. **Vùng Nguy hiểm Kỹ thuật số (Virtual Danger Zone / Polygon ROI):** Định nghĩa các vùng đa giác ảo trên mặt phẳng tọa độ của khung hình camera tương ứng với khu vực cấm (Làn xe nâng, vùng gần máy cắt) nhằm kích hoạt cảnh báo xâm nhập (Intrusion Detection).

---

### 1.3. Lịch sử Phát triển và Xu hướng Công nghệ
- **Giai đoạn 1 (Truyền thống - Rule-based CV):** Sử dụng các kỹ thuật xử lý ảnh cổ điển (Background Subtraction, Optical Flow, bộ lọc màu). Nhược điểm: Cực kỳ nhạy cảm với ánh sáng, góc quay và tỷ lệ báo động giả rất cao.
- **Giai đoạn 2 (Học sâu - Deep Learning Object Detection 2015–2022):** Sự bùng nổ của các mạng nơ-ron tích chập như Faster R-CNN, SSD, và đặc biệt là dòng họ YOLO (You Only Look Once). Máy tính đã nhận diện được con người, vật thể với độ chính xác và tốc độ vượt trội (Real-time). Tuy nhiên, các hệ thống này hoạt động độc lập, chỉ hiển thị hộp bounding box mà thiếu khả năng hiểu ngữ cảnh tổng thể và tương tác với con người.
- **Giai đoạn 3 (Hiện tại - Multimodal Agentic AI 2023–nay):** Sự kết hợp đột phá giữa Mô hình Ngôn ngữ Lớn (LLMs) và Thị giác máy tính. LLM đóng vai trò trung tâm chỉ huy điều phối các công cụ thị giác máy, biến hệ thống giám sát từ một chiếc "máy quay ghi hình câm lặng" thành một "Người Trợ lý Điều hành Ảo" có thể đối thoại, suy luận logic và giải trình bằng chứng.

---

### 1.4. Nguyên lý Hoạt động Tổng thể của Hệ thống
Hệ thống vận hành theo nguyên lý **Hướng sự kiện (Event-Driven Pre-indexing Pipeline)** kết hợp **Truy vấn Tác nhân (Agentic Querying)**:
1. **Pha Thu nạp & Giám sát Tự động (Video Ingestion):** Luồng video camera được định kỳ phân tích (1 FPS). Mô hình YOLOv8 phát hiện người, kết hợp phép toán hình học xác định điểm chạm sàn của bước chân (`foot_point`) so với vùng đa giác (`PolygonZone`). Nếu có vi phạm, hệ thống tự động chốt mốc thời gian vi phạm (`start_second` $\rightarrow$ `end_second`), trích xuất ảnh bằng chứng khoanh đỏ và ghi nhận vào "Sổ nhật ký sự kiện" (`events.json`).
2. **Pha Tương tác Hội thoại (Conversational Interaction):** Khi người quản lý đặt câu hỏi (VD: *"Lúc 2 giờ chiều có ai đi vào làn xe nâng không?"*), Não bộ Agent (LangGraph) phân tích ý định, tra cứu siêu dữ liệu sự kiện trong vài mili-giây, tổng hợp báo cáo và điều khiển Web Player tua thẳng đến giây vi phạm kèm ảnh bằng chứng xác thực.

---

## PHẦN 2: CƠ SỞ LÝ THUYẾT VỀ CÁC CÔNG NGHỆ SỬ DỤNG (HƯỚNG ỨNG DỤNG)

### 2.1. Thị giác Máy tính & Mô hình Nhận diện Đối tượng (YOLOv8 & OpenCV)
- **Kiến trúc Ultralytics YOLOv8:**
  - Là kiến trúc phát hiện vật thể tiên tiến nhất hiện nay, hoạt động theo cơ chế *Anchor-free Single-stage Detector*.
  - YOLOv8 cải tiến phần Backbone (sử dụng module C2f thay cho C3) và tách biệt phần đầu dự đoán (Decoupled Head) cho bài toán phân loại (Classification) và xác định vị trí (Bounding Box Regression).
  - Tối ưu hóa cực tốt trên tập dữ liệu COCO, nhận diện lớp người (`person` - class 0) với độ tin cậy trên 90–95%, tốc độ xử lý đạt trên 60–100 FPS trên GPU phổ thông.
- **Kỹ thuật Lấy mẫu Khung hình (Frame Sampling 1 FPS):**
  - Video camera gốc thường có 25–30 FPS. Việc quét toàn bộ 30 frame/giây là lãng phí tài nguyên tính toán vì hành vi xâm nhập của con người diễn ra tối thiểu 1–2 giây.
  - Áp dụng module `VideoReader` trích xuất đều đặn 1 frame/giây giúp tăng tốc độ phân tích của hệ thống lên **25 đến 30 lần**, cho phép video 30 giây được phân tích hoàn tất chỉ trong 1–2 giây.
- **Thuật toán Kiểm tra Điểm trong Đa giác (Point-in-Polygon Test):**
  - Sử dụng thuật toán đúc tia (Ray-Casting Algorithm) cài đặt qua hàm `cv2.pointPolygonTest` trong OpenCV:
    $$\text{distance} = \text{pointPolygonTest}(\text{contour}, (x, y), \text{measureDist}=\text{False})$$
  - Trả về giá trị $\ge 0$ nếu điểm bàn chân nằm trên biên hoặc bên trong vùng đa giác phối cảnh, kích hoạt ngay lập tức trạng thái cảnh báo vi phạm.

---

### 2.2. Kiến trúc Tác nhân AI Điều phối (LangGraph & LangChain)
- **Mô hình Tác nhân Dựa trên Đồ thị Trạng thái (LangGraph StateGraph):**
  - Khác với chuỗi tuần tự thông thường (LangChain Chains), LangGraph cho phép xây dựng luồng làm việc có chu trình (Cycles), phân nhánh điều kiện (Conditional Branching) và duy trì bộ nhớ trạng thái (`AgentState`).
  - Đồ thị bao gồm 2 node chính: Node `agent` (LLM suy luận ý định) và Node `tools` (kích hoạt các hàm trích xuất dữ liệu camera). Hàm điều hướng `should_continue` kiểm tra xem LLM có phát sinh yêu cầu gọi công cụ (`tool_calls`) hay không để quyết định luồng rẽ.
- **Mô hình Ngôn ngữ Lớn (LLMs):**
  - Tận dụng Google Gemini API (Gemini 1.5 Flash / 2.0 Flash) thông qua thư viện `langchain-google-genai`. Mô hình có cửa sổ ngữ cảnh lớn (Context Window lên tới 1 triệu tokens), tốc độ phản hồi dưới 1 giây và khả năng suy luận công cụ (Function Calling) chính xác cao.
- **Cơ chế Trích dẫn Bằng chứng Đa phương thức (Evidence Grounding):**
  - Loại bỏ hoàn toàn hiện tượng "ảo giác" (Hallucination) của AI: Mọi phát biểu của Chatbot đều được neo chặt (grounded) vào ID sự kiện cụ thể, mốc giây tua video chính xác và đường dẫn ảnh bằng chứng được hệ thống thị giác máy sinh ra.

---

### 2.3. Kiến trúc Lưu trữ Hướng Sự kiện (Event-Driven Data Storage)
- **Tách biệt Pipeline Quét và Pipeline Hỏi đáp:**
  - Không để Chatbot trực tiếp mở video nặng để quét khi người dùng hỏi (tránh độ trễ 20–30 giây gây treo trải nghiệm).
  - Sử dụng mô hình Ingestion ngầm: Dữ liệu video nạp vào $\rightarrow$ `VideoScanner` quét tự động $\rightarrow$ Lưu kết quả vào sổ nhật ký `storage/events/events.json` và thư mục ảnh `storage/evidence/`.
- **Cấu trúc Siêu dữ liệu Sự kiện (Schema chuẩn):**
  - Lưu trữ đầy đủ: `event_id`, `camera_id`, `violation_type`, `start_second`, `end_second`, `duration_seconds`, `timestamp`, `severity`, `evidence_image`, `description`.

---

### 2.4. Công nghệ Kết nối Backend & Trình phát Camera Dual-Mode
- **FastAPI Framework:**
  - Xây dựng API Gateway bất đồng bộ (Asynchronous ASGI) với hiệu năng xử lý I/O cao, tự động sinh tài liệu Swagger UI chuẩn OpenAPI.
  - Phục vụ Static Files cho các tài nguyên video và ảnh bằng chứng thời gian thực.
- **Kiến trúc Trình phát Dual-Mode (Live <-> Playback):**
  - **Chế độ Bình thường (LIVE):** Camera phát mô phỏng thời gian thực, đồng hồ OSD đếm giây liên tục.
  - **Chế độ Xem lại Bằng chứng (PLAYBACK):** Khi Chatbot trả lời câu hỏi có vi phạm, giao diện tự động bắt tín hiệu sự kiện, tua `video.currentTime = start_second`, làm nổi bật vùng vi phạm để người quản trị đối chiếu ngay lập tức.

---

## PHẦN 3: KẾT QUẢ ĐẠT ĐƯỢC BƯỚC ĐẦU & KẾ HOẠCH TIẾP THEO

### 3.1. Các Kết quả Đã Hoàn Thành Thực Tế
1. **Thiết lập Khung Dự án & Môi trường Kỹ thuật:**
   - Hoàn thành cấu trúc thư mục chuẩn công nghiệp, khởi tạo môi trường ảo `.venv` và đóng gói toàn diện file phụ thuộc `requirements.txt`.
   - Đưa dự án lên GitHub công khai, chuẩn hóa mã nguồn mở với giấy phép MIT License tại: [https://github.com/NguyenVanTruong123/agentic-cctv-warehouse](https://github.com/NguyenVanTruong123/agentic-cctv-warehouse).
2. **Xây dựng File Cấu hình Hệ thống (`config/cameras.json`):**
   - Thiết lập số hóa thông số camera `CAM-03` ("Dock Bốc Dỡ & Làn Xe Nâng"), tọa độ đa giác nguy hiểm và mốc giờ ảo `14:05:00`.
3. **Phát triển Công cụ Chọn Vùng Tương tác Chuột (`scripts/select_zone.py`):**
   - Cho phép người dùng click chuột trực tiếp lên khung hình camera để khoanh vùng nguy hiểm (Polygon) và tự động ghi tọa độ pixel vào file cấu hình.
4. **Phát triển Module Đọc Video 1 FPS (`src/cv_engine/video_reader.py`):**
   - Trích xuất khung hình theo tần suất 1 frame/giây, tối ưu hiệu năng gấp 25-30 lần, tự động đồng bộ đồng hồ thời gian thực.
5. **Hoàn thiện & Thực nghiệm Thành công Module Quét Tự động (`src/cv_engine/video_scanner.py`):**
   - Thử nghiệm trên video camera kho bãi thực tế: AI đã phát hiện chính xác sự kiện xâm nhập làn xe nâng `EVT-20261019-001` diễn ra trong 2 giây (từ `14:05:06` đến `14:05:07`).
   - Tự động xuất ảnh bằng chứng có vẽ vùng nguy hiểm đỏ rực và khoanh hộp người vi phạm tại `storage/evidence/EVT-20261019-001.jpg`.
   - Tự động lập chỉ mục sự kiện vào `storage/events/events.json`.
6. **Xây dựng Trình phát Giám sát Trực quan (`scripts/preview_detection.py`):**
   - Hiển thị trực tiếp luồng video với vùng an toàn (xanh lá) chuyển sang báo động đỏ rực kèm dải cảnh báo khi có công nhân bước chân vào làn xe nâng.

---

### 3.2. Kế hoạch Triển khai Giai đoạn Tiếp theo
- **Tuần tiếp theo:** Đóng gói hàm tra cứu sự kiện thành `@tool` cho LangGraph, viết System Prompt cho Tác nhân Điều hành Kho và hoàn thiện Đồ thị Trạng thái (LangGraph StateGraph).
- **Giai đoạn hoàn thiện:** Xây dựng API Endpoint FastAPI (`POST /api/v1/chat`) và thiết kế giao diện Web Split-Screen Dual-Mode (Trình phát Camera thông minh bên trái và Khung chat Bot bên phải).
