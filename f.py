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
    WebDriverWait(driver, 20)
    driver.find_element('xpath', '//*[@id="onetrust-accept-btn-handler"]').click()
    
    unroll_elements = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='wcl-icon-action-navigation-arrow-down']"))
    )

    print("Unroll elements number --------> ", len(unroll_elements))
    i = 0
    for element in unroll_elements:
        while True:
            try:
                element.click()
                i += 1
                print('Clicked: ', i)
                break
            except:
                driver.execute_script("window.scrollBy(0,100)", "")
                print(i, "...")
                              
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

    if len(top_score_teams) < 4:
        print("Score lengths: =======",  len(top_score_teams))
        print("\n### Skipped because there are less than 4 top scorers! ###")
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
    time.sleep(3)
    
    standings_div = driver.find_element(By.ID, 'tournament-table-tabs-and-content')
    soup_standings = BeautifulSoup(standings_div.get_attribute('innerHTML'), 'html.parser')
    standings_data = soup_standings.find_all("div", {"class": "ui-table__row table__row--selected"})
    
    # Initialize variables to store the form icon values
    form_icons_G_H = ["", ""]  # To be saved in columns G and H
    form_icons_J_K = ["", ""]  # To be saved in columns J and K
    
    # Initialize variable to store values for column M
    min_value_span = None
    
    # Iterate over the standings_data divs
    for idx, standing_div in enumerate(standings_data):
        # 1. Find the <a> tag with class "tableCellParticipant__name"
        team_name_tag = standing_div.find("a", {"class": "tableCellParticipant__name"})
        team_name = team_name_tag.text.strip() if team_name_tag else "N/A"
        
        # 2. Find all <div> tags with class "tableCellFormIcon _trigger_1dbpj_26"
        form_icons = standing_div.find_all("div", {"class": "tableCellFormIcon _trigger_1dbpj_26"})
        form_icons_text = [icon.text.strip() for icon in form_icons[:2]]  # Only take the first two form icons
        
        # 3. Find all <span> tags with class "table__cell table__cell--value"
        value_spans = standing_div.find_all("span", {"class": "table__cell table__cell--value"})
        value_spans_text = [int(span.text.strip()) for span in value_spans[:1]]  # Only take the first value span
        
        # Update the min_value_span for column M
        if min_value_span is None:
            min_value_span = value_spans_text[0]
        else:
            min_value_span = min(min_value_span, value_spans_text[0])
    
        # Determine where to store the form icons
        if idx == 0:  # First standing_div
            if team_name == tm_name_h:
                form_icons_G_H = form_icons_text  # Save in columns G and H
            else:
                form_icons_J_K = form_icons_text  # Save in columns J and K
        elif idx == 1:  # Second standing_div
            if team_name == tm_name_h:
                form_icons_G_H = form_icons_text  # Save in columns G and H
            else:
                form_icons_J_K = form_icons_text  # Save in columns J and K
    
    # Now form_icons_G_H contains values for columns G and H
    # form_icons_J_K contains values for columns J and K
    # min_value_span contains the smallest value for column M
    
    # Example of how to include these in your results
    res = [leg_name, tm_name_h, tm_name_a, game_time, '\t', '\t', round_number, '\t', 
           form_icons_G_H[0], form_icons_G_H[1], '\t', form_icons_J_K[0], form_icons_J_K[1], '\t', min_value_span, team_info[0][1], team_info[0][2], 
           '\t', '\t', odds[0], odds[1], odds[2]]
    
    print(res)
    return res

# Main process
date, match_ids = get_match_ids(driver)
all_data = []

# Assuming 'odds' is predefined or fetched separately for each match
for match_id in match_ids:
    odds = ["odds1", "odds2", "odds3"]  # Replace with actual odds fetching logic
    result = scrape_team_1_2(driver, match_id, odds)
    if result:
        all_data.append(result)

# Close the driver after scraping
driver.quit()

# Save the data to an Excel file
df = pd.DataFrame(all_data)
df.to_excel(f"scraped_data_{date}.xlsx", index=False)
