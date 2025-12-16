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

            # Create new table with updated schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commute_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    origin TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    travel_mode TEXT NOT NULL,
                    arrival_time TEXT NOT NULL,
                    day_of_week TEXT NOT NULL,
                    query_date DATE NOT NULL,

                    -- For all modes: basic duration and distance
                    duration_seconds INTEGER NOT NULL,
                    distance_meters INTEGER NOT NULL,

                    -- For driving mode: traffic range (min, typical, max)
                    min_duration_seconds INTEGER,
                    typical_duration_seconds INTEGER,
                    max_duration_seconds INTEGER,

                    -- Legacy field for backward compatibility
                    duration_in_traffic_seconds INTEGER,

                    -- For transit mode: step-by-step breakdown (JSON)
                    transit_steps TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(origin, destination, travel_mode, arrival_time, day_of_week, query_date)
                )
            """)

            conn.commit()

    def get_cached_result(
        self,
        origin: str,
        destination: str,
        travel_mode: str,
        arrival_time: str,
        day_of_week: str,
        query_date: str
    ) -> Optional[Dict]:
        """
        Retrieve cached commute result if it exists.

        Args:
            origin: Starting location
            destination: Ending location
            travel_mode: Mode of transportation (driving, transit)
            arrival_time: Arrival time (HH:MM format)
            day_of_week: Day of week (weekday/weekend)
            query_date: Date of the query (YYYY-MM-DD)

        Returns:
            Dictionary with commute data or None if not cached
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT duration_seconds, distance_meters,
                       min_duration_seconds, typical_duration_seconds, max_duration_seconds,
                       transit_steps
                FROM commute_results
                WHERE origin = ? AND destination = ? AND travel_mode = ?
                    AND arrival_time = ? AND day_of_week = ? AND query_date = ?
            """, (origin, destination, travel_mode, arrival_time, day_of_week, query_date))

            row = cursor.fetchone()
            if row:
                result = {
                    'duration_seconds': row[0],
                    'distance_meters': row[1],
                    'min_duration_seconds': row[2],
                    'typical_duration_seconds': row[3],
                    'max_duration_seconds': row[4],
                }

                # Parse transit steps if available
                if row[5]:
                    result['transit_steps'] = json.loads(row[5])
                else:
                    result['transit_steps'] = None

                return result
            return None

    def save_result(
        self,
        origin: str,
        destination: str,
        travel_mode: str,
        arrival_time: str,
        day_of_week: str,
        query_date: str,
        duration_seconds: int,
        distance_meters: int,
        min_duration_seconds: Optional[int] = None,
        typical_duration_seconds: Optional[int] = None,
        max_duration_seconds: Optional[int] = None,
        transit_steps: Optional[List[Dict]] = None
    ):
        """
        Save a commute result to the cache.

        Args:
            origin: Starting location
            destination: Ending location
            travel_mode: Mode of transportation
            arrival_time: Arrival time (HH:MM format)
            day_of_week: Day of week (weekday/weekend)
            query_date: Date of the query
            duration_seconds: Base duration
            distance_meters: Distance in meters
            min_duration_seconds: Minimum duration (for driving with traffic)
            typical_duration_seconds: Typical duration (for driving with traffic)
            max_duration_seconds: Maximum duration (for driving with traffic)
            transit_steps: Transit step breakdown (for transit mode)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Serialize transit steps to JSON
            transit_steps_json = json.dumps(transit_steps) if transit_steps else None

            try:
                cursor.execute("""
                    INSERT INTO commute_results
                    (origin, destination, travel_mode, arrival_time, day_of_week, query_date,
                     duration_seconds, distance_meters,
                     min_duration_seconds, typical_duration_seconds, max_duration_seconds,
                     transit_steps)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (origin, destination, travel_mode, arrival_time, day_of_week, query_date,
                      duration_seconds, distance_meters,
                      min_duration_seconds, typical_duration_seconds, max_duration_seconds,
                      transit_steps_json))
                conn.commit()
            except sqlite3.IntegrityError:
                # Entry already exists, update it
                cursor.execute("""
                    UPDATE commute_results
                    SET duration_seconds = ?,
                        distance_meters = ?,
                        min_duration_seconds = ?,
                        typical_duration_seconds = ?,
                        max_duration_seconds = ?,
                        transit_steps = ?,
                        created_at = CURRENT_TIMESTAMP
                    WHERE origin = ? AND destination = ? AND travel_mode = ?
                        AND arrival_time = ? AND day_of_week = ? AND query_date = ?
                """, (duration_seconds, distance_meters,
                      min_duration_seconds, typical_duration_seconds, max_duration_seconds,
                      transit_steps_json,
                      origin, destination, travel_mode, arrival_time, day_of_week, query_date))
                conn.commit()

    def get_all_results_for_location(self, origin: str, day_of_week: str, query_date: str) -> List[Dict]:
        """
        Get all cached results for a specific origin location.

        Args:
            origin: Starting location
            day_of_week: Day of week (weekday/weekend)
            query_date: Date of the query

        Returns:
            List of dictionaries with commute data
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT destination, travel_mode, arrival_time,
                       duration_seconds, distance_meters,
                       min_duration_seconds, typical_duration_seconds, max_duration_seconds,
                       transit_steps
                FROM commute_results
                WHERE origin = ? AND day_of_week = ? AND query_date = ?
                ORDER BY arrival_time
            """, (origin, day_of_week, query_date))

            results = []
            for row in cursor.fetchall():
                result = {
                    'destination': row[0],
                    'travel_mode': row[1],
                    'arrival_time': row[2],
                    'duration_seconds': row[3],
                    'distance_meters': row[4],
                    'min_duration_seconds': row[5],
                    'typical_duration_seconds': row[6],
                    'max_duration_seconds': row[7],
                }

                # Parse transit steps if available
                if row[8]:
                    result['transit_steps'] = json.loads(row[8])
                else:
                    result['transit_steps'] = None

                results.append(result)
            return results
