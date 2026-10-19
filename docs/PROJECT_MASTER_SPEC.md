# BẢN ĐẶC TẢ Ý TƯỞNG & KIẾN TRÚC HỆ THỐNG TOÀN DIỆN
## ĐỀ TÀI: MULTIMODAL AGENTIC CHATBOT GIÁM SÁT & QUẢN TRỊ VẬN HÀNH DOANH NGHIỆP
### (Smart Warehouse & Factory Operations Agent)

---

## I. TỔNG QUAN ĐỀ TÀI & ĐỊNH VỊ SẢN PHẨM
* **Tên đề tài đăng ký**: Ứng dụng Chatbot hỗ trợ Doanh nghiệp.
* **Tên kỹ thuật chuyên sâu**: Multimodal Agentic Chatbot Giám sát & Quản trị Vận hành Doanh nghiệp Đa cơ sở (Multi-facility Operations Agent).
* **Bối cảnh ứng dụng chính thức**: Hệ thống quản lý vận hành kho bãi, xưởng sản xuất và trung tâm logistics (Smart Warehouse & Logistics Hub).
* **Định hướng cốt lõi**: Kết hợp giữa **Agentic AI (LangGraph / LLM)** làm bộ não điều phối tự động và **Computer Vision (YOLOv8 / Tracking / Supervision / OCR)** làm công cụ thị giác để truy vấn, kiểm tra và trích xuất bằng chứng vi phạm từ camera giám sát thông qua ngôn ngữ tự nhiên.

---

## II. BÀI TOÁN THỰC TẾ & ĐỘT PHÁ CÔNG NGHỆ (PROBLEM & SOLUTION)

### 1. Nỗi đau thực tế của doanh nghiệp (The Pain Point)
* **Dữ liệu camera bị bỏ phí (Dark Data)**: Hàng chục camera an ninh (CCTV) ghi hình 24/7 tạo ra hàng trăm GB dữ liệu video mỗi ngày nhưng hầu như không ai xem lại trừ khi có sự cố nghiêm trọng xảy ra.
* **Tốn thời gian rà soát thủ công**: Khi cần kiểm tra vi phạm an toàn lao động, mất mát đồ đạc, tắc nghẽn lối đi hay xe giao hàng trễ, người quản lý phải tua video hàng chục tiếng rất mệt mỏi và dễ sót lỗi.
* **Giới hạn của Chatbot RAG truyền thống**: Chatbot thông thường chỉ đọc được văn bản (PDF, Word, Database) chứ không có "đôi mắt" để kiểm chứng những gì đang diễn ra trong thực tế tại nhà xưởng.

### 2. Giải pháp đột phá: Multimodal Agentic AI
* Người quản lý chỉ cần chat tự nhiên: *"Kiểm tra chiều nay ở Xưởng A xem có công nhân nào không đội mũ bảo hộ không?"* hoặc *"Cửa thoát hiểm Kho B có bị thùng hàng nào chắn quá 15 phút không?"*.
* **LLM đóng vai trò Orchestrator (Bộ não)**: Không trả lời bịa đặt (hallucination) mà tự động bóc tách tham số (khu vực, camera, thời gian, loại vi phạm), sau đó kích hoạt các công cụ thị giác máy tính (CV Tools) quét đúng đoạn video tương ứng.
* **Bằng chứng xác thực (Grounding Evidence)**: Phản hồi của Bot gồm văn bản tổng hợp mạch lạc kèm **ảnh frame trích xuất trực tiếp từ camera có đóng khung đỏ/vàng (bounding box / zone)** chứng minh lỗi vi phạm.

---

## III. ĐÁNH GIÁ TÍNH KHẢ THI TOÀN DIỆN (FEASIBILITY ANALYSIS)

| Khía cạnh | Đánh giá | Chi tiết giải pháp & Khả năng đáp ứng |
| :--- | :---: | :--- |
| **Thuật toán & Mô hình (AI/CV)** | **9.5/10** | **Không cần train mô hình từ con số 0.** Sử dụng 100% Pre-trained models mã nguồn mở chất lượng cao: YOLOv8 (detect người, xe), YOLOv8-PPE (mũ, áo bảo hộ), YOLO-World (zero-shot detect thùng hàng, pallet), ByteTrack (tracking thời gian) và Supervision (quản lý vùng polygon). |
| **Tài nguyên & Phần cứng (Hardware)** | **10/10** | Chạy tốt trên laptop sinh viên có GPU rời (RTX 2060/3050/4050...) hoặc CPU Core i5/i7 thế hệ mới. Dùng kỹ thuật **Frame Sampling** (lấy mẫu 1–2 fps thay vì quét toàn bộ 30 fps) giúp tốc độ xử lý nhanh gấp 15–30 lần. |
| **Chi phí API (Cost)** | **10/10** | Dùng **Google Gemini 1.5 Flash** (có gói Google AI Studio Free tier 15 RPM hoàn toàn miễn phí, độ trễ < 1s) hoặc OpenAI GPT-4o-mini với chi phí cực thấp (~1-2$ cho toàn bộ quá trình phát triển). |
| **Dữ liệu Video (Dataset)** | **9.5/10** | Không cần big data. Chỉ cần 3–6 đoạn clip mẫu ngắn (30s – 2 phút) từ Roboflow Universe, Kaggle, YouTube CCTV hoặc tự quay bằng điện thoại để mô phỏng các góc camera. |
| **Nhân lực & Tiến độ (Workload)** | **9.5/10** | Rất vừa vặn cho nhóm 2 người trong 4–6 tuần. Hai mảng (Computer Vision và Backend/Web) phát triển độc lập song song dựa trên hợp đồng dữ liệu JSON Schema. |

---

## IV. KIẾN TRÚC KỸ THUẬT & LUỒNG DỮ LIỆU (SYSTEM ARCHITECTURE)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js / React Web Chat)                  │
│   - Chat interface hiện đại, phản hồi thời gian thực                    │
│   - Evidence Viewer: Hiển thị ảnh trích xuất camera kèm Bounding Box    │
│   - Multi-facility Selector: Chọn xem camera Xưởng A, Xưởng B, Kho C    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ (REST API / Server-Sent Events)
┌────────────────────────────────────▼────────────────────────────────────┐
│                    BACKEND GATEWAY (FastAPI Python)                     │
│   - API tiếp nhận tin nhắn, quản lý Session & History                   │
│   - Static File Server: Cung cấp URL ảnh bằng chứng (/static/evidence/) │
│   - Multi-site Camera Router: Quản lý ánh xạ Camera ID -> Video File    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│               AGENTIC ORCHESTRATOR (LangGraph + Gemini / GPT)           │
│   - Phân loại Intent (Nghiệp vụ camera vs Câu hỏi nội quy/tổng quát)    │
│   - Trích xuất tham số: {facility, camera_id, time_range, target, roi}  │
│   - Quản lý luồng Tool Calling Loop & Xử lý Fallback/Clarification      │
│   - Tổng hợp kết quả JSON từ CV Tools thành câu trả lời tự nhiên        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ (Internal Python Function Calls)
┌────────────────────────────────────▼────────────────────────────────────┐
│              COMPUTER VISION TOOLS REGISTRY (Python Services)           │
│                                                                         │
│  [Tool 1: detect_safety_violation]  --> YOLOv8-PPE (Helmet, Vest)       │
│  [Tool 2: detect_zone_obstruction] --> YOLO-World + ByteTrack           │
│  [Tool 3: check_crowd_density]     --> YOLOv8 Person + Supervision Zone│
│  [Tool 4: detect_zone_intrusion]   --> YOLOv8 + Restricted Polygon Zone│
│                                                                         │
│  Input: Video Path + Parameters                                         │
│  Output: JSON Metadata + Evidence Image Path (Bounding Box vẽ sẵn)      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## V. CHI TIẾT DANH MỤC 4 CÔNG CỤ THỊ GIÁC (CV TOOL REGISTRY)

Thay vì viết code gom cụm, mỗi bài toán được đóng gói thành một Tool độc lập chuẩn Pydantic:

### 1. `detect_safety_violation` (Kiểm tra An toàn Bảo hộ Lao động)
* **Nghiệp vụ**: Giám sát công nhân, tài xế tại khu vực bốc dỡ hàng có chấp hành đội mũ bảo hộ (`helmet`) và mặc áo phản quang (`vest`) hay không.
* **Công nghệ CV**: Model YOLOv8 fine-tuned trên tập dữ liệu PPE (Roboflow Universe).
* **Đầu vào (Args)**: `camera_id`, `required_gear` (mặc định: `["helmet", "vest"]`).
* **Đầu ra (JSON)**:
  ```json
  {
    "violation_detected": true,
    "violation_type": "missing_helmet",
    "timestamp": "14:23:10",
    "count": 1,
    "evidence_image_url": "/static/evidence/ppe_violation_142310.jpg"
  }
  ```

### 2. `detect_zone_obstruction` (Kiểm tra Vật cản Lối đi & Thoát hiểm PCCC)
* **Nghiệp vụ**: Phát hiện thùng hàng (`box`), kiện pallet gỗ bị bỏ quên chiếm dụng lối đi bộ, cửa thoát hiểm hoặc làn đường xe nâng quá thời gian quy định.
* **Công nghệ CV**: YOLO-World (zero-shot detect `cardboard box`, `wooden pallet`) + `ByteTrack` (tính thời gian tồn tại của ID vật thể) + `Supervision PolygonZone`.
* **Đầu vào (Args)**: `camera_id`, `roi_name` ("emergency_exit", "walkway"), `max_allowed_minutes` (mặc định: 15).
* **Đầu ra (JSON)**:
  ```json
  {
    "is_obstructed": true,
    "object_type": "pallet_and_boxes",
    "duration_minutes": 22,
    "start_time": "15:05",
    "end_time": "15:27",
    "evidence_image_url": "/static/evidence/obstruction_gate2_1520.jpg"
  }
  ```

### 3. `check_crowd_density` (Giám sát Mật độ Nhân sự & Ùn tắc Đóng gói)
* **Nghiệp vụ**: Đếm số lượng công nhân làm việc tại bàn đóng hàng/chuyền chia chọn theo các mốc thời gian để phát hiện dồn ứ đơn hoặc thiếu hụt nhân lực.
* **Công nghệ CV**: YOLOv8 (detect `person`) + `Supervision PolygonZone` (đếm số box có anchor nằm trong vùng đa giác).
* **Đầu vào (Args)**: `camera_id`, `threshold_max` (ngưỡng quá tải), `threshold_min` (ngưỡng thiếu người).
* **Đầu ra (JSON)**:
  ```json
  {
    "current_count": 8,
    "status": "overcrowded",
    "peak_time": "11:35:00",
    "evidence_image_url": "/static/evidence/crowd_peak_1135.jpg"
  }
  ```

### 4. `detect_zone_intrusion` (Phát hiện Xâm nhập Vùng cấm / Giờ giới nghiêm)
* **Nghiệp vụ**: Cảnh báo khi có người bước vào khu vực nguy hiểm (làn đường di chuyển của xe nâng hàng) hoặc xuất hiện trong kho sau giờ làm việc (sau 22h).
* **Công nghệ CV**: Tận dụng chung bộ detect `person` của YOLOv8 kết hợp logic cảnh báo tức thì khi anchor của người chạm vào đa giác `danger_zone`.
* **Đầu ra (JSON)**: Trả về trạng thái xâm nhập, mốc thời gian và ảnh chụp khoanh đỏ đối tượng vi phạm.

---

## VI. CƠ CHẾ ĐIỀU PHỐI THÔNG MINH CỦA AGENT (ORCHESTRATION & FALLBACK)

Khác biệt cốt lõi của Agentic AI so với các script CV thông thường là khả năng xử lý linh hoạt:

1. **Khả năng Multi-site / Multi-camera Routing**:
   * Khi người dùng hỏi *"Kiểm tra ở Xưởng A..."* hay *"Thế còn bên Kho B..."*, Agent tự tra cứu file cấu hình `config/cameras.json` để trích xuất đúng file video của cơ sở đó.
2. **Khả năng ghép nối nhiều Tool (Multi-tool Chaining)**:
   * Câu hỏi: *"Lúc 14h khu bốc dỡ có đông người không và họ có đội mũ bảo hộ không?"*
   * $\rightarrow$ Agent tự động gọi `check_crowd_density` trước (đếm ra 4 người), sau đó gọi tiếp `detect_safety_violation` (phát hiện 1 người không đội mũ), rồi tổng hợp thành 1 câu trả lời hoàn chỉnh.
3. **Cơ chế Fallback & Phản xạ linh hoạt**:
   * **Hỏi nội quy/quy chế**: *"Quy định để hàng tối đa bao lâu?"* $\rightarrow$ Không gọi CV tool, trả lời ngay bằng kiến thức nội quy nạp sẵn trong System Prompt.
   * **Hỏi thiếu thông tin**: *"Kiểm tra vi phạm giúp tôi"* $\rightarrow$ Agent hỏi ngược lại: *"Bạn muốn kiểm tra ở cơ sở nào (Xưởng A hay Kho B) và kiểm tra đồ bảo hộ hay vật cản lối đi?"*.
   * **Hỏi ngoài khả năng**: *"Có ai hút thuốc trong kho không?"* $\rightarrow$ Agent từ chối lịch sự và nêu rõ danh sách 4 chức năng mà hệ thống đang hỗ trợ.

---

## VII. TỔ CHỨC DỮ LIỆU & KỊCH BẢN THUYẾT TRÌNH DEMO

### 1. Tổ chức dữ liệu đa cơ sở (`config/cameras.json`)
Hệ thống cho phép nạp bao nhiêu video và bao nhiêu xưởng tùy ý mà không phải sửa code:
```json
{
  "facilities": {
    "xuong_A": {
      "name": "Nhà máy Sản xuất Xưởng A",
      "cameras": {
        "cam_boc_do": {
          "title": "Khu bốc dỡ nguyên liệu",
          "video_source": "data/videos/xuong_A_boc_do.mp4"
        },
        "cam_loi_di": {
          "title": "Hành lang thoát hiểm Cửa 2",
          "video_source": "data/videos/xuong_A_loi_di.mp4",
          "roi_polygon": [[120, 250], [480, 250], [480, 720], [120, 720]]
        }
      }
    },
    "kho_B": {
      "name": "Tổng kho Logistics Kho B",
      "cameras": {
        "cam_dong_goi": {
          "title": "Chuyền đóng gói và chia chọn",
          "video_source": "data/videos/kho_B_dong_goi.mp4"
        }
      }
    }
  }
}
```

### 2. Kịch bản thuyết trình Demo ngày báo cáo
1. **Bước 1**: Mở Web Chat, màn hình hiển thị danh sách các xưởng và camera đang quản lý.
2. **Bước 2**: Gõ câu hỏi tự nhiên: *"Kiểm tra chiều nay ở Xưởng A xem khu bốc dỡ có ai không đội mũ bảo hộ không?"*.
3. **Bước 3**: Web hiển thị trạng thái Agent đang suy nghĩ: *[Đang tải video Xưởng A...] $\rightarrow$ [Đang chạy mô hình YOLOv8 PPE...]*.
4. **Bước 4**: Bot phản hồi kết quả: Thông báo phát hiện 1 trường hợp vi phạm lúc 14:23, kèm **hình ảnh trích xuất từ camera có đóng khung đỏ** quanh người vi phạm.
5. **Bước 5**: Hỏi tiếp nối (Multi-turn): *"Thế còn bên Kho B lối thoát hiểm có bị hàng chắn không?"* $\rightarrow$ Bot tự đổi sang video Kho B và trả lời chuẩn xác.

---

## VIII. PHÂN CHIA CÔNG VIỆC (WBS) & LỘ TRÌNH 4 TUẦN

### Phân chia công việc nhóm 2 người:
* **Thành viên 1 (Phụ trách Computer Vision Engine)**:
  * Thu thập và cắt ghép 4–6 video clip mẫu cho các xưởng.
  * Code 4 hàm CV Tools (`safety_violation`, `zone_obstruction`, `crowd_density`, `zone_intrusion`).
  * Tích hợp hàm vẽ bounding box/polygon và lưu file ảnh bằng chứng chuẩn kích thước.
* **Thành viên 2 (Phụ trách Agent, Backend & Web UI)**:
  * Xây dựng Agentic Graph bằng LangGraph, cấu hình System Prompt và schema Tool Calling.
  * Xây dựng FastAPI server (REST API, static file serving cho ảnh bằng chứng).
  * Xây dựng giao diện Web Chat bằng Next.js/React (hiển thị tin nhắn và Evidence Card).

### Lộ trình thực hiện 4 tuần:
* **Tuần 1**: Khởi tạo cấu trúc repository, file cấu hình `cameras.json`, tải video mẫu và chốt Pydantic Schema.
* **Tuần 2**: Viết độc lập 4 module CV Tools và dựng khung LangGraph Agent + FastAPI.
* **Tuần 3**: Tích hợp CV Tools vào ToolNode của LangGraph, kết nối giao diện Web Chat hiển thị ảnh bằng chứng.
* **Tuần 4**: Tối ưu tốc độ lấy mẫu frame (Frame sampling), chạy thử toàn bộ kịch bản và chuẩn bị Slide/Báo cáo.
