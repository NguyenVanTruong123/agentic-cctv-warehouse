"""
Script scan_cam02_obstruction.py:
Su dung YOLO-World (yolov8s-worldv2.pt) de quet tu dong 2 video vat can tren hanh lang thoat hiem CAM-02.
Tu dong lap chi muc 2 su kien vi pham:
  - Video 1 (Hom qua: 2026-10-20, gio: 10:30:00) -> EVT-20261020-003
  - Video 2 (Hom nay: 2026-10-21, gio: 14:15:00) -> EVT-20261021-001
Xuat anh bang chung khoanh do vao storage/evidence va cap nhat Database SQLite.
"""

import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ultralytics import YOLO
from src.database.db_manager import db_manager


def scan_video_session(
    model: YOLO,
    video_path: str,
    date_str: str,
    start_time_str: str,
    event_id: str,
    polygon_pts: np.ndarray,
    cam_info: dict,
    evidence_dir: Path
):
    if not os.path.exists(video_path):
        print(f"[ERROR] Video {video_path} khong ton tai!")
        return None

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps
    print(f"\n[SCAN] Bat dau quet: {video_path}")
    print(f"       Ngay: {date_str} | Gio bat dau: {start_time_str} | Do dai: {duration_sec:.1f}s")

    base_time = datetime.strptime(start_time_str, "%H:%M:%S")

    # Lay mau moi giay 1 frame (1 FPS)
    step_frames = int(round(fps))
    current_sec = 0
    frame_idx = 0

    violating_seconds = []
    best_frame = None
    best_boxes = []
    max_box_area = 0

    while frame_idx < total_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        current_time = base_time + timedelta(seconds=current_sec)
        time_str = current_time.strftime("%H:%M:%S")

        # Nhan dien vat the bang YOLOv8 (ho tro chair, box, suitcase, couch...)
        results = model(frame, conf=0.35, verbose=False)
        frame_violations = []

        # Danh sach cac loai vat the xem la vat can loi thoat hiem
        OBSTACLE_CLASSES = ["chair", "couch", "box", "suitcase", "backpack", "bench", "bed"]

        for r in results:
            for b in r.boxes:
                conf = float(b.conf[0])
                cls_id = int(b.cls[0])
                cls_name = model.names.get(cls_id, "obstacle")
                x1, y1, x2, y2 = map(int, b.xyxy[0])
                bw, bh = x2 - x1, y2 - y1

                if cls_name.lower() in OBSTACLE_CLASSES:
                    # Lay tam vat the
                    cx = (x1 + x2) // 2
                    cy = int(y1 + bh * 0.65)

                    # Kiem tra xem tam vat co nam trong polygon vung loi thoat hiem
                    inside_dist = cv2.pointPolygonTest(polygon_pts, (float(cx), float(cy)), False)
                    if inside_dist >= 0 and bw > 40 and bh > 40:
                        frame_violations.append({
                            "bbox": [x1, y1, x2, y2],
                            "conf": conf,
                            "class_name": cls_name,
                            "point": (cx, cy),
                            "area": bw * bh
                        })

        if frame_violations:
            violating_seconds.append(current_sec)
            total_area = sum(v["area"] for v in frame_violations)
            if total_area > max_box_area:
                max_box_area = total_area
                best_frame = frame.copy()
                best_boxes = frame_violations

        frame_idx += step_frames
        current_sec += 1

    cap.release()

    if not violating_seconds:
        print(f"[INFO] Khong phat hien vat can trong vung thoat hiem tai video {video_path}.")
        return None

    start_sec = violating_seconds[0]
    end_sec = violating_seconds[-1]
    duration = end_sec - start_sec + 1

    start_timestamp = (base_time + timedelta(seconds=start_sec)).strftime("%H:%M:%S")
    end_timestamp = (base_time + timedelta(seconds=end_sec)).strftime("%H:%M:%S")

    print(f"[FOUND] Phat hien vat can chan loi thoat hiem:")
    print(f"        Tu giay {start_sec} ({start_timestamp}) den giay {end_sec} ({end_timestamp}) | Thoi luong: {duration}s")

    # Ve anh bang chung Evidence
    annotated = best_frame.copy() if best_frame is not None else np.zeros((720, 1280, 3), dtype=np.uint8)

    # 1. Overlay to do vung nguy hiem loi thoat hiem
    overlay = annotated.copy()
    cv2.fillPoly(overlay, [polygon_pts], (0, 0, 220))
    cv2.addWeighted(overlay, 0.35, annotated, 0.65, 0, annotated)
    cv2.polylines(annotated, [polygon_pts], isClosed=True, color=(0, 0, 255), thickness=3)

    # 2. Ve Bounding box khoanh do vat can
    for item in best_boxes:
        x1, y1, x2, y2 = item["bbox"]
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)
        label = f"VAT CAN PCCC: {item['class_name'].upper()} {item['conf']*100:.0f}%"
        cv2.rectangle(annotated, (x1, max(0, y1 - 28)), (x1 + 320, max(0, y1)), (0, 0, 200), -1)
        cv2.putText(annotated, label, (x1 + 6, max(0, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

    # 3. Top Banner OSD
    cv2.rectangle(annotated, (0, 0), (annotated.shape[1], 46), (15, 15, 15), -1)
    banner_text = f"[CAM-02] CANH BAO: VAT CAN CHAN HANH LANG THOAT HIEM PCCC | NGAY {date_str} - {start_timestamp}"
    cv2.putText(annotated, banner_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

    evidence_rel_path = f"storage/evidence/{event_id}.jpg"
    evidence_abs_path = PROJECT_ROOT / evidence_rel_path
    cv2.imwrite(str(evidence_abs_path), annotated)
    print(f"[EVIDENCE] Da xuat anh bang chung: {evidence_rel_path}")

    event_data = {
        "event_id": event_id,
        "camera_id": "CAM-02",
        "location": cam_info.get("location", "Nhà Kho Thông Minh - Tuyến Hành Lang Thoát Hiểm Tầng 1"),
        "zone_id": "ZONE_EMERGENCY_EXIT",
        "violation_type": "EMERGENCY_EXIT_OBSTRUCTION",
        "violation_name": "Vật cản chắn lối thoát hiểm PCCC",
        "date": date_str,
        "start_second": int(start_sec),
        "end_second": int(end_sec),
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp,
        "severity": "CRITICAL",
        "evidence_image": evidence_rel_path,
        "duration_seconds": int(duration),
        "description": f"Phát hiện vật cản (kiện hàng/thùng carton) chiếm dụng hành lang thoát hiểm PCCC trong {duration} giây (từ {start_timestamp} đến {end_timestamp})",
        "status": "UNRESOLVED"
    }

    return event_data


def main():
    config_path = PROJECT_ROOT / "config" / "cameras.json"
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    cam_02 = next((c for c in cfg.get("cameras", []) if c["camera_id"] == "CAM-02"), None)
    if not cam_02:
        print("[ERROR] Khong tim thay CAM-02 trong config/cameras.json!")
        return

    polygon_pts = np.array(cam_02["danger_zones"][0]["polygon"], dtype=np.int32)
    print(f"[INFO] Toa do vung loi thoat hiem CAM-02:\n{polygon_pts.tolist()}")

    # Khoi tao model YOLOv8 (ho tro day du chair, suitcase, couch...)
    model_path = PROJECT_ROOT / "yolov8n.pt"
    print(f"[INFO] Dang khoi tao mo hinh YOLO tu {model_path}...")
    model = YOLO(str(model_path))

    evidence_dir = PROJECT_ROOT / "storage" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    sessions = [
        {
            "video_path": "data/videos/vat_can_chan_duong_di_thoat_hiem_1.mp4",
            "date": "2026-10-20",
            "start_time": "10:30:00",
            "event_id": "EVT-20261020-003"
        },
        {
            "video_path": "data/videos/vat_can_chan_duong_di_thoat_hiem_2.mp4",
            "date": "2026-10-21",
            "start_time": "14:15:00",
            "event_id": "EVT-20261021-001"
        }
    ]

    new_events = []
    for s in sessions:
        ev = scan_video_session(
            model=model,
            video_path=str(PROJECT_ROOT / s["video_path"]),
            date_str=s["date"],
            start_time_str=s["start_time"],
            event_id=s["event_id"],
            polygon_pts=polygon_pts,
            cam_info=cam_02,
            evidence_dir=evidence_dir
        )
        if ev:
            new_events.append(ev)

    if new_events:
        print("\n=========================================================")
        print(f"[SUCCESS] Da phat hien tong cong {len(new_events)} su kien vi pham!")

        # 1. Cap nhat vao Database SQLite
        for ev in new_events:
            db_manager.insert_event(ev)
            print(f"  -> Da ghi vao Database SQLite: {ev['event_id']} ({ev['date']} | {ev['start_timestamp']})")

        # 2. Dong bo vao file storage/events/events.json
        events_json_path = PROJECT_ROOT / "storage" / "events" / "events.json"
        existing_events = []
        if events_json_path.exists():
            try:
                with open(events_json_path, "r", encoding="utf-8") as f:
                    existing_events = json.load(f)
            except Exception:
                existing_events = []

        existing_ids = {e["event_id"] for e in existing_events}
        for ev in new_events:
            if ev["event_id"] not in existing_ids:
                existing_events.append(ev)

        with open(events_json_path, "w", encoding="utf-8") as f:
            json.dump(existing_events, f, ensure_ascii=False, indent=2)
        print(f"  -> Da dong bo vao file {events_json_path}")
        print("=========================================================")


if __name__ == "__main__":
    main()
