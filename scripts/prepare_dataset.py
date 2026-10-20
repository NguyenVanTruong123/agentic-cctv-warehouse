"""
Script prepare_dataset.py:
Trich xuat cac khung hinh mau tu vatcanchanduongxenang.mp4 va tu dong tao nhan YOLO.
Lop 0: pallet (vat can)
Lop 1: forklift (phuong tien xe nang)
"""

import os
import cv2
import numpy as np
from pathlib import Path

def main():
    video_path = "data/videos/vatcanchanduongxenang.mp4"
    if not os.path.exists(video_path):
        print(f"[ERROR] Video khong ton tai: {video_path}")
        return

    base_dir = Path("dataset")
    img_train = base_dir / "images" / "train"
    img_val = base_dir / "images" / "val"
    lbl_train = base_dir / "labels" / "train"
    lbl_val = base_dir / "labels" / "val"

    for d in [img_train, img_val, lbl_train, lbl_val]:
        d.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"[INFO] Doc video {video_path} ({w}x{h}, {total_frames} frames)...")

    # Danh sach cac moc thoi gian trich xuat frame (tinh bang giay)
    # Bao gom: pallet tinh tren san, xe nang tiep can, xe nang nang pallet, va nhieu mau san trong (background)
    time_points = [
        0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, # Pallet tinh tren san + xe nang o duoi
        4.8, 5.5, 6.2, 7.0, 8.0, 9.5, 11.0,     # Xe nang tiep can va nang pallet
        16.0, 20.0, 24.0, 28.0, 32.0, 36.0, 42.0, 48.0 # San trong (Background negative samples)
    ]

    extracted_samples = []

    for idx, sec in enumerate(time_points):
        f_pos = int(sec * fps)
        if f_pos >= total_frames:
            continue
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_pos)
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 1. Tim Xe nang qua mau Cyan cua than xe
        cyan_mask = cv2.inRange(hsv, np.array([90, 100, 90]), np.array([120, 255, 255]))
        cyan_cnts, _ = cv2.findContours(cyan_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        fl_box = None
        for cc in cyan_cnts:
            if cv2.contourArea(cc) > 500:
                fx, fy, fw, fh = cv2.boundingRect(cc)
                fl_box = (max(0, fx - 10), max(0, fy - 120), fw + 20, fh + 125)
                break

        # 2. Tim Pallet go qua mau go cam (H: 10-24, S: 50-255, V: 60-240)
        lower_wood = np.array([9, 50, 60])
        upper_wood = np.array([25, 255, 240])
        pallet_mask = cv2.inRange(hsv, lower_wood, upper_wood)
        close_k = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        pallet_closed = cv2.morphologyEx(pallet_mask, cv2.MORPH_CLOSE, close_k)

        # Neu xe nang chua toi pallet (sec <= 4.0), loai bo vung xe nang
        if fl_box and sec <= 4.0:
            bx, by, bw, bh = fl_box
            cv2.rectangle(pallet_closed, (bx, by), (bx + bw, by + bh), 0, -1)

        pallet_cnts, _ = cv2.findContours(pallet_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        pal_box = None
        for pc in pallet_cnts:
            area = cv2.contourArea(pc)
            px, py, pw, ph = cv2.boundingRect(pc)
            # Chi lay pallet o khu vuc hanh lang chinh
            if 700 <= px <= 1250 and 400 <= py <= 650 and area > 1000:
                pal_box = (px, py, pw, ph)
                break

        labels = []
        # Lop 0: pallet (chuan YOLO: class x_center y_center w h)
        if pal_box and sec <= 8.5:
            px, py, pw, ph = pal_box
            xc = (px + pw / 2) / w
            yc = (py + ph / 2) / h
            nw = pw / w
            nh = ph / h
            labels.append(f"0 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}")

        # Lop 1: forklift
        if fl_box:
            fx, fy, fw, fh = fl_box
            xc = (fx + fw / 2) / w
            yc = (fy + fh / 2) / h
            nw = fw / w
            nh = fh / h
            labels.append(f"1 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}")

        # Phan chia train (80%) va val (20%)
        is_val = (idx % 5 == 0)
        target_img_dir = img_val if is_val else img_train
        target_lbl_dir = lbl_val if is_val else lbl_train

        fname = f"frame_{idx:03d}_{int(sec*1000)}ms"
        img_out = str(target_img_dir / f"{fname}.jpg")
        lbl_out = str(target_lbl_dir / f"{fname}.txt")

        cv2.imwrite(img_out, frame)
        with open(lbl_out, "w", encoding="utf-8") as f:
            f.write("\n".join(labels))

        extracted_samples.append({
            "name": fname,
            "split": "val" if is_val else "train",
            "pallet": bool(pal_box and sec <= 8.5),
            "forklift": bool(fl_box)
        })

    cap.release()

    # Tao file cau hinh data.yaml
    yaml_content = f"""path: {os.path.abspath(str(base_dir)).replace(chr(92), '/')}
train: images/train
val: images/val

names:
  0: pallet
  1: forklift
"""
    with open(base_dir / "data.yaml", "w", encoding="utf-8") as f:
        f.write(yaml_content)

    print(f"[SUCCESS] Da tao xong tap dataset gom {len(extracted_samples)} anh tai {base_dir}!")
    print(f" - data.yaml da tao tai {base_dir / 'data.yaml'}")
    train_count = sum(1 for s in extracted_samples if s["split"] == "train")
    val_count = sum(1 for s in extracted_samples if s["split"] == "val")
    print(f" - Train images: {train_count} | Val images: {val_count}")

if __name__ == "__main__":
    main()
