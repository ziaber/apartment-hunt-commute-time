"""
Configuration module for the commute calculator.
"""
import os
from dotenv import load_dotenv
from typing import Optional


class Config:
    """Configuration handler for the application."""

    def __init__(self):
        """Load configuration from environment variables."""
        load_dotenv()

        # Google Maps API Key
        self.google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.google_maps_api_key:
            raise ValueError(
                "GOOGLE_MAPS_API_KEY not found in environment variables. "
                "Please create a .env file with your API key."
            )

        # Job locations
        self.my_job_location = os.getenv('MY_JOB_LOCATION')
        self.girlfriend_job_location = os.getenv('GIRLFRIEND_JOB_LOCATION')

        if not self.my_job_location:
            raise ValueError("MY_JOB_LOCATION not found in environment variables")
        if not self.girlfriend_job_location:
            raise ValueError("GIRLFRIEND_JOB_LOCATION not found in environment variables")

        # Travel modes
        self.my_travel_mode = os.getenv('MY_TRAVEL_MODE', 'transit')
        self.girlfriend_travel_mode = os.getenv('GIRLFRIEND_TRAVEL_MODE', 'driving')

        # Commute time settings
        self.start_hour = int(os.getenv('START_HOUR', '7'))
        self.end_hour = int(os.getenv('END_HOUR', '18'))
        self.interval_minutes = int(os.getenv('INTERVAL_MINUTES', '30'))

        # Database path
        self.db_path = os.getenv('DB_PATH', 'commute_cache.db')

    def get_arrival_times(self):
        """
        Generate list of arrival times based on configuration.

        Returns:
            List of time strings in HH:MM format
        """
        times = []
        current_hour = self.start_hour
        current_minute = 0

        while current_hour < self.end_hour or (current_hour == self.end_hour and current_minute == 0):
            times.append(f"{current_hour:02d}:{current_minute:02d}")

            current_minute += self.interval_minutes
            if current_minute >= 60:
                current_hour += 1
                current_minute = 0

        return times
