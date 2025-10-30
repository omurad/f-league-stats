"""
ESPN Fantasy Basketball League Configuration

To get your espn_s2 and swid values:
1. Log in to your ESPN Fantasy Basketball league in a web browser
2. Open Developer Tools (F12)
3. Go to Application > Cookies > espn.com
4. Copy the values for 'espn_s2' and 'SWID'

Note: For public leagues, you can leave espn_s2 and swid as None
"""

# Your ESPN Fantasy Basketball League ID
# Found in the URL: https://fantasy.espn.com/basketball/league?leagueId=YOUR_LEAGUE_ID
LEAGUE_ID = 73608366  # Replace with your actual league ID

# Season year
YEAR = 2026  # Replace with the season year you want to analyze

# Authentication cookies (required for private leagues only)
ESPN_S2 = None  # Replace with your espn_s2 cookie value
# Replace with your SWID cookie value (format: {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX})
SWID = None

# Output settings
OUTPUT_DIR = "output"
OUTPUT_FILENAME = "league_stats.html"

# Chart settings
TOP_PLAYERS_PER_TEAM = 5  # Number of top players to show in stacked bar chart

TEAM_1_LOGO_URL = "https://i.redd.it/9gwy9lt732091.jpg"
TEAM_2_LOGO_URL = "https://g.espncdn.com/lm-static/logo-packs/fba/Jerseys-ESPN/fba-jerseys-07.svg"
TEAM_3_LOGO_URL = "https://g.espncdn.com/lm-static/fba/images/default_logos/20.svg"
TEAM_4_LOGO_URL = "https://g.espncdn.com/lm-static/fba/images/default_logos/1.svg"
TEAM_5_LOGO_URL = "https://i1.sndcdn.com/avatars-000416422656-cgstbk-t500x500.jpg"
TEAM_6_LOGO_URL = "https://g.espncdn.com/lm-static/logo-packs/core/BobsBurgers/Bob_OnModel.svg"
TEAM_7_LOGO_URL = "https://g.espncdn.com/lm-static/fba/images/default_logos/16.svg"
TEAM_8_LOGO_URL = "https://g.espncdn.com/lm-static/logo-packs/core/RalphBreaksTheInternet/ralph-11.svg"
TEAM_9_LOGO_URL = "https://g.espncdn.com/lm-static/fba/images/default_logos/3.svg"
TEAM_10_LOGO_URL = "https://g.espncdn.com/lm-static/logo-packs/core/OldTimeMickeyAndFriends/Basketball_Mickey.svg"
