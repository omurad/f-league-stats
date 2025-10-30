#!/usr/bin/env python3
"""
ESPN Fantasy Basketball Stats Generator

Generates a static HTML page with interactive charts showing league statistics.
"""

import json
import os
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any

from espn_api.basketball import League

import settings


def fetch_league_data():
    """
    Connect to ESPN API and fetch all league data.

    Returns:
        League: ESPN League object with all data
    """
    print(
        f"Connecting to ESPN league {settings.LEAGUE_ID} for year {settings.YEAR}...")

    try:
        league = League(
            league_id=settings.LEAGUE_ID,
            year=settings.YEAR,
            espn_s2=settings.ESPN_S2,
            swid=settings.SWID
        )
        print(f"✓ Connected successfully to: {league.settings.name}")
        print(f"  Teams: {len(league.teams)}")
        print(f"  Current Week: {league.currentMatchupPeriod}")
        return league
    except Exception as e:
        print(f"✗ Error connecting to league: {e}")
        raise


def get_team_logos(league: League) -> Dict[str, str]:
    """
    Map team abbreviations to hardcoded logo URLs from settings.

    Returns:
        Dict mapping team abbreviations to logo URLs
    """
    print("\nMapping team logos from settings...")

    team_logos = {}

    # List of logo URL attributes from settings
    logo_urls = [
        settings.TEAM_1_LOGO_URL,
        settings.TEAM_2_LOGO_URL,
        settings.TEAM_3_LOGO_URL,
        settings.TEAM_4_LOGO_URL,
        settings.TEAM_5_LOGO_URL,
        settings.TEAM_6_LOGO_URL,
        settings.TEAM_7_LOGO_URL,
        settings.TEAM_8_LOGO_URL,
        settings.TEAM_9_LOGO_URL,
        settings.TEAM_10_LOGO_URL,
    ]

    # Map teams by their index to logo URLs
    for idx, team in enumerate(league.teams):
        if idx < len(logo_urls) and logo_urls[idx]:
            team_logos[team.team_abbrev] = logo_urls[idx]
            print(f"  ✓ {team.team_abbrev} -> Logo {idx + 1}")
        else:
            print(f"  ✗ No logo configured for {team.team_abbrev}")

    print(f"✓ Mapped logos for {len(team_logos)} teams")

    return team_logos


def get_weekly_scores(league: League) -> Dict[str, Any]:
    """
    Fetch weekly total points for each team.

    Returns:
        Dict with structure:
        {
            'weeks': [1, 2, 3, ...],
            'teams': {
                'Team Abbrev': [score_week1, score_week2, ...],
                ...
            }
        }
    """
    print("\nFetching weekly scores...")

    weekly_data = defaultdict(list)
    weeks = []

    # Get the number of weeks to process
    current_week = league.currentMatchupPeriod

    for week in range(1, current_week + 1):
        weeks.append(week)
        print(f"  Processing week {week}...")

        # Get box scores for this week
        box_scores = league.box_scores(matchup_period=week)

        # Track which teams we've seen this week
        teams_this_week = {}

        for box in box_scores:
            # Get home team score
            if box.home_team:
                team_abbrev = box.home_team.team_abbrev
                teams_this_week[team_abbrev] = box.home_score

            # Get away team score
            if box.away_team:
                team_abbrev = box.away_team.team_abbrev
                teams_this_week[team_abbrev] = box.away_score

        # Add scores for all teams (in consistent order)
        for team in league.teams:
            score = teams_this_week.get(team.team_abbrev, 0)
            weekly_data[team.team_abbrev].append(score)

    print(f"✓ Fetched {len(weeks)} weeks of data for {len(weekly_data)} teams")

    return {
        'weeks': weeks,
        'teams': dict(weekly_data)
    }


def get_cumulative_points(weekly_scores: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate cumulative total points for each team across weeks.

    Args:
        weekly_scores: Output from get_weekly_scores() function

    Returns:
        Dict with structure:
        {
            'weeks': [1, 2, 3, ...],
            'teams': {
                'Team Abbrev': [cumulative_week1, cumulative_week2, ...],
                ...
            }
        }
    """
    print("\nCalculating cumulative points...")

    cumulative_data = {}
    weeks = weekly_scores['weeks']

    for team_abbrev, weekly_points in weekly_scores['teams'].items():
        cumulative_points = []
        running_total = 0

        for points in weekly_points:
            running_total += points
            cumulative_points.append(running_total)

        cumulative_data[team_abbrev] = cumulative_points

    print(f"✓ Calculated cumulative points for {len(cumulative_data)} teams")

    return {
        'weeks': weeks,
        'teams': cumulative_data
    }


def get_standings_progression(league: League) -> Dict[str, Any]:
    """
    Calculate team rankings for each week.

    Returns:
        Dict with structure:
        {
            'weeks': [1, 2, 3, ...],
            'teams': {
                'Team Abbrev': [rank_week1, rank_week2, ...],
                ...
            }
        }
    """
    print("\nCalculating standings progression...")

    current_week = league.currentMatchupPeriod
    weeks = list(range(1, current_week + 1))

    # Track cumulative wins for each team
    team_records = {team.team_abbrev: {'wins': 0, 'losses': 0}
                    for team in league.teams}
    standings_by_week = []

    for week in weeks:
        print(f"  Processing week {week} standings...")
        box_scores = league.box_scores(matchup_period=week)

        # Update records based on this week's results
        for box in box_scores:
            if box.home_team and box.away_team:
                home_abbrev = box.home_team.team_abbrev
                away_abbrev = box.away_team.team_abbrev

                if box.winner == 'HOME':
                    team_records[home_abbrev]['wins'] += 1
                    team_records[away_abbrev]['losses'] += 1
                elif box.winner == 'AWAY':
                    team_records[away_abbrev]['wins'] += 1
                    team_records[home_abbrev]['losses'] += 1
                # Ties are possible but rare in points leagues

        # Rank teams by wins (then by losses if tied)
        ranked_teams = sorted(
            team_records.items(),
            key=lambda x: (x[1]['wins'], -x[1]['losses']),
            reverse=True
        )

        # Store rankings for this week
        week_rankings = {team_abbrev: rank + 1 for rank,
                         (team_abbrev, _) in enumerate(ranked_teams)}
        standings_by_week.append(week_rankings)

    # Transpose data to be team-centric
    team_standings = defaultdict(list)
    for week_rankings in standings_by_week:
        for team_abbrev in team_records.keys():
            team_standings[team_abbrev].append(
                week_rankings.get(team_abbrev, len(team_records)))

    print(f"✓ Calculated standings for {len(weeks)} weeks")

    return {
        'weeks': weeks,
        'teams': dict(team_standings)
    }


def get_top_player_contributions(league: League) -> Dict[str, Any]:
    """
    Get top player contributions for each team by week.

    Returns:
        Dict with structure for each week and team showing top players
    """
    print("\nFetching top player contributions...")

    current_week = league.currentMatchupPeriod
    weeks = list(range(1, current_week + 1))

    # Structure: {week: {team_name: [(player_name, points), ...]}}
    contributions = {}

    for week in weeks:
        print(f"  Processing week {week} player stats...")
        contributions[week] = {}

        box_scores = league.box_scores(matchup_period=week)

        for box in box_scores:
            # Process home team
            if box.home_team:
                team_abbrev = box.home_team.team_abbrev
                player_stats = []

                for player in box.home_lineup:
                    if hasattr(player, 'points') and player.points > 0:
                        player_stats.append({
                            'name': player.name,
                            'points': player.points,
                            'playerId': player.playerId if hasattr(player, 'playerId') else None
                        })

                # Sort by points and take top N
                player_stats.sort(key=lambda x: x['points'], reverse=True)
                contributions[week][team_abbrev] = player_stats[:settings.TOP_PLAYERS_PER_TEAM]

            # Process away team
            if box.away_team:
                team_abbrev = box.away_team.team_abbrev
                player_stats = []

                for player in box.away_lineup:
                    if hasattr(player, 'points') and player.points > 0:
                        player_stats.append({
                            'name': player.name,
                            'points': player.points,
                            'playerId': player.playerId if hasattr(player, 'playerId') else None
                        })

                # Sort by points and take top N
                player_stats.sort(key=lambda x: x['points'], reverse=True)
                contributions[week][team_abbrev] = player_stats[:settings.TOP_PLAYERS_PER_TEAM]

    print(f"✓ Fetched player contributions for {len(weeks)} weeks")

    return {
        'weeks': weeks,
        'contributions': contributions
    }


def get_top_team_by_week(league: League) -> Dict[str, Any]:
    """
    Get the team with the most points each week.

    Returns:
        Dict with structure:
        {
            'weeks': [1, 2, 3, ...],
            'top_teams': {
                1: {'team': 'Team Name', 'points': 123.4},
                2: {...},
                ...
            }
        }
    """
    print("\nFetching top team by week...")

    current_week = league.currentMatchupPeriod
    weeks = list(range(1, current_week + 1))
    top_teams = {}

    for week in weeks:
        print(f"  Processing week {week} top team...")
        box_scores = league.box_scores(matchup_period=week)

        week_scores = {}

        for box in box_scores:
            # Get home team score
            if box.home_team:
                team_abbrev = box.home_team.team_abbrev
                week_scores[team_abbrev] = box.home_score

            # Get away team score
            if box.away_team:
                team_abbrev = box.away_team.team_abbrev
                week_scores[team_abbrev] = box.away_score

        # Find team with highest score
        if week_scores:
            top_team = max(week_scores.items(), key=lambda x: x[1])
            top_teams[week] = {
                'team': top_team[0],
                'points': top_team[1]
            }

    print(f"✓ Fetched top team for {len(weeks)} weeks")

    return {
        'weeks': weeks,
        'top_teams': top_teams
    }


def get_top_players_by_week(league: League) -> Dict[str, Any]:
    """
    Get the top 3 players with the most points each week across all teams.

    Returns:
        Dict with structure:
        {
            'weeks': [1, 2, 3, ...],
            'top_players': {
                1: [{'name': 'Player Name', 'points': 123.4, 'playerId': 123, 'team': 'Team Name'}, ...],
                2: [...],
                ...
            }
        }
    """
    print("\nFetching top players by week...")

    current_week = league.currentMatchupPeriod
    weeks = list(range(1, current_week + 1))
    top_players = {}

    for week in weeks:
        print(f"  Processing week {week} top players...")
        all_players = []

        box_scores = league.box_scores(matchup_period=week)

        for box in box_scores:
            # Process home team
            if box.home_team:
                team_abbrev = box.home_team.team_abbrev
                for player in box.home_lineup:
                    if hasattr(player, 'points') and player.points > 0:
                        all_players.append({
                            'name': player.name,
                            'points': player.points,
                            'playerId': player.playerId if hasattr(player, 'playerId') else None,
                            'team': team_abbrev
                        })

            # Process away team
            if box.away_team:
                team_abbrev = box.away_team.team_abbrev
                for player in box.away_lineup:
                    if hasattr(player, 'points') and player.points > 0:
                        all_players.append({
                            'name': player.name,
                            'points': player.points,
                            'playerId': player.playerId if hasattr(player, 'playerId') else None,
                            'team': team_abbrev
                        })

        # Sort by points and take top 3
        all_players.sort(key=lambda x: x['points'], reverse=True)
        top_players[week] = all_players[:3]

    print(f"✓ Fetched top 3 players for {len(weeks)} weeks")

    return {
        'weeks': weeks,
        'top_players': top_players
    }


def get_top_player_performances(league: League) -> Dict[str, Any]:
    """
    Get the top 3 highest scoring performances by any player in a single week.

    Returns:
        Dict with structure:
        {
            'top_performances': [
                {
                    'name': 'Player Name',
                    'playerId': 123,
                    'points': 123.4,
                    'week': 5,
                    'team': 'Team Abbrev'
                },
                ...
            ]
        }
    """
    print("\nFetching top player performances...")

    current_week = league.currentMatchupPeriod
    all_performances = []

    for week in range(1, current_week + 1):
        print(f"  Processing week {week} performances...")
        box_scores = league.box_scores(matchup_period=week)

        for box in box_scores:
            # Process home team
            if box.home_team:
                team_abbrev = box.home_team.team_abbrev
                for player in box.home_lineup:
                    if hasattr(player, 'points') and player.points > 0:
                        all_performances.append({
                            'name': player.name,
                            'playerId': player.playerId if hasattr(player, 'playerId') else None,
                            'points': player.points,
                            'week': week,
                            'team': team_abbrev
                        })

            # Process away team
            if box.away_team:
                team_abbrev = box.away_team.team_abbrev
                for player in box.away_lineup:
                    if hasattr(player, 'points') and player.points > 0:
                        all_performances.append({
                            'name': player.name,
                            'playerId': player.playerId if hasattr(player, 'playerId') else None,
                            'points': player.points,
                            'week': week,
                            'team': team_abbrev
                        })

    # Sort by points and take top 3
    all_performances.sort(key=lambda x: x['points'], reverse=True)
    top_3 = all_performances[:3]

    print(
        f"✓ Found top 3 performances from {len(all_performances)} total performances")

    return {
        'top_performances': top_3
    }


def get_all_play_records(league: League) -> Dict[str, Any]:
    """
    Calculate all-play records where each team's score is compared against
    every other team's score each week.

    In a standard week, each team plays one opponent. This function calculates
    how each team would perform if they played against ALL other teams each week.

    Returns:
        Dict with structure:
        {
            'weeks': [1, 2, 3, ...],
            'teams': {
                'Team Abbrev': {
                    'weekly_wins': [wins_week1, wins_week2, ...],
                    'weekly_losses': [losses_week1, losses_week2, ...],
                    'cumulative_wins': total_wins,
                    'cumulative_losses': total_losses,
                    'win_percentage': win_pct
                },
                ...
            }
        }
    """
    print("\nCalculating all-play records...")

    current_week = league.currentMatchupPeriod
    weeks = list(range(1, current_week + 1))

    # Initialize tracking for all teams
    team_data = {team.team_abbrev: {
        'weekly_wins': [],
        'weekly_losses': [],
        'cumulative_wins': 0,
        'cumulative_losses': 0
    } for team in league.teams}

    for week in weeks:
        print(f"  Processing week {week} all-play records...")
        box_scores = league.box_scores(matchup_period=week)

        # Get all team scores for this week
        week_scores = {}
        for box in box_scores:
            if box.home_team:
                week_scores[box.home_team.team_abbrev] = box.home_score
            if box.away_team:
                week_scores[box.away_team.team_abbrev] = box.away_score

        # For each team, calculate wins/losses against all other teams
        for team_abbrev, team_score in week_scores.items():
            wins = 0
            losses = 0

            for opponent_abbrev, opponent_score in week_scores.items():
                if opponent_abbrev != team_abbrev:
                    if team_score > opponent_score:
                        wins += 1
                    elif team_score < opponent_score:
                        losses += 1
                    # Ties are not counted as wins or losses

            team_data[team_abbrev]['weekly_wins'].append(wins)
            team_data[team_abbrev]['weekly_losses'].append(losses)
            team_data[team_abbrev]['cumulative_wins'] += wins
            team_data[team_abbrev]['cumulative_losses'] += losses

    # Calculate win percentages
    for team_abbrev in team_data:
        total_wins = team_data[team_abbrev]['cumulative_wins']
        total_losses = team_data[team_abbrev]['cumulative_losses']
        total_games = total_wins + total_losses

        if total_games > 0:
            team_data[team_abbrev]['win_percentage'] = total_wins / total_games
        else:
            team_data[team_abbrev]['win_percentage'] = 0.0

    print(f"✓ Calculated all-play records for {len(weeks)} weeks")

    return {
        'weeks': weeks,
        'teams': team_data
    }


def get_win_margins(league: League) -> List[float]:
    """
    Get all win margins from completed matchups.

    Returns:
        List of win margins (absolute values)
    """
    print("\nCalculating win margins...")

    current_week = league.currentMatchupPeriod
    margins = []

    for week in range(1, current_week + 1):
        box_scores = league.box_scores(matchup_period=week)

        for box in box_scores:
            if box.home_score > 0 and box.away_score > 0:
                margin = abs(box.home_score - box.away_score)
                margins.append(margin)

    print(f"✓ Calculated {len(margins)} matchup margins")

    return margins


def create_histogram_data(margins: List[float], num_bins: int = 10) -> Dict[str, Any]:
    """
    Create histogram data from win margins.

    Args:
        margins: List of margin values
        num_bins: Number of bins for the histogram

    Returns:
        Dict with bin labels and counts
    """
    if not margins:
        return {'labels': [], 'counts': []}

    # Calculate bin edges
    min_margin = 0
    max_margin = max(margins)
    bin_width = (max_margin - min_margin) / num_bins

    # Create bins
    bins = []
    counts = []

    for i in range(num_bins):
        bin_start = min_margin + (i * bin_width)
        bin_end = bin_start + bin_width

        # Count margins in this bin
        count = sum(1 for m in margins if bin_start <= m < bin_end)

        # Special case for last bin to include the max value
        if i == num_bins - 1:
            count = sum(1 for m in margins if bin_start <= m <= bin_end)

        bins.append(f"{bin_start:.0f}-{bin_end:.0f}")
        counts.append(count)

    return {
        'labels': bins,
        'counts': counts
    }


def generate_html(league: League, data: Dict[str, Any]) -> str:
    """
    Generate the complete HTML page with embedded data and charts.

    Args:
        league: ESPN League object
        data: Dictionary containing all processed chart data

    Returns:
        Complete HTML string
    """
    print("\nGenerating HTML...")

    # Generate color palette for teams
    colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384',
        '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'
    ]

    team_colors = {}
    team_names = {}
    for idx, team in enumerate(league.teams):
        team_colors[team.team_abbrev] = colors[idx % len(colors)]
        team_names[team.team_abbrev] = team.team_name

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{league.settings.name} Stats</title>
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #0f1419;
            color: #e4e6eb;
            padding: 20px;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
        }}

        header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px 20px;
            background: linear-gradient(135deg, #1e2732 0%, #2d3748 100%);
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}

        h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            color: #fff;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }}

        .subtitle {{
            font-size: 1.1rem;
            color: #a0aec0;
            margin-bottom: 15px;
        }}

        .meta {{
            font-size: 0.9rem;
            color: #718096;
        }}

        @media (max-width: 768px) {{
            header {{
                margin-bottom: 20px;
                padding: 20px 15px;
                border-radius: 8px;
            }}

            h1 {{
                font-size: 1.75rem;
            }}

            .subtitle {{
                font-size: 0.95rem;
            }}

            .meta {{
                font-size: 0.8rem;
            }}
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}

        .chart-container {{
            background: #1a202c;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border: 1px solid #2d3748;
        }}

        .chart-container h2 {{
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: #fff;
            border-bottom: 2px solid #4299e1;
            padding-bottom: 10px;
        }}

        .chart-wrapper {{
            position: relative;
            height: 400px;
        }}

        .player-contributions-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            padding: 10px 0;
        }}

        .team-card {{
            background: #2d3748;
            border-radius: 8px;
            padding: 15px;
            border: 1px solid #4a5568;
        }}

        .team-card h3 {{
            font-size: 1.1rem;
            margin-bottom: 15px;
            color: #fff;
            border-bottom: 2px solid #4299e1;
            padding-bottom: 8px;
        }}

        @media (max-width: 768px) {{
            .player-contributions-grid {{
                grid-template-columns: 1fr;
                gap: 15px;
            }}

            .team-card {{
                padding: 12px;
            }}

            .team-card h3 {{
                font-size: 1rem;
                margin-bottom: 12px;
            }}
        }}

        .player-item {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            background: #1a202c;
            border-radius: 6px;
            padding: 8px;
            transition: transform 0.2s;
        }}

        .player-item:hover {{
            transform: translateX(5px);
            background: #2d3748;
        }}

        .player-photo {{
            width: 50px;
            height: 50px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #4299e1;
            margin-right: 12px;
            background: #2d3748;
        }}

        .player-photo-error {{
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin-right: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            font-size: 1.2rem;
            border: 2px solid #4299e1;
        }}

        .player-info {{
            flex: 1;
            min-width: 0;
        }}

        .player-name {{
            font-weight: 600;
            color: #e4e6eb;
            font-size: 0.95rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .player-points {{
            color: #4299e1;
            font-weight: 700;
            font-size: 1.1rem;
        }}

        .points-bar {{
            height: 4px;
            background: #4299e1;
            border-radius: 2px;
            margin-top: 4px;
            transition: width 0.3s ease;
        }}

        .full-width {{
            grid-column: 1 / -1;
        }}

        .week-selector {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 20px;
            justify-content: center;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            padding: 5px 0;
        }}

        .week-button {{
            padding: 8px 16px;
            background: #2d3748;
            border: 2px solid #4a5568;
            border-radius: 6px;
            color: #e4e6eb;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: 600;
            white-space: nowrap;
            min-height: 44px;
            min-width: 44px;
        }}

        .week-button:hover {{
            background: #4a5568;
            border-color: #4299e1;
        }}

        .week-button.active {{
            background: #4299e1;
            border-color: #4299e1;
            color: white;
        }}

        @media (max-width: 768px) {{
            .week-selector {{
                gap: 6px;
                justify-content: flex-start;
            }}

            .week-button {{
                padding: 10px 14px;
                font-size: 0.9rem;
                min-height: 48px;
                min-width: 48px;
            }}
        }}

        .top-players-display {{
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            padding: 20px 0;
        }}

        .top-player-card {{
            background: #2d3748;
            border-radius: 12px;
            padding: 20px;
            width: 280px;
            text-align: center;
            border: 2px solid #4a5568;
            position: relative;
            transition: transform 0.2s, border-color 0.2s;
        }}

        .top-player-card:hover {{
            transform: translateY(-4px);
            border-color: #4299e1;
        }}

        @media (max-width: 768px) {{
            .top-players-display {{
                gap: 15px;
                padding: 15px 0;
            }}

            .top-player-card {{
                width: 100%;
                max-width: 320px;
                padding: 15px;
            }}

            .top-player-card:hover {{
                transform: none;
            }}
        }}

        .top-player-card.rank-1 {{
            border-color: #ffd700;
        }}

        .top-player-card.rank-2 {{
            border-color: #c0c0c0;
        }}

        .top-player-card.rank-3 {{
            border-color: #cd7f32;
        }}

        .rank-badge {{
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1rem;
            border: 3px solid #1a202c;
        }}

        .rank-badge.rank-1 {{
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            color: #333;
        }}

        .rank-badge.rank-2 {{
            background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
            color: #333;
        }}

        .rank-badge.rank-3 {{
            background: linear-gradient(135deg, #cd7f32 0%, #e6a157 100%);
            color: white;
        }}

        .top-player-photo {{
            width: 120px;
            height: 120px;
            border-radius: 50%;
            object-fit: cover;
            border: 4px solid #4299e1;
            margin: 15px auto 15px;
            background: #2d3748;
        }}

        .top-player-photo-error {{
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 15px auto 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            font-size: 2.5rem;
            border: 4px solid #4299e1;
        }}

        .top-player-name {{
            font-size: 1.2rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 8px;
        }}

        .top-player-team {{
            font-size: 0.9rem;
            color: #a0aec0;
            margin-bottom: 12px;
        }}

        .top-player-points {{
            font-size: 2rem;
            font-weight: 700;
            color: #4299e1;
        }}

        @media (max-width: 768px) {{
            .top-player-photo,
            .top-player-photo-error {{
                width: 100px;
                height: 100px;
                margin: 10px auto 10px;
                border-width: 3px;
            }}

            .top-player-photo-error {{
                font-size: 2rem;
            }}

            .top-player-name {{
                font-size: 1.1rem;
            }}

            .top-player-team {{
                font-size: 0.85rem;
            }}

            .top-player-points {{
                font-size: 1.75rem;
            }}
        }}

        .top-team-display {{
            display: flex;
            justify-content: center;
            padding: 20px 0;
        }}

        .top-team-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            padding: 30px 40px;
            min-width: 320px;
            text-align: center;
            border: 3px solid #ffd700;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
            position: relative;
            transition: transform 0.3s;
        }}

        .top-team-card:hover {{
            transform: scale(1.05);
        }}

        .top-team-trophy {{
            font-size: 4rem;
            margin-bottom: 15px;
        }}

        .top-team-logo {{
            width: 100px;
            height: 100px;
            margin: 0 auto 20px;
            border-radius: 50%;
            border: 4px solid #ffd700;
            background: white;
            padding: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }}

        .top-team-name {{
            font-size: 1.8rem;
            font-weight: 800;
            color: white;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }}

        .top-team-points {{
            font-size: 2.5rem;
            font-weight: 900;
            color: #ffd700;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }}

        .top-team-label {{
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.8);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 5px;
        }}

        @media (max-width: 768px) {{
            .top-team-card {{
                padding: 25px 20px;
                min-width: auto;
                width: 100%;
                max-width: 350px;
                margin: 0 auto;
            }}

            .top-team-card:hover {{
                transform: none;
            }}

            .top-team-trophy {{
                font-size: 3rem;
                margin-bottom: 10px;
            }}

            .top-team-logo {{
                width: 80px;
                height: 80px;
                margin: 0 auto 15px;
                border-width: 3px;
                padding: 8px;
            }}

            .top-team-name {{
                font-size: 1.4rem;
                margin-bottom: 8px;
            }}

            .top-team-points {{
                font-size: 2rem;
            }}

            .top-team-label {{
                font-size: 0.8rem;
            }}
        }}

        footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #718096;
            font-size: 0.9rem;
        }}

        @media (max-width: 768px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}

            .chart-container {{
                padding: 15px;
            }}

            .chart-container h2 {{
                font-size: 1.25rem;
                margin-bottom: 15px;
            }}

            .chart-wrapper {{
                height: 280px;
            }}

            .player-item {{
                padding: 6px;
                margin-bottom: 10px;
            }}

            .player-photo,
            .player-photo-error {{
                width: 40px;
                height: 40px;
                margin-right: 10px;
            }}

            .player-photo-error {{
                font-size: 1rem;
            }}

            .player-name {{
                font-size: 0.9rem;
            }}

            .player-points {{
                font-size: 1rem;
            }}

            .rank-badge {{
                width: 28px;
                height: 28px;
                font-size: 0.9rem;
            }}
        }}

        @media (max-width: 480px) {{
            body {{
                padding: 5px;
            }}

            .chart-container {{
                padding: 12px;
                border-radius: 8px;
            }}

            .chart-wrapper {{
                height: 250px;
            }}

            .top-player-card {{
                max-width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{league.settings.name}</h1>
            <p class="subtitle">Fantasy Basketball Stats Dashboard - {settings.YEAR - 1}-{settings.YEAR} Season</p>
            <p class="meta">Last Updated: {datetime.now().astimezone().strftime('%B %d, %Y at %I:%M %p %z')}</p>
        </header>

        <div class="charts-grid">
            <div class="chart-container full-width">
                <h2>👑 Top Team of the Week</h2>
                <p style="color: #a0aec0; margin-bottom: 15px; font-size: 0.95rem;">
                    Highest scoring team each week based on total fantasy points.
                </p>
                <div class="week-selector" id="topTeamWeekSelector"></div>
                <div class="top-team-display" id="topTeamDisplay"></div>
            </div>

            <div class="chart-container full-width">
                <h2>🎯 All-Play Standings</h2>
                <p style="color: #a0aec0; margin-bottom: 15px; font-size: 0.95rem;">
                    Shows how each team would rank if they played against every other team each week,
                    removing the impact of schedule luck.
                </p>
                <div class="chart-wrapper">
                    <canvas id="allPlayStandingsChart"></canvas>
                </div>
            </div>

            <div class="chart-container full-width">
                <h2>🏆 Top 3 Players of the Week</h2>
                <p style="color: #a0aec0; margin-bottom: 15px; font-size: 0.95rem;">
                    Best individual player performances each week across all teams.
                </p>
                <div class="week-selector" id="weekSelector"></div>
                <div class="top-players-display" id="topPlayersDisplay"></div>
            </div>

            <div class="chart-container full-width">
                <h2>🔥 Top 3 Player Performances of the Season</h2>
                <p style="color: #a0aec0; margin-bottom: 15px; font-size: 0.95rem;">
                    Highest scoring individual performances in a single week this season.
                </p>
                <div class="top-players-display" id="topPerformancesDisplay"></div>
            </div>

            <div class="chart-container full-width">
                <h2>📈 All-Play Win Percentage Progression</h2>
                <p style="color: #a0aec0; margin-bottom: 15px; font-size: 0.95rem;">
                    Track each team's all-play win percentage over time, showing performance trends.
                </p>
                <div class="chart-wrapper">
                    <canvas id="allPlayProgressionChart"></canvas>
                </div>
            </div>

            <div class="chart-container full-width">
                <h2>📈 Weekly Total Points</h2>
                <p style="color: #a0aec0; margin-bottom: 15px; font-size: 0.95rem;">
                    Track each team's total points scored per week throughout the season.
                </p>
                <div class="chart-wrapper">
                    <canvas id="weeklyPointsChart"></canvas>
                </div>
            </div>

            <div class="chart-container full-width">
                <h2>📊 Cumulative Total Points</h2>
                <p style="color: #a0aec0; margin-bottom: 15px; font-size: 0.95rem;">
                    Running total of all points scored by each team over time.
                </p>
                <div class="chart-wrapper">
                    <canvas id="cumulativePointsChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>📊 Standings Progression</h2>
                <p style="color: #a0aec0; margin-bottom: 15px; font-size: 0.95rem;">
                    Track how team rankings change week by week based on actual head-to-head results.
                </p>
                <div class="chart-wrapper">
                    <canvas id="standingsChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>📉 Win Margin Distribution</h2>
                <p style="color: #a0aec0; margin-bottom: 15px; font-size: 0.95rem;">
                    Distribution of point differences in matchups showing competitiveness of games.
                </p>
                <div class="chart-wrapper">
                    <canvas id="marginChart"></canvas>
                </div>
            </div>

            <div class="chart-container full-width">
                <h2>⭐ Top Player Contributions by Team (Week {league.currentMatchupPeriod})</h2>
                <p style="color: #a0aec0; margin-bottom: 15px; font-size: 0.95rem;">
                    Highest scoring players on each team for the most recent week.
                </p>
                <div class="player-contributions-grid" id="playerContributionsGrid"></div>
            </div>
        </div>

        <footer>
            <p>Generated with ESPN API | Data accurate as of {datetime.now().astimezone().strftime('%B %d, %Y at %I:%M %p %z')}</p>
        </footer>
    </div>

    <script>
        // Embedded data
        const weeklyScoresData = {json.dumps(data['weekly_scores'])};
        const cumulativePointsData = {json.dumps(data['cumulative_points'])};
        const standingsData = {json.dumps(data['standings_progression'])};
        const playerContributions = {json.dumps(data['player_contributions'])};
        const topTeamByWeek = {json.dumps(data['top_team_by_week'])};
        const topPlayersByWeek = {json.dumps(data['top_players_by_week'])};
        const topPlayerPerformances = {json.dumps(data['top_player_performances'])};
        const allPlayRecords = {json.dumps(data['all_play_records'])};
        const marginData = {json.dumps(data['win_margins'])};
        const teamColors = {json.dumps(team_colors)};
        const teamNames = {json.dumps(team_names)};
        const teamLogos = {json.dumps(data['team_logos'])};

        // Chart.js default settings for dark theme
        Chart.defaults.color = '#e4e6eb';
        Chart.defaults.borderColor = '#2d3748';

        // Load team logo images
        const teamLogoImages = {{}};
        Object.keys(teamLogos).forEach(teamName => {{
            if (teamLogos[teamName]) {{
                const img = new Image(30, 30);
                img.src = teamLogos[teamName];
                teamLogoImages[teamName] = img;
            }}
        }});

        // 1. Weekly Total Points Line Chart
        const weeklyPointsCtx = document.getElementById('weeklyPointsChart').getContext('2d');
        const weeklyPointsChart = new Chart(weeklyPointsCtx, {{
            type: 'line',
            data: {{
                labels: weeklyScoresData.weeks.map(w => `Week ${{w}}`),
                datasets: Object.keys(weeklyScoresData.teams).map(teamName => {{
                    const dataPoints = weeklyScoresData.teams[teamName];
                    const numPoints = dataPoints.length;

                    // Create pointStyle array - use logo for all points if available
                    let pointStyle = 'circle';
                    const pointRadii = Array(numPoints).fill(4);
                    const pointHoverRadii = Array(numPoints).fill(6);

                    if (teamLogoImages[teamName]) {{
                        pointStyle = teamLogoImages[teamName];
                        pointRadii[numPoints - 1] = 15;
                        pointHoverRadii[numPoints - 1] = 18;
                    }}

                    return {{
                        label: '\u00A0\u00A0' + teamName,  // Add non-breaking spaces for margin
                        data: dataPoints,
                        borderColor: teamColors[teamName],
                        backgroundColor: teamColors[teamName] + '20',
                        borderWidth: 2,
                        tension: 0.3,
                        pointStyle: pointStyle,
                        pointRadius: pointRadii,
                        pointHoverRadius: pointHoverRadii
                    }};
                }})
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 15,
                            usePointStyle: true
                        }}
                    }},
                    tooltip: {{
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {{
                            size: 14
                        }},
                        bodyFont: {{
                            size: 13
                        }},
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + ' pts';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{
                            color: '#2d3748'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return value + ' pts';
                            }}
                        }}
                    }},
                    x: {{
                        grid: {{
                            color: '#2d3748'
                        }}
                    }}
                }}
            }}
        }});

        // 2. Cumulative Total Points Line Chart
        const cumulativePointsCtx = document.getElementById('cumulativePointsChart').getContext('2d');
        const cumulativePointsChart = new Chart(cumulativePointsCtx, {{
            type: 'line',
            data: {{
                labels: cumulativePointsData.weeks.map(w => `Week ${{w}}`),
                datasets: Object.keys(cumulativePointsData.teams).map(teamName => {{
                    const dataPoints = cumulativePointsData.teams[teamName];
                    const numPoints = dataPoints.length;

                    // Create pointStyle array - use logo for all points if available
                    let pointStyle = 'circle';
                    const pointRadii = Array(numPoints).fill(4);
                    const pointHoverRadii = Array(numPoints).fill(6);

                    if (teamLogoImages[teamName]) {{
                        pointStyle = teamLogoImages[teamName];
                        pointRadii[numPoints - 1] = 15;
                        pointHoverRadii[numPoints - 1] = 18;
                    }}

                    return {{
                        label: '\u00A0\u00A0' + teamName,  // Add non-breaking spaces for margin
                        data: dataPoints,
                        borderColor: teamColors[teamName],
                        backgroundColor: teamColors[teamName] + '20',
                        borderWidth: 2,
                        tension: 0.3,
                        pointStyle: pointStyle,
                        pointRadius: pointRadii,
                        pointHoverRadius: pointHoverRadii
                    }};
                }})
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 15,
                            usePointStyle: true
                        }}
                    }},
                    tooltip: {{
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {{
                            size: 14
                        }},
                        bodyFont: {{
                            size: 13
                        }},
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + ' pts (total)';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{
                            color: '#2d3748'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return value + ' pts';
                            }}
                        }},
                        title: {{
                            display: true,
                            text: 'Cumulative Total Points'
                        }}
                    }},
                    x: {{
                        grid: {{
                            color: '#2d3748'
                        }}
                    }}
                }}
            }}
        }});

        // 3. Standings Progression Step Chart
        const standingsCtx = document.getElementById('standingsChart').getContext('2d');
        const standingsChart = new Chart(standingsCtx, {{
            type: 'line',
            data: {{
                labels: standingsData.weeks.map(w => `Week ${{w}}`),
                datasets: Object.keys(standingsData.teams).map(teamName => {{
                    const dataPoints = standingsData.teams[teamName];
                    const numPoints = dataPoints.length;

                    // Create pointStyle array - use logo for all points if available
                    let pointStyle = 'circle';
                    const pointRadii = Array(numPoints).fill(3);
                    const pointHoverRadii = Array(numPoints).fill(5);

                    if (teamLogoImages[teamName]) {{
                        pointStyle = teamLogoImages[teamName];
                        pointRadii[numPoints - 1] = 15;
                        pointHoverRadii[numPoints - 1] = 18;
                    }}

                    return {{
                        label: '\u00A0\u00A0' + teamName,  // Add non-breaking spaces for margin
                        data: dataPoints,
                        borderColor: teamColors[teamName],
                        backgroundColor: teamColors[teamName] + '20',
                        borderWidth: 2,
                        stepped: true,
                        pointStyle: pointStyle,
                        pointRadius: pointRadii,
                        pointHoverRadius: pointHoverRadii
                    }};
                }})
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 15,
                            usePointStyle: true
                        }}
                    }},
                    tooltip: {{
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': Rank #' + context.parsed.y;
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        reverse: true,
                        min: 1,
                        grid: {{
                            color: '#2d3748'
                        }},
                        ticks: {{
                            stepSize: 1,
                            callback: function(value) {{
                                return '#' + value;
                            }}
                        }},
                        title: {{
                            display: true,
                            text: 'League Rank'
                        }}
                    }},
                    x: {{
                        grid: {{
                            color: '#2d3748'
                        }}
                    }}
                }}
            }}
        }});

        // 4. Win Margin Distribution Histogram
        const marginCtx = document.getElementById('marginChart').getContext('2d');
        const marginChart = new Chart(marginCtx, {{
            type: 'bar',
            data: {{
                labels: marginData.labels,
                datasets: [{{
                    label: 'Number of Matchups',
                    data: marginData.counts,
                    backgroundColor: '#4299e1',
                    borderColor: '#2b6cb0',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        callbacks: {{
                            title: function(context) {{
                                return 'Margin: ' + context[0].label + ' points';
                            }},
                            label: function(context) {{
                                return 'Matchups: ' + context.parsed.y;
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{
                            color: '#2d3748'
                        }},
                        ticks: {{
                            stepSize: 1
                        }},
                        title: {{
                            display: true,
                            text: 'Number of Matchups'
                        }}
                    }},
                    x: {{
                        grid: {{
                            color: '#2d3748'
                        }},
                        title: {{
                            display: true,
                            text: 'Point Margin Range'
                        }}
                    }}
                }}
            }}
        }});

        // 5. All-Play Standings Chart
        const allPlayStandingsCtx = document.getElementById('allPlayStandingsChart').getContext('2d');

        // Sort teams by win percentage
        const teamsByWinPct = Object.keys(allPlayRecords.teams)
            .map(teamName => ({{
                name: teamName,
                wins: allPlayRecords.teams[teamName].cumulative_wins,
                losses: allPlayRecords.teams[teamName].cumulative_losses,
                winPct: allPlayRecords.teams[teamName].win_percentage
            }}))
            .sort((a, b) => b.winPct - a.winPct);

        const allPlayStandingsChart = new Chart(allPlayStandingsCtx, {{
            type: 'bar',
            data: {{
                labels: teamsByWinPct.map(t => t.name),
                datasets: [
                    {{
                        label: 'Wins',
                        data: teamsByWinPct.map(t => t.wins),
                        backgroundColor: '#48bb78',
                        borderColor: '#38a169',
                        borderWidth: 1
                    }},
                    {{
                        label: 'Losses',
                        data: teamsByWinPct.map(t => t.losses),
                        backgroundColor: '#f56565',
                        borderColor: '#e53e3e',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        callbacks: {{
                            footer: function(tooltipItems) {{
                                const teamName = tooltipItems[0].label;
                                const teamData = teamsByWinPct.find(t => t.name === teamName);
                                const winPct = (teamData.winPct * 100).toFixed(1);
                                const record = `${{teamData.wins}}-${{teamData.losses}}`;
                                return `Record: ${{record}} (${{winPct}}%)`;
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        stacked: false,
                        grid: {{
                            color: '#2d3748'
                        }},
                        ticks: {{
                            maxRotation: 45,
                            minRotation: 45,
                            color: '#e4e6eb',
                            font: {{
                                size: 11,
                                weight: 600
                            }},
                            callback: function(value, index) {{
                                const teamName = teamsByWinPct[index].name;
                                // Add team logo icon if available
                                return teamName;
                            }}
                        }}
                    }},
                    y: {{
                        beginAtZero: true,
                        grid: {{
                            color: '#2d3748'
                        }},
                        title: {{
                            display: true,
                            text: 'Games'
                        }}
                    }}
                }}
            }},
            plugins: [{{
                id: 'customLegend',
                afterDraw: function(chart) {{
                    const ctx = chart.ctx;
                    const chartArea = chart.chartArea;
                    const datasets = chart.data.datasets;

                    // Draw custom legend with team logos on x-axis
                    chart.data.labels.forEach((label, index) => {{
                        const meta = chart.getDatasetMeta(0);
                        const bar = meta.data[index];
                        const x = bar.x;

                        // Draw team logo if available
                        if (teamLogoImages[label]) {{
                            const logo = teamLogoImages[label];
                            const logoSize = 24;
                            ctx.drawImage(logo, x - logoSize/2, chartArea.bottom + 5, logoSize, logoSize);
                        }}
                    }});
                }}
            }}]
        }});

        // 6. All-Play Win Percentage Progression Chart
        const allPlayProgressionCtx = document.getElementById('allPlayProgressionChart').getContext('2d');

        // Calculate cumulative win percentage for each team by week
        const allPlayProgressionData = {{}};
        Object.keys(allPlayRecords.teams).forEach(teamName => {{
            const weeklyWins = allPlayRecords.teams[teamName].weekly_wins;
            const weeklyLosses = allPlayRecords.teams[teamName].weekly_losses;
            const cumulativeWinPcts = [];

            let totalWins = 0;
            let totalLosses = 0;

            for (let i = 0; i < weeklyWins.length; i++) {{
                totalWins += weeklyWins[i];
                totalLosses += weeklyLosses[i];
                const totalGames = totalWins + totalLosses;
                const winPct = totalGames > 0 ? (totalWins / totalGames) * 100 : 0;
                cumulativeWinPcts.push(winPct);
            }}

            allPlayProgressionData[teamName] = cumulativeWinPcts;
        }});

        const allPlayProgressionChart = new Chart(allPlayProgressionCtx, {{
            type: 'line',
            data: {{
                labels: allPlayRecords.weeks.map(w => `Week ${{w}}`),
                datasets: Object.keys(allPlayProgressionData).map(teamName => {{
                    const dataPoints = allPlayProgressionData[teamName];
                    const numPoints = dataPoints.length;

                    let pointStyle = 'circle';
                    const pointRadii = Array(numPoints).fill(4);
                    const pointHoverRadii = Array(numPoints).fill(6);

                    if (teamLogoImages[teamName]) {{
                        pointStyle = teamLogoImages[teamName];
                        pointRadii[numPoints - 1] = 15;
                        pointHoverRadii[numPoints - 1] = 18;
                    }}

                    return {{
                        label: '\u00A0\u00A0' + teamName,
                        data: dataPoints,
                        borderColor: teamColors[teamName],
                        backgroundColor: teamColors[teamName] + '20',
                        borderWidth: 2,
                        tension: 0.3,
                        pointStyle: pointStyle,
                        pointRadius: pointRadii,
                        pointHoverRadius: pointHoverRadii
                    }};
                }})
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 15,
                            usePointStyle: true
                        }}
                    }},
                    tooltip: {{
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        callbacks: {{
                            label: function(context) {{
                                const teamName = context.dataset.label.trim();
                                const weekIndex = context.dataIndex;
                                const teamData = allPlayRecords.teams[teamName];
                                const wins = teamData.weekly_wins.slice(0, weekIndex + 1).reduce((a, b) => a + b, 0);
                                const losses = teamData.weekly_losses.slice(0, weekIndex + 1).reduce((a, b) => a + b, 0);
                                const winPct = context.parsed.y.toFixed(1);
                                return `${{context.dataset.label}}: ${{winPct}}% (${{wins}}-${{losses}})`;
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        grid: {{
                            color: '#2d3748'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }},
                        title: {{
                            display: true,
                            text: 'Win Percentage'
                        }}
                    }},
                    x: {{
                        grid: {{
                            color: '#2d3748'
                        }}
                    }}
                }}
            }}
        }});

        // 7. Top Player Contributions with Images
        const latestWeek = playerContributions.weeks[playerContributions.weeks.length - 1];
        const latestContributions = playerContributions.contributions[latestWeek];

        function getPlayerImageUrl(playerId) {{
            if (!playerId) return null;
            return `https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/${{playerId}}.png&w=426&h=320&cb=1`;
        }}

        function getInitials(name) {{
            const parts = name.split(' ');
            if (parts.length >= 2) {{
                return parts[0][0] + parts[parts.length - 1][0];
            }}
            return name.substring(0, 2).toUpperCase();
        }}

        function renderPlayerContributions() {{
            const grid = document.getElementById('playerContributionsGrid');
            const teams = Object.keys(latestContributions);

            // Calculate max points for scaling bars
            let maxPoints = 0;
            teams.forEach(team => {{
                latestContributions[team].forEach(player => {{
                    if (player.points > maxPoints) maxPoints = player.points;
                }});
            }});

            teams.forEach(team => {{
                const teamCard = document.createElement('div');
                teamCard.className = 'team-card';

                const teamTitle = document.createElement('h3');
                const teamFullName = teamNames[team] || team;
                teamTitle.textContent = teamFullName;
                teamCard.appendChild(teamTitle);

                const players = latestContributions[team];
                players.forEach(player => {{
                    const playerItem = document.createElement('div');
                    playerItem.className = 'player-item';

                    // Create image or fallback
                    const imageUrl = getPlayerImageUrl(player.playerId);
                    if (imageUrl) {{
                        const img = document.createElement('img');
                        img.className = 'player-photo';
                        img.src = imageUrl;
                        img.alt = player.name;

                        // Fallback to initials if image fails to load
                        img.onerror = function() {{
                            const fallback = document.createElement('div');
                            fallback.className = 'player-photo-error';
                            fallback.textContent = getInitials(player.name);
                            playerItem.replaceChild(fallback, img);
                        }};

                        playerItem.appendChild(img);
                    }} else {{
                        const fallback = document.createElement('div');
                        fallback.className = 'player-photo-error';
                        fallback.textContent = getInitials(player.name);
                        playerItem.appendChild(fallback);
                    }}

                    // Player info
                    const playerInfo = document.createElement('div');
                    playerInfo.className = 'player-info';

                    const playerName = document.createElement('div');
                    playerName.className = 'player-name';
                    playerName.textContent = player.name;
                    playerInfo.appendChild(playerName);

                    const pointsBar = document.createElement('div');
                    pointsBar.className = 'points-bar';
                    const barWidth = (player.points / maxPoints) * 100;
                    pointsBar.style.width = barWidth + '%';
                    playerInfo.appendChild(pointsBar);

                    playerItem.appendChild(playerInfo);

                    // Points display
                    const playerPoints = document.createElement('div');
                    playerPoints.className = 'player-points';
                    playerPoints.textContent = player.points.toFixed(1);
                    playerItem.appendChild(playerPoints);

                    teamCard.appendChild(playerItem);
                }});

                grid.appendChild(teamCard);
            }});
        }}

        renderPlayerContributions();

        // Top 3 Players by Week
        let selectedWeek = topPlayersByWeek.weeks[topPlayersByWeek.weeks.length - 1];

        function renderWeekSelector() {{
            const selector = document.getElementById('weekSelector');
            selector.innerHTML = '';  // Clear existing buttons
            topPlayersByWeek.weeks.forEach(week => {{
                const button = document.createElement('button');
                button.className = 'week-button';
                button.textContent = `Week ${{week}}`;
                if (week === selectedWeek) {{
                    button.classList.add('active');
                }}
                button.onclick = () => {{
                    selectedWeek = week;
                    renderWeekSelector();
                    renderTopPlayers();
                }};
                selector.appendChild(button);
            }});
        }}

        function renderTopPlayers() {{
            const display = document.getElementById('topPlayersDisplay');
            display.innerHTML = '';

            const players = topPlayersByWeek.top_players[selectedWeek];

            players.forEach((player, index) => {{
                const card = document.createElement('div');
                card.className = `top-player-card rank-${{index + 1}}`;

                // Rank badge
                const badge = document.createElement('div');
                badge.className = `rank-badge rank-${{index + 1}}`;
                badge.textContent = index + 1;
                card.appendChild(badge);

                // Player photo
                const imageUrl = getPlayerImageUrl(player.playerId);
                if (imageUrl) {{
                    const img = document.createElement('img');
                    img.className = 'top-player-photo';
                    img.src = imageUrl;
                    img.alt = player.name;

                    img.onerror = function() {{
                        const fallback = document.createElement('div');
                        fallback.className = 'top-player-photo-error';
                        fallback.textContent = getInitials(player.name);
                        card.replaceChild(fallback, img);
                    }};

                    card.appendChild(img);
                }} else {{
                    const fallback = document.createElement('div');
                    fallback.className = 'top-player-photo-error';
                    fallback.textContent = getInitials(player.name);
                    card.appendChild(fallback);
                }}

                // Player name
                const name = document.createElement('div');
                name.className = 'top-player-name';
                name.textContent = player.name;
                card.appendChild(name);

                // Player team (full name)
                const team = document.createElement('div');
                team.className = 'top-player-team';
                const teamFullName = teamNames[player.team] || player.team;
                team.textContent = teamFullName;
                card.appendChild(team);

                // Player points
                const points = document.createElement('div');
                points.className = 'top-player-points';
                points.textContent = player.points.toFixed(1);
                card.appendChild(points);

                display.appendChild(card);
            }});
        }}

        renderWeekSelector();
        renderTopPlayers();

        // Top 10 Player Performances of the Season
        function renderTopPerformances() {{
            const display = document.getElementById('topPerformancesDisplay');
            display.innerHTML = '';

            const performances = topPlayerPerformances.top_performances;

            performances.forEach((player, index) => {{
                const card = document.createElement('div');
                card.className = `top-player-card`;

                // Add special styling for top 3
                if (index < 3) {{
                    card.classList.add(`rank-${{index + 1}}`);
                }}

                // Rank badge
                const badge = document.createElement('div');
                badge.className = `rank-badge`;
                if (index < 3) {{
                    badge.classList.add(`rank-${{index + 1}}`);
                }}
                badge.textContent = index + 1;
                card.appendChild(badge);

                // Player photo
                const imageUrl = getPlayerImageUrl(player.playerId);
                if (imageUrl) {{
                    const img = document.createElement('img');
                    img.className = 'top-player-photo';
                    img.src = imageUrl;
                    img.alt = player.name;

                    img.onerror = function() {{
                        const fallback = document.createElement('div');
                        fallback.className = 'top-player-photo-error';
                        fallback.textContent = getInitials(player.name);
                        card.replaceChild(fallback, img);
                    }};

                    card.appendChild(img);
                }} else {{
                    const fallback = document.createElement('div');
                    fallback.className = 'top-player-photo-error';
                    fallback.textContent = getInitials(player.name);
                    card.appendChild(fallback);
                }}

                // Player name
                const name = document.createElement('div');
                name.className = 'top-player-name';
                name.textContent = player.name;
                card.appendChild(name);

                // Player team and week
                const team = document.createElement('div');
                team.className = 'top-player-team';
                const teamFullName = teamNames[player.team] || player.team;
                team.textContent = `${{teamFullName}} - Week ${{player.week}}`;
                card.appendChild(team);

                // Player points
                const points = document.createElement('div');
                points.className = 'top-player-points';
                points.textContent = player.points.toFixed(1);
                card.appendChild(points);

                display.appendChild(card);
            }});
        }}

        renderTopPerformances();

        // Top Team by Week
        let selectedTeamWeek = topTeamByWeek.weeks[topTeamByWeek.weeks.length - 1];

        function renderTopTeamWeekSelector() {{
            const selector = document.getElementById('topTeamWeekSelector');
            selector.innerHTML = '';  // Clear existing buttons
            topTeamByWeek.weeks.forEach(week => {{
                const button = document.createElement('button');
                button.className = 'week-button';
                button.textContent = `Week ${{week}}`;
                if (week === selectedTeamWeek) {{
                    button.classList.add('active');
                }}
                button.onclick = () => {{
                    selectedTeamWeek = week;
                    renderTopTeamWeekSelector();
                    renderTopTeam();
                }};
                selector.appendChild(button);
            }});
        }}

        function renderTopTeam() {{
            const display = document.getElementById('topTeamDisplay');
            display.innerHTML = '';

            const teamData = topTeamByWeek.top_teams[selectedTeamWeek];
            const teamAbbrev = teamData.team;
            const teamFullName = teamNames[teamAbbrev] || teamAbbrev;

            const card = document.createElement('div');
            card.className = 'top-team-card';

            // Trophy emoji
            const trophy = document.createElement('div');
            trophy.className = 'top-team-trophy';
            trophy.textContent = '👑';
            card.appendChild(trophy);

            // Team logo
            if (teamLogos[teamAbbrev]) {{
                const logo = document.createElement('img');
                logo.className = 'top-team-logo';
                logo.src = teamLogos[teamAbbrev];
                logo.alt = teamFullName;
                card.appendChild(logo);
            }}

            // Team name (full name)
            const name = document.createElement('div');
            name.className = 'top-team-name';
            name.textContent = teamFullName;
            card.appendChild(name);

            // Team points
            const points = document.createElement('div');
            points.className = 'top-team-points';
            points.textContent = teamData.points.toFixed(1);
            card.appendChild(points);

            // Label
            const label = document.createElement('div');
            label.className = 'top-team-label';
            label.textContent = 'Total Points';
            card.appendChild(label);

            display.appendChild(card);
        }}

        renderTopTeamWeekSelector();
        renderTopTeam();
    </script>
</body>
</html>"""

    return html


def main():
    """Main execution function."""
    print("=" * 60)
    print("ESPN Fantasy Basketball Stats Generator")
    print("=" * 60)

    try:
        # Fetch league data
        league = fetch_league_data()

        # Fetch team logos
        team_logos = get_team_logos(league)

        # Collect all data
        weekly_scores = get_weekly_scores(league)
        cumulative_points = get_cumulative_points(weekly_scores)
        standings_progression = get_standings_progression(league)
        player_contributions = get_top_player_contributions(league)
        top_team_by_week = get_top_team_by_week(league)
        top_players_by_week = get_top_players_by_week(league)
        top_player_performances = get_top_player_performances(league)
        all_play_records = get_all_play_records(league)
        win_margins = get_win_margins(league)

        # Process histogram data
        margin_histogram = create_histogram_data(win_margins)

        # Combine all data
        all_data = {
            'weekly_scores': weekly_scores,
            'cumulative_points': cumulative_points,
            'standings_progression': standings_progression,
            'player_contributions': player_contributions,
            'top_team_by_week': top_team_by_week,
            'top_players_by_week': top_players_by_week,
            'top_player_performances': top_player_performances,
            'all_play_records': all_play_records,
            'win_margins': margin_histogram,
            'team_logos': team_logos
        }

        # Generate HTML
        html_content = generate_html(league, all_data)

        # Ensure output directory exists
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

        # Write HTML file
        output_path = os.path.join(
            settings.OUTPUT_DIR, settings.OUTPUT_FILENAME)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n{'=' * 60}")
        print(f"✓ SUCCESS!")
        print(f"{'=' * 60}")
        print(f"HTML file generated: {output_path}")
        print(f"Open this file in your web browser to view the stats dashboard.")
        print(f"{'=' * 60}\n")

    except Exception as e:
        print(f"\n{'=' * 60}")
        print(f"✗ ERROR: {e}")
        print(f"{'=' * 60}\n")
        raise


if __name__ == "__main__":
    main()
