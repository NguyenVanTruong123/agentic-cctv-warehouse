"""
Module tools.py:
Dinh nghia cac cong cu (@tool) ket noi truc tiep vao Database SQLite.
Cac cong cu nay duoc bien dich thanh JSON Schema de LLM tu dong goi thong qua Function Calling.
"""

import json
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool

from src.database.db_manager import db_manager


@tool
def query_safety_events(
    camera_id: Optional[str] = None,
    date: Optional[str] = None,
    violation_type: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Tra cuu danh sach cac su kien vi pham an toan kho bai tu Database SQLite.
    
    Tham so:
      - camera_id: Ma camera can loc (VD: 'CAM-01', 'CAM-03'). De trong neu muon tim toan xuong.
      - date: Ngay dien ra su kien theo dinh dang YYYY-MM-DD (VD: '2026-10-19').
      - violation_type: Ma loai vi pham cu the (VD: 'DANGER_ZONE_INTRUSION', 'UNIFORM_PPE_VIOLATION', 'PATHWAY_OBSTRUCTION').
      - start_time: Gio bat dau theo dinh dang HH:MM:SS (VD: '14:00:00').
      - end_time: Gio ket thuc theo dinh dang HH:MM:SS (VD: '15:00:00').
      - limit: So luong ban ghi toi da (mac dinh 10).
    """
    events = db_manager.query_events(
        camera_id=camera_id,
        date=date,
        violation_type=violation_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    if not events:
        filter_desc = []
        if camera_id: filter_desc.append(f"camera {camera_id}")
        if date: filter_desc.append(f"ngay {date}")
        if violation_type: filter_desc.append(f"loai {violation_type}")
        ctx = " ".join(filter_desc) if filter_desc else "toan bo he thong"
        return f"Khong tim thay su kien vi pham nao phu hop voi {ctx} trong co so du lieu."

    return json.dumps(events, ensure_ascii=False, indent=2)


@tool
def get_camera_list(keyword: Optional[str] = None) -> str:
    """
    Lay danh sach tat ca camera dang giam sat trong nha kho va vi tri lap dat cua chung.
    
    Tham so:
      - keyword: Tu khoa vi tri muon tim (VD: 'xe nang', 'boc do', 'cua'). De trong de lay toan bo.
    """
    cameras = db_manager.get_cameras()
    if keyword:
        kw = keyword.lower()
        cameras = [
            c for c in cameras 
            if kw in c["name"].lower() or kw in c.get("location", "").lower() or kw in c["camera_id"].lower()
        ]

    if not cameras:
        return f"Khong tim thay camera nao phu hop voi tu khoa '{keyword}'."

    return json.dumps(cameras, ensure_ascii=False, indent=2)


@tool
def get_violation_policy(violation_type: Optional[str] = None) -> str:
    """
    Tra cuu quy che an toan lao dong va muc xu phat cua cac loai vi pham trong nha kho.
    
    Tham so:
      - violation_type: Ma loai vi pham cu the:
          + 'DANGER_ZONE_INTRUSION': Di vao lan xe nang / vung cam
          + 'UNIFORM_PPE_VIOLATION': Khong mac dong phuc / do bao ho
          + 'PATHWAY_OBSTRUCTION': Vat can chan loi di / loi thoat hiem
        De trong de xem quy che tat ca cac loai.
    """
    v_types = db_manager.get_violation_types()
    if violation_type:
        vt_clean = violation_type.upper().strip()
        v_types = [v for v in v_types if v["violation_type"] == vt_clean]

    if not v_types:
        return f"Khong tim thay quy che cho loai vi pham '{violation_type}'."

    return json.dumps(v_types, ensure_ascii=False, indent=2)


@tool
def get_safety_stats() -> str:
    """
    Lay so lieu thong ke tong quan ve tinh hinh an toan toan xuong:
    Tong so vu vi pham, so vu chua xu ly, va tong so camera dang hoat dong.
    """
    stats = db_manager.get_summary_stats()
    return json.dumps(stats, ensure_ascii=False, indent=2)


# Danh sach toan bo tools cung cap cho Agent
ALL_TOOLS = [
    query_safety_events,
    get_camera_list,
    get_violation_policy,
    get_safety_stats
]
