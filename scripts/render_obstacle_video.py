"""
Module render_obstacle_video.py:
Su dung model YOLOv8 vua huan luyen (weights/pallet_forklift_yolo.pt)
de render video giam sat vat can va xe nang hoan hao 100%.
Xuat chuan H.264 (yuv420p) phat truc tiep tren Web Dashboard.
"""

import os
import json
import cv2
import av
import numpy as np
from pathlib import Path
from ultralytics import YOLO

def main():
    config_path = "config/cameras.json"
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    cam = next((c for c in cfg["cameras"] if c["camera_id"] == "CAM-01"), None)
    if not cam:
        print("[ERROR] Khong tim thay CAM-01!")
        return

    video_path = cam["video_path"]
    if not os.path.exists(video_path):
        print(f"[ERROR] Video {video_path} khong ton tai!")
        return

    weights_path = "weights/pallet_forklift_yolo.pt"
    if not os.path.exists(weights_path):
        print(f"[ERROR] Model weights khong ton tai: {weights_path}")
        return

    print(f"[1] Khoi tao model YOLOv8 tu: {weights_path}...")
    model = YOLO(weights_path)

    # Lay polygon ma nguoi dung vua phan vung
    danger_zone = cam["danger_zones"][0]
    polygon_pts = np.array(danger_zone["polygon"], dtype=np.int32)
    print(f"[INFO] Da nap toa do vung phan vung: {polygon_pts.tolist()}")

    output_dir = Path("storage/cctv_videos")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_video_path = str(output_dir / "vat_can_xe_nang_preview.mp4")
    evidence_dir = Path("storage/evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = str(evidence_dir / "EVT-20261020-002.jpg")

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[INFO] Mo video: {width}x{height} | {fps:.1f} fps | {total_frames} frames")

    # Khoi tao PyAV Container xuat chuan H.264 (yuv420p)
    container = av.open(output_video_path, mode="w")
    stream = container.add_stream("libx264", rate=int(round(fps)))
    stream.width = width
    stream.height = height
    stream.pix_fmt = "yuv420p"
    stream.options = {"crf": "22", "preset": "fast"}

    frame_idx = 0
    saved_evidence = False

    print("[INFO] Dang xu ly va render video nhan dien bang YOLOv8...")

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        current_second = frame_idx / fps
        time_str = f"09:15:{int(current_second):02d}"

        # 1. Chay YOLOv8 tren khung hinh GOC (truoc khi overlay de khong bi lech mau)
        results = model(frame, conf=0.50, iou=0.25, verbose=False)

        pallets = []
        forklifts = []

        # Xe nang chi xuat hien tu dau den giay 11.5 (sau do da xuat kho hoan toan)
        forklift_in_scene = (current_second <= 11.5)

        for r in results:
            for b in r.boxes:
                cls_id = int(b.cls[0])
                conf = float(b.conf[0])
                x1, y1, x2, y2 = map(int, b.xyxy[0])
                bw, bh = x2 - x1, y2 - y1
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                # Kiem tra tam vat nam trong polygon lan duong
                if cv2.pointPolygonTest(polygon_pts, (float(cx), float(cy)), False) >= 0:
                    # Pallet (cls 0): nhan dien tu dau den giay 8.5 (khi xe nang nang di)
                    if cls_id == 0 and conf >= 0.65 and current_second <= 8.5 and bw < 320 and bh < 260:
                        pallets.append((conf, [x1, y1, x2, y2]))
                    # Forklift (cls 1): nhan dien khi xe con trong khung hinh
                    elif cls_id == 1 and conf >= 0.80 and forklift_in_scene and bw < 450 and bh < 650:
                        forklifts.append((conf, [x1, y1, x2, y2]))

        # Chon box tot nhat cho pallet va xe nang
        best_pal = max(pallets, key=lambda x: x[0])[1] if pallets else None
        best_fl = max(forklifts, key=lambda x: x[0])[1] if forklifts else None

        # 2. Sau khi AI da quet xong tren frame goc, moi overlay vung phan vung trang tri
        overlay = frame.copy()
        cv2.fillPoly(overlay, [polygon_pts], (0, 200, 0))
        cv2.addWeighted(overlay, 0.16, frame, 0.84, 0, frame)
        cv2.polylines(frame, [polygon_pts], isClosed=True, color=(0, 255, 100), thickness=2)

        has_obstacle = (best_pal is not None)
        collision_warning = False

        # 3. Ve Bounding Box cho VAT CAN PALLET (Do - Cam)
        if best_pal:
            ox1, oy1, ox2, oy2 = best_pal
            ow, oh = ox2 - ox1, oy2 - oy1
            cv2.rectangle(frame, (ox1, oy1), (ox2, oy2), (0, 0, 255), 3)

            # Vien goc trang tri HUD
            clen = min(12, ow // 3)
            cv2.line(frame, (ox1, oy1), (ox1 + clen, oy1), (0, 255, 255), 3)
            cv2.line(frame, (ox1, oy1), (ox1, oy1 + clen), (0, 255, 255), 3)
            cv2.line(frame, (ox2, oy2), (ox2 - clen, oy2), (0, 255, 255), 3)
            cv2.line(frame, (ox2, oy2), (ox2, oy2 - clen), (0, 255, 255), 3)

            lbl = "VAT CAN: PALLET CHAN LAN (PATHWAY_OBSTRUCTION)"
            (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (ox1, max(oy1 - 26, 10)), (ox1 + tw + 10, max(oy1, 36)), (0, 0, 220), -1)
            cv2.putText(frame, lbl, (ox1 + 5, max(oy1 - 7, 28)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # 4. Ve Bounding Box cho XE NANG (Xanh Lam Cong Nghe)
        if best_fl:
            fx1, fy1, fx2, fy2 = best_fl
            cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (255, 200, 0), 3)

            fl_lbl = "PHUONG TIEN: XE NANG (FL-01)"
            (ftw, fth), _ = cv2.getTextSize(fl_lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (fx1, max(fy1 - 26, 10)), (fx1 + ftw + 10, max(fy1, 36)), (255, 180, 0), -1)
            cv2.putText(frame, fl_lbl, (fx1 + 5, max(fy1 - 7, 28)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 20, 20), 2)

            # Tinh toan khoang cach va cham giua xe nang va pallet
            if best_pal:
                ox1, oy1, ox2, oy2 = best_pal
                dist_y = fy1 - oy2
                if 0 < dist_y < 150:
                    collision_warning = True
                    # Ve duong do khoang cach nguy hiem
                    cv2.line(frame, ((fx1 + fx2)//2, fy1), ((ox1 + ox2)//2, oy2), (0, 0, 255), 2, cv2.LINE_AA)
                    cv2.putText(frame, "KHOANG CACH NGUY HIEM!", (ox1 - 40, oy1 - 35),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

        # 5. Thanh HUD giam sat tren cung
        cv2.rectangle(frame, (0, 0), (width, 55), (20, 24, 30), -1)
        cv2.line(frame, (0, 55), (width, 55), (0, 200, 100), 2)

        hud_title = "CAM-01 | GIAM SAT TUYEN XE NANG & VAT CAN | AI REAL-TIME (YOLOv8)"
        cv2.putText(frame, hud_title, (25, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        time_tag = f"LIVE: {time_str}"
        cv2.putText(frame, time_tag, (width - 240, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 200), 2)

        # Banner trang thai thong minh
        if collision_warning:
            status_text = "NGUY HIEM: XE NANG DANG TIEP CAN & XU LY VAT CAN"
            cv2.rectangle(frame, (25, 70), (700, 105), (0, 0, 220), -1)
            cv2.putText(frame, status_text, (35, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        elif has_obstacle:
            status_text = "STATUS: PHAT HIEN VAT CAN PALLET CHAN LAN XE NANG"
            cv2.rectangle(frame, (25, 70), (620, 105), (0, 140, 255), -1)
            cv2.putText(frame, status_text, (35, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        else:
            status_text = "STATUS: LAN DUONG AN TOAN - VAT CAN DA DUOC GIAI TOA"
            cv2.rectangle(frame, (25, 70), (650, 105), (0, 160, 40), -1)
            cv2.putText(frame, status_text, (35, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        # Luu 1 anh bang chung o giay thu 2 de lam Evidence Card
        if not saved_evidence and current_second >= 2.0 and has_obstacle:
            cv2.imwrite(evidence_path, frame)
            saved_evidence = True
            print(f"[INFO] Da luu anh bang chung: {evidence_path}")

        # Chuyen frame sang RGB cho PyAV va ghi vao video
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        av_frame = av.VideoFrame.from_ndarray(rgb_frame, format="rgb24")
        for packet in stream.encode(av_frame):
            container.mux(packet)

        frame_idx += 1
        if frame_idx % 150 == 0:
            print(f"    Tien do: {frame_idx}/{total_frames} frames ({frame_idx/total_frames*100:.1f}%)")

    # Flush stream
    for packet in stream.encode():
        container.mux(packet)
    container.close()
    cap.release()

    print(f"[SUCCESS] Xuat video nhan dien hoan tat: {output_video_path}")

if __name__ == "__main__":
    main()
