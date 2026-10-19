"""
Module VideoScanner: Quet tu dong video camera va lap chi muc su kien vi pham (Event Logging).
Phat hien nguoi xam nhap vung nguy hiem (Zone Intrusion) bang YOLOv8 va PolygonZone.
Ket qua duoc xuat truc tiep vao file storage/events/events.json kem anh bang chung.
"""

import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Dam bao import duoc package src khi chay truc tiep
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ultralytics import YOLO
from src.cv_engine.video_reader import VideoReader


class VideoScanner:
    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        config_path: str = "config/cameras.json",
        events_output_path: str = "storage/events/events.json",
        evidence_dir: str = "storage/evidence"
    ):
        self.config_path = config_path
        self.events_output_path = events_output_path
        self.evidence_dir = evidence_dir
        
        os.makedirs(self.evidence_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.events_output_path), exist_ok=True)

        # Khoi tao model YOLOv8 (chi tai 1 lan)
        print(f"[INFO] Dang khoi tao mo hinh YOLO: {model_name}...")
        self.model = YOLO(model_name)
        print("[INFO] Khoi tao YOLO hoan tat!")

    def load_config(self) -> Dict[str, Any]:
        """Doc file cau hinh camera."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def scan_camera(self, camera_id: str) -> List[Dict[str, Any]]:
        """
        Quet toan bo video cua mot camera, phat hien vi pham va ghi nhan su kien.
        """
        config = self.load_config()
        camera = next((c for c in config.get("cameras", []) if c["camera_id"] == camera_id), None)
        if not camera:
            raise ValueError(f"Camera ID not found in config: {camera_id}")

        video_path = camera["video_path"]
        if not os.path.exists(video_path):
            print(f"[WARNING] Video file does not exist: {video_path}")
            return []

        print(f"[INFO] Bat dau quet video: {video_path} (Camera: {camera_id})")
        reader = VideoReader(
            video_path=video_path,
            sample_fps=camera.get("fps_sample_rate", 1),
            virtual_start_time=camera.get("virtual_start_time", "14:05:00")
        )

        danger_zones = camera.get("danger_zones", [])
        if not danger_zones:
            print("[INFO] Camera khong co vung nguy hiem nao duoc cau hinh.")
            return []

        # Chuyen toa do polygon sang numpy array
        primary_zone = danger_zones[0]
        polygon_np = np.array(primary_zone["polygon"], dtype=np.int32)

        events: List[Dict[str, Any]] = []
        current_event: Optional[Dict[str, Any]] = None
        event_counter = 1

        for frame_data in reader.extract_frames():
            frame = frame_data["frame"]
            second = frame_data["second"]
            timestamp_str = frame_data["timestamp_str"]

            # Nhan dien nguoi (class 0: person trong tap COCO)
            results = self.model(frame, classes=[0], verbose=False)
            violating_boxes = []

            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    
                    # Toa do ban chan nguoi (diem giua day hop)
                    foot_point = (int((x1 + x2) / 2), int(y2))
                    
                    # Kiem tra diem ban chan co nam trong da giac nguy hiem khong
                    inside_dist = cv2.pointPolygonTest(polygon_np, foot_point, False)
                    if inside_dist >= 0:
                        violating_boxes.append({
                            "bbox": [x1, y1, x2, y2],
                            "confidence": round(conf, 2),
                            "foot_point": foot_point
                        })

            has_violation = len(violating_boxes) > 0

            # May trang thai theo doi su kien (Event Tracking)
            if has_violation:
                if current_event is None:
                    # Bat dau mot su kien vi pham moi
                    date_str = datetime.now().strftime("%Y%m%d")
                    event_id = f"EVT-{date_str}-{event_counter:03d}"
                    event_counter += 1

                    current_event = {
                        "event_id": event_id,
                        "camera_id": camera_id,
                        "location": camera.get("location", ""),
                        "zone_id": primary_zone.get("zone_id", ""),
                        "violation_type": "DANGER_ZONE_INTRUSION",
                        "violation_name": primary_zone.get("name", "Xam nhap vung nguy hiem"),
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "start_second": second,
                        "end_second": second,
                        "start_timestamp": timestamp_str,
                        "end_timestamp": timestamp_str,
                        "severity": primary_zone.get("severity", "HIGH"),
                        "best_frame": frame.copy(),
                        "best_boxes": violating_boxes,
                        "evidence_image": ""
                    }
                else:
                    # Su kien dang tiep dien -> cap nhat giay ket thuc
                    current_event["end_second"] = second
                    current_event["end_timestamp"] = timestamp_str
                    # Cap nhat frame net nhat
                    current_event["best_frame"] = frame.copy()
                    current_event["best_boxes"] = violating_boxes
            else:
                # Neu khong con vi pham ma dang co su kien mo -> Chot su kien
                if current_event is not None:
                    self._finalize_event(current_event, polygon_np, events)
                    current_event = None

        # Chot su kien neu van dang mo o cuoi video
        if current_event is not None:
            self._finalize_event(current_event, polygon_np, events)

        # Luu danh sach su kien vao file JSON
        self._save_events_to_file(events)
        print(f"[SUCCESS] Hoan tat quet video {camera_id}. Phat hien {len(events)} su kien vi pham.")
        return events

    def _finalize_event(
        self,
        event: Dict[str, Any],
        polygon_np: np.ndarray,
        events_list: List[Dict[str, Any]]
    ) -> None:
        """Xu ly anh bang chung va them su kien vao danh sach."""
        duration = event["end_second"] - event["start_second"] + 1
        event["duration_seconds"] = duration
        event["description"] = (
            f"Phat hien nguoi di bo xam nhap {event['violation_name']} "
            f"trong {duration} giay (tu {event['start_timestamp']} den {event['end_timestamp']})"
        )

        # Ve anh bang chung
        best_frame = event.pop("best_frame")
        best_boxes = event.pop("best_boxes")
        evidence_filename = f"{event['event_id']}.jpg"
        evidence_path = os.path.join(self.evidence_dir, evidence_filename)

        annotated_frame = self._draw_annotations(
            best_frame, polygon_np, best_boxes, event["start_timestamp"], event["event_id"]
        )
        cv2.imwrite(evidence_path, annotated_frame)
        event["evidence_image"] = f"storage/evidence/{evidence_filename}"
        event["status"] = "UNRESOLVED"

        events_list.append(event)
        print(f"[EVENT] Ghi nhan su kien: {event['event_id']} ({event['description']})")

    def _draw_annotations(
        self,
        frame: np.ndarray,
        polygon_np: np.ndarray,
        boxes: List[Dict[str, Any]],
        timestamp_str: str,
        event_id: str
    ) -> np.ndarray:
        """Ve vung da giac do phat sang va bounding box len anh bang chung."""
        output = frame.copy()
        
        # 1. Ve lop phu vung da giac mau do trong suot (Overlay)
        overlay = output.copy()
        cv2.fillPoly(overlay, [polygon_np], (0, 0, 255))
        cv2.addWeighted(overlay, 0.35, output, 0.65, 0, output)
        
        # 2. Ve vien da giac do day
        cv2.polylines(output, [polygon_np], isClosed=True, color=(0, 0, 255), thickness=3)

        # 3. Ve hop khoanh nguoi vi pham
        for b in boxes:
            x1, y1, x2, y2 = b["bbox"]
            conf = b["confidence"]
            # Hop do
            cv2.rectangle(output, (x1, y1), (x2, y2), (0, 0, 255), 3)
            # Nhan canh bao
            label = f"VIOLATION: INTRUSION ({conf*100:.0f}%)"
            cv2.rectangle(output, (x1, max(0, y1 - 25)), (x1 + 250, y1), (0, 0, 255), -1)
            cv2.putText(output, label, (x1 + 5, y1 - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
            # Cham chan nguoi
            fx, fy = b["foot_point"]
            cv2.circle(output, (fx, fy), 6, (0, 255, 255), -1)

        # 4. Banner OSD tren dau anh bang chung
        h, w = output.shape[:2]
        cv2.rectangle(output, (0, 0), (w, 40), (20, 20, 20), -1)
        banner_text = f"[EVIDENCE] {event_id} | TIME: {timestamp_str} | SEVERITY: CRITICAL"
        cv2.putText(output, banner_text, (15, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return output

    def _save_events_to_file(self, new_events: List[Dict[str, Any]]) -> None:
        """Ghi danh sach su kien vao file storage/events/events.json."""
        existing_events = []
        if os.path.exists(self.events_output_path):
            try:
                with open(self.events_output_path, "r", encoding="utf-8") as f:
                    existing_events = json.load(f)
            except Exception:
                existing_events = []

        # Cap nhat su kien theo event_id
        existing_ids = {e["event_id"] for e in existing_events}
        for ev in new_events:
            if ev["event_id"] not in existing_ids:
                existing_events.append(ev)

        with open(self.events_output_path, "w", encoding="utf-8") as f:
            json.dump(existing_events, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print("[TEST] Khoi chay thu nghiem module VideoScanner...")
    scanner = VideoScanner()
    # Quet thu camera CAM-03
    events = scanner.scan_camera("CAM-03")
    print(f"[TEST] Ket qua quet: {len(events)} su kien.")
