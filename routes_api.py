"""
Google Routes API integration for calculating commute times with detailed breakdowns.
Replaces the legacy Distance Matrix API with the new Routes API.
"""
import requests
from datetime import datetime
from typing import Dict, Optional, List
import time


class RoutesAPIClient:
    """Wrapper for Google Routes API operations."""

    BASE_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

    def __init__(self, api_key: str):
        """
        Initialize the Routes API client.

        Args:
            api_key: Google Maps API key
        """
        self.api_key = api_key

    def get_commute_time(
        self,
        origin: str,
        destination: str,
        arrival_datetime: datetime,
        travel_mode: str = 'DRIVE',
        traffic_model: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get commute time from origin to destination using Routes API.

        Args:
            origin: Starting location (address or POI)
            destination: Destination location (address or POI)
            arrival_datetime: Desired arrival datetime
            travel_mode: 'DRIVE' or 'TRANSIT'
            traffic_model: For driving: 'BEST_GUESS', 'OPTIMISTIC', 'PESSIMISTIC' (default: BEST_GUESS)

        Returns:
            Dictionary with duration, distance, traffic info, and transit steps (if applicable)
        """
        try:
            # Prepare request headers
            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': self._get_field_mask(travel_mode)
            }

            # Prepare request body
            body = self._build_request_body(
                origin, destination, arrival_datetime, travel_mode, traffic_model
            )

            # Make API request
            response = requests.post(self.BASE_URL, headers=headers, json=body)
            response.raise_for_status()

            # Parse response
            data = response.json()

            if 'routes' in data and len(data['routes']) > 0:
                route = data['routes'][0]
                return self._parse_route_response(route, travel_mode, traffic_model)
            else:
                print(f"No routes found from {origin} to {destination}")
                return None

        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text if e.response else 'No response'}")
            return None
        except Exception as e:
            print(f"Error getting commute time: {str(e)}")
            return None

    def _get_field_mask(self, travel_mode: str) -> str:
        """
        Get the appropriate field mask for the API request.

        Args:
            travel_mode: 'DRIVE' or 'TRANSIT'

        Returns:
            Comma-separated field mask string
        """
        base_fields = [
            'routes.duration',
            'routes.distanceMeters',
            'routes.legs.steps.navigationInstruction',
            'routes.legs.steps.localizedValues'
        ]

        if travel_mode == 'TRANSIT':
            transit_fields = [
                'routes.legs.steps.transitDetails.stopDetails',
                'routes.legs.steps.transitDetails.localizedValues',
                'routes.legs.steps.transitDetails.transitLine'
            ]
            base_fields.extend(transit_fields)
        else:  # DRIVE
            drive_fields = [
                'routes.staticDuration',
                'routes.travelAdvisory.speedReadingIntervals'
            ]
            base_fields.extend(drive_fields)

        return ','.join(base_fields)

    def _build_request_body(
        self,
        origin: str,
        destination: str,
        arrival_datetime: datetime,
        travel_mode: str,
        traffic_model: Optional[str]
    ) -> Dict:
        """
        Build the request body for the Routes API.

        Args:
            origin: Starting location
            destination: Destination location
            arrival_datetime: Arrival datetime
            travel_mode: 'DRIVE' or 'TRANSIT'
            traffic_model: Traffic model for driving mode

        Returns:
            Request body dictionary
        """
        body = {
            'origin': {
                'address': origin
            },
            'destination': {
                'address': destination
            },
            'travelMode': travel_mode,
            'languageCode': 'pl',
            'units': 'METRIC'
        }

        if travel_mode == 'TRANSIT':
            # For transit, use arrival time
            body['arrivalTime'] = arrival_datetime.isoformat() + 'Z'
            body['transitPreferences'] = {
                'allowedTravelModes': ['BUS', 'SUBWAY', 'TRAIN', 'LIGHT_RAIL', 'RAIL']
            }
        else:  # DRIVE
            # For driving, use departure time (calculate from arrival time - will be adjusted)
            # We'll use current time for traffic-aware routing
            body['departureTime'] = datetime.now().isoformat() + 'Z'
            body['routingPreference'] = 'TRAFFIC_AWARE'

            # Set traffic model if specified
            if traffic_model:
                body['trafficModel'] = traffic_model
            else:
                body['trafficModel'] = 'BEST_GUESS'

        return body

    def _parse_route_response(
        self,
        route: Dict,
        travel_mode: str,
        traffic_model: Optional[str]
    ) -> Dict:
        """
        Parse the route response from Routes API.

        Args:
            route: Route object from API response
            travel_mode: Travel mode used
            traffic_model: Traffic model used (for driving)

        Returns:
            Parsed route data dictionary
        """
        # Extract basic information
        duration_seconds = int(route.get('duration', '0s').rstrip('s'))
        distance_meters = route.get('distanceMeters', 0)

        result = {
            'duration_seconds': duration_seconds,
            'distance_meters': distance_meters,
            'duration_text': self._format_duration(duration_seconds),
            'distance_text': self._format_distance(distance_meters),
            'traffic_model': traffic_model if travel_mode == 'DRIVE' else None
        }

        # For driving, get static duration (without traffic)
        if travel_mode == 'DRIVE':
            static_duration_seconds = int(route.get('staticDuration', '0s').rstrip('s'))
            result['static_duration_seconds'] = static_duration_seconds
            result['static_duration_text'] = self._format_duration(static_duration_seconds)

        # For transit, extract step-by-step breakdown
        if travel_mode == 'TRANSIT':
            result['transit_steps'] = self._extract_transit_steps(route)

        return result

    def _extract_transit_steps(self, route: Dict) -> List[Dict]:
        """
        Extract transit step breakdown from route.

        Args:
            route: Route object from API response

        Returns:
            List of transit step dictionaries
        """
        steps = []

        if 'legs' not in route or len(route['legs']) == 0:
            return steps

        leg = route['legs'][0]
        if 'steps' not in leg:
            return steps

        for step in leg['steps']:
            step_data = {
                'type': None,
                'duration_seconds': 0,
                'distance_meters': 0,
                'instruction': '',
                'transit_line': None,
                'departure_stop': None,
                'arrival_stop': None,
                'num_stops': None,
                'vehicle_type': None
            }

            # Get localized values if available
            if 'localizedValues' in step:
                local_values = step['localizedValues']
                if 'distance' in local_values:
                    step_data['distance_meters'] = local_values['distance'].get('value', 0)
                if 'staticDuration' in local_values:
                    duration_str = local_values['staticDuration']
                    step_data['duration_seconds'] = int(duration_str.rstrip('s'))

            # Get navigation instruction
            if 'navigationInstruction' in step:
                step_data['instruction'] = step['navigationInstruction'].get('instructions', '')

            # Check if this is a transit step
            if 'transitDetails' in step:
                step_data['type'] = 'TRANSIT'
                transit = step['transitDetails']

                # Get stop details
                if 'stopDetails' in transit:
                    stop_details = transit['stopDetails']
                    if 'departureStop' in stop_details:
                        step_data['departure_stop'] = stop_details['departureStop'].get('name', '')
                    if 'arrivalStop' in stop_details:
                        step_data['arrival_stop'] = stop_details['arrivalStop'].get('name', '')

                # Get transit line information
                if 'transitLine' in transit:
                    line = transit['transitLine']
                    step_data['transit_line'] = line.get('name', '') or line.get('nameShort', '')

                    if 'vehicle' in line:
                        vehicle = line['vehicle']
                        step_data['vehicle_type'] = vehicle.get('type', '').lower()

                # Get number of stops
                if 'localizedValues' in transit:
                    local_transit = transit['localizedValues']
                    if 'stopCount' in local_transit:
                        step_data['num_stops'] = local_transit['stopCount']

            else:
                # This is a walking/other step
                step_data['type'] = 'WALK'

            steps.append(step_data)

        return steps

    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human-readable string."""
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes} min"
        else:
            hours = minutes // 60
            mins = minutes % 60
            if mins == 0:
                return f"{hours} h"
            return f"{hours} h {mins} min"

    def _format_distance(self, meters: int) -> str:
        """Format distance in meters to human-readable string."""
        if meters < 1000:
            return f"{meters} m"
        else:
            km = meters / 1000
            return f"{km:.1f} km"

    def get_commute_time_with_traffic_range(
        self,
        origin: str,
        destination: str,
        arrival_datetime: datetime
    ) -> Optional[Dict]:
        """
        Get commute time for driving with traffic range (optimistic, typical, pessimistic).

        Args:
            origin: Starting location
            destination: Destination location
            arrival_datetime: Desired arrival datetime

        Returns:
            Dictionary with min, typical, max durations and distances
        """
        results = {}

        # Make 3 API calls with different traffic models
        for model in ['OPTIMISTIC', 'BEST_GUESS', 'PESSIMISTIC']:
            result = self.get_commute_time(
                origin, destination, arrival_datetime, 'DRIVE', model
            )
            if result:
                results[model.lower()] = result
            # Small delay between requests
            time.sleep(0.1)

        if not results:
            return None

        # Combine results
        return {
            'optimistic': results.get('optimistic'),
            'best_guess': results.get('best_guess'),
            'pessimistic': results.get('pessimistic'),
            'min_duration_seconds': results.get('optimistic', {}).get('duration_seconds'),
            'typical_duration_seconds': results.get('best_guess', {}).get('duration_seconds'),
            'max_duration_seconds': results.get('pessimistic', {}).get('duration_seconds'),
            'distance_meters': results.get('best_guess', {}).get('distance_meters'),
            'distance_text': results.get('best_guess', {}).get('distance_text')
        }
