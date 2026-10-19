"""
Script view_db.py:
In toan bo du lieu cac bang trong Database SQLite (storage/cctv_warehouse.db) ra man hinh.
"""

import sys
from pathlib import Path

# Dam bao import duoc package src
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.db_manager import db_manager


def display_table(title: str, headers: list, rows: list):
    print("\n" + "=" * 90)
    print(f" {title} (Tong cong: {len(rows)} dong)")
    print("=" * 90)
    
    if not rows:
        print("  (Chua co du lieu)")
        return

    # In header
    header_line = " | ".join(f"{h:<16}" for h in headers)
    print(header_line)
    print("-" * 90)

    # In tung row
    for r in rows:
        row_str = " | ".join(f"{str(r.get(h, ''))[:16]:<16}" for h in headers)
        print(row_str)


def main():
    print("\n>>> DANG KET NOI CO SO DU LIEU: storage/cctv_warehouse.db <<<")
    
    # 1. Thong ke tong quan
    stats = db_manager.get_summary_stats()
    print(f"-> So luong Camera : {stats['total_cameras']}")
    print(f"-> Tong so su kien : {stats['total_events']} (Chua xu ly: {stats['unresolved_events']})")

    # 2. Xem bang cameras
    cameras = db_manager.get_cameras()
    cam_headers = ["camera_id", "name", "location", "virtual_start_time"]
    display_table("BANG: CAMERAS", cam_headers, cameras)

    # 3. Xem bang events
    events = db_manager.query_events(limit=20)
    event_headers = ["event_id", "camera_id", "violation_type", "date", "start_timestamp", "duration_seconds", "severity", "status"]
    display_table("BANG: EVENTS (SU KIEN VI PHAM)", event_headers, events)

    print("\n" + "=" * 90)
    print("[CHI TIET SU KIEN MOI NHAT]:")
    if events:
        latest = events[0]
        print(f" - Ma su kien     : {latest['event_id']}")
        print(f" - Camera         : {latest['camera_id']} ({latest['location']})")
        print(f" - Thoi gian      : {latest['start_timestamp']} -> {latest['end_timestamp']} (Dai {latest['duration_seconds']}s)")
        print(f" - Loai vi pham   : {latest['violation_name']} ({latest['violation_type']})")
        print(f" - Anh bang chung : {latest['evidence_image']}")
        print(f" - Mo ta          : {latest['description']}")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    main()
