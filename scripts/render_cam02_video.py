"""
Module render_cam02_video.py:
Render video giam sat Han Lang Thoat Hiem (CAM-02) chuyen nghiep:
  - Ve vung da giac ranh gioi loi thoat hiem (Xanh la khi an toan -> Do ruc khi bi chan)
  - Khoanh Bounding Box cong nghe kem label [VAT CAN PCCC] quanh ghe/chuong ngai vat
  - Thanh HUD giam sat OSD (gio thuc te, trang thai canh bao)
  - Xuat chuan H.264 (yuv420p) bang PyAV de phat truc tiep muot ma tren Web Dashboard.
"""

import os
import sys
import json
import cv2
import av
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def render_session_video(
    model: YOLO,
    input_video_path: str,
    output_video_path: str,
    start_time_str: str,
    date_str: str,
    polygon_pts: np.ndarray,
    session_title: str
):
    if not os.path.exists(input_video_path):
        print(f"[ERROR] Video dau vao khong ton tai: {input_video_path}")
        return

    cap = cv2.VideoCapture(input_video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps

    print(f"\n=======================================================")
    print(f"[RENDER] {session_title}")
    print(f"  Input : {input_video_path} ({width}x{height} | {fps:.1f} fps | {total_frames} frames | {duration_sec:.1f}s)")
    print(f"  Output: {output_video_path}")
    print(f"=======================================================")

    Path(output_video_path).parent.mkdir(parents=True, exist_ok=True)

    # Khoi tao PyAV Container xuat chuan H.264 (yuv420p) tuong thich 100% moi trinh duyet
    container = av.open(output_video_path, mode="w")
    stream = container.add_stream("libx264", rate=int(round(fps)))
    stream.width = width
    stream.height = height
    stream.pix_fmt = "yuv420p"
    stream.options = {"crf": "23", "preset": "fast"}

    base_time = datetime.strptime(start_time_str, "%H:%M:%S")

    OBSTACLE_CLASSES = ["chair", "couch", "box", "suitcase", "backpack", "bench", "bed"]

    frame_idx = 0
    recent_obstacles = []
    
    # Bo nho dem de lam min (smoothing) bounding box
    active_boxes = []

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        current_second = frame_idx / fps
        current_time = base_time + timedelta(seconds=int(current_second))
        time_str = current_time.strftime("%H:%M:%S")

        # 1. Chay YOLOv8 nhan dien tren frame goc
        results = model(frame, conf=0.35, verbose=False)
        detected_obstacles = []

        for r in results:
            for b in r.boxes:
                cls_id = int(b.cls[0])
                cls_name = model.names.get(cls_id, "obstacle")
                conf = float(b.conf[0])
                x1, y1, x2, y2 = map(int, b.xyxy[0])
                bw, bh = x2 - x1, y2 - y1

                if cls_name.lower() in OBSTACLE_CLASSES:
                    cx = (x1 + x2) // 2
                    cy = int(y1 + bh * 0.65)

                    # Kiem tra diem tam nam trong ranh gioi da giac loi thoat hiem
                    if cv2.pointPolygonTest(polygon_pts, (float(cx), float(cy)), False) >= 0 and bw > 40 and bh > 40:
                        detected_obstacles.append({
                            "bbox": [x1, y1, x2, y2],
                            "conf": conf,
                            "label": cls_name.upper()
                        })

        has_violation = (len(detected_obstacles) > 0)

        # 2. Ve VUNG DA GIAC RANH GIOI LOI THOAT HIEM
        # Mau: Xanh la (An toan) hoac Do ruc (Bi vat can chan)
        overlay = frame.copy()
        if has_violation:
            zone_color = (0, 0, 220)      # Do ruc canh bao
            border_color = (0, 0, 255)
            status_text = "CANH BAO: BI CHAN LOI THOAT HIEM"
            alpha = 0.28
        else:
            zone_color = (0, 180, 0)      # Xanh la an toan
            border_color = (0, 255, 120)
            status_text = "LOI THOAT HIEM THONG THOANG"
            alpha = 0.18

        cv2.fillPoly(overlay, [polygon_pts], zone_color)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        cv2.polylines(frame, [polygon_pts], isClosed=True, color=border_color, thickness=3)

        # 3. Ve Bounding Box cong nghe quanh vat can
        for obs in detected_obstacles:
            ox1, oy1, ox2, oy2 = obs["bbox"]
            ow, oh = ox2 - ox1, oy2 - oy1

            # Khung chu nhat do
            cv2.rectangle(frame, (ox1, oy1), (ox2, oy2), (0, 0, 255), 3)

            # 4 goc cong nghe HUD
            clen = min(15, ow // 3)
            cv2.line(frame, (ox1, oy1), (ox1 + clen, oy1), (0, 255, 255), 3)
            cv2.line(frame, (ox1, oy1), (ox1, oy1 + clen), (0, 255, 255), 3)
            cv2.line(frame, (ox2, oy2), (ox2 - clen, oy2), (0, 255, 255), 3)
            cv2.line(frame, (ox2, oy2), (ox2, oy2 - clen), (0, 255, 255), 3)

            # Label tren dau vat the
            lbl = f"VAT CAN PCCC: {obs['label']} {obs['conf']*100:.0f}%"
            (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            label_y = max(oy1 - 6, th + 10)
            cv2.rectangle(frame, (ox1, label_y - th - 8), (ox1 + tw + 12, label_y + 4), (0, 0, 200), -1)
            cv2.putText(frame, lbl, (ox1 + 6, label_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        # 4. Thanh HUD OSD tren cung man hinh
        cv2.rectangle(frame, (0, 0), (width, 54), (18, 22, 28), -1)
        hud_line_color = (0, 0, 255) if has_violation else (0, 200, 100)
        cv2.line(frame, (0, 54), (width, 54), hud_line_color, 2)

        # Tieu de camera & ngay gio
        cv2.putText(frame, "CAM-02 | HANH LANG & CUA THOAT HIEM PCCC", (20, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        clock_str = f"NGAY: {date_str}  {time_str}"
        cv2.putText(frame, clock_str, (width - 340, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.60, (0, 255, 255), 2)

        # Badge trang thai giua man hinh
        if has_violation:
            badge_text = "🚨 [VI PHAM PCCC: VAT CAN CHAN LOI]"
            badge_color = (0, 0, 220)
        else:
            badge_text = "🟢 [AN TOAN: KHONG CO VAT CAN]"
            badge_color = (0, 150, 0)

        (bw, bh), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        bx = (width - bw) // 2
        cv2.rectangle(frame, (bx - 8, 12), (bx + bw + 8, 44), badge_color, -1)
        cv2.putText(frame, badge_text, (bx, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        # Ghi frame vao PyAV stream
        av_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
        for packet in stream.encode(av_frame):
            container.mux(packet)

        frame_idx += 1
        if frame_idx % int(round(fps * 5)) == 0:
            pct = (frame_idx / total_frames) * 100
            print(f"  -> Rendered {frame_idx}/{total_frames} frames ({pct:.0f}%) | {current_second:.0f}s")

    # Flush stream
    for packet in stream.encode():
        container.mux(packet)
    container.close()
    cap.release()
    print(f"[SUCCESS] Hoan tat render: {output_video_path}")


def main():
    config_path = PROJECT_ROOT / "config" / "cameras.json"
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    cam_02 = next((c for c in cfg.get("cameras", []) if c["camera_id"] == "CAM-02"), None)
    if not cam_02:
        print("[ERROR] Khong tim thay CAM-02!")
        return

    polygon_pts = np.array(cam_02["danger_zones"][0]["polygon"], dtype=np.int32)
    print(f"[INFO] Toa do ranh gioi CAM-02:\n{polygon_pts.tolist()}")

    model_path = PROJECT_ROOT / "yolov8n.pt"
    print(f"[INFO] Khoi tao YOLO tu {model_path}...")
    model = YOLO(str(model_path))

    output_dir = PROJECT_ROOT / "storage" / "cctv_videos"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Render Video 1 (Hom qua: 2026-10-20)
    render_session_video(
        model=model,
        input_video_path=str(PROJECT_ROOT / "data" / "videos" / "vat_can_chan_duong_di_thoat_hiem_1.mp4"),
        output_video_path=str(output_dir / "hanh_lang_thoat_hiem_preview_1.mp4"),
        start_time_str="10:30:00",
        date_str="2026-10-20",
        polygon_pts=polygon_pts,
        session_title="VIDEO 1 (HOM QUA: 2026-10-20 - 10:30:00)"
    )

    # 2. Render Video 2 (Hom nay: 2026-10-21)
    render_session_video(
        model=model,
        input_video_path=str(PROJECT_ROOT / "data" / "videos" / "vat_can_chan_duong_di_thoat_hiem_2.mp4"),
        output_video_path=str(output_dir / "hanh_lang_thoat_hiem_preview_2.mp4"),
        start_time_str="14:15:00",
        date_str="2026-10-21",
        polygon_pts=polygon_pts,
        session_title="VIDEO 2 (HOM NAY: 2026-10-21 - 14:15:00)"
    )

    print("\n=======================================================")
    print("[ALL DONE] Da xuat xong 2 video preview kem vung ranh gioi va khoanh vat can!")
    print("  1. storage/cctv_videos/hanh_lang_thoat_hiem_preview_1.mp4")
    print("  2. storage/cctv_videos/hanh_lang_thoat_hiem_preview_2.mp4")
    print("=======================================================")


if __name__ == "__main__":
    main()
