"""
Module VideoReader: Trích xuất khung hình từ video camera theo mốc thời gian.
Tối ưu hóa hiệu năng bằng kỹ thuật lấy mẫu (Frame Sampling - mặc định 1 FPS).
"""

import cv2
import os
from datetime import datetime, timedelta
from typing import Generator, Dict, Any, Optional


class VideoReader:
    def __init__(
        self,
        video_path: str,
        sample_fps: int = 1,
        virtual_start_time: str = "14:05:00"
    ):
        """
        Khởi tạo bộ đọc video.
        :param video_path: Đường dẫn tới file video (.mp4, .avi, ...)
        :param sample_fps: Tốc độ lấy mẫu (1 FPS = mỗi giây lấy 1 khung hình)
        :param virtual_start_time: Mốc giờ thực tế ban đầu (HH:MM:SS)
        """
        self.video_path = video_path
        self.sample_fps = max(1, sample_fps)
        self.virtual_start_time = virtual_start_time
        
        # Parse mốc giờ bắt đầu
        try:
            self.base_time = datetime.strptime(virtual_start_time, "%H:%M:%S")
        except ValueError:
            self.base_time = datetime.strptime("14:00:00", "%H:%M:%S")

    def get_video_info(self) -> Dict[str, Any]:
        """Lay thong so ky thuat cua video."""
        if not os.path.exists(self.video_path):
            return {"error": f"File not found: {self.video_path}"}
        
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            return {"error": f"Cannot open video file: {self.video_path}"}

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_sec = total_frames / fps if fps > 0 else 0
        cap.release()

        return {
            "video_path": self.video_path,
            "width": width,
            "height": height,
            "original_fps": round(fps, 2),
            "total_frames": total_frames,
            "duration_seconds": round(duration_sec, 2),
            "virtual_start_time": self.virtual_start_time
        }

    def extract_frames(self) -> Generator[Dict[str, Any], None, None]:
        """
        Generator trích xuất frame theo tần suất 1 FPS.
        Trả về dictionary gồm: frame ảnh, số giây hiện tại, mốc giờ thực tế.
        """
        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"Video file does not exist: {self.video_path}")

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video: {self.video_path}")

        original_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_interval = int(round(original_fps / self.sample_fps))
        if frame_interval <= 0:
            frame_interval = 1

        frame_count = 0
        second_counter = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Chỉ lấy frame ở mỗi khoảng cách thời gian (1 giây)
            if frame_count % frame_interval == 0:
                # Tính giờ thực tế hiển thị
                current_timestamp = (self.base_time + timedelta(seconds=second_counter)).strftime("%H:%M:%S")
                
                yield {
                    "second": second_counter,
                    "timestamp_str": current_timestamp,
                    "frame": frame,
                    "frame_index": frame_count
                }
                second_counter += 1

            frame_count += 1

        cap.release()


if __name__ == "__main__":
    # Test nhanh module
    print("[TEST] Module VideoReader san sang hoat dong!")
    reader = VideoReader("data/videos/dock_boc_do.mp4", sample_fps=1, virtual_start_time="14:05:00")
    print("[TEST] Thong so cau hinh:", reader.get_video_info())
