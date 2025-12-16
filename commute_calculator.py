#!/usr/bin/env python3
"""
Apartment Commute Calculator
Calculates commute times from potential apartment locations to job locations.
"""
import sys
import argparse
from datetime import datetime
from typing import Dict, List
from config import Config
from cache import CommuteCache
from routes_api import RoutesAPIClient


def format_duration(seconds: int) -> str:
    """Convert seconds to human-readable format."""
    minutes = seconds // 60
    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours > 0:
        return f"{hours}h {remaining_minutes}min"
    return f"{minutes}min"


def format_transit_step(step: Dict) -> str:
    """
    Format a transit step for compact display with stop names.

    Args:
        step: Transit step dictionary

    Returns:
        Formatted step string
    """
    if step['type'] == 'WALK':
        duration = format_duration(step['duration_seconds'])
        return f"Walk {duration}"
    elif step['type'] == 'TRANSIT':
        duration = format_duration(step['duration_seconds'])
        vehicle = step.get('vehicle_type', 'transit').title()
        line = step.get('transit_line', '')
        dep_stop = step.get('departure_stop', '')
        arr_stop = step.get('arrival_stop', '')

        # Build transit segment description
        parts = []
        if line:
            parts.append(f"{vehicle} {line}")
        else:
            parts.append(vehicle)

        parts.append(f"({duration})")

        # Add stop names if available
        if dep_stop and arr_stop:
            parts.append(f"[{dep_stop} → {arr_stop}]")

        return " ".join(parts)
    else:
        return f"{step['type']} {format_duration(step['duration_seconds'])}"


def format_transit_breakdown(steps: List[Dict]) -> str:
    """
    Format the transit step breakdown compactly.

    Args:
        steps: List of transit step dictionaries

    Returns:
        Formatted breakdown string
    """
    if not steps:
        return ""

    formatted_steps = [format_transit_step(step) for step in steps]
    return " → ".join(formatted_steps)


def calculate_commutes(
    apartment_address: str,
    config: Config,
    cache: CommuteCache,
    routes_client: RoutesAPIClient,
    force_refresh: bool = False
) -> Dict:
    """
    Calculate commute times for both people from the apartment location.

    Args:
        apartment_address: Address or POI of the potential apartment
        config: Configuration object
        cache: Cache object
        routes_client: Routes API client
        force_refresh: If True, ignore cache and fetch fresh data

    Returns:
        Dictionary with commute results for both people
    """
    # Get target date based on day_of_week setting
    target_date = config.get_target_date()
    query_date_str = target_date.strftime('%Y-%m-%d')
    day_of_week = config.day_of_week

    arrival_times = config.get_arrival_times()

    results = {
        'apartment': apartment_address,
        'query_date': query_date_str,
        'day_of_week': day_of_week,
        'my_commutes': [],
        'girlfriend_commutes': []
    }

    print(f"\nCalculating commutes from: {apartment_address}")
    print(f"Target date: {query_date_str} ({day_of_week})")
    print("=" * 90)

    # Calculate my commutes (transit)
    print(f"\n🚊 Your commute to {config.my_job_location} (via {config.my_travel_mode}):")
    print("-" * 90)

    for arrival_time in arrival_times:
        # Check cache first
        cached = None
        if not force_refresh:
            cached = cache.get_cached_result(
                apartment_address,
                config.my_job_location,
                config.my_travel_mode,
                arrival_time,
                day_of_week,
                query_date_str
            )

        if cached:
            duration_text = format_duration(cached['duration_seconds'])
            distance_km = cached['distance_meters'] / 1000

            print(f"  {arrival_time} - {duration_text:>8} ({distance_km:.1f} km) [cached]")

            # Show transit breakdown if available
            if cached.get('transit_steps'):
                breakdown = format_transit_breakdown(cached['transit_steps'])
                print(f"    └─ {breakdown}")

            results['my_commutes'].append({
                'arrival_time': arrival_time,
                'duration_seconds': cached['duration_seconds'],
                'distance_meters': cached['distance_meters'],
                'transit_steps': cached.get('transit_steps'),
                'cached': True
            })
        else:
            # Fetch from API
            # Create arrival datetime
            hour, minute = map(int, arrival_time.split(':'))
            arrival_datetime = datetime.combine(
                target_date,
                datetime.min.time().replace(hour=hour, minute=minute)
            )

            commute_data = routes_client.get_commute_time(
                apartment_address,
                config.my_job_location,
                arrival_datetime,
                'TRANSIT'
            )

            if commute_data:
                # Save to cache
                cache.save_result(
                    apartment_address,
                    config.my_job_location,
                    config.my_travel_mode,
                    arrival_time,
                    day_of_week,
                    query_date_str,
                    commute_data['duration_seconds'],
                    commute_data['distance_meters'],
                    transit_steps=commute_data.get('transit_steps')
                )

                duration_text = format_duration(commute_data['duration_seconds'])
                distance_km = commute_data['distance_meters'] / 1000

                print(f"  {arrival_time} - {duration_text:>8} ({distance_km:.1f} km)")

                # Show transit breakdown if available
                if commute_data.get('transit_steps'):
                    breakdown = format_transit_breakdown(commute_data['transit_steps'])
                    print(f"    └─ {breakdown}")

                results['my_commutes'].append({
                    'arrival_time': arrival_time,
                    'duration_seconds': commute_data['duration_seconds'],
                    'distance_meters': commute_data['distance_meters'],
                    'transit_steps': commute_data.get('transit_steps'),
                    'cached': False
                })
            else:
                print(f"  {arrival_time} - Error fetching data")

    # Calculate girlfriend's commutes (driving with traffic range)
    print(f"\n🚗 Girlfriend's commute to {config.girlfriend_job_location} (via {config.girlfriend_travel_mode}):")
    print("-" * 90)

    for arrival_time in arrival_times:
        # Check cache first
        cached = None
        if not force_refresh:
            cached = cache.get_cached_result(
                apartment_address,
                config.girlfriend_job_location,
                config.girlfriend_travel_mode,
                arrival_time,
                day_of_week,
                query_date_str
            )

        if cached and cached.get('min_duration_seconds') and cached.get('max_duration_seconds'):
            # Display time range
            min_time = format_duration(cached['min_duration_seconds'])
            max_time = format_duration(cached['max_duration_seconds'])
            typical_time = format_duration(cached['typical_duration_seconds'] or cached['duration_seconds'])
            distance_km = cached['distance_meters'] / 1000

            print(f"  {arrival_time} - {min_time}-{max_time} (typically {typical_time}) ({distance_km:.1f} km) [cached]")

            results['girlfriend_commutes'].append({
                'arrival_time': arrival_time,
                'min_duration_seconds': cached['min_duration_seconds'],
                'typical_duration_seconds': cached['typical_duration_seconds'],
                'max_duration_seconds': cached['max_duration_seconds'],
                'distance_meters': cached['distance_meters'],
                'cached': True
            })
        else:
            # Fetch from API with 3 traffic models
            # Create arrival datetime
            hour, minute = map(int, arrival_time.split(':'))
            arrival_datetime = datetime.combine(
                target_date,
                datetime.min.time().replace(hour=hour, minute=minute)
            )

            commute_data = routes_client.get_commute_time_with_traffic_range(
                apartment_address,
                config.girlfriend_job_location,
                arrival_datetime
            )

            if commute_data and commute_data.get('min_duration_seconds'):
                # Save to cache
                cache.save_result(
                    apartment_address,
                    config.girlfriend_job_location,
                    config.girlfriend_travel_mode,
                    arrival_time,
                    day_of_week,
                    query_date_str,
                    commute_data['typical_duration_seconds'],
                    commute_data['distance_meters'],
                    min_duration_seconds=commute_data['min_duration_seconds'],
                    typical_duration_seconds=commute_data['typical_duration_seconds'],
                    max_duration_seconds=commute_data['max_duration_seconds']
                )

                min_time = format_duration(commute_data['min_duration_seconds'])
                max_time = format_duration(commute_data['max_duration_seconds'])
                typical_time = format_duration(commute_data['typical_duration_seconds'])
                distance_km = commute_data['distance_meters'] / 1000

                print(f"  {arrival_time} - {min_time}-{max_time} (typically {typical_time}) ({distance_km:.1f} km)")

                results['girlfriend_commutes'].append({
                    'arrival_time': arrival_time,
                    'min_duration_seconds': commute_data['min_duration_seconds'],
                    'typical_duration_seconds': commute_data['typical_duration_seconds'],
                    'max_duration_seconds': commute_data['max_duration_seconds'],
                    'distance_meters': commute_data['distance_meters'],
                    'cached': False
                })
            else:
                print(f"  {arrival_time} - Error fetching data")

    # Print summary statistics
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)

    if results['my_commutes']:
        my_durations = [c['duration_seconds'] for c in results['my_commutes']]
        my_avg = sum(my_durations) / len(my_durations)
        my_min = min(my_durations)
        my_max = max(my_durations)

        print(f"\n🚊 Your commute:")
        print(f"  Average: {format_duration(int(my_avg))}")
        print(f"  Best:    {format_duration(my_min)}")
        print(f"  Worst:   {format_duration(my_max)}")

    if results['girlfriend_commutes']:
        # Use typical duration for summary
        gf_durations = [
            c.get('typical_duration_seconds', 0)
            for c in results['girlfriend_commutes']
        ]
        gf_avg = sum(gf_durations) / len(gf_durations)
        gf_min = min(gf_durations)
        gf_max = max(gf_durations)

        print(f"\n🚗 Girlfriend's commute (typical times with traffic):")
        print(f"  Average: {format_duration(int(gf_avg))}")
        print(f"  Best:    {format_duration(gf_min)}")
        print(f"  Worst:   {format_duration(gf_max)}")

    print()

    return results


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description='Calculate commute times from potential apartment locations'
    )
    parser.add_argument(
        'address',
        nargs='?',
        help='Apartment address or POI (e.g., "Rynek Główny, Kraków" or "Ulica Floriańska 15, Kraków")'
    )
    parser.add_argument(
        '--force-refresh',
        action='store_true',
        help='Force refresh data from API, ignoring cache'
    )
    parser.add_argument(
        '--day',
        choices=['weekday', 'weekend'],
        help='Override DAY_OF_WEEK setting (weekday or weekend)'
    )

    args = parser.parse_args()

    # If no address provided, ask for it
    if not args.address:
        print("Apartment Commute Calculator")
        print("=" * 90)
        args.address = input("\nEnter apartment address or POI in Kraków: ").strip()

        if not args.address:
            print("Error: Address is required")
            sys.exit(1)

    try:
        # Load configuration
        config = Config()

        # Override day_of_week if specified
        if args.day:
            config.day_of_week = args.day

        # Initialize cache
        cache = CommuteCache(config.db_path)

        # Initialize Routes API client
        routes_client = RoutesAPIClient(config.google_maps_api_key)

        # Calculate commutes
        results = calculate_commutes(
            args.address,
            config,
            cache,
            routes_client,
            args.force_refresh
        )

        print("\n✓ Results saved to cache for future lookups")

    except ValueError as e:
        print(f"Configuration Error: {str(e)}")
        print("\nPlease create a .env file with the required configuration.")
        print("See .env.example for reference.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nAborted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
