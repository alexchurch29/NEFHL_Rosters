"""
generates a list of all contracts signed by active players
"""

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd
from main import get_url, teams


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
    For a given team scrapes the roster for all player IDs
    :param team_id: id for team
    :return: array with all player IDs for the roster of a given team
    """

    try:
        html = get_html(team_id)
        time.sleep(1)
    except Exception as e:
        print('Roster for team {} is not there'.format(team_id), e)
        raise Exception

    soup = BeautifulSoup(html.content, 'html.parser')
    players = []

    for item in soup.find_all(attrs={'class': 'name'}):
        for link in item.find_all('a'):
            player = {}
            if link.get('onclick').find("playerID") > -1:
                player["pos"] = 'P'
            else:
                player["pos"] = 'G'
            player["id"] = (link.get('onclick')[link.get('onclick').index("ID=")+3:link.get('onclick').index("';")])
            players.append(player)

    return players


def scrape_all_rosters():
    """
    create dataframe with full list of players IDs
    :return: dataframe with all players
    """
    players = []
    for key in teams:
        players.append(scrape_roster(teams[key]))

    return players


def scrape_player_pages(player_id, pos):
    """
    For a given player scrapes their player page
    :param player_id: id for player
    :param pos: position of player
    :return: dict with all contract info available
    """

    if pos == 'G':
        url = 'http://nefhl.com/player?goalieID={}&'.format(player_id)
    else:
        url = 'http://nefhl.com/player?playerID={}&'.format(player_id)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get(url)

    e = driver.find_element_by_id('t3-content')
    iframe = e.find_element_by_tag_name('iframe')
    iframe_url = iframe.get_attribute('src')
    
    driver.get(iframe_url)
    wait = WebDriverWait(driver, 5)
    wait.until(EC.presence_of_element_located((By.ID, 'full_page')))
    rosters = driver.find_element_by_id('full_page').text.split('\n')

    player_details = {}

    for i in rosters:
        if i.find("Age: ") > -1:
            player_details["Age"] = int(i[5:])

    name = rosters[0].strip().split()
    player_details["Name"] = name[0] + " " + name[1]

    curr_year = int(rosters[rosters.index('Yearly Stats') + 2][14:18])

    transactions = []
    try:
        for i in rosters[rosters.index('Transactions'):rosters.index('Career Stats')]:
            if i.find('Signed') > -1 or i.find('Re-signed') > -1:
                signing = {}
                signing["year"] = int(i[:4])
                try:
                    signing["length"] = int(i[i.find("to a ")+5:][0])
                except:
                    if i[i.find("to a ")+5:][:3] == "one":
                        signing["length"] = 1
                    elif i[i.find("to a ")+5:][:3] == "two":
                        signing["length"] = 2
                    elif i[i.find("to a ")+5:][:5] == "three":
                        signing["length"] = 3
                    elif i[i.find("to a ")+5:][:4] == "four":
                        signing["length"] = 4
                signing["age"] = int(player_details["Age"] - (curr_year - signing["year"]))
                if i.find('Re-signed') > -1:
                    signing["status"] = "RFA"
                else:
                    signing["status"] = "UFA"
                transactions.append(signing)
    except:
        try:
            for i in rosters[rosters.index('Trades'):rosters.index('Career Stats')]:
                if i.find('Signed') > -1 or i.find('Re-signed') > -1:
                    signing = {}
                    signing["year"] = int(i[:4])
                    try:
                        signing["length"] = int(i[i.find("to a ")+5:][0])
                    except:
                        if i[i.find("to a ")+5:][:3] == "one":
                            signing["length"] = 1
                        elif i[i.find("to a ")+5:][:3] == "two":
                            signing["length"] = 2
                        elif i[i.find("to a ")+5:][:5] == "three":
                            signing["length"] = 3
                        elif i[i.find("to a ")+5:][:4] == "four":
                            signing["length"] = 4
                    signing["age"] = int(player_details["Age"] - (curr_year - signing["year"]))
                    if i.find('Re-signed') > -1:
                        signing["status"] = "RFA"
                    else:
                        signing["status"] = "UFA"
                    transactions.append(signing)
        except:
            print(player_id)
            return

    player_details["Transactions"] = transactions

    for i in player_details["Transactions"]:
        year = i["year"]
        try:
            for j in rosters[rosters.index('Player Ratings'):rosters.index('Transactions')]:
                if j[:4] == str(year):
                    salary = j[j.find('$'):j.find('$') + 10].strip()
                    salary = salary.replace(',', '')
                    salary = salary.replace('$', '')
                    salary = salary.split()
                    i["salary"] = int(salary[0])
                    if year < 2016:
                        i["OV"] = j[-5:-3]
                    else:
                        i["OV"] = j[-2:]
        except:
            for j in rosters[rosters.index('Player Ratings'):rosters.index('Trades')]:
                if j[:4] == str(year):
                    salary = j[j.find('$'):j.find('$') + 10].strip()
                    salary = salary.replace(',', '')
                    salary = salary.replace('$', '')
                    salary = salary.split()
                    i["salary"] = int(salary[0])
                    i["OV"] = j[-2:]

    driver.quit()

    return player_details


def scrape_all_player_pages():
    """
    create dataframe with full list of contracts
    :return: dataframe with all contracts
    """
    signings = []
    ids = scrape_all_rosters()
    for i in ids:
        for j in i:
            try:
                player = (scrape_player_pages(j["id"], j["pos"]))
                for v, k in enumerate(player["Transactions"]):
                    if k["status"] == "RFA":
                        signing = []
                        signing.append(player["Name"])
                        signing.append(j["pos"])
                        signing.append(k["age"])
                        signing.append(k["length"])
                        signing.append(k["salary"])
                        try:
                            signing.append(player["Transactions"][v+1]["salary"])
                            signing.append(k["OV"])
                            signings.append(signing)
                        except:
                            continue
            except:
                continue

    headers = ['Player', 'Pos', 'Age', 'Length', 'Salary', 'PrevSalary', 'OV']
    df = pd.DataFrame.from_records(signings, columns=headers)
    df["Salary"] = pd.to_numeric(df["Salary"])
    df["OV"] = pd.to_numeric(df["OV"])
    df.to_excel("Contracts.xlsx", index=False)

    return

print(scrape_all_player_pages())
