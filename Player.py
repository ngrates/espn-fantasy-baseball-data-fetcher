from espn_constant import DEFAULT_POSITION_ID_MAP, HITTING_MAP, PITCHING_MAP, FIELDING_MAP
import math


class Player:
    def __init__(self, player_json):
        # Store raw JSON data
        self.other_stats = None
        self.season_stats_placeholder = None
        self.projections_placeholder = None
        self._raw_data = player_json

        # Initialize attributes
        self.player_id = None
        self.full_name = None
        self.active = None
        self.default_position_id = None
        self.pro_team_id = None
        self.injury_status = None
        self.ownership = None
        self.eligible_slots = None
        self.team_id = None
        self.fantasy_team = None
        self.waiver_status = None
        self.projections = None
        self.projected_pa = None
        self.projected_ip = None
        self.season_stats = None

        # Parse initial data
        self._parse_basic_info()
        self._parse_fantasy_status()
        self._parse_stats()

    @property
    def player_data(self):
        """
        Returns the core player data regardless of JSON nesting.
        """
        if "playerPoolEntry" in self._raw_data:
            return self._raw_data["playerPoolEntry"]["player"]
        return self._raw_data["player"]

    @property
    def fantasy_data(self):
        """
        Returns the fantasy status data for the player.
        """
        if "playerPoolEntry" in self._raw_data:
            return self._raw_data["playerPoolEntry"]
        return self._raw_data

    @property
    def is_hitter(self):
        if self.default_position_id is None:
            return False
        # Lookup the position using the updated DEFAULT_POSITION_ID_MAP
        position = DEFAULT_POSITION_ID_MAP.get(self.default_position_id)
        # Consider a player a hitter if their position is not 'SP' or 'RP'
        return position not in ('SP', 'RP')

    def _parse_basic_info(self):
        """
        Parse basic player information from the raw data.
        """
        data = self.player_data
        self.player_id = data.get("id")
        self.full_name = data.get("fullName", "Unknown Player")
        self.active = data.get("active")
        self.default_position_id = data.get("defaultPositionId")
        self.pro_team_id = data.get("proTeamId")
        self.injury_status = data.get("injuryStatus", "N/A")
        self.ownership = data.get("ownership", {}).get("percentOwned", 0)
        self.eligible_slots = data.get("eligibleSlots", [])
        if self.default_position_id is None:
            print(f"Warning: Player {self.full_name} (ID: {self.player_id}) has no default_position_id. Skipping projection calculation.")

    def _parse_fantasy_status(self):
        """
        Parse fantasy league status information.
        """
        data = self.fantasy_data
        if data["onTeamId"] != 0:
            self.team_id = data["onTeamId"]
            self.fantasy_team = "Unknown"  # Will be updated by League class
        else:
            self.fantasy_team = "Free Agent"
        self.waiver_status = data.get("waiverStatus", {}).get("status", "NONE")

    import math

    def _parse_stats(self):
        """
        Update all stats from the player's raw data.
        Stores projection stats, season stats, and any other stat entries as placeholders.
        This version converts the keys from string to int while converting the values to ints (handling infinity).
        """
        data = self.player_data
        if not data.get("stats"):
            return

        # Reset any previous stats
        self.projections = {}
        self.season_stats = {}
        self.projections_placeholder = {}  # for other projection entries
        self.season_stats_placeholder = []  # for non-primary season stat splits
        self.other_stats = {}  # for any other stat sources

        def convert_stats_keys(stats_dict):
            """
            Helper function to convert keys in stats_dict from strings to integers.
            Also converts each value to int (via float conversion) and handles infinity.
            """
            converted = {}
            for k, v in stats_dict.items():
                try:
                    # Convert key to an integer if possible.
                    new_key = int(k)
                except (ValueError, TypeError):
                    new_key = k  # leave as-is if conversion fails

                try:
                    # Convert the value to float first (to handle strings like "123.0"), then to int.
                    value = float(v)
                    if math.isinf(value):
                        converted[new_key] = 0
                    else:
                        converted[new_key] = int(value)
                except (ValueError, TypeError, OverflowError):
                    converted[new_key] = v
            return converted

        for stat in data["stats"]:
            stat_source = stat.get("statSourceId")
            stat_id = stat.get("id")
            stats_dict = stat.get("stats", {})

            # Convert the stat keys from string to int.
            stats_dict = convert_stats_keys(stats_dict)

            # For ESPN projections (statSourceId 1)
            if stat_source == 1:
                if stat_id == "102025":
                    self.projections = stats_dict
                    if self.is_hitter:
                        self.projected_pa = stats_dict.get("PA", 0)  # if "PA" exists as a key
                    else:
                        self.projected_ip = stats_dict.get("IP", 0)  # if "IP" exists as a key
                else:
                    self.projections_placeholder[stat_id] = stats_dict

            # For actual season stats (statSourceId 0)
            elif stat_source == 0:
                if stat.get("statSplitTypeId") == 0:
                    self.season_stats = stats_dict
                else:
                    self.season_stats_placeholder.append({
                        "id": stat_id,
                        "splitType": stat.get("statSplitTypeId"),
                        "stats": stats_dict
                    })
            else:
                self.other_stats[stat_source] = stats_dict

    def get_player_stats(self):
        """
        Get the player's actual season stats.
        """
        if self.season_stats is None:
            self._parse_stats()
        return self.season_stats

    def get_weighted_projection(self, stat):
        """
        Get a weighted projection for a given statistic based on playing time.
        """
        if self.projections is None:
            self._parse_projections()

        if not self.projections:
            return 0

        if self.is_hitter:
            if not self.projected_pa:
                return 0
            value = self.projections.get(stat, 0) * (self.projected_pa / 600)
        else:
            if not self.projected_ip:
                return 0
            value = self.projections.get(stat, 0) * (self.projected_ip / 180)

        return value

    def __str__(self):
        return f"{self.full_name} ({self.fantasy_team or 'FA'})"
