"""
Module main.py:
FastAPI Backend Gateway - May chu tich hop toan dien cho He thong Giam sat Kho Thong minh:
  1. Phuc vu REST API cho Frontend (/api/v1/cameras, /api/v1/chat, /api/v1/events)
  2. Ket noi truc tiep vao LangGraph Agent (gemini-2.5-flash + DeepSeek fallback)
  3. Mount Static Files cho anh bang chung (/storage/evidence) va video (/storage/cctv_videos)
  4. Mount toan bo giao dien Frontend tai thu muc / de nguoi dung truy cap truc tiep tren trinh duyet.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Thiet lap duong dan goc cua du an
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.db_manager import db_manager
from src.agent.graph import chat_with_agent

# Khoi tao ung dung FastAPI
app = FastAPI(
    title="Smart Warehouse Operations - Agentic CCTV API",
    description="Backend API Gateway ket noi Computer Vision, SQLite va LangGraph Multi-Agent",
    version="1.0.0"
)

# Cau hinh CORS cho phep moi domain ket noi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount cac thu muc tinh (Static Files)
STORAGE_DIR = PROJECT_ROOT / "storage"
WEB_DIR = PROJECT_ROOT / "web"
DATA_DIR = PROJECT_ROOT / "data"

if STORAGE_DIR.exists():
    app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")

if DATA_DIR.exists():
    app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")


# ==============================================================================
# SCHEMAS (Pydantic Models)
# ==============================================================================
class ChatRequest(BaseModel):
    message: str
    active_camera: Optional[str] = "CAM-03"
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    status: str
    reply: str
    active_camera: Optional[str] = "CAM-03"
    seek_second: Optional[float] = None
    video_url: Optional[str] = None
    evidence_image: Optional[str] = None
    events: Optional[List[Dict[str, Any]]] = None


# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================

@app.get("/api/v1/health")
def health_check():
    """Kiem tra trang thai hoat dong cua Server, Database va AI."""
    stats = db_manager.get_summary_stats()
    return {
        "status": "healthy",
        "service": "Smart Warehouse CCTV Agent",
        "database": "connected",
        "active_cameras": stats.get("total_cameras", 0),
        "total_violations": stats.get("total_events", 0)
    }


@app.get("/api/v1/cameras")
def get_cameras():
    """Lay danh sach tat ca camera tu Database de hien thi len Frontend."""
    cameras = db_manager.get_cameras()
    result = []
    for c in cameras:
        cam_id = c["camera_id"]
        # Gan video cho camera
        video_url = ""
        if cam_id == "CAM-03":
            preview_file = STORAGE_DIR / "cctv_videos" / "dock_boc_do_preview.mp4"
            if preview_file.exists():
                video_url = "/storage/cctv_videos/dock_boc_do_preview.mp4"
            else:
                video_url = "/data/videos/YTSave.to_YouTube_Media_DU4aGZdyJBI_warehouse-camera-hd-sdi_001_1080p.mp4"
        elif cam_id == "CAM-01":
            preview_file = STORAGE_DIR / "cctv_videos" / "vat_can_xe_nang_preview.mp4"
            if preview_file.exists():
                video_url = "/storage/cctv_videos/vat_can_xe_nang_preview.mp4"
            else:
                video_url = "/data/videos/VatCanChanLoiDiXeNang.mp4"
        elif cam_id == "CAM-02":
            preview_file = STORAGE_DIR / "cctv_videos" / "hanh_lang_thoat_hiem_preview_1.mp4"
            if preview_file.exists():
                video_url = "/storage/cctv_videos/hanh_lang_thoat_hiem_preview_1.mp4"
            else:
                video_url = "/data/videos/vat_can_chan_duong_di_thoat_hiem_1.mp4"
        elif c.get("video_path"):
            v_path = c["video_path"].replace("\\", "/").lstrip("/")
            video_url = f"/{v_path}"

        result.append({
            "id": cam_id,
            "name": f"{cam_id} - {c['name']}",
            "location": c.get("location", ""),
            "live": True,
            "videoUrl": video_url,
            "dangerZones": c.get("polygon_json", "")
        })
    return result


@app.get("/api/v1/events")
def get_events(camera_id: Optional[str] = None, date: Optional[str] = None):
    """Truy van danh sach cac su kien vi pham tu Database."""
    events = db_manager.query_events(camera_id=camera_id, date=date)
    formatted = []
    for ev in events:
        evidence_url = ""
        if ev.get("evidence_image"):
            evidence_url = "/" + ev["evidence_image"].replace("\\", "/")

        ev_id = ev.get("event_id", "")
        ev_video_url = ""
        if ev_id == "EVT-20261021-001":
            ev_video_url = "/storage/cctv_videos/hanh_lang_thoat_hiem_preview_2.mp4"
        elif ev_id == "EVT-20261020-003":
            ev_video_url = "/storage/cctv_videos/hanh_lang_thoat_hiem_preview_1.mp4"
        elif ev.get("camera_id") == "CAM-01":
            ev_video_url = "/storage/cctv_videos/vat_can_xe_nang_preview.mp4"
        elif ev.get("camera_id") == "CAM-03":
            ev_video_url = "/storage/cctv_videos/dock_boc_do_preview.mp4"

        formatted.append({
            "id": ev["event_id"],
            "camera_id": ev["camera_id"],
            "violation_type": ev["violation_type"],
            "violation_name": ev.get("violation_name", ev["violation_type"]),
            "start_time": ev.get("start_timestamp", ""),
            "end_time": ev.get("end_timestamp", ""),
            "duration": ev.get("duration_seconds", 0),
            "severity": ev.get("severity", "Cao"),
            "status": ev.get("status", "UNRESOLVED"),
            "seek_second": ev.get("start_second", 0),
            "evidenceUrl": evidence_url,
            "videoUrl": ev_video_url,
            "description": ev.get("description", "")
        })
class UpdateEventStatusRequest(BaseModel):
    status: str


@app.post("/api/v1/events/{event_id}/status")
def update_event_status_api(event_id: str, req: UpdateEventStatusRequest):
    """Cap nhat trang thai xu ly cua mot su kien vi pham."""
    raw_status = req.status.strip()
    status_lower = raw_status.lower()
    if "unresolved" in status_lower or "chưa" in status_lower or "chua" in status_lower:
        mapped_status = "UNRESOLVED"
    elif any(k in status_lower for k in ["đã", "da", "resolved", "done", "xong"]):
        mapped_status = "RESOLVED"
    elif any(k in status_lower for k in ["đang", "dang", "progress"]):
        mapped_status = "IN_PROGRESS"
    else:
        mapped_status = "UNRESOLVED"


    success = db_manager.update_event_status(event_id, mapped_status)
    if not success:
        raise HTTPException(status_code=404, detail=f"Khong tim thay su kien '{event_id}'")

    vi_status = "Đã xử lý" if mapped_status == "RESOLVED" else ("Đang xử lý" if mapped_status == "IN_PROGRESS" else "Chưa xử lý")
    return {
        "status": "success",
        "event_id": event_id,
        "db_status": mapped_status,
        "vi_status": vi_status
    }


# Luu tru bo nho hoi thoai theo phien (Session Memory by thread_id)
CHAT_SESSIONS: Dict[str, list] = {}


@app.post("/api/v1/chat", response_model=ChatResponse)
def handle_chat(req: ChatRequest):
    """
    Endpoint tiep nhan hoi thoai tu nguoi dung, kich hoat LangGraph ReAct Agent:
      - Duy tri bo nho hoi thoai State theo thread_id (Multi-turn conversation)
      - Tu dong goi Tools de doc Database SQLite
      - Trich xuat giay tua video (seek_second) va anh bang chung (evidence_image)
    """
    user_msg = req.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Tin nhan khong duoc de trong.")

    # 1. Lay lich su hoi thoai cua phien hien tai
    session_id = req.thread_id or "default_session"
    history = CHAT_SESSIONS.get(session_id, [])

    try:
        reply_text, updated_messages = chat_with_agent(
            user_message=user_msg,
            history=history,
            active_camera=req.active_camera or "CAM-03"
        )

        # 2. Luu lai lich su hoi thoai vao State cua session (giu 20 tin gan nhat)
        CHAT_SESSIONS[session_id] = list(updated_messages)[-20:]

        # ======================================================================
        # TRIPLE-LOCK EVENT GROUNDING (CHỐNG HIỂN THỊ NHẦM TRIỆT ĐỂ)
        # ======================================================================
        import re
        import json

        target_event_ids = []

        # 1. KHÓA 1 (User Intent): Người dùng chỉ đích danh mã EVT trong câu hỏi
        user_targets = re.findall(r"EVT-\d{8}-\d{3}", user_msg, re.IGNORECASE)
        if user_targets:
            target_event_ids = [t.upper() for t in user_targets]
        else:
            # 2. KHÓA 2 (Tool Output): Lấy các event_id thực sự được Tool trả về trong lượt gọi này
            tool_event_ids = []
            for msg in reversed(updated_messages):
                if hasattr(msg, "name") and msg.name == "query_safety_events":
                    try:
                        content_data = json.loads(msg.content)
                        if isinstance(content_data, list):
                            for item in content_data:
                                if isinstance(item, dict) and "event_id" in item:
                                    tool_event_ids.append(item["event_id"])
                    except Exception:
                        pass
                if msg.__class__.__name__ == "HumanMessage":
                    break

            if tool_event_ids:
                # Chỉ giữ lại mã từ Tool mà thực sự được đề cập trong câu trả lời
                target_event_ids = [eid for eid in tool_event_ids if eid in reply_text]
                if not target_event_ids:
                    target_event_ids = tool_event_ids
            else:
                # 3. KHÓA 3 (Regex Text): Tìm mã EVT xuất hiện trong văn bản trả lời
                reply_evts = re.findall(r"EVT-\d{8}-\d{3}", reply_text)
                if reply_evts:
                    seen = set()
                    target_event_ids = [x for x in reply_evts if not (x in seen or seen.add(x))]

        matched_events = []
        seek_sec = None
        evidence_img = None

        # Lấy thông tin chính xác từ Database cho các sự kiện đã được khóa mục tiêu
        for ev_id in target_event_ids:
            ev = db_manager.get_event_by_id(ev_id)
            if not ev:
                continue

            cur_seek = float(ev.get("start_second", 6.0))
            cur_img = "/" + ev["evidence_image"].replace("\\", "/") if ev.get("evidence_image") else ""

            if seek_sec is None:
                seek_sec = cur_seek
            if evidence_img is None and cur_img:
                evidence_img = cur_img

            # Xác định đúng tệp video tương ứng của sự kiện đó
            ev_video_url = ""
            if ev_id == "EVT-20261021-001":
                ev_video_url = "/storage/cctv_videos/hanh_lang_thoat_hiem_preview_2.mp4"
            elif ev_id == "EVT-20261020-003":
                ev_video_url = "/storage/cctv_videos/hanh_lang_thoat_hiem_preview_1.mp4"
            elif ev.get("camera_id") == "CAM-01":
                ev_video_url = "/storage/cctv_videos/vat_can_xe_nang_preview.mp4"
            elif ev.get("camera_id") == "CAM-03":
                ev_video_url = "/storage/cctv_videos/dock_boc_do_preview.mp4"

            matched_events.append({
                "id": ev["event_id"],
                "source": f"{ev['camera_id']} ({ev['violation_type']})",
                "time": cur_seek,
                "type": ev.get("violation_name", ev["violation_type"]),
                "level": ev.get("severity", "Cao"),
                "status": "Đã xử lý" if ev.get("status") in ["RESOLVED", "PROCESSED", "DONE"] else "Chưa xử lý",
                "evidenceUrl": cur_img,
                "videoUrl": ev_video_url,
                "description": ev.get("description", "")
            })

        # Neu trong cau tra loi co chua chuoi 'storage/evidence/'
        if not evidence_img and "storage/evidence/" in reply_text:
            import re
            img_match = re.search(r"storage/evidence/[A-Za-z0-9_\-\.]+\.jpg", reply_text)
            if img_match:
                evidence_img = "/" + img_match.group(0)

        # Neu trong cau tra loi co giay tua video
        if seek_sec is None:
            import re
            sec_match = re.search(r"(?:giây|thứ)\s*(\d+)", reply_text)
            if sec_match:
                seek_sec = float(sec_match.group(1))

        ev_video_target = None
        target_cam_id = req.active_camera
        if matched_events:
            ev_video_target = matched_events[0].get("videoUrl")
            target_cam_id = matched_events[0].get("source", "").split()[0] or req.active_camera

        return ChatResponse(
            status="success",
            reply=reply_text,
            active_camera=target_cam_id,
            seek_second=seek_sec,
            video_url=ev_video_target,
            evidence_image=evidence_img,
            events=matched_events if matched_events else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Loi xu ly Agent: {str(e)}")


# Mount thu muc web tai root '/' DE TRINH DUYET MO THANG VAO INDEX.HTML
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="frontend")
