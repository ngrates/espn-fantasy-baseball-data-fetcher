import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import table
from collections import defaultdict
from League import League


def calculate_roto_standings(df, categories):
    # This function still needs to be finished. Do not use yet
    roto_scores = pd.DataFrame(index=df.index)
    for col in categories:
        assert col in df.columns, f'Category {col} is not found in the dataframe.'
        # Roto score calculation is wrong.  Revise below statement
        roto_scores[col] = df[col].rank(ascending=False, method='min')
    roto_scores['Roto Points'] = roto_scores.sum(axis=1)
    return roto_scores


def aggregate_season_stats(hitting_data, pitching_data, league_names):
    hitting_combined = pd.concat(hitting_data, ignore_index=False)
    pitching_combined = pd.concat(pitching_data, ignore_index=False)

    # Identify counting stats
    hitting_counting_stats = ["AB", "H", "2B", "3B", "HR", "BB", "HBP", "SF", "R", "RBI", "SB"]
    pitching_counting_stats = ["GS", "OUTS", "H", "BB", "ER", "K", "SV", "HLD", "QS"]

    # Sum counting stats over multiple seasons
    hitting_agg = hitting_combined.groupby(hitting_combined.index)[hitting_counting_stats].sum()
    pitching_agg = pitching_combined.groupby(pitching_combined.index)[pitching_counting_stats].sum()

    # Calculate new stats from summed counting stats
    hitting_agg['PA'] = hitting_agg['AB'] + hitting_agg['BB'] + hitting_agg['HBP'] + hitting_agg['SF']
    hitting_agg['TB'] = hitting_agg['H'] + hitting_agg['2B'] + 2 * hitting_agg['3B'] + 3 * hitting_agg['HR']
    hitting_agg['AVG'] = hitting_agg['H'] / hitting_agg['AB']
    hitting_agg['OBP'] = hitting_agg['H'] + hitting_agg['BB'] + hitting_agg['HBP'] / hitting_agg['PA']
    hitting_agg['SLG'] = hitting_agg['TB'] / hitting_agg['AB']
    pitching_agg['WHIP'] = pitching_agg['BB'] + pitching_agg['H'] / (pitching_agg['OUTS'] / 3)
    pitching_agg['ERA'] = pitching_agg['ER'] / (27 * pitching_agg['OUTS'])

    # Rename index for readability
    hitting_agg = hitting_agg.rename(index=league_names)
    pitching_agg = pitching_agg.rename(index=league_names)

    return hitting_agg, pitching_agg


def get_all_time_records(league_id, start_season, end_season, swid, espn_s2, filename='standings.png', names=None):
    team_records = defaultdict(lambda: {'wins': 0, "losses": 0, "ties": 0, 'team_name': ''})

    for season in range(start_season, end_season + 1):
        league = League(league_id, season, swid=swid, espn_s2=espn_s2)

        for team in league.teams:
            swid = team.swid
            record = team.record
            team_id = team.team_id

            team_records[swid]['wins'] += record['wins']
            team_records[swid]['losses'] += record['losses']
            team_records[swid]['ties'] += record['ties']

            team_records[swid]['team_name'] = team.name
            team_records[swid]['id'] = team_id

    df = pd.DataFrame.from_dict(team_records, orient='index')
    # Renames the index if the variable names was given in the function call
    if names is None:
        df.index.name = 'SWID'
    else:
        df.index.name = 'Manager'
        df = df.rename(index=names)
    df['Win%'] = ((df['wins'] + 0.5 * df['ties']) / (df['wins'] + df['ties'] + df['losses'])).round(3)
    df = df.sort_values(by='Win%', ascending=False)
    return df


def df_to_image(df, filename='table.png', dpi=150, keep_index=False):
    """
    Convert a pandas DataFrame to a PNG image, with column widths sized
    according to the longest string in each column.

    :param df:         pandas DataFrame
    :param filename:   output file name (e.g., 'my_table.png')
    :param dpi:        resolution of the output PNG
    :param keep_index: if True, include the DataFrame's index as the first column.
    """
    # Copy to avoid modifying the original DataFrame
    df_str = df.copy()

    # Optionally include the index as the first column
    if keep_index:
        # If the index has a name, use it; otherwise call it 'index'
        index_col_name = df_str.index.name if df_str.index.name else 'index'
        # Insert it as the first column
        df_str.insert(0, index_col_name, df_str.index.astype(str))

    # Convert all (remaining) columns to string for consistent measuring
    df_str = df_str.astype(str)

    # 1) Determine the max width (in characters) for each column
    col_widths = []
    for col in df_str.columns:
        # Longest string in that column
        max_len = df_str[col].map(len).max()
        # Compare with the column name length
        header_len = len(col)
        col_widths.append(max(max_len, header_len))

    # 2) Estimate figure size based on column widths & number of rows
    CHAR_WIDTH = 0.15  # Approx. width in inches of a single character
    ROW_HEIGHT = 0.3  # Row height in inches
    n_rows = len(df_str) + 1  # +1 for the header row

    table_width = sum(w * CHAR_WIDTH for w in col_widths)
    table_height = n_rows * ROW_HEIGHT

    fig, ax = plt.subplots(figsize=(table_width, table_height))
    ax.set_axis_off()

    # 3) Prepare table data (header + rows)
    #    The first row of table_data is the column headers.
    table_data = [df_str.columns.tolist()] + df_str.values.tolist()

    # 4) Create the table
    the_table = ax.table(
        cellText=table_data,
        cellLoc='center',  # Center text horizontally
        loc='center'  # Place table in the center of the axes
    )

    # 5) Adjust each column's width proportionally
    for col_idx, col_width in enumerate(col_widths):
        for row_idx in range(n_rows):
            cell = the_table._cells[(row_idx, col_idx)]
            # Scale the fraction of total width
            cell.set_width(col_width * CHAR_WIDTH / table_width)

    # (Optional) Adjust font size; disable auto-scaling if you want precise control
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(10)

    # 6) Save to file
    plt.savefig(filename, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
