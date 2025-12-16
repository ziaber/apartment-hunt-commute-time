"""
Configuration module for the commute calculator.
"""
import os
from datetime import datetime, timedelta
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

        # Day of week for commute calculation
        self.day_of_week = os.getenv('DAY_OF_WEEK', 'weekday').lower()
        if self.day_of_week not in ['weekday', 'weekend']:
            raise ValueError("DAY_OF_WEEK must be either 'weekday' or 'weekend'")

    def get_target_date(self):
        """
        Calculate the target date for commute predictions based on day_of_week setting.

        - 'weekday': Returns next Monday (or today if today is Monday)
        - 'weekend': Returns next Saturday (or today if today is Saturday)

        Returns:
            datetime.date object representing the target date
        """
        today = datetime.now().date()
        weekday = today.weekday()  # Monday=0, Sunday=6

        if self.day_of_week == 'weekday':
            # Target: Monday (weekday=0)
            if weekday == 0:
                # Today is Monday
                return today
            elif weekday < 0:
                # Should never happen, but handle it
                days_ahead = 0
            else:
                # Calculate days until next Monday
                days_ahead = (7 - weekday) % 7
                if days_ahead == 0:
                    days_ahead = 7
            return today + timedelta(days=days_ahead)
        else:  # weekend
            # Target: Saturday (weekday=5)
            if weekday == 5:
                # Today is Saturday
                return today
            elif weekday < 5:
                # Days until this Saturday
                days_ahead = 5 - weekday
            else:
                # Days until next Saturday (Sunday=6, so next Saturday is 6 days away)
                days_ahead = 6
            return today + timedelta(days=days_ahead)

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
