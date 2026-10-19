# 🏭 Agentic CCTV Warehouse: Multimodal Operations & Safety Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/Agent-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![YOLOv8](https://img.shields.io/badge/CV-YOLOv8-green.svg)](https://github.com/ultralytics/ultralytics)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-teal.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Hệ thống Giám sát & Quản trị Vận hành Doanh nghiệp Tự động** kết hợp giữa **Thị giác máy tính (Computer Vision)** và **Tác nhân AI Đa phương thức (Multimodal Agentic AI)**. Tự động quét camera, phát hiện xâm nhập vùng nguy hiểm, lập chỉ mục sự kiện và hỗ trợ người quản trị truy vấn hội thoại theo thời gian thực.

---

## 🌟 Tính Năng Nổi Bật (Key Features)

- **🎥 Tự động hóa Giám sát (Event-Driven Video Ingestion):** Tự động quét video camera định kỳ (1 FPS), phát hiện người/vật thể vi phạm mà không làm tắc nghẽn hệ thống.
- **🚨 Phát hiện Xâm nhập Vùng Nguy hiểm (Polygon Zone Intrusion):** Sử dụng mô hình YOLOv8 kết hợp thuật toán kiểm tra tọa độ bước chân (`foot_point`) trong đa giác phối cảnh (`PolygonZone`) bao quanh làn xe nâng / máy móc.
- **⚡ Phản hồi Hội thoại Mili-giây (< 0.5s):** Chatbot tra cứu trực tiếp từ Sổ nhật ký sự kiện (`storage/events/events.json`), trả lời ngay lập tức kèm ảnh chụp bằng chứng khoanh đỏ và mốc thời gian vi phạm.
- **⏪ Điều khiển Trình phát Dual-Mode:** Tự động điều khiển camera chuyển đổi giữa chế độ **[🔴 LIVE]** và chế độ **[⏪ PLAYBACK]**, tua video đến đúng số giây vi phạm.

---

## 🏗️ Kiến Trúc Hệ Thống (System Architecture)

```
┌────────────────────────────────────────────────────────┐
│             NVR / CCTV Video Feeds (mp4)               │
└───────────────────────────┬────────────────────────────┘
                            │ (Tự động nạp định kỳ)
                            ▼
┌────────────────────────────────────────────────────────┐
│           COMPUTER VISION INGESTION ENGINE             │
│  - VideoReader (1 FPS Frame Sampling)                  │
│  - YOLOv8 Person Detection                             │
│  - Polygon Zone Intrusion Verification                 │
│  - Event Tracking & Evidence Annotator                 │
└───────────────────────────┬────────────────────────────┘
                            │ (Ghi nhật ký & Xuất ảnh)
                            ▼
┌────────────────────────────────────────────────────────┐
│       STRUCTURED EVENT STORE & EVIDENCE STORAGE        │
│  - storage/events/events.json                          │
│  - storage/evidence/EVT-YYYYMMDD-XXX.jpg               │
└───────────────────────────▲────────────────────────────┘
                            │ (Truy vấn sự kiện tức thì)
                            ▼
┌────────────────────────────────────────────────────────┐
│           LANGGRAPH AGENTIC ORCHESTRATOR               │
│  - Intent Parsing & Tool Calling                       │
│  - Synthesizing Summary & Citing Evidence              │
└───────────────────────────▲────────────────────────────┘
                            │ (Hỏi đáp đa phương thức)
                            ▼
┌────────────────────────────────────────────────────────┐
│            FASTAPI BACKEND & DUAL-MODE UI              │
│  - Khung trái: Video Player (Live <-> Playback)        │
│  - Khung phải: Trò chuyện với Agent & Evidence Card    │
└────────────────────────────────────────────────────────┘
```

---

## 📂 Cấu Trúc Thư Mục (Project Structure)

```text
agentic-cctv-warehouse/
├── config/
│   └── cameras.json          # Cấu hình danh sách camera & tọa độ vùng đa giác nguy hiểm
├── data/
│   └── videos/               # Thư mục chứa các video camera gốc (.mp4)
├── storage/
│   ├── cctv_videos/          # Video phục vụ stream web
│   ├── evidence/             # Ảnh chụp bằng chứng khoanh đỏ vi phạm
│   └── events/               # Sổ nhật ký sự kiện vi phạm (events.json)
├── src/
│   ├── cv_engine/            # Module Thị giác máy tính (VideoReader, VideoScanner)
│   ├── agent/                # Bộ não Agentic AI (LangGraph StateGraph, Tools, Prompts)
│   └── api/                  # FastAPI Backend Server & Endpoints
├── web/                      # Giao diện Frontend Dual-Mode
├── docs/                     # Tài liệu thiết kế hệ thống (WBS, System Architecture...)
├── requirements.txt          # Danh sách thư viện phụ thuộc
└── .env.example              # Mẫu cấu hình biến môi trường
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Thử (Quick Start)

### 1. Khởi tạo môi trường ảo Python
```powershell
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt trên Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Nâng cấp pip và cài đặt thư viện
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường
Sao chép file `.env.example` thành `.env` và điền API Key:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Quét video camera và kiểm tra sự kiện
```powershell
python -m src.cv_engine.video_scanner
```

---

## 📜 Giấy Phép (License)
Dự án được phân phối dưới giấy phép [MIT License](LICENSE).
