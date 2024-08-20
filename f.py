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
    answer = input('Are you ready to run the scraper? Y/N >> ')
    if answer.lower() == "n":
        exit()
    print('Scraper is running, please wait...\n')
    
    date_elem = driver.find_element(By.CLASS_NAME, 'calendar__datepicker')
    date = date_elem.text  # chosen specific day
    print("\n\n**** Date : ", date, "  ****\n\n")
    
    # Unroll all hidden games
    # WebDriverWait(driver, 20)
    # driver.find_element('xpath', '//*[@id="onetrust-accept-btn-handler"]').click()
    
    # unroll_elements = WebDriverWait(driver, 20).until(
    #     EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='wcl-icon-action-navigation-arrow-down']"))
    # )

    # print("Unroll elements number --------> ", len(unroll_elements))
    # i = 0
    # for element in unroll_elements:
    #     while True:
    #         try:
    #             element.click()
    #             i += 1
    #             print('Clicked: ', i)
    #             break
    #         except:
    #             driver.execute_script("window.scrollBy(0,100)", "")
    #             print(i, "...")
                              
    # Get all match ids
    matches = driver.find_elements(By.CLASS_NAME, 'event__match--twoLine')
    matches_number = len(matches)  # the number of matches of specific day
    print("\n**** Total Matches Number: ", matches_number, "  ****\n")
    
    match_ids = []
    for match in matches:
        soup_sc = BeautifulSoup(match.get_attribute('innerHTML'), 'html.parser')
        scores_list = soup_sc.find_all("div", {"class": "event__score"})
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
    print(f"\n**** Total Available Unplayed Matches Number: {len(match_ids)}  ****\n")
    return date, match_ids

def scrape_team_1_2(driver, temp_id):
    url_overall = f"https://www.flashscore.com/match/{temp_id}/#/standings/top_scorers"
    driver.get(url_overall)
    
    # Wait until the element with class 'tournamentHeader__sportNavWrapper' is present
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'tournamentHeader__sportNavWrapper'))
    )

    league_info = driver.find_element(By.CLASS_NAME, 'tournamentHeader__sportNavWrapper')
    soup_leg = BeautifulSoup(league_info.get_attribute('innerHTML'), 'html.parser')
    
    # Extract text from the <a> tag within the <span>
    a_tag = soup_leg.find("a")
    if a_tag:
        leg_and_round_text = a_tag.text.strip()
        try:
            parts = leg_and_round_text.split(" - Round ")
            if len(parts) == 2:
                leg_name = parts[0].strip()
                round_number = parts[1].strip()
            else:
                leg_name = leg_and_round_text
                round_number = 'Unknown'
        except IndexError:
            print("Error parsing round number from:", leg_and_round_text)
            leg_name = leg_and_round_text
            round_number = 'Unknown'
    else:
        print("No <a> tag found in league info.")
        leg_name = 'Unknown'
        round_number = 'Unknown'
    
    # Check if the game is a women's game
    if 'women' in soup_leg.find("span", {"class": "tournamentHeader__country"}).text.lower():
        print("\n*** Skipped, WOMEN game...")
        return None
    
    # Wait for the teams_div element to be present
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'duelParticipant'))
    )
    
    teams_div = driver.find_element(By.CLASS_NAME, 'duelParticipant')
    soup_tm = BeautifulSoup(teams_div.get_attribute('innerHTML'), 'html.parser')
    
    # Handle the case where detailScore__wrapper might not be present
    detail_score_wrapper = soup_tm.find("div", {"class": "detailScore__wrapper"})
    if detail_score_wrapper:
        game_score = detail_score_wrapper.text.strip()
    else:
        print("No game score found.")
        game_score = 'N/A'  # Or any other default value or handling
    
    # Extract game time
    game_time_div = soup_tm.find("div", {"class": "duelParticipant__startTime"})
    game_time = game_time_div.text.strip() if game_time_div else 'Unknown'
    
    # Wait for the scores_div element to be present
    try:
        scores_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'tournament-table-tabs-and-content'))
        )
        soup_score = BeautifulSoup(scores_div.get_attribute('innerHTML'), 'html.parser')
        top_score_teams = soup_score.find_all("div", {"class": "ui-table__row topScorers__row topScorers__row--selected"})
    except Exception as e:
        print(f"Error finding scores_div element: {e}")
        top_score_teams = []
    
    # Check game score and round number validity
    if game_score != '-' and round_number != 'Unknown':
        try:
            if int(round_number) <= 5:
                print("\n### Skipped because the round number is 5 or less! ###")
                return None
        except ValueError:
            print("Invalid round number value:", round_number)
            return None

    if len(top_score_teams) < 4:
        print("Score lengths: =======", len(top_score_teams))
        print("\n### Skipped because there are less than 4 top scorers! ###")
        return None

    tms = soup_tm.find_all("div", {"class": "participant__participantNameWrapper"})
    if len(tms) < 2:
        print("Insufficient team data found.")
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
    
    # Switch to the standings table URL
    url_table = f"https://www.flashscore.com/match/{temp_id}/#/standings/table/overall"
    driver.get(url_table)
    
    # Wait for the standings_div element to be present
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'tournament-table-tabs-and-content'))
    )
    
    standings_div = driver.find_element(By.ID, 'tournament-table-tabs-and-content')
    soup_standings = BeautifulSoup(standings_div.get_attribute('innerHTML'), 'html.parser')
    standings_data = soup_standings.find_all("div", {"class": "ui-table__row table__row--selected"})
    
    form_icons_G_H = ["", ""]
    form_icons_J_K = ["", ""]
    
    min_value_span = None
    
    for idx, standing_div in enumerate(standings_data):
        team_name_tag = standing_div.find("a", {"class": "tableCellParticipant__name"})
        team_name = team_name_tag.text.strip() if team_name_tag else "N/A"
        
        form_icons = standing_div.find_all("div", {"class": "tableCellFormIcon _trigger_1dbpj_26"})
        form_icons_text = [icon.text.strip() for icon in form_icons[:2]]
         
        value_spans = standing_div.find_all("span", {"class": "table__cell table__cell--value"})
        value_spans_text = [int(span.text.strip()) for span in value_spans[:1]]
        
        if min_value_span is None:
            min_value_span = value_spans_text[0]
        else:
            min_value_span = min(min_value_span, value_spans_text[0])
    
        if idx == 0:
            if team_name == tm_name_h:
                form_icons_G_H = form_icons_text
            else:
                form_icons_J_K = form_icons_text
    
    res = [leg_name, tm_name_h, tm_name_a, game_time, '\t', '\t', min_value_span, '\t', form_icons_G_H[0], form_icons_G_H[1], '\t', form_icons_J_K[0], form_icons_J_K[1], '\t', team_info[0][1], team_info[0][2]]
    
    print(res)
    return res



# Main process
date, match_ids = get_match_ids(driver)
all_data = []

# Assuming 'odds' is predefined or fetched separately for each match
for match_id in match_ids:
    result = scrape_team_1_2(driver, match_id)
    if result:
        all_data.append(result)

# Close the driver after scraping
driver.quit()

# Save the data to an Excel file
df = pd.DataFrame(all_data)
df.to_excel(f"scraped_data_{date}.xlsx", index=False)
