# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 09:11:42 2021
@author: k1332
"""

from selenium import webdriver
import pandas as pd
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import openpyxl

# Initialize WebDriver
driver = webdriver.Chrome()

def get_match_ids(driver):
    search_url = "https://www.flashscore.com"
    driver.get(search_url)
    time.sleep(1)
    answer = input('are you ready to run scraper ?..Y/N>>')
    if answer == "n" or answer == "N":
        exit()
    print('scraper is running please wait..\n')
    
    date_elem = driver.find_element(By.CLASS_NAME, 'calendar__datepicker')
    date = date_elem.text           # chosen specific day
    print("\n\n**** Date : ", date, "  ****\n\n")
    
    
    ## unroll all hidden games
    WebDriverWait(driver, 20)
    driver.find_element('xpath', '//*[@id="onetrust-accept-btn-handler"]').click()
    
    unroll_elements = WebDriverWait(driver, 20).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='wcl-icon-action-navigation-arrow-down']")))

    print("unroll elements number --------> ",len(unroll_elements))
    i = 0
    for element in unroll_elements:
        while True:
            try:
                #driver.execute_script("window.scrollBy(0,100)","")
                element.click()
                i  += 1
                print('clicked : ', i)
                break
            except:
                driver.execute_script("window.scrollBy(0,100)","")
                print(i, "...")
                              
    ## get all match ids
    matches = driver.find_elements(By.CLASS_NAME, 'event__match--twoLine')
    matches_number = len(matches)   # the number of matches of specific day
    print("\n**** Total Matches Number : ", matches_number, "  ****\n")
    
    match_ids = []
    for match in matches:
        #event__score
        soup_sc = BeautifulSoup(match.get_attribute('innerHTML'), 'html.parser')
        scores_list = soup_sc.find_all("div", {"class" : "event__score"})
        if len(scores_list)>0:
            try:
                s = int(scores_list[0].text.strip())
            except:
                row_id = match.get_attribute('id')
                row_id = row_id[4:]
                match_ids.append(row_id)
        else:
            row_id = match.get_attribute('id')
            row_id = row_id[4:]
            match_ids.append(row_id)            
    print(f"\n**** Total Available Unplayed Matches Number : ", {len(match_ids)}, "  ****\n")
    return date, match_ids


def scrape_team_1_2(driver, temp_id, odds):
    url_overall = f"https://www.flashscore.com/match/{temp_id}/#/standings/top_scorers"
    driver.get(url_overall)
    time.sleep(3)
    
    league_info = driver.find_element(By.CLASS_NAME, 'tournamentHeader__sportNavWrapper')
    soup_leg = BeautifulSoup(league_info.get_attribute('innerHTML'), 'html.parser')
    
    if 'women' in soup_leg.find("span", {"class": "tournamentHeader__country"}).text.lower():
        print("\n*** Skipped, WOMEN game...")
        return None
    
    leg_name = soup_leg.find("span", {"class": "tournamentHeader__country"}).text.split("- Round")[0].strip()
    round_number = soup_leg.find("span", {"class": "tournamentHeader__country"}).text.split("- Round ")[1].strip()

    teams_div = driver.find_element(By.CLASS_NAME, 'duelParticipant')
    soup_tm = BeautifulSoup(teams_div.get_attribute('innerHTML'), 'html.parser')
    tms = soup_tm.find_all("div", {"class": "participant__participantNameWrapper"})
    game_time = soup_tm.find("div", {"class": "duelParticipant__startTime"}).text.split(" ")[-1]
    game_score = soup_tm.find("div", {"class": "detailScore__wrapper"}).text.strip()
    
    scores_div = driver.find_element(By.ID, 'tournament-table-tabs-and-content')
    soup_score = BeautifulSoup(scores_div.get_attribute('innerHTML'), 'html.parser')
    top_score_teams = soup_score.find_all("div", {"class": "ui-table__row topScorers__row topScorers__row--selected"})
    
    if game_score != '-':
        print("\n### Skipped because the game is finished! ###")
        return None

    if int(round_number) <= 5:
        print("\n### Skipped because the round number is 5 or less! ###")
        return None

    if len(top_score_teams) < 3:
        print("score lengths: =======",  len(top_score_teams))
        print("\n### Skipped because there are less than 4 top scorers! ###")
        return None

    tm_name_h = tms[0].text.strip()
    tm_name_a = tms[1].text.strip()
    
    team_info = []

    # Loop through the first four items
    for item in top_score_teams[:4]:
        # Find all <a> tags within the item
        a_tags = item.find_all("a")
        if len(a_tags) > 1:
            # Get the text of the second <a> tag
            score_team = a_tags[1].get_text(strip=True)
            
            # Find the following <span> tag and get its text
            following_span = a_tags[1].find_next("span")
            score = following_span.get_text(strip=True) if following_span else ""
            if (score_team == tm_name_h):
                team_number = 1
            else : team_number = 2
            # Append a list containing the second <a> tag text and the following <span> text
            team_info.append([score_team, team_number, score])

    # Print the two-dimensional array of team information
    print(team_info)
    
    
    res = [leg_name, tm_name_h, tm_name_a, game_time, '\t', '\t', round_number, '\t', 
           team_info[0][1], team_info[0][2], '\t', team_info[1][1], team_info[1][2], '\t', team_info[2][1], team_info[2][2], '\t', team_info[3][1], team_info[3][2]]
    
    print(res)
    return res


def get_odds_data_2():
    odds_data = {}
    browser_2 = webdriver.Chrome()
    target_url = "https://www.betexplorer.com/next/soccer/"
    browser_2.get(target_url)
    WebDriverWait(browser_2, 10).until(
        EC.presence_of_element_located((By.ID, 'nr-ko-all'))
    )
    time.sleep(5)
    
    process_key = input("Do you process from this odds portal page? y(yes)/Enter(no) ")
    browser_2.minimize_window()
    print("\n\n*** Getting Odds Data from betexplorer.com....")
    
    soup_tm = BeautifulSoup(browser_2.find_element(By.ID, 'nr-ko-all').get_attribute('innerHTML'), 'html.parser')
    soup_tbody_list = soup_tm.find_all("ul", {"class": "table-main__matchInfo"})
    print(len(soup_tbody_list))
    
    for idx, item in enumerate(soup_tbody_list):
        if 'data-def' in item.attrs:
            td_name = item.find("li", {"class": "table-main__participants"})
            match_id = td_name.find("a").get("href").rsplit('/', 2)[-2]
            td_odds = item.find("div", {"class": "table-main__oddsLi"})
            odds_data[match_id] = td_odds.text.strip().split("\n")
            print(idx, match_id, odds_data[match_id])
    
    browser_2.close()
    return odds_data

date, match_ids = get_match_ids(driver)
odds_data = get_odds_data_2()
data = []

for idx, match_id in enumerate(match_ids, 1):
    print(f"\n{idx} / {len(match_ids)} : {match_id}")
    try:
        odds = odds_data.get(match_id, ["\t", "\t", "\t"])
        res = scrape_team_1_2(driver, match_id, odds)
        if res is not None:
            data.append(res)
    except Exception as e:
        print("\tSkipped due to exception:", str(e))
    
print(len(data))
if data:
    output = pd.DataFrame(data)
    output.columns = [str(val) for val in range(len(data[0]))]
    output = output.style.set_properties(subset=[str(val+3) for val in range(len(data[0])-3)], **{'text-align': 'center'})
    
    date = date.replace("/", "_").replace(" ", "_")
    output_file_name = f"soccer_{date}.xlsx"
    
    output.to_excel(output_file_name, index=False, header=False)
    wb = openpyxl.load_workbook(output_file_name)
    sheet = wb.active
    sheet.column_dimensions['A'].width = 40
    sheet.column_dimensions['B'].width = 25
    sheet.column_dimensions['C'].width = 25
    sheet.column_dimensions['D'].width = 10
    wb.save(output_file_name)
    
    print(f"\n\n*** Successfully Created to {output_file_name} ***\n")
else:
    print("\n *** There is no result  \n")

driver.close()
