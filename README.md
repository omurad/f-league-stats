# ESPN Fantasy Basketball Stats Generator

A Python application that generates a beautiful, static HTML dashboard with interactive charts for your ESPN Fantasy Basketball league. Perfect for sharing stats with your league members!

## Features

The generated dashboard includes four interactive charts:

1. **Weekly Total Points** (Line Chart) - Track each team's scoring performance week-by-week
2. **Standings Progression** (Step Chart) - Visualize how team rankings have changed throughout the season
3. **Top Player Contributions** (Stacked Bar Chart) - See which players carried their teams each week
4. **Win Margin Distribution** (Histogram) - Analyze how close your league's matchups have been

## Requirements

- Python 3.7 or higher
- ESPN Fantasy Basketball League (Points League)

## Installation

### 1. Clone or download this repository

```bash
cd fantasy-bball-league-stats
```

### 2. Create a virtual environment (recommended)

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Edit `settings.py`

Open `settings.py` and configure your league details:

```python
LEAGUE_ID = 123456789  # Your ESPN league ID
YEAR = 2025            # Season year
ESPN_S2 = None         # Required for private leagues
SWID = None            # Required for private leagues
```

### 2. Finding Your League ID

Your league ID is in the ESPN Fantasy Basketball URL:
```
https://fantasy.espn.com/basketball/league?leagueId=YOUR_LEAGUE_ID
```

### 3. Getting ESPN Authentication Cookies (Private Leagues Only)

If your league is private, you'll need to provide authentication cookies:

1. Log in to your ESPN Fantasy Basketball league in a web browser
2. Open Developer Tools (F12 or Right-click → Inspect)
3. Go to the **Application** tab (Chrome) or **Storage** tab (Firefox)
4. Navigate to **Cookies** → `espn.com`
5. Find and copy the values for:
   - `espn_s2` - A long string
   - `SWID` - Format: `{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}`

6. Update `settings.py`:
```python
ESPN_S2 = "your_espn_s2_value_here"
SWID = "{your-swid-value-here}"
```

**Note:** For public leagues, you can leave these as `None`.

## Usage

### Generate the Stats Dashboard

With your virtual environment activated, run:

```bash
python generate_stats.py
```

You'll see output like:
```
============================================================
ESPN Fantasy Basketball Stats Generator
============================================================
Connecting to ESPN league 123456789 for year 2025...
✓ Connected successfully to: My Awesome League
  Teams: 10
  Current Week: 12

Fetching weekly scores...
  Processing week 1...
  Processing week 2...
  ...
✓ Fetched 12 weeks of data for 10 teams

Calculating standings progression...
  ...
✓ Calculated standings for 12 weeks

Fetching top player contributions...
  ...
✓ Fetched player contributions for 12 weeks

Calculating win margins...
✓ Calculated 60 matchup margins

Generating HTML...

============================================================
✓ SUCCESS!
============================================================
HTML file generated: output/league_stats.html
Open this file in your web browser to view the stats dashboard.
============================================================
```

### View the Dashboard

Open the generated file in your web browser:

**On Windows:**
```bash
start output\league_stats.html
```

**On macOS:**
```bash
open output/league_stats.html
```

**On Linux:**
```bash
xdg-open output/league_stats.html
```

Or simply navigate to the `output` folder and double-click `league_stats.html`.

## Deployment

The generated HTML file is completely self-contained (except for Chart.js loaded from CDN). You can:

1. **Upload to any web hosting** - Just upload the single HTML file
2. **Share via file sharing** - Send the HTML file directly to league members
3. **Host on GitHub Pages** - Commit the output file to a GitHub Pages repository
4. **Deploy to Netlify/Vercel** - Drag and drop the HTML file

## Customization

### Adjust Settings

In `settings.py`, you can modify:

```python
TOP_PLAYERS_PER_TEAM = 5  # Number of top scorers shown in the stacked bar chart
OUTPUT_DIR = "output"      # Where to save the HTML file
OUTPUT_FILENAME = "league_stats.html"  # Name of the output file
```

### Styling

The dashboard uses a dark theme by default. To customize colors, edit the CSS in `generate_stats.py` within the `generate_html()` function.

### Chart Colors

Team colors are automatically assigned from a predefined palette. To customize, modify the `colors` list in the `generate_html()` function.

## Troubleshooting

### Authentication Issues

**Error:** `Exception: Unable to access league data`

- **Solution:** Verify your `LEAGUE_ID` is correct
- For private leagues, ensure your `ESPN_S2` and `SWID` cookies are up-to-date (they expire periodically)

### No Data Available

**Error:** No weeks or matchups found

- **Solution:** Ensure the season has started and games have been played
- Verify the `YEAR` in settings matches the season you want to analyze

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'espn_api'`

- **Solution:** Ensure you've activated your virtual environment and installed requirements:
```bash
# Activate venv first
pip install -r requirements.txt
```

## Project Structure

```
fantasy-bball-league-stats/
├── generate_stats.py      # Main script - fetches data and generates HTML
├── settings.py            # Configuration file for league credentials
├── requirements.txt       # Python dependencies
├── CHECKLIST.md          # Implementation checklist
├── README.md             # This file
└── output/
    └── league_stats.html # Generated dashboard (after running script)
```

## Technical Details

- **Data Source:** ESPN Fantasy API via [espn-api](https://github.com/cwendt94/espn-api) library
- **Charts:** [Chart.js](https://www.chartjs.org/) v4.4.0
- **Output:** Single self-contained HTML file with embedded CSS and JavaScript

## License

This project uses the espn-api library, which is licensed under MIT.

## Support

For issues with:
- **ESPN API:** Visit [cwendt94/espn-api](https://github.com/cwendt94/espn-api)
- **This project:** Check CHECKLIST.md for implementation details

## Credits

Built with:
- [espn-api](https://github.com/cwendt94/espn-api) by cwendt94
- [Chart.js](https://www.chartjs.org/) for interactive charts

---

**Enjoy your stats dashboard!** 🏀📊
