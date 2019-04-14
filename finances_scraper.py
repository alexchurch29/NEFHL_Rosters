"""
Used to scrape team finances
"""

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from main import teams


def scrape_finances(team_id):
    """
    For a given team scrapes the finances
    :param team_id: id for team
    :return: array of arrays with full pro and farm finances for given team
        in format [first_name, last_name, salary, term]
    """

    url = 'http://nefhl.com/finance?team={}&'.format(str(team_id))

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get(url)

    e = driver.find_element_by_id('t3-content')
    iframe = e.find_element_by_tag_name('iframe')
    iframe_url = iframe.get_attribute('src')

    driver.get(iframe_url)
    wait = WebDriverWait(driver, 5)
    wait.until(EC.presence_of_element_located((By.ID, 'statistics')))
    rosters = driver.find_element_by_id('statistics').text.split('\n')

    rosters = rosters[rosters.index('PRO PAYROLL'):len(rosters)-1]
    rosters = [x for x in rosters if x.find(')') != -1 or x.find('FARM PAYROLL') != -1]
    rosters = [x.replace(',', '') for x in rosters]
    rosters = [x.replace('(', ' ') for x in rosters]
    rosters = [x.replace(')', '') for x in rosters]
    rosters = [x[::-1].split(' ', 2) for x in rosters]

    team = [key for key, value in teams.items() if value == team_id][0].upper()
    farm_index = rosters.index(['LLORYAP', 'MRAF'])

    for x, elem in enumerate(rosters):
        rosters[x] = rosters[x][::-1]
        for y, elem in enumerate(rosters[x]):
            rosters[x][y] = rosters[x][y][::-1]
        rosters[x].append(team)
        if x > farm_index:
            rosters[x][1] = int(rosters[x][1]) * 10

    rosters.remove(['FARM', 'PAYROLL', team])

    driver.quit()

    return rosters


def scrape_all_salaries():
    """
    create dataframe with full list of players and salaries from all teams
    :return: dataframe with all players
    """
    players = []
    for key in teams:
        if key != '':
            roster = scrape_finances(teams[key])
            for player in roster:
                players.append(player)

    headers = ['Player', 'Salary', 'Year', 'TEAM']
    df = pd.DataFrame.from_records(players, columns=headers)
    df["Salary"] = pd.to_numeric(df["Salary"])
    df["Year"] = pd.to_numeric(df["Year"])

    return df

# scrape_all_salaries()
