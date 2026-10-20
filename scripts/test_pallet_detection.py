"""
Script kiem tra nhan dien Pallet tren video VatCanChanLoiDiXeNang.mp4 bang YOLO-World.
"""

import cv2
import os
from pathlib import Path
from ultralytics import YOLO

def main():
    video_path = "data/videos/VatCanChanLoiDiXeNang.mp4"
    output_image = "storage/evidence/test_pallet_detected.jpg"
    os.makedirs(os.path.dirname(output_image), exist_ok=True)

    print(f"[1] Dang load model YOLO-World...")
    model = YOLO("yolov8s-worldv2.pt")
    
    # Thiet lap cac lop can phat hien
    classes = ["wooden pallet", "pallet", "box", "crate", "forklift"]
    model.set_classes(classes)
    print(f"    Cac lop duoc thiet lap: {classes}")

    print(f"[2] Dang doc video {video_path}...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Khong the mo video {video_path}")
        return

    # Doc frame tai khoang giay thu 1 (frame 25-30)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps * 2))
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print("Error: Khong the doc frame!")
        return

    print(f"[3] Dang chay nhan dien tren frame...")
    results = model(frame, conf=0.10, verbose=False)
    
    detections = []
    annotated_frame = frame.copy()

    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            cls_name = model.names.get(cls_id, str(cls_id))
            
            detections.append({
                "class": cls_name,
                "confidence": round(conf, 2),
                "box": [x1, y1, x2, y2]
            })

            # Ve bounding box len anh
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
            label = f"{cls_name} {conf:.2f}"
            cv2.putText(annotated_frame, label, (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imwrite(output_image, annotated_frame)
    print(f"[4] Da luu anh ket qua vao: {output_image}")
    print(f"    So vat the nhan dien duoc: {len(detections)}")
    for d in detections:
        print(f"    - {d['class']}: {d['confidence']} tai {d['box']}")

if __name__ == "__main__":
    main()
