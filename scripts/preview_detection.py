"""
Script preview_detection.py:
Phat video truc quan thoi gian thuc tren man hinh:
  - Binh thuong: Vung cam vien XANH LA (An toan)
  - Khi co nguoi buoc vao: Vung cam doi sang DO RUC, khoanh hop do va phat co bao dong!
  - Dong thoi xuat video ra: storage/cctv_videos/dock_boc_do_preview.mp4

Phim tat khi xem:
  - Phim SPACE: Tam dung / Tiep tuc
  - Phim 'Q' hoac ESC: Thoat
"""

import cv2
import json
import os
import numpy as np
from datetime import datetime, timedelta
from ultralytics import YOLO


def run_preview(
    config_path: str = "config/cameras.json",
    camera_id: str = "CAM-03",
    save_output: bool = True
):
    if not os.path.exists(config_path):
        print(f"[ERROR] Khong tim thay config: {config_path}")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    camera = next((c for c in config.get("cameras", []) if c["camera_id"] == camera_id), None)
    if not camera:
        print(f"[ERROR] Khong tim thay camera {camera_id}")
        return

    video_path = camera["video_path"]
    if not os.path.exists(video_path):
        print(f"[ERROR] Khong tim thay video: {video_path}")
        return

    polygon_pts = camera["danger_zones"][0]["polygon"]
    polygon_np = np.array(polygon_pts, dtype=np.int32)
    zone_name = camera["danger_zones"][0].get("name", "VUNG NGUY HIEM")

    print("[INFO] Dang khoi tao YOLOv8...")
    model = YOLO("yolov8n.pt")

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    base_time = datetime.strptime(camera.get("virtual_start_time", "14:05:00"), "%H:%M:%S")

    out_writer = None
    if save_output:
        out_dir = "storage/cctv_videos"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "dock_boc_do_preview.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
        print(f"[INFO] Video ket qua se duoc luu tai: {out_path}")

    window_name = "CCTV AI MONITOR - [LIVE FEED & DANGER DETECTION] (SPACE: Pause | Q: Thoat)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)

    print("=============================================================")
    print("[INFO] DANG PHAT VIDEO TRUC QUAN TREN MAN HINH...")
    print(" - Xem truc tiep tren cua so pop-up.")
    print(" - Phim SPACE de Tam dung / Xem tiep.")
    print(" - Phim Q de Thoat.")
    print("=============================================================")

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        elapsed_sec = frame_count / fps
        cur_time = (base_time + timedelta(seconds=elapsed_sec)).strftime("%H:%M:%S")

        # Nhan dien nguoi (class 0)
        results = model(frame, classes=[0], verbose=False)
        violating_boxes = []

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                foot_point = (int((x1 + x2) / 2), int(y2))

                # Kiem tra buoc chan nam trong da giac
                if cv2.pointPolygonTest(polygon_np, foot_point, False) >= 0:
                    violating_boxes.append((x1, y1, x2, y2, conf, foot_point))

        has_violation = len(violating_boxes) > 0

        # 1. Ve lop phu vung da giac
        overlay = frame.copy()
        if has_violation:
            # Vi pham: Mau DO ruc
            zone_color = (0, 0, 255)
            alpha = 0.35
            cv2.fillPoly(overlay, [polygon_np], zone_color)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            cv2.polylines(frame, [polygon_np], isClosed=True, color=zone_color, thickness=3)
        else:
            # Binh thuong: Mau XANH LA nhe
            zone_color = (0, 255, 0)
            alpha = 0.15
            cv2.fillPoly(overlay, [polygon_np], zone_color)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            cv2.polylines(frame, [polygon_np], isClosed=True, color=zone_color, thickness=2)

        # 2. Ve nhan tren vung cam
        p_top = polygon_pts[0]
        label_zone = f"[{zone_name}]" if not has_violation else f"[⚠️ {zone_name} - VI PHAM!]"
        cv2.putText(frame, label_zone, (p_top[0] - 20, p_top[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, zone_color, 2)

        # 3. Ve nguoi vi pham
        for (x1, y1, x2, y2, conf, foot_point) in violating_boxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            # Label
            tag = f"DANGER INTRUSION ({conf*100:.0f}%)"
            cv2.rectangle(frame, (x1, max(0, y1 - 25)), (x1 + 250, y1), (0, 0, 255), -1)
            cv2.putText(frame, tag, (x1 + 5, y1 - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
            # Diem tiep xuc chan
            cv2.circle(frame, foot_point, 6, (0, 255, 255), -1)

        # 4. Banner OSD Camera o tren dau
        cv2.rectangle(frame, (0, 0), (width, 45), (20, 20, 20), -1)
        osd_left = f"{camera['camera_id']} | {camera['name']} | TIME: {cur_time} [LIVE]"
        cv2.putText(frame, osd_left, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 5. Co bao dong nhap nhay khi co vi pham
        if has_violation:
            alarm_text = "🚨 CANH BAO: CO NGUOI BUOC VAO VUNG NGUY HIEM!"
            cv2.rectangle(frame, (0, height - 50), (width, height), (0, 0, 220), -1)
            cv2.putText(frame, alarm_text, (int(width/2) - 350, height - 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2)

        if out_writer:
            out_writer.write(frame)

        cv2.imshow(window_name, frame)
        frame_count += 1

        key = cv2.waitKey(int(1000 / fps)) & 0xFF
        if key in [ord('q'), ord('Q'), 27]:
            print("[INFO] Da dung xem preview.")
            break
        elif key == 32:  # Phim SPACE: Pause
            cv2.waitKey(0)

    cap.release()
    if out_writer:
        out_writer.release()
        print(f"[SUCCESS] Da luu xong video demo tai: storage/cctv_videos/dock_boc_do_preview.mp4")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_preview()
