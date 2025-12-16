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
from maps_api import MapsAPIClient


def format_duration(seconds: int) -> str:
    """Convert seconds to human-readable format."""
    minutes = seconds // 60
    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours > 0:
        return f"{hours}h {remaining_minutes}min"
    return f"{minutes}min"


def calculate_commutes(
    apartment_address: str,
    config: Config,
    cache: CommuteCache,
    maps_client: MapsAPIClient,
    force_refresh: bool = False
) -> Dict:
    """
    Calculate commute times for both people from the apartment location.

    Args:
        apartment_address: Address or POI of the potential apartment
        config: Configuration object
        cache: Cache object
        maps_client: Google Maps API client
        force_refresh: If True, ignore cache and fetch fresh data

    Returns:
        Dictionary with commute results for both people
    """
    query_date = datetime.now().strftime('%Y-%m-%d')
    arrival_times = config.get_arrival_times()

    results = {
        'apartment': apartment_address,
        'query_date': query_date,
        'my_commutes': [],
        'girlfriend_commutes': []
    }

    print(f"\nCalculating commutes from: {apartment_address}")
    print("=" * 70)

    # Calculate my commutes (transit)
    print(f"\n🚊 Your commute to {config.my_job_location} (via {config.my_travel_mode}):")
    print("-" * 70)

    for arrival_time in arrival_times:
        # Check cache first
        cached = None
        if not force_refresh:
            cached = cache.get_cached_result(
                apartment_address,
                config.my_job_location,
                config.my_travel_mode,
                arrival_time,
                query_date
            )

        if cached:
            print(f"  {arrival_time} - {format_duration(cached['duration_seconds']):>8} "
                  f"({cached['distance_meters'] / 1000:.1f} km) [cached]")
            results['my_commutes'].append({
                'arrival_time': arrival_time,
                'duration_seconds': cached['duration_seconds'],
                'distance_meters': cached['distance_meters'],
                'cached': True
            })
        else:
            # Fetch from API
            commute_data = maps_client.get_commute_time(
                apartment_address,
                config.my_job_location,
                arrival_time,
                config.my_travel_mode
            )

            if commute_data:
                # Save to cache
                cache.save_result(
                    apartment_address,
                    config.my_job_location,
                    config.my_travel_mode,
                    arrival_time,
                    query_date,
                    commute_data['duration_seconds'],
                    commute_data.get('duration_in_traffic_seconds'),
                    commute_data['distance_meters']
                )

                print(f"  {arrival_time} - {format_duration(commute_data['duration_seconds']):>8} "
                      f"({commute_data['distance_meters'] / 1000:.1f} km)")

                results['my_commutes'].append({
                    'arrival_time': arrival_time,
                    'duration_seconds': commute_data['duration_seconds'],
                    'distance_meters': commute_data['distance_meters'],
                    'cached': False
                })
            else:
                print(f"  {arrival_time} - Error fetching data")

    # Calculate girlfriend's commutes (driving)
    print(f"\n🚗 Girlfriend's commute to {config.girlfriend_job_location} (via {config.girlfriend_travel_mode}):")
    print("-" * 70)

    for arrival_time in arrival_times:
        # Check cache first
        cached = None
        if not force_refresh:
            cached = cache.get_cached_result(
                apartment_address,
                config.girlfriend_job_location,
                config.girlfriend_travel_mode,
                arrival_time,
                query_date
            )

        if cached:
            traffic_info = ""
            if cached['duration_in_traffic_seconds']:
                traffic_duration = format_duration(cached['duration_in_traffic_seconds'])
                traffic_info = f" (with traffic: {traffic_duration})"

            print(f"  {arrival_time} - {format_duration(cached['duration_seconds']):>8} "
                  f"({cached['distance_meters'] / 1000:.1f} km){traffic_info} [cached]")

            results['girlfriend_commutes'].append({
                'arrival_time': arrival_time,
                'duration_seconds': cached['duration_seconds'],
                'duration_in_traffic_seconds': cached['duration_in_traffic_seconds'],
                'distance_meters': cached['distance_meters'],
                'cached': True
            })
        else:
            # Fetch from API
            commute_data = maps_client.get_commute_time(
                apartment_address,
                config.girlfriend_job_location,
                arrival_time,
                config.girlfriend_travel_mode
            )

            if commute_data:
                # Save to cache
                cache.save_result(
                    apartment_address,
                    config.girlfriend_job_location,
                    config.girlfriend_travel_mode,
                    arrival_time,
                    query_date,
                    commute_data['duration_seconds'],
                    commute_data.get('duration_in_traffic_seconds'),
                    commute_data['distance_meters']
                )

                traffic_info = ""
                if commute_data.get('duration_in_traffic_seconds'):
                    traffic_duration = format_duration(commute_data['duration_in_traffic_seconds'])
                    traffic_info = f" (with traffic: {traffic_duration})"

                print(f"  {arrival_time} - {format_duration(commute_data['duration_seconds']):>8} "
                      f"({commute_data['distance_meters'] / 1000:.1f} km){traffic_info}")

                results['girlfriend_commutes'].append({
                    'arrival_time': arrival_time,
                    'duration_seconds': commute_data['duration_seconds'],
                    'duration_in_traffic_seconds': commute_data.get('duration_in_traffic_seconds'),
                    'distance_meters': commute_data['distance_meters'],
                    'cached': False
                })
            else:
                print(f"  {arrival_time} - Error fetching data")

    # Print summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

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
        gf_durations = [
            c.get('duration_in_traffic_seconds') or c['duration_seconds']
            for c in results['girlfriend_commutes']
        ]
        gf_avg = sum(gf_durations) / len(gf_durations)
        gf_min = min(gf_durations)
        gf_max = max(gf_durations)

        print(f"\n🚗 Girlfriend's commute (with traffic):")
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
        '--verify',
        action='store_true',
        help='Verify the address with Google Maps before calculating'
    )

    args = parser.parse_args()

    # If no address provided, ask for it
    if not args.address:
        print("Apartment Commute Calculator")
        print("=" * 70)
        args.address = input("\nEnter apartment address or POI in Kraków: ").strip()

        if not args.address:
            print("Error: Address is required")
            sys.exit(1)

    try:
        # Load configuration
        config = Config()

        # Initialize cache
        cache = CommuteCache(config.db_path)

        # Initialize Google Maps client
        maps_client = MapsAPIClient(config.google_maps_api_key)

        # Verify address if requested
        if args.verify:
            print(f"\nVerifying address: {args.address}")
            formatted_address = maps_client.geocode_address(args.address)
            if formatted_address:
                print(f"Found: {formatted_address}")
                confirm = input("Use this address? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("Aborted")
                    sys.exit(0)
                args.address = formatted_address
            else:
                print("Could not find this address. Proceeding anyway...")

        # Calculate commutes
        results = calculate_commutes(
            args.address,
            config,
            cache,
            maps_client,
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
