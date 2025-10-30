# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python application that generates a static HTML dashboard with interactive Chart.js visualizations for ESPN Fantasy Basketball leagues. The tool fetches data from ESPN's Fantasy API and creates a self-contained HTML file with four charts: Weekly Total Points (line), Standings Progression (step), Top Player Contributions (stacked bar), and Win Margin Distribution (histogram).

## Development Commands

### Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Generate stats dashboard
python generate_stats.py

# View output
start output\league_stats.html  # Windows
open output/league_stats.html   # macOS
```

## Architecture

### Core Data Flow
1. **Data Fetching** (`fetch_league_data()`) - Establishes ESPN API connection using espn-api library
2. **Data Processing** - Four parallel extraction functions process weekly matchup data:
   - `get_weekly_scores()` - Extracts total points per team per week from box scores
   - `get_standings_progression()` - Calculates cumulative win-loss records to derive weekly rankings
   - `get_top_player_contributions()` - Extracts top N scorers per team from player lineups in box scores
   - `get_win_margins()` - Computes absolute point differences between opponents
3. **Data Transformation** (`create_histogram_data()`) - Bins win margins for histogram visualization
4. **HTML Generation** (`generate_html()`) - Embeds all processed data as JSON and generates self-contained HTML with Chart.js initialization

### Key Design Patterns
- **Single-file output**: All CSS, JavaScript, and data are embedded in one HTML file for easy deployment
- **Week iteration**: Most functions iterate through `league.currentMatchupPeriod` to process historical data sequentially
- **Box score parsing**: ESPN API provides `box_scores(matchup_period=week)` which contains both team scores and player lineups
- **Team color mapping**: Static color palette assigned by team index for consistent chart visualization

### Configuration
`settings.py` contains all user-configurable values:
- `LEAGUE_ID`, `YEAR` - ESPN league identification
- `ESPN_S2`, `SWID` - Authentication cookies required for private leagues (obtained from browser dev tools)
- `TOP_PLAYERS_PER_TEAM` - Controls stacked bar chart detail level
- `OUTPUT_DIR`, `OUTPUT_FILENAME` - Controls where HTML is written

### Dependencies
- **espn-api==0.36.0** - ESPN Fantasy API wrapper (provides `League` class and all data access)
- No test framework or build tools (pure Python script)

### Important Constraints
- Requires ESPN Fantasy Basketball Points League (not category-based)
- Authentication cookies (`ESPN_S2`, `SWID`) expire periodically and must be manually refreshed
- Output HTML loads Chart.js from CDN (requires internet to view charts)
- No git repository initialized (see `.gitignore` exists but not initialized)
