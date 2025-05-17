import pandas as pd
from espn_constant import HITTING_MAP, PITCHING_MAP, POSITION_MAP, MATCHUP_PERIOD_MAP_2021


class Team:
    def __init__(self, team_json: dict = None):
        self.team_id = None
        self.current_roster = None
        self.season_hitting = None
        self.season_pitching = None
        self.record = None
        self.logo = None
        self.swid = None
        self.abbrev = None
        self.name = None
        self.transaction_counter = None
        self.division_id = None
        self.team_json = team_json
        self.hitting_frame = pd.DataFrame()
        self.pitching_frame = pd.DataFrame()
        self.roster_df = self.get_roster_df()
        self.create_frame_templates()
        if self.team_json is not None:
            self.update_team_info(self.team_json)
            self.update_season_stats(self.team_json)

    def __repr__(self):
        return f"{self.name}"

    def create_frame_templates(self):
        """
        Creates a list of the pitching and hitting columns to be used in the statistical DataFrames.
        The column lists are stored in the Team attributes.
        :return: None
        """
        shared_columns = ["Team ID", "Player Name", "ESPN Player ID", "Scoring Period", "Matchup Period",
                          "Lineup ID", "Position"]
        hitting_columns = shared_columns.copy()
        pitching_columns = shared_columns.copy()
        for stat in HITTING_MAP:
            hitting_columns.append(HITTING_MAP[stat])
        for stat in PITCHING_MAP:
            pitching_columns.append(PITCHING_MAP[stat])
        self.hitting_frame = pd.DataFrame(columns=hitting_columns)
        self.pitching_frame = pd.DataFrame(columns=pitching_columns)

    def update_team_info(self, team_json: dict):
        """
        Updates the Team
        :param team_json: JSON data for the team
        :return: None
        """
        data = team_json
        self.team_id = data["id"]
        self.abbrev = data["abbrev"]
        self.division_id = data["divisionId"]
        self.logo = data.get("logo")
        self.name = data["name"]
        self.swid = data["primaryOwner"]
        self.record = data["record"]["overall"]
        self.transaction_counter = data["transactionCounter"]

    def update_season_stats(self, team_json):
        """
        Parses the JSON data for the team and stores the total hitting and pitching stats for the team in attributes.
        :param team_json: JSON data for the team
        :return: None
        """
        data = team_json["valuesByStat"]
        hitting_dict = {}
        pitching_dict = {}
        for stat in data:
            stat = int(stat)
            if stat <= 31:
                hitting_dict[HITTING_MAP[stat]] = data[str(stat)]
            elif 33 <= stat <= 66:
                pitching_dict[PITCHING_MAP[stat]] = data[str(stat)]
        self.season_hitting = pd.DataFrame(hitting_dict, index=[self.team_id])
        self.season_hitting.index.name = 'team_id'
        self.season_hitting.insert(0, "Team", self.name)
        self.season_pitching = pd.DataFrame(pitching_dict, index=[self.team_id])
        self.season_pitching.index.name = 'team_id'
        self.season_pitching.insert(0, "Team", self.name)

    def get_daily_stats(self, roster_json: dict):
        """
        Parses the JSON info returned from the ESPN API and stores the statistics of the team in a DataFrame.
        Need to sort stats for ease of viewing.
        :param roster_json: The team roster JSON returned from the ESPN API for the specified scoring period.
        :return: Pandas DataFrame
        """
        hitting_df = self.hitting_frame.copy(deep=True)
        pitching_df = self.pitching_frame.copy(deep=True)
        for player in roster_json:
            player_dict = {"Team ID": self.team_id, "Player Name": player["playerPoolEntry"]["player"]["fullName"],
                           "ESPN Player ID": player["playerId"], "Lineup ID": player["lineupSlotId"],
                           "Position": POSITION_MAP[player["lineupSlotId"]]}
            for stat_set in player["playerPoolEntry"]["player"]["stats"]:
                if stat_set["statSourceId"] == 0 and stat_set["statSplitTypeId"] == 5:
                    player_dict["Scoring Period"] = stat_set["scoringPeriodId"]
                    for key in MATCHUP_PERIOD_MAP_2021:
                        if player_dict["Scoring Period"] in MATCHUP_PERIOD_MAP_2021[key]:
                            player_dict["Matchup Period"] = key
                    # checks if the player is in an active hitting spot and adds hitting stats to the player dict
                    if int(player_dict["Lineup ID"]) <= 12 or int(player_dict["Lineup ID"]) == 19:
                        player_dict.update(self.process_hitting_stats(stat_set["stats"]))
                        player_df = pd.DataFrame([player_dict])
                        hitting_df = pd.concat([hitting_df, player_df], ignore_index=True)
                    # checks if the player is in an active pitching spot and adds pitching stats to the player dict
                    elif 13 <= int(player_dict["Lineup ID"]) <= 15:
                        player_dict.update(self.process_pitching_stats(stat_set["stats"]))
                        player_df = pd.DataFrame(
                            [player_dict])  # Convert dict to DataFrame (ensure it's a list of dicts)
                        pitching_df = pd.concat([pitching_df, player_df], ignore_index=True)
        hitting_df.fillna(0, inplace=True)
        pitching_df.fillna(0, inplace=True)
        return hitting_df, pitching_df

    @staticmethod
    def process_hitting_stats(stat_dict):
        """
        Takes a stat dictionary found in the roster JSON data and returns a dictionary with the hitting statistic names
        as keys and their respective values as values.
        :param stat_dict: statistic dictionary taken from roster JSON data
        :return: human-readable hitting dictionary
        """
        hitting_columns = []
        for stat in HITTING_MAP:
            hitting_columns.append(HITTING_MAP[stat])
        hitting_dict = dict()
        for stat in stat_dict:
            stat = int(stat)
            if stat <= 31:
                hitting_dict[HITTING_MAP[stat]] = stat_dict[str(stat)]
        return hitting_dict

    @staticmethod
    def process_pitching_stats(stat_dict):
        """
        Takes a stat dictionary found in the roster JSON data and returns a dictionary with the pitching statistic names
        as keys and their respective values as values.
        :param stat_dict: statistic dictionary taken from roster JSON data
        :return: human-readable pitching dictionary
        """
        pitching_dict = dict()
        for stat in stat_dict:
            stat = int(stat)
            if 33 <= stat <= 66:
                pitching_dict[PITCHING_MAP[stat]] = stat_dict[str(stat)]
        return pitching_dict

    def get_roster_df(self):
        """
        Extracts and processes the roster only for this team.
        :return: Pandas DataFrame containing this team's roster.
        """
        if not self.team_json or "roster" not in self.team_json:
            return pd.DataFrame()  # Return empty DataFrame if no data

        roster_entries = self.team_json.get("roster", {}).get("entries", [])
        return self.parse_roster(roster_entries)

    def parse_roster(self, roster_entries):
        """
        Parses the roster JSON data and structures it into a DataFrame.
        :param roster_entries: List of players in the roster
        :return: DataFrame with player details.
        """
        roster_data = []

        for entry in roster_entries:
            player = entry["playerPoolEntry"]["player"]
            roster_data.append({
                "Team ID": self.team_id,
                "Team Name": self.name,
                "Player ID": player["id"],
                "Full Name": player["fullName"],
                "Position ID": player["defaultPositionId"],
                "Injury Status": player.get("injuryStatus", "N/A"),
                "Ownership %": player["ownership"]["percentOwned"],
            })

        return pd.DataFrame(roster_data)

    def update_roster(self, player_pool: dict, roster_json):
        """
        Update the team's roster using the shared player pool.

        This method looks up players based on the team roster information found in self.team_json.
        You can choose to either reference the player objects directly or create a deep copy.

        Option 1: Reference directly (recommended if you want the roster to reflect live updates)
        Option 2: Create a copy (if you need a static snapshot of the roster)
        """
        self.current_roster = {}  # Reset roster

        # Assume that self.team_json["roster"]["entries"] contains the roster entries with player IDs.
        roster_entries = roster_json.get("roster", {}).get("entries", [])
        for entry in roster_entries:
            player_id = entry["playerPoolEntry"]["player"]["id"]
            if player_id in player_pool:
                # Option 1: Reference the same Player object
                self.current_roster[player_id] = player_pool[player_id]
                player_pool[player_id].fantasy_team = self.name

                # Option 2: Make a deep copy (uncomment the following line if needed)
                # self.current_roster[player_id] = copy.deepcopy(player_pool[player_id])

    def display_all_rosters(self):
        """
        Prints the combined roster DataFrame for all teams.
        """
        if self.roster_df.empty:
            print("No roster data available.")
        else:
            print(self.roster_df)
