# Migration Guide - Routes API Update

## 🎉 What's Been Updated

Your apartment commute calculator has been migrated from the legacy Distance Matrix API to the new Google Routes API with significant improvements:

### New Features Implemented

1. **Traffic Time Ranges (Driving)**
   - Instead of a single number, you now get: `15min-25min (typically 18min)`
   - Uses 3 API calls per time slot: OPTIMISTIC, BEST_GUESS, PESSIMISTIC
   - Helps you plan for worst-case scenarios

2. **Transit Journey Breakdown**
   - Detailed step-by-step breakdown: `Walk 3min → Tram 50 (15min) [Stop A → Stop B] → Walk 2min`
   - Includes transit line numbers, vehicle types, and stop names
   - Shows each segment duration

3. **Day-of-Week Awareness**
   - Separate results for weekday vs weekend
   - Weekday = next Monday, Weekend = next Saturday
   - Critical for accurate transit schedules and traffic patterns

4. **Permanent Cache**
   - Results cached forever (no expiration)
   - Separate cache for weekday/weekend
   - Faster lookups for previously checked locations

5. **Routes API Migration**
   - Uses Google's latest Routes API
   - More accurate predictions
   - Better transit information

## 📋 What You Need to Do

### Step 1: Enable Routes API

1. Go to [Google Cloud Console](https://console.cloud.google.com/google/maps-apis/)
2. Select your project
3. Click "Enable APIs & Services"
4. Search for "Routes API"
5. Click "Enable"

**Important**: The old Distance Matrix API is being deprecated on March 1, 2025!

### Step 2: Update Your .env File

Your `.env` file has been created. Edit it and add your API key:

```bash
nano /home/user/apartment-hunt-commute-time/.env
```

Or open it in your editor and update:

```env
# Add your actual Google Maps API key here
GOOGLE_MAPS_API_KEY=your_actual_api_key_here

# Your job locations (these are examples - update with real addresses)
MY_JOB_LOCATION=Rynek Główny, Kraków
GIRLFRIEND_JOB_LOCATION=AGH University of Science and Technology, Kraków

# Travel modes
MY_TRAVEL_MODE=transit
GIRLFRIEND_TRAVEL_MODE=driving

# Day of week (new!)
DAY_OF_WEEK=weekday

# Time range
START_HOUR=7
END_HOUR=18
INTERVAL_MINUTES=30
```

### Step 3: Clear Old Cache (Optional)

If you have an existing cache database with old results, you can delete it to start fresh:

```bash
rm /home/user/apartment-hunt-commute-time/commute_cache.db
```

The new cache schema is incompatible with the old one, so you'll get better results starting fresh.

### Step 4: Test the Application

Try running with a test location:

```bash
cd /home/user/apartment-hunt-commute-time
python commute_calculator.py "Kazimierz, Kraków"
```

Expected output:
- Transit routes will show step-by-step breakdown
- Driving routes will show time ranges
- You'll see "Target date: YYYY-MM-DD (weekday)"

### Step 5: Try Weekend Comparison

Check how weekends differ:

```bash
python commute_calculator.py --day weekend "Kazimierz, Kraków"
```

You'll likely see:
- Different transit frequencies
- Less traffic for driving
- Different journey times

## 🔧 Files Changed

### New Files
- `routes_api.py` - New Routes API client
- `MIGRATION_GUIDE.md` - This guide

### Modified Files
- `commute_calculator.py` - Complete rewrite to use Routes API
- `config.py` - Added day-of-week handling and target date calculation
- `cache.py` - Updated schema for time ranges and transit steps
- `requirements.txt` - Removed googlemaps dependency (no longer needed)
- `.env.example` - Added DAY_OF_WEEK configuration
- `README.md` - Updated with new features and usage examples

### Deprecated Files
- `maps_api.py` - Old Distance Matrix API wrapper (kept for reference, not used)

## 📊 API Cost Changes

**Before (Distance Matrix API)**:
- 2 people × 23 time slots = 46 requests per location
- $5 per 1,000 requests
- Free tier: ~869 locations/month

**After (Routes API)**:
- Transit: 1 × 23 = 23 requests
- Driving: 3 × 23 = 69 requests (3 traffic models)
- Total: 92 requests per location
- Free tier: ~434 locations/month
- **For 100 locations: Still within $200 free credit!**

## 🐛 Troubleshooting

### "Routes API not enabled"
- Make sure you enabled Routes API in Google Cloud Console
- Check that billing is enabled (required for any Google Maps API)

### "No routes found"
- The Routes API might interpret addresses differently
- Try using more specific addresses
- Check if the route is actually possible with that travel mode

### "HTTP 403 Forbidden"
- Routes API is not enabled
- API key doesn't have permissions
- Billing is not set up

### Different results than before
- This is expected! Routes API is more accurate
- Transit breakdown shows actual stops and transfers
- Traffic ranges give you better planning information

### Field mask errors
- The Routes API field mask might need adjustment
- Check the API documentation for updates
- Open an issue if you see this error

## 🚀 Next Steps

1. **Test thoroughly**: Run on multiple locations to verify accuracy
2. **Compare weekday vs weekend**: You'll see significant differences
3. **Check transit breakdowns**: Verify stop names and line numbers are correct
4. **Validate traffic ranges**: Do the min/max times make sense?

## 📚 Resources

- [Routes API Documentation](https://developers.google.com/maps/documentation/routes)
- [Routes API Migration Guide](https://developers.google.com/maps/documentation/routes/migrate-routes)
- [Google Cloud Console](https://console.cloud.google.com/)

## ✅ Testing Checklist

- [ ] Routes API enabled in Google Cloud Console
- [ ] .env file updated with API key and job locations
- [ ] Tested with a real address - transit mode works
- [ ] Tested with a real address - driving mode works
- [ ] Transit breakdown shows stop names
- [ ] Driving shows time ranges (min-max-typical)
- [ ] Weekday calculation uses next Monday
- [ ] Weekend calculation uses next Saturday
- [ ] Cache works (second run is instant)
- [ ] Results look reasonable

## 🎯 What to Expect

### Transit Output Example
```
07:00 -    18min (3.2 km)
  └─ Walk 3min → Tram 50 (12min) [Kazimierz → Starowiślna] → Walk 3min
```

### Driving Output Example
```
07:00 - 12min-18min (typically 15min) (4.5 km)
```

Good luck testing! If you encounter any issues, check the troubleshooting section above.
