import requests
import json
import os


class ESPNRequester:
    def __init__(self, league_id: int, season_id: int, swid: str = None, espn_s2: str = None):
        self.league_id = league_id
        self.season_id = season_id
        # The base url for api requests of the specified fantasy league.  Only valid for season_id > 2018
        if self.season_id >= 2018:
            self.url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/flb/seasons/{season_id}/segments/0/leagues/{league_id}"
        elif self.season_id <= 2017:
            self.url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/flb/leagueHistory/{league_id}?seasonId={season_id}"
        self.cookies = {"SWID": swid, "espn_s2": espn_s2}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",  # Forces ESPN to return JSON
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://fantasy.espn.com/",
            "Origin": "https://fantasy.espn.com"
        }

    def fetch_data(self, params, extend='', headers=None):
        """
        Helper function to fetch data with headers and error handling.

        Parameters:
          - params: dict, query parameters to include in the URL.
          - extend: str, additional URL path to append to the base URL (default is empty).
          - headers: dict, extra headers to merge with the default headers (default is None).
        """
        url = f"{self.url}{extend}"
        full_url = f"{url}?{requests.compat.urlencode(params)}"
        print(f"🔗 Fetching data from: {full_url}")  # Print the full URL

        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)

        try:
            response = requests.get(self.url, params=params, cookies=self.cookies,
                                    headers=request_headers)
            response.raise_for_status()  # Raises an error for HTTP errors (403, 404, etc.)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error fetching data from ESPN API: {e}")
            print(f"Status Code: {response.status_code}")
            print(
                f"Response Text: {response.text[:500]}")  # Print first 500 characters of the response for debugging
            return None  # Returns None instead of crashing

    def get_teams(self):
        """
        Returns JSON data for each team in the league
        :return: dict
        """
        params = {"view": "mTeam"}
        data = self.fetch_data(params)
        if not data:
            return None
        return data[0]["teams"] if self.season_id < 2018 else data["teams"]

    def get_daily_stats(self, scoring_period_id: int):
        """
        Fetch roster and scoring information for a specific scoring period
        """
        params = {"scoringPeriodId": str(scoring_period_id), "view": "mRoster"}
        data = self.fetch_data(params)  # CHANGED: Uses fetch_data() for error handling
        if not data:
            return None
        return data[0]["teams"] if self.season_id < 2018 else data["teams"]

    def get_league_settings(self):
        """
        Fetch league settings and status
        """
        params = {"view": "mSettings"}
        data = self.fetch_data(params)  # CHANGED: Uses fetch_data() for better error handling
        if not data:
            return None
        return data[0] if self.season_id < 2018 else data

    def get_player_projections(self):
        """
        Fetch player projections from local kona_player_info.json file
        """
        try:
            with open('kona_player_info.json', 'r') as f:
                data = json.load(f)
            
            # Debug print
            print("\nLocal JSON Data:")
            print(f"Data type: {type(data)}")
            if isinstance(data, list):
                print(f"Data length: {len(data)}")
                if len(data) > 0:
                    print(f"First item keys: {data[0].keys()}")
            else:
                print(f"Data keys: {data.keys()}")
            
            players = data[0]["players"] if self.season_id < 2018 else data["players"]
            print(f"\nNumber of players: {len(players)}")
            if len(players) > 0:
                print(f"First player keys: {players[0].keys()}")
            
            return players
        except FileNotFoundError:
            print("kona_player_info.json file not found")
            return None
        except json.JSONDecodeError:
            print("Error decoding kona_player_info.json")
            return None

    def get_all_players(self):
        """
        Fetch all available players from ESPN
        """
        params = {
            "view": "kona_player_info"
        }
        filters = {"players": {"filterActive": {"value": True}}}
        headers = {'x-fantasy-filter': json.dumps(filters)}
        data = self.fetch_data(extend='/players', params=params, headers=headers)
        if not data:
            return None
        return data[0]["players"] if self.season_id < 2018 else data["players"]

    def get_rosters(self):
        params = {
            "view": "mRoster"
        }
        data = self.fetch_data(params)  # CHANGED: Uses fetch_data() for better error handling
        if not data:
            return None
        return data["teams"]
