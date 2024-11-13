import json
from loguru import logger

statistic_minumum_criteria = {
    "points": 9,
    "reboundsTotal": 5,
    "assists": 3,
    "steals": 2,
    "blocks": 2,
}

players_to_watch = ["V. Wembanyama"]


def parse_single_game_statline(stat_line):
    parsed = parse_to_json(stat_line)
    if parsed and "boxscore" in parsed:
        parsed_boxscore = parse_to_json(stat_line)["boxscore"]
        return {
            "gameId": parsed_boxscore["gameId"],
            "gameStatus": parsed_boxscore["gameStatus"],
            "homeTeam": format_team_statline(parsed_boxscore["homeTeam"]),
            "awayTeam": format_team_statline(parsed_boxscore["awayTeam"]),
        }
    else:
        return None


def parse_scoreboard_game(game):
    return {
        "gameId": game["gameId"],
        "gameStatus": game["gameStatus"],
        "homeTeam": parse_scoreboard_game_team(game["homeTeam"]),
        "awayTeam": parse_scoreboard_game_team(game["awayTeam"]),
    }


def parse_scoreboard_game_team(team):
    return {
        "score": team["score"],
        "wins": team["wins"],
        "losses": team["losses"],
        "teamCity": team["teamCity"],
        "teamName": team["teamName"],
        "teamTricode": team["teamTricode"],
        "teamId": team["teamId"],
        "teamLogo": get_team_logo_link(team["teamId"]),
    }


def get_team_logo_link(team_id: str) -> str:
    return f"https://cdn.nba.com/logos/nba/{team_id}/primary/L/logo.svg"


def format_team_statline(team):
    players = []
    for player in team["players"]:
        if player["status"] == "ACTIVE":
            criterias = statistic_minumum_criteria
            player_to_append = {"name": player["nameI"]}
            if player_to_append["name"] in players_to_watch:
                criterias = {
                    "points": 1,
                    "reboundsTotal": 0,
                    "assists": 0,
                    "steals": 0,
                    "blocks": 0,
                }

            if player["statistics"]["points"] > criterias["points"]:
                player_to_append["points"] = player["statistics"]["points"]
            if player["statistics"]["reboundsTotal"] > criterias["reboundsTotal"]:
                player_to_append["reboundsTotal"] = player["statistics"][
                    "reboundsTotal"
                ]
            if player["statistics"]["assists"] > criterias["assists"]:
                player_to_append["assists"] = player["statistics"]["assists"]
            if player["statistics"]["steals"] > criterias["steals"]:
                player_to_append["steals"] = player["statistics"]["steals"]
            if player["statistics"]["blocks"] > criterias["blocks"]:
                player_to_append["blocks"] = player["statistics"]["blocks"]

            if len(player_to_append) > 1:
                if not "points" in player_to_append:
                    player_to_append["points"] = player["statistics"]["points"]
                players.append(player_to_append)

    players.sort(reverse=True, key=lambda p: p["points"])

    return {"tricode": team["teamTricode"], "players": players}


def parse_players_season_stats(league_leaders_json):
    if league_leaders_json and "resultSet" in league_leaders_json:
        categories = league_leaders_json["resultSet"][
            "headers"
        ]  # should be in format ["PLAYER_ID","RANK","PLAYER","TEAM_ID","TEAM","GP","MIN","FGM","FGA","FG_PCT","FG3M","FG3A","FG3_PCT","FTM","FTA","FT_PCT","OREB","DREB","REB","AST","STL","BLK","TOV","PTS","EFF"]

        all_players_stats = league_leaders_json["resultSet"]["rowSet"]

        return {
            "categories": categories,
            "all_players_stats": all_players_stats,
        }
    else:
        logger.debug("missed [resultSet] key in league_leaders_json")
        return None


def parse_to_json(value):
    if not value or "<HTML>" in value:
        logger.exception(f"Wrong input for parse_to_json method: {value}")
        return None

    try:
        return json.loads(value)
    except Exception as err:
        logger.exception(err)
        return None
