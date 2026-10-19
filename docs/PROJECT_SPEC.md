# TÀI LIỆU ĐẶC TẢ DỰ ÁN (PROJECT BRIEF)

- **Tên đề tài đăng ký**: Ứng dụng Chatbot hỗ trợ Doanh nghiệp
- **Tên kỹ thuật thực tế**: Multimodal Agentic Chatbot Giám sát & Quản trị Vận hành Doanh nghiệp (Store & Warehouse Operations Agent)
- **Định hướng cốt lõi**: Kết hợp Agentic AI (LangGraph/LLM) làm bộ não điều phối và Computer Vision (YOLO/Tracking/OCR) làm công cụ thị giác để trả lời câu hỏi tự nhiên về dữ liệu camera giám sát.

---

## 1. Vấn đề giải quyết & Ý tưởng đề tài (Problem & Solution)

### Vấn đề thực tế
1. Camera an ninh (CCTV) trong kho bãi/cửa hàng ghi hình 24/7 nhưng hầu như không ai có thời gian xem lại hàng chục tiếng video.
2. Khi phát sinh sự cố (mất đồ, tắc nghẽn quầy, vi phạm an toàn lao động), quản lý phải tua video thủ công rất mất thời gian.
3. Các chatbot văn bản thông thường (RAG đơn thuần) chỉ đọc được tài liệu PDF/văn bản chứ không có "đôi mắt" để nhìn dữ liệu thực tế.

### Giải pháp của nhóm
Xây dựng một Chatbot hỗ trợ điều hành doanh nghiệp dưới dạng **Agentic AI**:
- Người quản lý chat bằng ngôn ngữ tự nhiên: *"Kiểm tra chiều nay ở Cửa 2 có ai để thùng hàng chắn lối thoát hiểm không?"*
- LLM không trả lời cảm tính mà đóng vai trò **Orchestrator** tự phân rã câu hỏi, ra quyết định kích hoạt các CV Tools quét đúng đoạn video cần thiết.
- Bot tổng hợp báo cáo bằng văn bản kèm hình ảnh/video ngắn bằng chứng (evidence) gửi lại trên giao diện chat.

---

## 2. Luồng vận hành Agentic (End-to-End Workflow)

```
[1. User Chat] ("Kiểm tra lúc 15h ở Cửa 2 có ai để hàng chắn lối thoát hiểm không?")
      │
      ▼
[2. LLM Planner / LangGraph] 
      │ - Nhận diện Intent & trích xuất tham số:
      │   {zone: "gate_2", time: "15:00-15:30", target: ["box", "pallet"], roi: "walkway"}
      │ - Tự tạo JSON Tool Call
      ▼
[3. Computer Vision Engine (Python)]
      │ - Trích xuất video clip tương ứng (Decord/OpenCV)
      │ - Lấy mẫu frame & chạy Object Detection (YOLO-World / YOLOv8)
      │ - Kiểm tra vùng ROI (Supervision Polygon Zone)
      │ - Theo dõi thời gian tồn tại của vật thể (Tracking)
      ▼
[4. Tool Output (JSON Metadata)]
      │ - Trả về: Tìm thấy kiện hàng chiếm lối đi từ 15:12 đến 15:30 (18 phút).
      │ - Đính kèm URL ảnh frame có vẽ Bounding Box bằng chứng.
      ▼
[5. LLM Reflection & Response]
      │ - LLM đọc JSON, đối chiếu quy định an toàn (cho phép < 5 phút -> vi phạm).
      │ - Soạn tin nhắn báo cáo mạch lạc kèm ảnh vi phạm gửi về Web Chat.
```

---

## 3. Danh mục CV Tools cần xây dựng (Tool Registry)

Thay vì viết code dính chùm, các bài toán thị giác máy tính được đóng gói thành từng Tool độc lập (có input/output JSON chuẩn) để LLM tự gọi:

| Tên Tool | Nghiệp vụ doanh nghiệp | Mô hình / Kỹ thuật CV sử dụng | Dữ liệu trả về (Output) |
| :--- | :--- | :--- | :--- |
| `check_crowd_density` | Giám sát mật độ, phát hiện quá tải tại quầy thu ngân/lối đi. | YOLOv8 (detect person) + Supervision (Zone Count). | Biểu đồ/mật độ theo giờ, frame lúc đông nhất. |
| `detect_safety_violation` | Kiểm tra vi phạm an toàn lao động (đồ bảo hộ, mũ, áo, đồng phục). | YOLOv8 (PPE dataset) hoặc Grounding DINO (zero-shot prompt). | Danh sách vi phạm, mốc thời gian, ảnh crop người vi phạm. |
| `detect_zone_obstruction` | Phát hiện vật thể cản trở lối đi bộ/cửa thoát hiểm kéo dài. | YOLO-World (box, pallet) + ByteTrack (tính thời gian chiếm chỗ). | Tọa độ vật cản, thời gian tồn tại (phút), ảnh bằng chứng. |
| `search_vehicle_entry` | Tra cứu xe tải xuất/nhập kho theo biển số hoặc loại xe. | YOLOv8 (vehicle) + PaddleOCR (nhận diện biển số). | Lịch sử giờ vào/ra của phương tiện. |

---

## 4. Kiến trúc kỹ thuật & Tech Stack

```
┌────────────────────────────────────────────────────────┐
│  FRONTEND (Giao diện Chat Doanh nghiệp)                │
│  - Next.js / React, Tailwind CSS                       │
│  - Hiển thị hội thoại chat, render ảnh/video bằng chứng│
└───────────────────────────┬────────────────────────────┘
                            │ (REST API / WebSocket)
┌───────────────────────────▼────────────────────────────┐
│  BACKEND (API & Orchestrator Gateway)                  │
│  - FastAPI (Python)                                    │
│  - LangGraph: Quản lý Agent State, Loop & Tool Calling │
│  - LLM: OpenAI GPT-4o-mini / Gemini / Llama-3          │
└───────────────────────────┬────────────────────────────┘
                            │ (Internal Function Calls)
┌───────────────────────────▼────────────────────────────┐
│  COMPUTER VISION ENGINE (CV Services)                  │
│  - Framework: PyTorch, Ultralytics (YOLO), Supervision │
│  - Video I/O: OpenCV / Decord                          │
│  - Models: YOLOv8 / YOLO-World, ByteTrack, PaddleOCR   │
└───────────────────────────┘
```

---

## 5. Phân chia công việc đề xuất (Work Breakdown Structure)

### Thành viên phụ trách: Computer Vision (CV Engine)
1. **Thu thập/Chuẩn bị dữ liệu**: Cắt 3–4 video mẫu mô phỏng kịch bản (quầy thu ngân đông, nhân viên không mặc đồng phục/đồ bảo hộ, hàng hóa chắn lối thoát hiểm).
2. **Build các hàm Tool CV**:
   - Viết hàm detect + tracking + zone checking.
   - Input: `video_path`, tham số kiểm tra.
   - Output: File ảnh bằng chứng (có vẽ box/zone) + JSON kết quả.
   - Đóng gói các hàm thành các Python function/module sạch sẽ theo chuẩn Pydantic schema.

### Thành viên phụ trách: Agent, Backend & Frontend
1. **LangGraph Agent**: Cấu hình State Graph, viết System Prompt dạy LLM cách suy luận và định nghĩa Tool calling schema.
2. **FastAPI Backend**: Xây dựng API nhận tin nhắn chat, điều phối gọi Agent, lưu trữ lịch sử chat và quản lý đường dẫn file ảnh evidence.
3. **Frontend Chat Web**: Dựng trang web chat giao diện hiện đại (Next.js/React), hỗ trợ hiển thị tin nhắn kèm ảnh bằng chứng trực quan.

---

## 6. Kế hoạch Demo ngày báo cáo (Demo Strategy)
- Không cần stream camera thật 24/7 (tránh lỗi mạng/thiết bị).
- Chuẩn bị sẵn thư mục chứa 3 video kịch bản thực tế:
  - **Video 1**: Quầy thu ngân lúc vắng và lúc quá tải.
  - **Video 2**: Lối đi bộ có thùng hàng đặt chắn > 10 phút.
  - **Video 3**: Nhân viên ra vào kho (có người thiếu mũ bảo hộ).
- **Kịch bản thuyết trình**: Mở web chat, gõ câu hỏi tự nhiên $\rightarrow$ Hệ thống suy nghĩ, hiển thị trạng thái đang gọi tool $\rightarrow$ Trả lời kết quả phân tích chuẩn xác kèm đúng frame ảnh vi phạm.
