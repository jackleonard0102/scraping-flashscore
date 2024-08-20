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
        soup_sc = BeautifulSoup(match.get_attribute('innerHTML'), 'html.parser')
        scores_list = soup_sc.find_all("div", {"class" : "event__score"})
        if len(scores_list) > 0:
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


def scrape_team_1_2(driver, temp_id):
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
        print("\n### Skipped because there are less than 3 top scorers! ###")
        return None

    tm_name_h = tms[0].text.strip()
    tm_name_a = tms[1].text.strip()
    
    team_info = []

    for item in top_score_teams[:4]:
        a_tags = item.find_all("a")
        if len(a_tags) > 1:
            score_team = a_tags[1].get_text(strip=True)
            following_span = a_tags[1].find_next("span")
            score = following_span.get_text(strip=True) if following_span else ""
            team_number = 1 if score_team == tm_name_h else 2
            team_info.append([score_team, team_number, score])

    print(team_info)
    
    url_table = f"https://www.flashscore.com/match/{temp_id}/#/standings/table/overall"
    driver.get(url_table)
    time.sleep(3)
    
    standings_div = driver.find_element(By.ID, 'tournament-table-tabs-and-content')
    soup_standings = BeautifulSoup(standings_div.get_attribute('innerHTML'), 'html.parser')
    standings_data = soup_standings.find_all("div", {"class": "ui-table__row table__row--selected"})
    # print ("this is standings_data ========? ", standings_data)
    form_icons_G_H = ["", ""]
    form_icons_J_K = ["", ""]
    
    min_value_span = None
    
    for idx, standing_div in enumerate(standings_data):
        team_name_tag = standing_div.find("a", {"class": "tableCellParticipant__name"})
        team_name = team_name_tag.text.strip() if team_name_tag else "N/A"
        # print ("this is team_name ===================? ", team_name)
        form_icons = standing_div.find_all("div", {"class": "tableCellFormIcon _trigger_1dbpj_26"})
        form_icons_text = [icon.text.strip() for icon in form_icons[:2]]
        # print ("this is form_icons ============? " , form_icons, "===========" , form_icons_text)
        value_spans = standing_div.find_all("span", {"class": "table__cell table__cell--value"})
        value_spans_text = [int(span.text.strip()) for span in value_spans[:1]]
        # print ("this is value_spans =============? ", value_spans)
        if min_value_span is None:
            min_value_span = value_spans_text[0]
        else:
            min_value_span = min(min_value_span, value_spans_text[0])
    
        if idx == 0:
            if team_name == tm_name_h:
                form_icons_G_H = form_icons_text
            else:
                form_icons_J_K = form_icons_text
        
        if idx == 1:
            if team_name == tm_name_h:
                form_icons_G_H = form_icons_text
            else:
                form_icons_J_K = form_icons_text
    
    res = [leg_name, tm_name_h, tm_name_a, game_time, '\t', '\t', min_value_span, '\t', form_icons_G_H[0], form_icons_G_H[1], '\t',  form_icons_J_K[0], form_icons_J_K[1], '\t', team_info[0][1], team_info[0][2], '\t', team_info[1][1], team_info[1][2], '\t', team_info[2][1], team_info[2][2], '\t', team_info[3][1], team_info[3][2]]
    
    print(res)
    return res


date, match_ids = get_match_ids(driver)
data = []

for idx, match_id in enumerate(match_ids, 1):
    print(f"\n{idx} / {len(match_ids)} : {match_id}")
    try:
        res = scrape_team_1_2(driver, match_id)
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
    output_file = f"{date}.xlsx"
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        output.to_excel(writer, index=False)
    print(f"\n\nOutput saved as {output_file}")
else:
    print("\n\nNo data to save.")

driver.quit()
