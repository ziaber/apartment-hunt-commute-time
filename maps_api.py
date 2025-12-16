"""
Google Maps API integration for calculating commute times.
"""
import googlemaps
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import time


class MapsAPIClient:
    """Wrapper for Google Maps API operations."""

    def __init__(self, api_key: str):
        """
        Initialize the Google Maps client.

        Args:
            api_key: Google Maps API key
        """
        self.client = googlemaps.Client(key=api_key)

    def get_commute_time(
        self,
        origin: str,
        destination: str,
        arrival_time: str,
        travel_mode: str = 'driving',
        query_date: Optional[datetime] = None
    ) -> Optional[Dict]:
        """
        Get commute time from origin to destination.

        Args:
            origin: Starting location (address or POI)
            destination: Destination location (address or POI)
            arrival_time: Desired arrival time in HH:MM format
            travel_mode: 'driving' or 'transit'
            query_date: Date for the query (defaults to next occurrence of arrival_time)

        Returns:
            Dictionary with duration, distance, and traffic info or None if error
        """
        try:
            # Parse arrival time and create datetime object
            if query_date is None:
                query_date = datetime.now()

            hour, minute = map(int, arrival_time.split(':'))
            arrival_datetime = query_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # If the time has already passed today, use tomorrow
            if arrival_datetime <= datetime.now():
                arrival_datetime += timedelta(days=1)

            # Make API request
            result = self.client.distance_matrix(
                origins=[origin],
                destinations=[destination],
                mode=travel_mode,
                arrival_time=arrival_datetime,
                language='pl',
                units='metric'
            )

            # Parse response
            if result['status'] == 'OK':
                element = result['rows'][0]['elements'][0]

                if element['status'] == 'OK':
                    response_data = {
                        'duration_seconds': element['duration']['value'],
                        'distance_meters': element['distance']['value'],
                        'duration_text': element['duration']['text'],
                        'distance_text': element['distance']['text']
                    }

                    # Add traffic duration if available (for driving mode)
                    if 'duration_in_traffic' in element:
                        response_data['duration_in_traffic_seconds'] = element['duration_in_traffic']['value']
                        response_data['duration_in_traffic_text'] = element['duration_in_traffic']['text']
                    else:
                        response_data['duration_in_traffic_seconds'] = None
                        response_data['duration_in_traffic_text'] = None

                    return response_data
                else:
                    print(f"Error for route: {element['status']}")
                    return None
            else:
                print(f"API Error: {result['status']}")
                return None

        except Exception as e:
            print(f"Error getting commute time: {str(e)}")
            return None

    def geocode_address(self, address: str) -> Optional[str]:
        """
        Geocode an address to verify it's valid.

        Args:
            address: Address or POI to geocode

        Returns:
            Formatted address string or None if not found
        """
        try:
            result = self.client.geocode(address, language='pl')
            if result:
                return result[0]['formatted_address']
            return None
        except Exception as e:
            print(f"Error geocoding address: {str(e)}")
            return None

    def get_multiple_commute_times(
        self,
        origin: str,
        destination: str,
        arrival_times: List[str],
        travel_mode: str = 'driving'
    ) -> List[Dict]:
        """
        Get commute times for multiple arrival times.

        Args:
            origin: Starting location
            destination: Destination location
            arrival_times: List of arrival times in HH:MM format
            travel_mode: 'driving' or 'transit'

        Returns:
            List of dictionaries with commute data
        """
        results = []

        for arrival_time in arrival_times:
            result = self.get_commute_time(origin, destination, arrival_time, travel_mode)

            if result:
                result['arrival_time'] = arrival_time
                results.append(result)

            # Add a small delay to avoid hitting API rate limits
            time.sleep(0.1)

        return results
