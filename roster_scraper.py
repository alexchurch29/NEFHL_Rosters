"""
Used to scrape team rosters
"""

from bs4 import BeautifulSoup
import time
import pandas as pd
from main import get_url


teams = {'ana': 1, 'ari': 23, 'bos': 3, 'buf': 4, 'cal': 5, 'car': 6, 'chi': 8, 'col': 9, 'cbj': 7, 'dal': 10,
         'det': 11, 'edm': 12, 'fla': 13, 'los': 14, 'min': 15, 'mtl': 16, 'nsh': 18, 'njd': 17, 'nyi': 19,
         'nyr': 20, 'ott': 21, 'phi': 22, 'pit': 24, 'san': 25, 'stl': 26, 'tam': 27, 'tor': 28, 'van': 29,
         'vgk': 31, 'wsh': 30, 'wpg': 2, '': 0}


def get_html(team_id):
    """
    Given a team id returns the roster page html
    Ex: http://nefhl.com/rosters?team=2
    :param team_id: 2
    :return: raw html of given team's roster page
    """
    team_id = str(team_id)
    if team_id != '0':
        url = 'http://nefhl.com/cgi-bin/rosters.cgi?team={}&'.format(team_id)
    else:
        url = 'http://nefhl.com/cgi-bin/unassigned.cgi?'

    return get_url(url)


def scrape_roster(team_id):
    """
    For a given team scrapes the roster and attributes
    :param team_id: id for team
    :return: array of arrays with full pro and farm rosters for given team
    """

    try:
        html = get_html(team_id)
        time.sleep(1)
    except Exception as e:
        print('Roster for team {} is not there'.format(team_id), e)
        raise Exception

    soup = BeautifulSoup(html.content, 'html.parser')
    table = soup.find_all('td')
    players = [x.get_text() for x in table]

    if team_id !=0:
        # need to normalize the length of goalie rows, which are missing AOV otherwise
        for i, j in enumerate(players):
            if j == 'G':
                players.insert(i+18, players[i+17])

        # now we split our master list into a list of lists (one for each player)
        players = [players[i:i + 21] for i in range(0, len(players), 21)]
        # add team
        team = [key for key, value in teams.items() if value == team_id][0].upper()
        for i in players:
            i.append(team)

    # unassigned has different formatting
    else:
        # delete headers
        del players[0:17]

        # split our master list into a list of lists (one for each player)
        players = [players[i:i + 17] for i in range(0, len(players), 17)]
        # remove whitespace in player name, and convert unassigned wingers to proper positions
        for i in players:
            if i[2] == 'LW':
                i[2] = 'L'
            if i[2] == 'RW':
                i[2] = 'R'
            i[0] = i[0].rstrip()
        # add fabricated #, HD, CD, IJ, AOV and remove Age
            del i[1]
            i.insert(0, '0')
            i.insert(3, 'NA')
            i.insert(4, 'OK')
            i.insert(5, '')
            i.append(i[len(i)-1])
            i.append('')

    return players


def scrape_all_teams():
    """
    create dataframe with full list of players and attributes from all teams
    :return: dataframe with all players
    """
    players = []
    for key in teams:
        roster = scrape_roster(teams[key])
        for player in roster:
            players.append(player)

    headers = ['#', 'Player', 'PO', 'HD', 'CD', 'IJ', 'IT', 'SP', 'ST', 'EN', 'DU', 'DI', 'SK', 'PA', 'PC', 'DF', 'SC',
               'EX', 'LD', 'OV', 'AOV', 'TEAM']
    df = pd.DataFrame.from_records(players, columns=headers)
    df.to_excel("Ratings.xlsx", index=False)
    df = pd.read_excel("Ratings.xlsx")

    # add average columns
    df['AVG'] = (df.PA + df.PC + df.SC) / 3
    df['Rank'] = df.groupby('PO')['AVG'].rank(ascending=False, method='min')
    df['Rank(PA)'] = df.groupby('PO')['PA'].rank(ascending=False, method='min')
    df['Rank(PC)'] = df.groupby('PO')['PC'].rank(ascending=False, method='min')
    df['Rank(SC)'] = df.groupby('PO')['SC'].rank(ascending=False, method='min')

    df.to_excel("Ratings.xlsx", index=False)

    return df
