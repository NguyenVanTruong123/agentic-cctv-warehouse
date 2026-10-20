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
            "description": ev.get("description", "")
        })
    return formatted


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

        # Tim kiem xem co su kien vi pham nao duoc de cap trong cau tra loi khong
        matched_events = []
        seek_sec = None
        evidence_img = None

        all_events = db_manager.query_events()
        for ev in all_events:
            ev_id = ev["event_id"]
            if ev_id in reply_text or (ev.get("violation_type") and ev["violation_type"] in reply_text):
                seek_sec = float(ev.get("start_second", 6.0))
                if ev.get("evidence_image"):
                    evidence_img = "/" + ev["evidence_image"].replace("\\", "/")
                
                matched_events.append({
                    "id": ev["event_id"],
                    "source": f"{ev['camera_id']} ({ev['violation_type']})",
                    "time": seek_sec,
                    "type": ev.get("violation_name", ev["violation_type"]),
                    "level": ev.get("severity", "Cao"),
                    "status": "Chưa xử lý" if ev.get("status") == "UNRESOLVED" else "Đã xử lý",
                    "evidenceUrl": evidence_img,
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

        return ChatResponse(
            status="success",
            reply=reply_text,
            active_camera=req.active_camera,
            seek_second=seek_sec,
            evidence_image=evidence_img,
            events=matched_events if matched_events else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Loi xu ly Agent: {str(e)}")


# Mount thu muc web tai root '/' DE TRINH DUYET MO THANG VAO INDEX.HTML
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="frontend")
