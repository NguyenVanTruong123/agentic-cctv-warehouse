"""
Script select_zone.py:
Cong cu click chuot truc quan de chon toa do Vung Nguy Hiem (Polygon Zone).
Tu dong luu toa do cac diem vao file config/cameras.json.

Phim tat:
  - Click chuot trai : Chon 1 diem
  - Phim 'S' hoac ENTER: Luu toa do vao cameras.json va thoat
  - Phim 'R'         : Xoa ve lai tu dau (Reset)
  - Phim 'Q' hoac ESC: Thoat khong luu
"""

import cv2
import json
import os
import argparse
import numpy as np

# Danh sach cac diem duoc click chuot
points = []
clean_frame = None
display_frame = None


def mouse_callback(event, x, y, flags, param):
    global points, clean_frame, display_frame

    if event == cv2.EVENT_LBUTTONDOWN:
        # Them diem vua click
        points.append([x, y])
        print(f"[POINT] Da chon diem {len(points)}: ({x}, {y})")

        # Cap nhat hinh anh hien thi
        display_frame = clean_frame.copy()

        # Ve cac diem da chon
        for i, pt in enumerate(points):
            cv2.circle(display_frame, tuple(pt), 6, (0, 0, 255), -1)
            cv2.putText(display_frame, f"P{i+1}", (pt[0] + 8, pt[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

        # Ve cac duong noi giua cac diem
        if len(points) > 1:
            pts_arr = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(display_frame, [pts_arr], isClosed=False, color=(0, 255, 0), thickness=2)

        # Neu da co tu 3 diem tro len, to mo vung da giac
        if len(points) >= 3:
            overlay = display_frame.copy()
            cv2.fillPoly(overlay, [np.array(points, dtype=np.int32)], (0, 0, 255))
            cv2.addWeighted(overlay, 0.25, display_frame, 0.75, 0, display_frame)

        cv2.imshow("CHON VUNG NGUY HIEM (Click 4 goc | 'S': Luu | 'R': Xoa lai | 'Q': Thoat)", display_frame)


def main():
    global clean_frame, display_frame, points

    parser = argparse.ArgumentParser(description="Chon vung nguy hiem bang chuot")
    parser.add_argument("--config", default="config/cameras.json", help="File cau hinh")
    parser.add_argument("--camera", default="CAM-03", help="Ma camera can cau hinh")
    parser.add_argument("--frame_sec", type=int, default=2, help="Lay frame o giay thu may")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"[ERROR] Khong tim thay file cau hinh: {args.config}")
        return

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    camera = next((c for c in config.get("cameras", []) if c["camera_id"] == args.camera), None)
    if not camera:
        print(f"[ERROR] Khong tim thay camera {args.camera} trong {args.config}")
        return

    video_path = camera.get("video_path", "")
    if not os.path.exists(video_path):
        print(f"[ERROR] Khong tim thay file video: {video_path}")
        return

    # Mo video va trich xuat frame
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    target_frame = int(args.frame_sec * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print("[ERROR] Khong the doc frame tu video.")
        return

    clean_frame = frame.copy()
    display_frame = frame.copy()

    # Ve huong dan tren anh
    guide_text = "Click chuot de chon cac goc cua Vung Cam | Phim 'S': Luu | 'R': Reset | 'Q': Thoat"
    cv2.rectangle(display_frame, (0, 0), (display_frame.shape[1], 40), (20, 20, 20), -1)
    cv2.putText(display_frame, guide_text, (20, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)

    window_name = "CHON VUNG NGUY HIEM (Click 4 goc | 'S': Luu | 'R': Xoa lai | 'Q': Thoat)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)
    cv2.setMouseCallback(window_name, mouse_callback)

    cv2.imshow(window_name, display_frame)

    print("=========================================================")
    print("[HUONG DAN] Cua so chon vung da mo tren man hinh!")
    print(" - Dung chuot trai click lan luot 4 goc cua Vung Can Canh Bao.")
    print(" - Nhan phim 'S' (hoac ENTER) de LUU toa do vao cameras.json.")
    print(" - Nhan phim 'R' neu click nham de ve lai tu dau.")
    print(" - Nhan phim 'Q' (hoac ESC) de thoat khong luu.")
    print("=========================================================")

    while True:
        key = cv2.waitKey(20) & 0xFF
        
        # Phim 'S' hoac ENTER: Luu
        if key in [ord('s'), ord('S'), 13]:
            if len(points) < 3:
                print("[WARNING] Vui long click it nhat 3 diem de tao thanh vung da giac!")
                continue

            # Luu vao config
            if "danger_zones" in camera and len(camera["danger_zones"]) > 0:
                camera["danger_zones"][0]["polygon"] = points
            else:
                camera["danger_zones"] = [{
                    "zone_id": "ZONE_DANGER_01",
                    "name": "Vung Nguy Hiem",
                    "polygon": points
                }]

            with open(args.config, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            print("---------------------------------------------------------")
            print(f"[SUCCESS] Da luu thanh cong {len(points)} diem vao {args.config}:")
            print(points)
            print("---------------------------------------------------------")
            break

        # Phim 'R': Reset
        elif key in [ord('r'), ord('R')]:
            points = []
            display_frame = clean_frame.copy()
            cv2.rectangle(display_frame, (0, 0), (display_frame.shape[1], 40), (20, 20, 20), -1)
            cv2.putText(display_frame, guide_text, (20, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
            cv2.imshow(window_name, display_frame)
            print("[RESET] Da xoa toan bo diem, hay click chon lai tu dau.")

        # Phim 'Q' hoac ESC: Thoat
        elif key in [ord('q'), ord('Q'), 27]:
            print("[CANCEL] Da thoat ma khong luu thay doi.")
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
