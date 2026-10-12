# Apartment Commute Calculator

A terminal application to automate the tedious process of checking commute times from potential apartment locations in Kraków. Calculates commute times for two different job locations with different transportation modes, using real Google Maps traffic data.

## Features

- 🚊 **Multiple transport modes**: Support for transit (tram/bus), driving, walking, and bicycling
- 🕐 **Time-based calculations**: Automatically calculates commute times for arrival hours from 7am to 6pm (configurable)
- 💾 **Smart caching**: Stores results in SQLite database to avoid duplicate API calls
- 📊 **Summary statistics**: Displays average, best, and worst commute times
- 🌍 **Google Maps data**: Uses the Google Maps Distance Matrix API for route durations and distances (see [Known Limitations](#known-limitations) about traffic)
- 🔎 **Address verification**: Optionally confirms how Google Maps resolved your address before calculating

## Requirements

- Python 3.8 or higher (required by `python-dotenv` 1.0)
- Google Maps API key with Distance Matrix API enabled
- Internet connection

## Installation

1. **Clone or download this repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Maps API**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the **Distance Matrix API** (and the **Geocoding API** if you want to use `--verify`)
   - Create API credentials (API Key)
   - Note: Billing must be enabled on the project. Since March 2025 Google no longer gives a $200 monthly credit; instead each API has a free monthly usage allowance (see [API Costs](#api-costs))
   - Note: The Distance Matrix API is now a *Legacy* API in Google's catalog. If it can't be enabled on a new project, you'll need a project that already has it enabled (or a port to the Routes API)

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
   ```

## Usage

### Basic usage

```bash
python commute_calculator.py "Kazimierz, Kraków"
```

### With address verification

```bash
python commute_calculator.py --verify "Ulica Floriańska 15, Kraków"
```

Shows how Google Maps resolved the address and asks for confirmation. If you confirm, the resolved address is used for the calculation (and as the cache key).

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
======================================================================

🚊 Your commute to Rynek Główny, Kraków (via transit):
----------------------------------------------------------------------
  07:00 -    15min (3.2 km)
  07:30 -    18min (3.2 km)
  08:00 -    22min (3.2 km)
  ...

🚗 Girlfriend's commute to AGH University of Science and Technology, Kraków (via driving):
----------------------------------------------------------------------
  07:00 -    14min (4.5 km)
  07:30 -    14min (4.5 km)
  08:00 -    14min (4.5 km)
  ...

======================================================================
SUMMARY
======================================================================

🚊 Your commute:
  Average: 19min
  Best:    15min
  Worst:   25min

🚗 Girlfriend's commute (with traffic):
  Average: 14min
  Best:    14min
  Worst:   14min

✓ Results saved to cache for future lookups
```

Rows served from the cache are marked with `[cached]`. Times and distances are illustrative. If traffic data is returned for a driving route, it's shown as `(with traffic: 25min)` after the distance, and the summary uses it.

## Configuration Options

All configuration is done via the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_MAPS_API_KEY` | Your Google Maps API key | Required |
| `MY_JOB_LOCATION` | Your job address | Required |
| `GIRLFRIEND_JOB_LOCATION` | Girlfriend's job address | Required |
| `MY_TRAVEL_MODE` | Your transportation mode | `transit` |
| `GIRLFRIEND_TRAVEL_MODE` | Girlfriend's transportation mode | `driving` |
| `START_HOUR` | Start of commute time range (24h format) | `7` |
| `END_HOUR` | End of commute time range (24h format) | `18` |
| `INTERVAL_MINUTES` | Minutes between each calculation (use a divisor of 60, e.g. 15, 20, 30, 60) | `30` |
| `DB_PATH` | Path to cache database file | `commute_cache.db` |

### Travel Modes

Available options for `MY_TRAVEL_MODE` and `GIRLFRIEND_TRAVEL_MODE`:
- `transit` - Public transportation (bus, tram, metro)
- `driving` - Car (includes traffic data)
- `walking` - On foot
- `bicycling` - Bicycle

The 🚊/🚗 icons in the output are fixed labels for the two people and don't change with the selected mode.

### Arrival times

Arrival times run from `START_HOUR:00` to `END_HOUR:00` inclusive, every `INTERVAL_MINUTES`. With the defaults that's 07:00, 07:30, …, 18:00 — **23 time slots**. If `INTERVAL_MINUTES` doesn't divide 60 evenly, the minutes reset at each full hour (e.g. `45` gives 07:00, 07:45, 08:00, 08:45, …).

## How It Works

1. **Address Input**: You provide an apartment address or POI (Point of Interest)
2. **Cache Check**: The app checks if results are already cached for today
3. **API Calls**: If not cached, makes requests to Google Maps Distance Matrix API
4. **Target Date**: Each arrival time is requested for today; if that time has already passed, it is requested for tomorrow
5. **Storage**: Saves all results to SQLite database
6. **Display**: Shows commute times for all configured arrival hours
7. **Summary**: Calculates and displays average, best, and worst case scenarios

## Caching System

- Results are cached per day (`query_date` = the day you run the tool)
- Cache key: origin, destination, travel mode, arrival time, and date
- The origin is matched as an exact string — `"Kazimierz, Kraków"` and `"kazimierz, krakow"` are cached separately. Use `--verify` to normalize addresses to Google's formatted version
- Prevents duplicate API calls for the same location on the same day
- Use `--force-refresh` to bypass cache and get fresh data
- Database file: `commute_cache.db` (SQLite)

## API Costs

Google Maps pricing changed in March 2025 — the $200 monthly credit was replaced by a free usage allowance per API. For the Distance Matrix API (Essentials tier) this is:
- 10,000 free elements per month
- ~$5 per 1,000 elements beyond that

Each apartment lookup uses 2 × 23 = **46 elements** with default settings (23 time slots × 2 people), so the free allowance covers roughly **217 apartment lookups per month**. Cached lookups are free. `--verify` additionally makes one Geocoding API request.

Prices change — check [Google Maps Platform pricing](https://developers.google.com/maps/billing-and-pricing/pricing) for current numbers.

## Tips

1. **Reduce API usage**: Narrow `START_HOUR`/`END_HOUR` or increase `INTERVAL_MINUTES` (e.g. 7–9am at 15-minute intervals is only 9 slots)
2. **Use specific addresses**: More specific addresses give better results
3. **POI support**: You can use landmarks like "Rynek Główny, Kraków"
4. **Check cache**: Run the same location twice - second time is instant (cached)
5. **Verify addresses**: Use `--verify` flag to confirm Google Maps understood your address
6. **Morning commute**: Focus on 7am-9am times as they usually have worst traffic
7. **Save locations**: Keep a list of interesting apartments and batch-check them

## Troubleshooting

### "GOOGLE_MAPS_API_KEY not found"
- Make sure you created the `.env` file
- Check that the API key is correctly copied
- No quotes needed around the API key in `.env`

### "API Error: REQUEST_DENIED"
- Verify Distance Matrix API is enabled in Google Cloud Console
- Check that billing is set up (required even for free tier)
- Ensure API key has proper permissions

### "Error for route: NOT_FOUND" / "ZERO_RESULTS"
- Google couldn't geocode one of the addresses, or no route exists for that mode
- Check `MY_JOB_LOCATION` / `GIRLFRIEND_JOB_LOCATION` in `.env`
- For `transit`, there may be no connection arriving at very early/late times

### "Could not find this address"
- Try more specific address (include city: "Kraków")
- Use Polish street names and formatting
- Try a nearby landmark or POI instead

### Slow performance
- First run for each location takes time (API calls)
- Subsequent runs are instant (cached)
- Consider reducing time range or interval in `.env`

## Known Limitations

- **No traffic data for driving.** The app requests routes by `arrival_time`. Google's Distance Matrix API only returns traffic-aware durations (`duration_in_traffic`) when a `departure_time` is given, and `arrival_time` is only honored for `transit`. In practice, `driving`, `walking` and `bicycling` results are typical durations that don't vary by time of day, and the "(with traffic: …)" annotation is not shown. The summary falls back to the regular duration when traffic data is missing.
- **Results are in Polish.** API requests use `language='pl'`, so resolved addresses from `--verify` are in Polish.
- **One query per time slot.** Requests are made sequentially, so the first lookup for a new address takes a little while.

## Development

Project structure:
```
.
├── commute_calculator.py   # Main CLI application
├── config.py              # Configuration handler
├── cache.py               # SQLite caching system
├── maps_api.py            # Google Maps API wrapper
├── requirements.txt       # Python dependencies
├── .env.example          # Example configuration
├── .env                  # Your configuration (not in git)
└── commute_cache.db      # SQLite database (created on first run)
```

## License

This is a personal utility tool. Use freely for your apartment hunting!

## Contributing

Feel free to extend this tool with additional features:
- Export results to CSV/Excel
- Web interface
- Comparison view for multiple apartments
- Integration with apartment listing sites
- Visualization of commute times on a map

Good luck finding your perfect apartment! 🏠
