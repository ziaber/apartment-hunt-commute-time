# Apartment Commute Calculator

A terminal application to automate the tedious process of checking commute times from potential apartment locations in Kraków. Calculates commute times for two different job locations with different transportation modes, using real Google Maps traffic data with time ranges and detailed transit breakdowns.

## ✨ New Features (2025 Update)

- 🔄 **Traffic Time Ranges**: Shows min-max-typical times instead of single numbers (e.g., "15-25min typically 18min")
- 🚊 **Transit Step Breakdown**: Detailed journey segments with stop names (e.g., "Walk 3min → Tram 50 (15min) [Stop A → Stop B]")
- 📅 **Day-of-Week Awareness**: Separate calculations for weekdays vs weekends with accurate traffic/transit schedules
- 🚀 **Routes API**: Migrated to Google's latest Routes API for more accurate predictions
- 💾 **Permanent Cache**: Results cached indefinitely for instant future lookups

## Features

- 🚊 **Multiple transport modes**: Support for transit (tram/bus), driving, walking, and bicycling
- 🕐 **Time-based calculations**: Automatically calculates commute times for arrival hours from 7am to 6pm (configurable)
- 📊 **Summary statistics**: Displays average, best, and worst commute times
- 🌍 **Real traffic data**: Uses Google Routes API for accurate, traffic-aware calculations
- 🔍 **Transit details**: Complete journey breakdown with vehicle types, line numbers, and stop names

## Requirements

- Python 3.7 or higher
- Google Maps API key with **Routes API** enabled
- Internet connection

## Installation

1. **Clone or download this repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Routes API**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the **Routes API** (not Distance Matrix API - that's deprecated)
   - Create API credentials (API Key)
   - Note: You may need to set up billing, but Google provides $200 free credit monthly

4. **Configure the application**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in your details:
   ```env
   GOOGLE_MAPS_API_KEY=your_actual_api_key_here
   MY_JOB_LOCATION=Your job address in Kraków
   GIRLFRIEND_JOB_LOCATION=Girlfriend's job address in Kraków
   MY_TRAVEL_MODE=transit
   GIRLFRIEND_TRAVEL_MODE=driving
   DAY_OF_WEEK=weekday
   ```

## Usage

### Basic usage (weekday commute)

```bash
python commute_calculator.py "Kazimierz, Kraków"
```

### Weekend commute

```bash
python commute_calculator.py --day weekend "Kazimierz, Kraków"
```

### Force refresh (ignore cache)

```bash
python commute_calculator.py --force-refresh "Nowa Huta, Kraków"
```

### Interactive mode

```bash
python commute_calculator.py
```

Then enter the address when prompted.

## Example Output

```
Calculating commutes from: Kazimierz, Kraków
Target date: 2025-12-22 (weekday)
==========================================================================================

🚊 Your commute to Rynek Główny, Kraków (via transit):
------------------------------------------------------------------------------------------
  07:00 -    15min (3.2 km)
    └─ Walk 3min → Tram 50 (10min) [Kazimierz → Rynek Główny] → Walk 2min
  07:30 -    18min (3.2 km)
    └─ Walk 3min → Bus 184 (12min) [Kazimierz → Starowiślna] → Walk 3min
  08:00 -    22min (3.2 km)
    └─ Walk 5min → Tram 50 (13min) [Kazimierz → Rynek Główny] → Walk 4min
  ...

🚗 Girlfriend's commute to AGH, Kraków (via driving):
------------------------------------------------------------------------------------------
  07:00 - 12min-18min (typically 15min) (4.5 km)
  07:30 - 15min-28min (typically 22min) (4.5 km)
  08:00 - 18min-35min (typically 28min) (4.5 km)
  ...

==========================================================================================
SUMMARY
==========================================================================================

🚊 Your commute:
  Average: 19min
  Best:    15min
  Worst:   25min

🚗 Girlfriend's commute (typical times with traffic):
  Average: 22min
  Best:    15min
  Worst:   28min

✓ Results saved to cache for future lookups
```

## Configuration Options

All configuration is done via the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_MAPS_API_KEY` | Your Google Maps API key | Required |
| `MY_JOB_LOCATION` | Your job address | Required |
| `GIRLFRIEND_JOB_LOCATION` | Girlfriend's job address | Required |
| `MY_TRAVEL_MODE` | Your transportation mode | `transit` |
| `GIRLFRIEND_TRAVEL_MODE` | Girlfriend's transportation mode | `driving` |
| `DAY_OF_WEEK` | Target day type (`weekday` or `weekend`) | `weekday` |
| `START_HOUR` | Start of commute time range (24h format) | `7` |
| `END_HOUR` | End of commute time range (24h format) | `18` |
| `INTERVAL_MINUTES` | Minutes between each calculation | `30` |
| `DB_PATH` | Path to cache database file | `commute_cache.db` |

### Travel Modes

Available options for `MY_TRAVEL_MODE` and `GIRLFRIEND_TRAVEL_MODE`:
- `transit` - Public transportation (bus, tram, metro) with detailed step breakdown
- `driving` - Car with traffic time ranges (optimistic/typical/pessimistic)
- `walking` - On foot
- `bicycling` - Bicycle

### Day of Week

- `weekday` - Uses next Monday for traffic/transit predictions
- `weekend` - Uses next Saturday for traffic/transit predictions

**Important**: Weekday vs weekend makes a HUGE difference:
- Transit schedules change (less frequent on weekends)
- Traffic patterns differ significantly
- Some routes may not run on weekends

## Command Line Options

```
python commute_calculator.py [OPTIONS] [ADDRESS]

Options:
  --force-refresh    Ignore cache and fetch fresh data from API
  --day {weekday,weekend}
                     Override DAY_OF_WEEK setting from .env file

Arguments:
  ADDRESS           Apartment address or POI (e.g., "Kazimierz, Kraków")
```

## How It Works

1. **Address Input**: You provide an apartment address or POI (Point of Interest)
2. **Date Calculation**: Determines target date (next Monday for weekday, next Saturday for weekend)
3. **Cache Check**: Checks if results are cached for this location, day-of-week, and date
4. **API Calls**: If not cached, makes requests to Google Routes API:
   - **Transit**: 1 request per time slot (gets detailed step breakdown)
   - **Driving**: 3 requests per time slot (optimistic, typical, pessimistic traffic models)
5. **Traffic Data**: For driving mode, shows time range based on traffic predictions
6. **Transit Breakdown**: For transit mode, shows each segment (walk, bus, tram) with stop names
7. **Storage**: Saves all results to SQLite database (permanent cache)
8. **Display**: Shows commute times with ranges and breakdowns for all configured arrival hours
9. **Summary**: Calculates and displays average, best, and worst case scenarios

## Caching System

- Results are cached permanently (no expiration)
- Cache key includes: origin, destination, travel mode, arrival time, day-of-week, and date
- Prevents duplicate API calls for the same route configuration
- Use `--force-refresh` to bypass cache and get fresh data
- Database file: `commute_cache.db` (SQLite)
- Weekday and weekend results are cached separately

## API Costs

Google Routes API pricing (as of 2025):
- $5 per 1,000 requests
- First $200/month is free (covers ~40,000 requests)
- **Per apartment location**:
  - Transit: 23 time slots × 1 request = 23 requests
  - Driving: 23 time slots × 3 traffic models = 69 requests
  - **Total per location**: ~92 requests
- **With free tier**: ~434 apartment locations per month
- **For 100 locations**: ~9,200 requests ≈ $46 (but $200 free credit covers it!)

## Understanding the Output

### Transit Times
```
07:00 -    18min (3.2 km)
  └─ Walk 3min → Tram 50 (12min) [Kazimierz → Starowiślna] → Walk 3min
```
- **18min**: Total journey time
- **Walk 3min**: Walk to tram stop
- **Tram 50**: Line number
- **[Stop A → Stop B]**: Departure and arrival stop names
- Each segment shows its duration

### Driving Times
```
07:00 - 12min-18min (typically 15min) (4.5 km)
```
- **12min**: Optimistic (best traffic conditions)
- **18min**: Pessimistic (worst traffic conditions)
- **typically 15min**: Most likely duration (best guess based on historical data)
- Use the "typical" time for planning

## Tips

1. **Use specific addresses**: More specific addresses give better results
2. **POI support**: You can use landmarks like "Rynek Główny, Kraków"
3. **Check cache**: Run the same location twice - second time is instant (cached)
4. **Weekday vs Weekend**: Always check both - they can differ significantly!
5. **Morning commute**: Focus on 7am-9am times as they usually have worst traffic
6. **Transit breakdown**: Look at number of transfers and walking distance
7. **Time ranges**: For driving, plan for the pessimistic time to avoid being late
8. **Save locations**: Keep a list of interesting apartments and batch-check them

## Troubleshooting

### "GOOGLE_MAPS_API_KEY not found"
- Make sure you created the `.env` file
- Check that the API key is correctly copied
- No quotes needed around the API key in `.env`

### "API Error: REQUEST_DENIED"
- Verify **Routes API** is enabled in Google Cloud Console (not Distance Matrix API)
- Check that billing is set up (required even for free tier)
- Ensure API key has proper permissions

### "Could not find this address"
- Try more specific address (include city: "Kraków")
- Use Polish street names and formatting
- Try a nearby landmark or POI instead

### "No routes found"
- The route might not be possible with the specified travel mode
- Try a different travel mode
- Check if the addresses are valid

### HTTP 403 Error
- Routes API might not be enabled
- Billing might not be set up
- API key restrictions might be blocking the request

### Slow performance
- First run for each location takes time (API calls)
- Driving mode is slower (3× API calls for traffic range)
- Subsequent runs are instant (cached)
- Consider reducing time range or interval in `.env`

## Development

Project structure:
```
.
├── commute_calculator.py   # Main CLI application
├── config.py              # Configuration handler
├── cache.py               # SQLite caching system
├── routes_api.py          # Google Routes API wrapper (NEW)
├── maps_api.py            # Legacy Google Maps API wrapper (deprecated)
├── requirements.txt       # Python dependencies
├── .env.example          # Example configuration
├── .env                  # Your configuration (not in git)
└── commute_cache.db      # SQLite database (created on first run)
```

## Migration from Old Version

If you were using the old Distance Matrix API version:

1. **Enable Routes API** in Google Cloud Console
2. **Update `.env`**: Add `DAY_OF_WEEK=weekday`
3. **Clear cache** (optional): Delete `commute_cache.db` to recalculate with new API
4. **Run normally**: The app now uses Routes API automatically

## What's Different from Google Maps App?

**Advantages**:
- Batch calculate multiple time slots at once
- Permanent caching (Google Maps doesn't save results)
- See time ranges for driving (optimistic to pessimistic)
- Compare multiple apartment locations side-by-side
- Automated statistics (average, best, worst)

**Limitations**:
- No turn-by-turn navigation
- No alternative routes shown
- No real-time updates (uses predictions)
- Cached results don't reflect last-minute changes

## License

This is a personal utility tool. Use freely for your apartment hunting!

## Contributing

Feel free to extend this tool with additional features:
- Export results to CSV/Excel
- Web interface
- Comparison view for multiple apartments
- Integration with apartment listing sites
- Visualization of commute times on a map
- Support for multiple people/job locations
- Email/SMS alerts for new apartment listings in good commute areas

Good luck finding your perfect apartment! 🏠
