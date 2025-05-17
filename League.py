import pandas as pd
from api_requests import ESPNRequester
from Team import Team
from espn_constant import HITTING_MAP, PITCHING_MAP
from Player import Player
import logging

class League:
    def __init__(self, league_id, season_id, swid=None, espn_s2=None):
        self.req = ESPNRequester(league_id, season_id, swid, espn_s2)
        self.league_id = league_id
        self.season_id = season_id
        self.teams = []
        self.season_hitting = pd.DataFrame()
        self.season_pitching = pd.DataFrame()
        self.final_scoring_period = None
        self.player_pool = {}  # Dictionary to store all players

        self.scoring_type = None
        # Roto Scoring Categories
        self.hitting_categories = {}
        self.pitching_categories = {}
        
        self.get_league_info()
        self.update_player_pool()
        self.update_teams()
        self.update_season_statistics()

    def update_teams(self):
        """
        Initializes and adds a new Team object for each team in the league,
        and adds it to the teams attribute for the League.
        """
        data = self.req.get_teams()
        roster_data = self.req.get_rosters()
        self.teams.clear()
        team_quantity = len(data)
        for i in range(1, team_quantity + 1):
            team_data = data[i - 1]
            roster_json = roster_data[i-1]
            new_team = Team(team_json=team_data)  # Initialize Team with roster data
            new_team.update_roster(self.player_pool, roster_json)
            self.teams.append(new_team)

    def update_season_statistics(self):
        """
        Updates the season statistics DataFrames for the league.
        :return: None
        """
        for team in self.teams:
            self.season_hitting = pd.concat([self.season_hitting, team.season_hitting], ignore_index=True)
            self.season_pitching = pd.concat([self.season_pitching, team.season_pitching], ignore_index=True)

    def update_daily_statistics(self, scoring_period_id: int):
        """
        Gets statistics for players in active roster spots for every team roster in the specified scoring period.
        :param scoring_period_id: The scoring period for which statistics will be gathered.
        :return: A DataFrame containing the league statistics for the scoring period.
        """
        league_roster_json = self.req.get_daily_stats(scoring_period_id=scoring_period_id)
        hitting_df = pd.DataFrame()
        pitching_df = pd.DataFrame()
        for team in self.teams:
            team_roster_json = league_roster_json[self.teams.index(team)]["roster"]["entries"]
            hitting, pitching = team.get_daily_stats(team_roster_json)
            hitting_df = pd.concat([hitting_df, hitting], ignore_index=True)
            pitching_df = pd.concat([pitching_df, pitching], ignore_index=True)
        return hitting_df, pitching_df

    def get_all_daily_stats(self):
        """
        gets daily stats for the entire season and outputs the data as two separate dataframes
        :return: A tuple of dataframes
        """
        hitting_df = pd.DataFrame()
        pitching_df = pd.DataFrame()
        for i in range(1, self.final_scoring_period + 1):
            hitting, pitching = self.update_daily_statistics(i)
            hitting_df = pd.concat([hitting_df, hitting], ignore_index=True)
            pitching_df = pd.concat([pitching_df, pitching], ignore_index=True)
        return hitting_df, pitching_df

    def get_league_info(self):
        """
        gathers league settings and stores them in attributes
        todo: add roster settings and scoring settings
        :return: None
        """
        settings_json = self.req.get_league_settings()
        settings = settings_json.get("settings")
        self.final_scoring_period = int(settings_json["status"]["finalScoringPeriod"])
        
        # Get scoring settings from league settings
        if "scoringSettings" in settings:
            scoring = settings["scoringSettings"]
            self.scoring_type = scoring["scoringType"]
            if "scoringItems" in scoring:
                for item in scoring["scoringItems"]:
                    stat_id = int(item.get("statId"))
                    points = item.get("points", 0)
                    is_reverse = item.get("isReverseItem", False)
                    # Only include categories that are scored
                    if points > 0:
                        # Hitting categories: stat IDs less than or equal to 31
                        if stat_id <= 31:
                            self.hitting_categories[stat_id] = is_reverse
                        # Pitching categories: stat IDs between 33 and 66
                        elif 33 <= stat_id <= 66:
                            self.pitching_categories[stat_id] = is_reverse

    def update_player_pool(self):
        """
        Updates the player pool with all available players from ESPN
        """
        player_data = self.req.get_all_players()
        if not player_data:
            return

        # Clear existing player pool
        self.player_pool.clear()

        # Create a map of team IDs to team names for easier lookup
        team_map = {team.team_id: team.name for team in self.teams}

        # Process each player
        for player_json in player_data:
            player = Player(player_json)
            
            # Get player's fantasy team info if they're on a roster
            if "onTeamId" in player_json:
                player.team_id = player_json["onTeamId"]
                player.fantasy_team = team_map.get(player.team_id, "Unknown")
            else:
                player.fantasy_team = "Free Agent"
            
            # Get waiver status
            player.waiver_status = player_json.get("waiverStatus", {}).get("status", "NONE")
            
            # Store player in pool
            self.player_pool[player.player_id] = player

    def get_player_by_id(self, player_id):
        """
        Get a player from the player pool by their ID
        """
        return self.player_pool.get(player_id)

    def get_players_by_team(self, team_id):
        """
        Get all players on a specific fantasy team
        """
        return [player for player in self.player_pool.values() if player.team_id == team_id]

    def get_free_agents(self):
        """
        Get all free agent players
        """
        return [player for player in self.player_pool.values() if player.fantasy_team == "Free Agent"]

    def get_players_on_waivers(self):
        """
        Get all players on waivers
        """
        return [player for player in self.player_pool.values() if player.waiver_status != "NONE"]

    def get_team_projections(self):
        """
        Calculate projected stats for each team using actual Player objects from the roster.
        Returns a DataFrame with team projections.
        """
        projections = []

        for team in self.teams:
            team_proj = {
                "Team": team.name,
                "Team ID": team.team_id
            }

            # Initialize totals for hitting and pitching categories
            hitting_totals = {cat: 0 for cat in self.hitting_categories}
            pitching_totals = {cat: 0 for cat in self.pitching_categories}

            # Iterate over the actual Player objects in the team's roster
            # (Assuming update_roster stores them in team.current_roster as a dict)
            for player in team.current_roster.values():
                print(player.default_position_id)
                if player.default_position_id <= 12:  # Hitter
                    for cat in hitting_totals:
                        hitting_totals[cat] += player.get_weighted_projection(cat)
                else:  # Pitcher
                    for cat in pitching_totals:
                        pitching_totals[cat] += player.get_weighted_projection(cat)

            team_proj.update(hitting_totals)
            team_proj.update(pitching_totals)
            projections.append(team_proj)

        return pd.DataFrame(projections)

    def get_roto_standings(self, team_df):
        """
        Compute roto standings from a team projections DataFrame.

        Assumptions:
          - team_df contains identifier columns "Team" and "Team ID".
          - All other columns are stat categories keyed by stat IDs (as numbers or numeric strings).
          - self.hitting_categories and self.pitching_categories are dictionaries keyed by stat ID (int)
            with boolean values indicating whether a higher value is better (True) or lower is better (False).
          - HITTING_MAP and PITCHING_MAP (from your constants) are used to convert a stat ID to a human‐readable name.

        The function partitions stat columns into hitting and pitching, computes a rank for each stat
        (using descending ranking when higher is better, ascending when lower is better), and returns
        a new DataFrame with one row per team. Each rank column is renamed to "[Stat Name] Rank".
        A Total Points column is added (sum of all category ranks). Finally, the "Team ID" column is removed.
        """
        import pandas as pd

        # Build a combined mapping from stat IDs to stat names.
        combined_mapping = {}
        combined_mapping.update({int(k): v for k, v in HITTING_MAP.items()})
        combined_mapping.update({int(k): v for k, v in PITCHING_MAP.items()})

        # Identify stat columns. We assume columns other than "Team" and "Team ID" are stat columns.
        stat_cols = [col for col in team_df.columns if col not in ["Team", "Team ID"]]

        # Partition stat columns into hitting and pitching categories based on self.hitting_categories and self.pitching_categories.
        hitting_cols = []
        pitching_cols = []
        for col in stat_cols:
            try:
                stat_id = int(col)
            except Exception:
                continue  # Skip if column name is not numeric
            if stat_id in self.hitting_categories:
                hitting_cols.append(col)
            elif stat_id in self.pitching_categories:
                pitching_cols.append(col)
        all_stat_cols = hitting_cols + pitching_cols

        # Start a new DataFrame with team identifiers.
        roto_df = team_df[["Team Name", "Team ID"]].copy()

        # For each stat column, determine ranking direction and compute a rank column.
        for col in all_stat_cols:
            try:
                stat_id = int(col)
            except Exception:
                continue
            # Determine if higher is better.
            if stat_id in self.hitting_categories:
                higher_is_better = self.hitting_categories[stat_id]
            elif stat_id in self.pitching_categories:
                higher_is_better = self.pitching_categories[stat_id]
            else:
                higher_is_better = True  # default assumption

            # Look up the human-readable name for this stat.
            stat_name = combined_mapping.get(stat_id, str(stat_id))
            rank_col = f"{stat_name} Rank"
            if higher_is_better:
                # Higher is better: rank descending (highest value gets rank 1)
                roto_df[rank_col] = team_df[col].rank(ascending=False, method="min")
            else:
                # Lower is better: rank ascending (lowest value gets rank 1)
                roto_df[rank_col] = team_df[col].rank(ascending=True, method="min")

        # Calculate total points as the sum of all rank columns.
        rank_columns = [col for col in roto_df.columns if col.endswith("Rank")]
        roto_df["Total Points"] = roto_df[rank_columns].sum(axis=1)

        # Sort teams by total points (ascending: lower total is better)
        roto_df = roto_df.sort_values("Total Points", ascending=True).reset_index(drop=True)

        # Drop the "Team ID" column as requested.
        roto_df.drop("Team ID", axis=1, inplace=True)

        return roto_df

    def get_all_rosters(self):
        """
        Compiles a DataFrame of all team rosters.
        :return: A DataFrame containing all team rosters.
        """
        all_rosters = pd.DataFrame()
        for team in self.teams:
            all_rosters = pd.concat([all_rosters, team.roster], ignore_index=True)  # Aggregate team rosters
        return all_rosters  # Return the compiled DataFrame of all rosters

    def compile_player_projections_df(self):
        """
        Compiles a DataFrame with projection stats for each player on every team.
        Each row represents one player and includes basic info and projection values.

        Assumes that each team object has a 'current_roster' attribute that is a dictionary
        of Player objects, and that each Player has its projections stored in player.projections.
        """
        # Use a logger to help with debugging in case any player is missing projections.
        logger = logging.getLogger(__name__)
        rows = []

        for team in self.teams:
            # Loop over each player in the team's current roster.
            for player in team.current_roster.values():
                # Start with basic information
                row = {
                    "Player ID": player.player_id,
                    "Player Name": player.full_name,
                    "Team ID": team.team_id,
                    "Team Name": team.name,
                    "Default Position ID": player.default_position_id
                }
                # Merge in the player's projection stats, if available.
                # If projections are missing, log a warning.
                if player.projections:
                    # player.projections is assumed to be a dictionary, so update the row.
                    row.update(player.projections)
                else:
                    logger.warning("Player %s (ID: %s) has no projections.", player.full_name, player.player_id)

                rows.append(row)

        # Create and return the DataFrame
        df = pd.DataFrame(rows)
        return df

    def group_projections_by_team(self, rename_stats=True):
        """
        Group player projections by team and aggregate stats.

        Assumptions:
          - The input DataFrame (projections_df) has these columns:
                "Team ID", "Team Name", "Default Position ID",
                plus stat columns such as:
                    For hitters: counting stats ("R", "HR", "RBI", "SB"),
                                rate stats ("OBP", "SLG"), and weight "PA"
                    For pitchers: counting stats ("SV", "K", "QS", "IP"),
                                  rate stats ("ERA", "WHIP"), and weight "IP"
          - The default position ID mapping is:
                {1: 'SP', 2: 'C', 3: '1B', 4: '2B', 5: '3B', 6: 'SS',
                 7: 'LF', 8: 'CF', 9: 'RF', 10: 'DH', 11: 'RP'}
          - Players with Default Position ID 1 or 11 are pitchers; all others are hitters.

        Aggregation rules:
          - Counting stats: Sum the stat over the group and then divide by the number of players
            in the subgroup (hitters or pitchers).
          - Rate stats: Compute a weighted average using the appropriate playing time column
            (using "PA" for hitters and "IP" for pitchers).

        Returns:
          A DataFrame with one row per team that includes aggregated stats.
        """
        # Gather projections
        projections_df = self.compile_player_projections_df()

        # Define which positions are considered pitchers
        pitcher_ids = {1, 11}

        # Define stat categories for hitters
        hitter_cats = self.hitting_categories
        projections_df.to_csv('player_projections.csv')
        hitter_counting = [5, 20, 21, 23]
        hitter_rate = [9, 17]

        # Define stat categories for pitchers
        pitcher_cats = self.pitching_categories
        pitcher_counting = [34, 48, 53, 57, 63]
        pitcher_rate = [41, 47]

        # Group the DataFrame by team
        team_groups = projections_df.groupby(["Team ID", "Team Name"])
        team_rows = []

        # Loop through each team group
        for (team_id, team_name), group in team_groups:
            team_data = {"Team ID": team_id, "Team Name": team_name}

            # Separate hitters and pitchers using the default position id
            hitters = group[~group["Default Position ID"].isin(pitcher_ids)]
            pitchers = group[group["Default Position ID"].isin(pitcher_ids)]

            # --- Aggregate Hitting Stats ---
            n_hitters = len(hitters)
            # Counting stats: sum and average (sum divided by count)
            for stat in hitter_cats:
                if stat in hitter_counting:
                    if stat in hitters.columns:
                        total = hitters[stat].sum()
                        team_data[stat] = total / n_hitters if n_hitters > 0 else None
                    else:
                        team_data[stat] = None

            # Rate stats: weighted average using hitter weight (PA)
                elif stat in hitter_rate:
                    if stat == 9:
                        slg = hitters[8].sum() / hitters[0].sum()
                        team_data[stat] = slg
                    elif stat == 17:
                        num = hitters[1].sum() + hitters[10].sum() + hitters[12].sum()
                        denom = hitters[0].sum() + hitters[10].sum() + hitters[12].sum() + hitters[13].sum()
                        obp = num / denom
                        team_data[stat] = obp
                    else:
                        team_data[stat] = None

            # Optionally include average playing time for hitters
            # team_data["Average PA"] = hitters[hitter_weight].mean() if (
                        # hitter_weight in hitters.columns and n_hitters > 0) else None

            # --- Aggregate Pitching Stats ---
            n_pitchers = len(pitchers)
            # Counting stats: sum then average
            for stat in pitcher_cats:
                if stat in pitcher_counting:
                    if stat in pitchers.columns:
                        total = pitchers[stat].sum()
                        team_data[stat] = total / n_pitchers if n_pitchers > 0 else None
                    else:
                        team_data[stat] = None

            # Rate stats: weighted average using pitcher weight (IP)
                elif stat in pitcher_rate:
                    if stat == 41:
                        whip = (pitchers[39].sum() + pitchers[37].sum()) / (pitchers[34].sum() / 3)
                        team_data[stat] = whip
                    elif stat == 47:
                        era = pitchers[45].sum() / (pitchers[34].sum() / 27)
                        team_data[stat] = era
                    else:
                        team_data[stat] = None

            # Optionally add counts for debugging or further analysis
            # team_data["Total Players"] = len(group)
            # team_data["Hitters Count"] = n_hitters
            # team_data["Pitchers Count"] = n_pitchers

            team_rows.append(team_data)

        df = pd.DataFrame(team_rows)

        if rename_stats:
            df.rename(
                columns=lambda col: ({**HITTING_MAP, **PITCHING_MAP}).get(int(col)) if str(col).isdigit() and int(col) in {
                    **HITTING_MAP, **PITCHING_MAP} else col, inplace=True)

        # Convert the list of dictionaries into a DataFrame
        return df
