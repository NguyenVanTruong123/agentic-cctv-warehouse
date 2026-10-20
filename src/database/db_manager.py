"""
Module DatabaseManager:
Quan ly Co so Du lieu SQLite (storage/cctv_warehouse.db).
Ho tro luu tru co cau truc, lap chi muc (Index) va truy van sieu toc (< 0.001s).
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


DB_PATH = "storage/cctv_warehouse.db"


class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Tao ket noi voi SQLite co bat Foreign Key va Row Factory tra ve Dict."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self) -> None:
        """Khoi tao cac bang du lieu va danh muc chi muc (Indexes)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Bang quan ly danh muc Loai Vi Pham (Violation Types)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS violation_types (
                violation_type TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                penalty TEXT,
                color_code TEXT DEFAULT '#EF4444',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 2. Bang quan ly danh muc Camera
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cameras (
                camera_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT,
                video_path TEXT,
                virtual_start_time TEXT DEFAULT '14:05:00',
                fps_sample_rate INTEGER DEFAULT 1,
                polygon_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 3. Bang quan ly Su kien Vi pham (Events)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                camera_id TEXT NOT NULL,
                location TEXT,
                zone_id TEXT,
                violation_type TEXT NOT NULL,
                violation_name TEXT,
                date TEXT NOT NULL,
                start_second INTEGER NOT NULL,
                end_second INTEGER NOT NULL,
                duration_seconds INTEGER NOT NULL,
                start_timestamp TEXT NOT NULL,
                end_timestamp TEXT NOT NULL,
                severity TEXT DEFAULT 'CRITICAL',
                evidence_image TEXT,
                description TEXT,
                status TEXT DEFAULT 'UNRESOLVED',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (camera_id) REFERENCES cameras(camera_id),
                FOREIGN KEY (violation_type) REFERENCES violation_types(violation_type)
            );
            """)

            # 4. Tao Indexes de tim kiem theo camera va ngay thang cuc nhanh
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_camera_date ON events(camera_id, date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_violation_type ON events(violation_type);")

            conn.commit()

        # Tu dong nap du lieu mau tu violations.json, cameras.json va events.json neu bang dang trong
        self._sync_from_json_files()

    def _sync_from_json_files(self) -> None:
        """Dong bo du lieu co san tu config va storage vao DB."""
        # 1. Sync violation types
        violations_path = "config/violations.json"
        if os.path.exists(violations_path):
            try:
                with open(violations_path, "r", encoding="utf-8") as f:
                    v_config = json.load(f)
                for vt in v_config.get("violation_types", []):
                    self.upsert_violation_type(vt)
            except Exception as e:
                print(f"[DB] Loi dong bo violations.json: {e}")

        # 2. Sync cameras
        config_path = "config/cameras.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                for cam in config.get("cameras", []):
                    polygon_str = json.dumps(cam.get("danger_zones", [{}])[0].get("polygon", []))
                    self.upsert_camera({
                        "camera_id": cam["camera_id"],
                        "name": cam["name"],
                        "location": cam.get("location", ""),
                        "video_path": cam.get("video_path", ""),
                        "virtual_start_time": cam.get("virtual_start_time", "14:05:00"),
                        "fps_sample_rate": cam.get("fps_sample_rate", 1),
                        "polygon_json": polygon_str
                    })
            except Exception as e:
                print(f"[DB] Loi dong bo cameras.json: {e}")

        # 3. Sync events
        events_path = "storage/events/events.json"
        if os.path.exists(events_path):
            try:
                with open(events_path, "r", encoding="utf-8") as f:
                    events = json.load(f)
                for ev in events:
                    self.insert_event(ev)
            except Exception as e:
                print(f"[DB] Loi dong bo events.json: {e}")

    def upsert_violation_type(self, v_type_data: Dict[str, Any]) -> None:
        """Them hoac cap nhat danh muc loai vi pham."""
        query = """
        INSERT INTO violation_types (violation_type, name, severity, description, penalty, color_code)
        VALUES (:violation_type, :name, :severity, :description, :penalty, :color_code)
        ON CONFLICT(violation_type) DO UPDATE SET
            name = excluded.name,
            severity = excluded.severity,
            description = excluded.description,
            penalty = excluded.penalty,
            color_code = excluded.color_code;
        """
        with self.get_connection() as conn:
            conn.execute(query, {
                "violation_type": v_type_data["violation_type"],
                "name": v_type_data["name"],
                "severity": v_type_data.get("severity", "MEDIUM"),
                "description": v_type_data.get("description", ""),
                "penalty": v_type_data.get("penalty", ""),
                "color_code": v_type_data.get("color_code", "#EF4444")
            })
            conn.commit()

    def get_violation_types(self) -> List[Dict[str, Any]]:
        """Lay danh sach tat ca cac loai vi pham quy dinh."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM violation_types ORDER BY severity ASC;")
            return [dict(row) for row in cursor.fetchall()]

    def upsert_camera(self, camera_data: Dict[str, Any]) -> None:
        """Them hoac cap nhat camera vao bang cameras."""
        query = """
        INSERT INTO cameras (camera_id, name, location, video_path, virtual_start_time, fps_sample_rate, polygon_json)
        VALUES (:camera_id, :name, :location, :video_path, :virtual_start_time, :fps_sample_rate, :polygon_json)
        ON CONFLICT(camera_id) DO UPDATE SET
            name = excluded.name,
            location = excluded.location,
            video_path = excluded.video_path,
            virtual_start_time = excluded.virtual_start_time,
            fps_sample_rate = excluded.fps_sample_rate,
            polygon_json = excluded.polygon_json;
        """
        with self.get_connection() as conn:
            conn.execute(query, camera_data)
            conn.commit()

    def insert_event(self, event_data: Dict[str, Any]) -> bool:
        """Them mot su kien vi pham moi vao bang events."""
        query = """
        INSERT OR IGNORE INTO events (
            event_id, camera_id, location, zone_id, violation_type, violation_name,
            date, start_second, end_second, duration_seconds, start_timestamp,
            end_timestamp, severity, evidence_image, description, status
        ) VALUES (
            :event_id, :camera_id, :location, :zone_id, :violation_type, :violation_name,
            :date, :start_second, :end_second, :duration_seconds, :start_timestamp,
            :end_timestamp, :severity, :evidence_image, :description, :status
        );
        """
        # Loai bo cac field phu neu co
        clean_data = {
            "event_id": event_data["event_id"],
            "camera_id": event_data["camera_id"],
            "location": event_data.get("location", ""),
            "zone_id": event_data.get("zone_id", ""),
            "violation_type": event_data["violation_type"],
            "violation_name": event_data.get("violation_name", ""),
            "date": event_data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "start_second": event_data["start_second"],
            "end_second": event_data["end_second"],
            "duration_seconds": event_data.get("duration_seconds", event_data["end_second"] - event_data["start_second"] + 1),
            "start_timestamp": event_data["start_timestamp"],
            "end_timestamp": event_data["end_timestamp"],
            "severity": event_data.get("severity", "CRITICAL"),
            "evidence_image": event_data.get("evidence_image", ""),
            "description": event_data.get("description", ""),
            "status": event_data.get("status", "UNRESOLVED")
        }
        with self.get_connection() as conn:
            cursor = conn.execute(query, clean_data)
            conn.commit()
            return cursor.rowcount > 0

    def query_events(
        self,
        camera_id: Optional[str] = None,
        date: Optional[str] = None,
        violation_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Truy van danh sach su kien theo nhieu tieu chi linh hoat."""
        conditions = []
        params = {}

        if camera_id:
            conditions.append("camera_id = :camera_id")
            params["camera_id"] = camera_id

        if date:
            conditions.append("date = :date")
            params["date"] = date

        if violation_type:
            conditions.append("violation_type = :violation_type")
            params["violation_type"] = violation_type

        if start_time:
            conditions.append("start_timestamp >= :start_time")
            params["start_time"] = start_time

        if end_time:
            conditions.append("end_timestamp <= :end_time")
            params["end_time"] = end_time

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
        SELECT * FROM events 
        WHERE {where_clause} 
        ORDER BY date DESC, start_timestamp DESC 
        LIMIT :limit;
        """
        params["limit"] = limit

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_cameras(self) -> List[Dict[str, Any]]:
        """Lay danh sach tat ca camera."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM cameras ORDER BY camera_id ASC;")
            return [dict(row) for row in cursor.fetchall()]

    def update_event_status(self, event_id: str, status: str) -> bool:
        """Cap nhat trang thai xu ly cua su kien (UNRESOLVED, RESOLVED, PENDING, IN_PROGRESS)."""
        clean_status = status.upper().strip()
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE events SET status = :status WHERE event_id = :event_id;",
                {"event_id": event_id, "status": clean_status}
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_summary_stats(self) -> Dict[str, Any]:
        """Thong ke tong quan so luong su kien trong he thong."""
        with self.get_connection() as conn:
            total_events = conn.execute("SELECT COUNT(*) FROM events;").fetchone()[0]
            unresolved = conn.execute("SELECT COUNT(*) FROM events WHERE status IN ('UNRESOLVED', 'NEW', 'PENDING');").fetchone()[0]
            cameras_count = conn.execute("SELECT COUNT(*) FROM cameras;").fetchone()[0]
            return {
                "total_events": total_events,
                "unresolved_events": unresolved,
                "total_cameras": cameras_count
            }


# Khoi tao singleton instance dung chung toan du an
db_manager = DatabaseManager()


if __name__ == "__main__":
    print("[TEST] Khoi tao Database thanh cong!")
    stats = db_manager.get_summary_stats()
    print("[TEST] Thong ke Database:", stats)
    events = db_manager.query_events()
    print(f"[TEST] So su kien tim thay: {len(events)}")
    for ev in events:
        safe_desc = ev['description'].encode('ascii', 'replace').decode('ascii')
        print(f"  -> [{ev['event_id']}] {ev['camera_id']} ({ev['start_timestamp']}): {safe_desc}")
