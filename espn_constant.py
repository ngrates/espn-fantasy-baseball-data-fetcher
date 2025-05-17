POSITION_MAP = {
    0: 'C',
    1: '1B',
    2: '2B',
    3: '3B',
    4: 'SS',
    5: 'OF',
    6: '2B/SS',
    7: '1B/3B',
    8: 'LF',
    9: 'CF',
    10: 'RF',
    11: 'DH',
    12: 'UTIL',
    13: 'P',
    14: 'SP',
    15: 'RP',
    16: 'BE',
    17: 'IL',
    19: 'IF',  # 1B/2B/SS/3B
    # reverse TODO
    # 18, 21, 22 have appeared but unknown what position they correspond to
}

DEFAULT_POSITION_ID_MAP = {
    1: 'SP',
    2: 'C',
    3: '1B',
    4: '2B',
    5: '3B',
    6: 'SS',
    7: 'LF',
    8: 'CF',
    9: 'RF',
    10: 'DH',
    11: 'RP'
}

PRO_TEAM_MAP = {
    0: 'FA',
    1: 'Bal',
    2: 'Bos',
    3: 'LAA',
    4: 'ChW',
    5: 'Cle',
    6: 'Det',
    7: 'KC',
    8: 'Mil',
    9: 'Min',
    10: 'NYY',
    11: 'Oak',
    12: 'Sea',
    13: 'Tex',
    14: 'Tor',
    15: 'Atl',
    16: 'ChC',
    17: 'Cin',
    18: 'Hou',
    19: 'LAD',
    20: 'Wsh',
    21: 'NYM',
    22: 'Phi',
    23: 'Pit',
    24: 'StL',
    25: 'SD',
    26: 'SF',
    27: 'Col',
    28: 'Mia',
    29: 'Ari',
    30: 'TB',
}

HITTING_MAP = {
    0: 'AB',
    1: 'H',
    2: 'AVG',
    3: '2B',
    4: '3B',
    5: 'HR',
    6: 'XBH',  # 2B + 3B + HR
    7: '1B',
    8: 'TB',  # 1 * COUNT(1B) + 2 * COUNT(2B) + 3 * COUNT(3B) + 4 * COUNT(HR)
    9: 'SLG',
    10: 'BB',
    11: 'IBB',
    12: 'HBP',
    13: 'SF',  # Sacrifice Fly
    14: 'SH',  # Sacrifice Hit - i.e. Sacrifice Bunt
    15: 'SAC',  # total sacrifices = SF + SH
    16: 'PA',
    17: 'OBP',
    18: 'OPS',  # OBP + SLG
    19: 'RC',  # Runs Created = TB * (H + BB) / (AB + BB)
    20: 'R',
    21: 'RBI',
    22: 'Unknown1',
    23: 'SB',
    24: 'CS',
    25: 'SB-CS',  # net steals
    26: 'GDP',
    27: 'SO',  # batter strike-outs
    28: 'PS',  # pitches seen
    29: 'PPA',  # pitches per plate appearance = PS / PA
    30: 'Unknown2',
    31: 'CYC'
}

PITCHING_MAP = {
    32: 'GP',  # pitcher games pitched
    33: 'GS',  # games started
    34: 'OUTS',  # divide by 3 for IP
    35: 'TBF',
    36: 'P',  # pitches
    37: 'H',
    38: 'OBA',  # Opponent Batting Average
    39: 'BB',
    40: 'IBB',  # intentional walks allowed
    41: 'WHIP',
    42: 'HBP',
    43: 'OOBP',  # Opponent On-Base Percentage
    44: 'R',
    45: 'ER',
    46: 'HR',
    47: 'ERA',
    48: 'K',
    49: 'K/9',
    50: 'WP',
    51: 'BK',
    52: 'PK',  # pickoff
    53: 'W',
    54: 'L',
    55: 'WPCT',  # Win Percentage
    56: 'SVO',  # Save opportunity
    57: 'SV',
    58: 'BS',  # BLown SaVe
    59: 'SV%',  # Save percentage
    60: 'HLD',
    61: 'Unknown1',
    62: 'CG',
    63: 'QS',
    64: 'Unknown2',
    65: 'NH',  # No-hitters
    66: 'PG',  # Perfect Games
}

FIELDING_MAP = {
    67: 'TC',  # Total Chances = PO + A + E
    68: 'PO',  # Put Outs
    69: 'A',  # Assists
    70: 'OFA',  # Outfield Assists
    71: 'FPCT',  # Fielding Percentage
    72: 'E',
    73: 'DP',  # Double plays turned
}

ACTIVITY_MAP = {
    178: 'FA ADDED',
    180: 'WAIVER ADDED',
    179: 'DROPPED',
    181: 'DROPPED',
    239: 'DROPPED',
    244: 'TRADED',
    'FA': 178,
    'WAIVER': 180,
    'TRADED': 244
}

MATCHUP_PERIOD_MAP_2021 = {
    1: (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11),
    2: (12, 13, 14, 15, 16, 17, 18),
    3: (19, 20, 21, 22, 23, 24, 25),
    4: (26, 27, 28, 29, 30, 31, 32),
    5: (33, 34, 35, 36, 37, 38, 39),
    6: (40, 41, 42, 43, 44, 45, 46),
    7: (47, 48, 49, 50, 51, 52, 53),
    8: (54, 55, 56, 57, 58, 59, 60),
    9: (61, 62, 63, 64, 65, 66, 67),
    10: (68, 69, 70, 71, 72, 73, 74),
    11: (75, 76, 77, 78, 79, 80, 81),
    12: (82, 83, 84, 85, 86, 87, 88),
    13: (89, 90, 91, 92, 93, 94, 95),
    14: (96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109),
    15: (110, 111, 112, 113, 114, 115, 116),
    16: (117, 118, 119, 120, 121, 122, 123),
    17: (124, 125, 126, 127, 128, 129, 130),
    18: (131, 132, 133, 134, 135, 136, 137),
    19: (138, 139, 140, 141, 142, 143, 144),
    20: (145, 146, 147, 148, 149, 150, 151),
    21: (152, 153, 154, 155, 156, 157, 158),
    22: (159, 160, 161, 162, 163, 164, 165),
    23: (166, 167, 168, 169, 170, 171, 172),
    24: (173, 174, 175, 176, 177, 178, 179),
    25: (180, 181, 182, 183, 184, 185, 186)
}
