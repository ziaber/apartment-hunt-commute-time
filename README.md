# Apartment Commute Calculator

A terminal application to automate the tedious process of checking commute times from potential apartment locations in Kraków. Calculates commute times for two different job locations with different transportation modes, using real Google Maps traffic data.

## Features

- 🚊 **Multiple transport modes**: Support for transit (tram/bus), driving, walking, and bicycling
- 🕐 **Time-based calculations**: Automatically calculates commute times for arrival hours from 7am to 6pm (configurable)
- 💾 **Smart caching**: Stores results in SQLite database to avoid duplicate API calls
- 📊 **Summary statistics**: Displays average, best, and worst commute times
- 🌍 **Real traffic data**: Uses Google Maps API for accurate, traffic-aware calculations

## Requirements

- Python 3.7 or higher
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
   - Enable the **Distance Matrix API**
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

🚗 Girlfriend's commute to AGH, Kraków (via driving):
----------------------------------------------------------------------
  07:00 -    12min (4.5 km) (with traffic: 18min)
  07:30 -    12min (4.5 km) (with traffic: 25min)
  08:00 -    12min (4.5 km) (with traffic: 30min)
  ...

======================================================================
SUMMARY
======================================================================

🚊 Your commute:
  Average: 19min
  Best:    15min
  Worst:   25min

🚗 Girlfriend's commute (with traffic):
  Average: 22min
  Best:    15min
  Worst:   35min

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
| `START_HOUR` | Start of commute time range (24h format) | `7` |
| `END_HOUR` | End of commute time range (24h format) | `18` |
| `INTERVAL_MINUTES` | Minutes between each calculation | `30` |
| `DB_PATH` | Path to cache database file | `commute_cache.db` |

### Travel Modes

Available options for `MY_TRAVEL_MODE` and `GIRLFRIEND_TRAVEL_MODE`:
- `transit` - Public transportation (bus, tram, metro)
- `driving` - Car (includes traffic data)
- `walking` - On foot
- `bicycling` - Bicycle

## How It Works

1. **Address Input**: You provide an apartment address or POI (Point of Interest)
2. **Cache Check**: The app checks if results are already cached for today
3. **API Calls**: If not cached, makes requests to Google Maps Distance Matrix API
4. **Traffic Data**: For driving mode, includes real-time traffic estimates
5. **Storage**: Saves all results to SQLite database
6. **Display**: Shows commute times for all configured arrival hours
7. **Summary**: Calculates and displays average, best, and worst case scenarios

## Caching System

- Results are cached per day (query_date)
- Cache includes: origin, destination, travel mode, arrival time, and date
- Prevents duplicate API calls for the same location on the same day
- Use `--force-refresh` to bypass cache and get fresh data
- Database file: `commute_cache.db` (SQLite)

## API Costs

Google Maps Distance Matrix API pricing (as of 2024):
- $5 per 1000 requests
- First $200/month is free (covers ~40,000 requests)
- Each apartment location requires 2 × 23 = 46 API calls (23 time slots × 2 people)
- With free tier: ~869 apartment locations per month

## Tips

1. **Use specific addresses**: More specific addresses give better results
2. **POI support**: You can use landmarks like "Rynek Główny, Kraków"
3. **Check cache**: Run the same location twice - second time is instant (cached)
4. **Verify addresses**: Use `--verify` flag to confirm Google Maps understood your address
5. **Morning commute**: Focus on 7am-9am times as they usually have worst traffic
6. **Save locations**: Keep a list of interesting apartments and batch-check them

## Troubleshooting

### "GOOGLE_MAPS_API_KEY not found"
- Make sure you created the `.env` file
- Check that the API key is correctly copied
- No quotes needed around the API key in `.env`

### "API Error: REQUEST_DENIED"
- Verify Distance Matrix API is enabled in Google Cloud Console
- Check that billing is set up (required even for free tier)
- Ensure API key has proper permissions

### "Could not find this address"
- Try more specific address (include city: "Kraków")
- Use Polish street names and formatting
- Try a nearby landmark or POI instead

### Slow performance
- First run for each location takes time (API calls)
- Subsequent runs are instant (cached)
- Consider reducing time range or interval in `.env`

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
