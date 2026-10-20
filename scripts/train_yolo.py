"""
Script train_yolo.py:
Huan luyen mo hinh YOLOv8 Nano tren tap du lieu da tu dong tao.
Moi truong: PyTorch + Ultralytics
Dau ra: weights/pallet_forklift_yolo.pt
"""

import os
from pathlib import Path
from ultralytics import YOLO

def main():
    data_yaml = Path("dataset/data.yaml").resolve()
    if not data_yaml.exists():
        print(f"[ERROR] Khong tim thay {data_yaml}!")
        return

    weights_dir = Path("weights")
    weights_dir.mkdir(parents=True, exist_ok=True)
    target_weights = weights_dir / "pallet_forklift_yolo.pt"

    print("[1] Khoi tao YOLOv8 Nano base model (yolov8n.pt)...")
    model = YOLO("yolov8n.pt")

    print(f"[2] Bat dau qua trinh huan luyen tren {data_yaml}...")
    results = model.train(
        data=str(data_yaml),
        epochs=15,
        imgsz=640,
        batch=4,
        workers=0,  # Windows safe
        project="runs/detect",
        name="pallet_forklift_train",
        exist_ok=True,
        verbose=True
    )

    # Copy file best.pt ra thu muc weights
    best_pt = Path("runs/detect/pallet_forklift_train/weights/best.pt")
    if best_pt.exists():
        import shutil
        shutil.copy(best_pt, target_weights)
        print(f"[SUCCESS] Huan luyen hoan tat! Model da luu tai: {target_weights}")
    else:
        print("[WARNING] Khong tim thay file best.pt sau khi train.")

if __name__ == "__main__":
    main()
