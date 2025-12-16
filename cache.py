"""
Caching module for storing commute time results in SQLite database.
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List


class CommuteCache:
    """Handles caching of commute time calculations."""

    def __init__(self, db_path: str = "commute_cache.db"):
        """Initialize the cache database."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create the database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commute_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    origin TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    travel_mode TEXT NOT NULL,
                    arrival_time TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    duration_in_traffic_seconds INTEGER,
                    distance_meters INTEGER NOT NULL,
                    query_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(origin, destination, travel_mode, arrival_time, query_date)
                )
            """)
            conn.commit()

    def get_cached_result(
        self,
        origin: str,
        destination: str,
        travel_mode: str,
        arrival_time: str,
        query_date: str
    ) -> Optional[Dict]:
        """
        Retrieve cached commute result if it exists.

        Args:
            origin: Starting location
            destination: Ending location
            travel_mode: Mode of transportation (driving, transit)
            arrival_time: Arrival time (HH:MM format)
            query_date: Date of the query (YYYY-MM-DD)

        Returns:
            Dictionary with commute data or None if not cached
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT duration_seconds, duration_in_traffic_seconds, distance_meters
                FROM commute_results
                WHERE origin = ? AND destination = ? AND travel_mode = ?
                    AND arrival_time = ? AND query_date = ?
            """, (origin, destination, travel_mode, arrival_time, query_date))

            row = cursor.fetchone()
            if row:
                return {
                    'duration_seconds': row[0],
                    'duration_in_traffic_seconds': row[1],
                    'distance_meters': row[2]
                }
            return None

    def save_result(
        self,
        origin: str,
        destination: str,
        travel_mode: str,
        arrival_time: str,
        query_date: str,
        duration_seconds: int,
        duration_in_traffic_seconds: Optional[int],
        distance_meters: int
    ):
        """
        Save a commute result to the cache.

        Args:
            origin: Starting location
            destination: Ending location
            travel_mode: Mode of transportation
            arrival_time: Arrival time (HH:MM format)
            query_date: Date of the query
            duration_seconds: Duration without traffic
            duration_in_traffic_seconds: Duration with traffic (if available)
            distance_meters: Distance in meters
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO commute_results
                    (origin, destination, travel_mode, arrival_time, query_date,
                     duration_seconds, duration_in_traffic_seconds, distance_meters)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (origin, destination, travel_mode, arrival_time, query_date,
                      duration_seconds, duration_in_traffic_seconds, distance_meters))
                conn.commit()
            except sqlite3.IntegrityError:
                # Entry already exists, update it
                cursor.execute("""
                    UPDATE commute_results
                    SET duration_seconds = ?,
                        duration_in_traffic_seconds = ?,
                        distance_meters = ?,
                        created_at = CURRENT_TIMESTAMP
                    WHERE origin = ? AND destination = ? AND travel_mode = ?
                        AND arrival_time = ? AND query_date = ?
                """, (duration_seconds, duration_in_traffic_seconds, distance_meters,
                      origin, destination, travel_mode, arrival_time, query_date))
                conn.commit()

    def get_all_results_for_location(self, origin: str, query_date: str) -> List[Dict]:
        """
        Get all cached results for a specific origin location.

        Args:
            origin: Starting location
            query_date: Date of the query

        Returns:
            List of dictionaries with commute data
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT destination, travel_mode, arrival_time,
                       duration_seconds, duration_in_traffic_seconds, distance_meters
                FROM commute_results
                WHERE origin = ? AND query_date = ?
                ORDER BY arrival_time
            """, (origin, query_date))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'destination': row[0],
                    'travel_mode': row[1],
                    'arrival_time': row[2],
                    'duration_seconds': row[3],
                    'duration_in_traffic_seconds': row[4],
                    'distance_meters': row[5]
                })
            return results
