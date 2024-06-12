# -*- coding: utf-8 -*-
# scrapping tennis score
"""
Created on Fri Jun  3 04:54:55 2022

@author: k1332
"""

from selenium import webdriver
import re
import pandas as pd
import time
import traceback
import openpyxl
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.action_chains import ActionChains

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)
original_window = driver.current_window_handle

def get_available_match_ids(driver):
    search_url = "https://www.flashscore.com/tennis/"
    driver.get(search_url)
    time.sleep(1)
    answer = input('are you ready to run scraper ?..Y/N>>')
    if answer == "n" or answer == "N":
        exit()
    print('scraper is running please wait..\n')
    
    try:
        date_elem = driver.find_element_by_class_name('calendar__datepicker')
    except:
        date_elem = driver.find_element(By.CLASS_NAME, 'calendar__datepicker')
    date = date_elem.text           # chosen specific day
    print("\n\n**** Date : ", date, "  ****\n\n")
    
    
    titles = driver.find_elements(By.CLASS_NAME, 'wclLeagueHeader')
    indexs = []
    for title in titles:
        temp_title = title.find_element(By.CLASS_NAME, 'wclLeagueHeader__overline').text
        print (temp_title)
        if "ITF" in temp_title:
            index = titles.index(title)
            driver.execute_script(f'document.querySelectorAll(".wclLeagueHeader button._accordion_nfn42_4")[{index}].click()')
    match_ids = []    
    matches = driver.find_elements(By.CLASS_NAME, 'event__match--twoLine')
    matches_number = len(matches)   # the number of matches of specific day
    print("\n**** Total Matches Number : ", matches_number, "  ****\n")
    

    for match in matches:
        if 1 == 1:
            try:
                score_home = match.find_element(By.CLASS_NAME, "event__score--home")
                #event__logo--home
                if score_home.text == '-':
                    if 1==1:
                        name_home = match.find_element(By.CLASS_NAME, "event__participant--home").text
                        if "/" not in name_home:
                            row_id = match.get_attribute('id')
                            row_id = row_id[4:]
                             #event__logo--away
                            if len(match.find_elements(By.CLASS_NAME, "event__logo--home"))==1:
                                country_home = match.find_element(By.CLASS_NAME, "event__logo--home").get_attribute('title')
                                country_away = match.find_element(By.CLASS_NAME, "event__logo--away").get_attribute('title')
                                #if country_home != country_away:
                                match_ids.append([row_id, country_home, country_away])
                        else:
                            pass
            except:
                name_home = match.find_element(By.CLASS_NAME, "event__participant--home").text            
                if "/" not in name_home:
                    row_id = match.get_attribute('id')
                    row_id = row_id[4:]
                    #print(row_id, len(match.find_elements(By.CLASS_NAME, "event__logo--home")))
                    if len(match.find_elements(By.CLASS_NAME, "event__logo--home"))==1:
                        country_home = match.find_element(By.CLASS_NAME, "event__logo--home").get_attribute('title')
                        country_away = match.find_element(By.CLASS_NAME, "event__logo--away").get_attribute('title')
                        #if country_home != country_away:
                        match_ids.append([row_id, country_home, country_away])
                else:
                    pass  
    print("\n**** Number of Available Single Matches  : ", len(match_ids), "  ****\n")
    return match_ids, date


def get_values(driver, match_data, odds):
    try:
        temp_id = match_data[0]
        country_home = match_data[1]
        country_away = match_data[2]
        
        url_h2h = f"https://www.flashscore.com/match/{temp_id}/#/h2h/overall"
        
        driver.minimize_window()
        driver.get(url_h2h)
        time.sleep(3)
        
        league_info = driver.find_element(By.CLASS_NAME, 'tournamentHeader__sportNavWrapper')
        soup_leg = BeautifulSoup(league_info.get_attribute('innerHTML'), 'html.parser')
        leg_name = soup_leg.find("span", {"class": "tournamentHeader__country"}).text.split(",")[0].strip()

        teams_div = driver.find_element(By.CLASS_NAME, 'duelParticipant')
        soup_tm = BeautifulSoup(teams_div.get_attribute('innerHTML'), 'html.parser')
        game_time = soup_tm.find("div", {"class": "duelParticipant__startTime"}).text.split(" ")[-1]
        game_score = soup_tm.find("div", {"class": "detailScore__wrapper"}).text.strip()

        if game_score != '-':
            print("\n@@@  Finished Game, Skipped !. @@@")
            return None

        # Extract team names and ranks
        tms = soup_tm.find_all("div", {"class": "participant__participantNameWrapper"})
        tm_name_h = tms[0].text.strip()
        tm_name_a = tms[1].text.strip()
        
        div_home = soup_tm.find("div", {"class": "duelParticipant__home"})
        try:
            tm_rank_1 = int(div_home.find("div", {"class": "participant__participantRank"}).text.strip().split(":")[1].replace(".", "").strip())
        except:
            tm_rank_1 = "9999"

        div_away = soup_tm.find("div", {"class": "duelParticipant__away"})
        try:
            tm_rank_2 = int(div_away.find("div", {"class": "participant__participantRank"}).text.strip().split(":")[1].replace(".", "").strip())
        except:
            tm_rank_2 = "9999"

        # Extract H2H data
        section_divs = driver.find_elements(By.CLASS_NAME, 'h2h__section.section')
        soup_section_1 = BeautifulSoup(section_divs[0].get_attribute('innerHTML'), 'html.parser')
        temp_soup_h2h_rows_1 = soup_section_1.find_all("div", {"class": "h2h__row"})
        soup_section_2 = BeautifulSoup(section_divs[1].get_attribute('innerHTML'), 'html.parser')
        temp_soup_h2h_rows_2 = soup_section_2.find_all("div", {"class": "h2h__row"}) 
        
        if len(temp_soup_h2h_rows_1) < 2 or len(temp_soup_h2h_rows_2) < 2:
            return None

        combined_soup_h2h_rows = []
        for k_1 in range(2):
            combined_soup_h2h_rows.append(temp_soup_h2h_rows_1[k_1])
            combined_soup_h2h_rows.append(temp_soup_h2h_rows_2[k_1])
        
        temp_league_status = [row.find("span", {"class": "h2h__icon"}).text.strip() for row in combined_soup_h2h_rows]
        temp_league_name = [row.find("span", {"class": "h2h__event"}).get('title').strip() for row in combined_soup_h2h_rows]

        if 'L' in temp_league_status:
            print("$$$   The previous game lost!!!   $$$")
            return None

        # Initialize variables with default values
        col_O = col_P = col_Q = col_R = col_S = col_T = col_W = col_X = col_Y = col_Z = col_AA = col_AB = "\t"

        if all(item == temp_league_name[0] for item in temp_league_name):
            # Iterate over H2H sections to extract required data
            for k_3, section in enumerate(section_divs[:3]):
                try:
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
                    ).click()
                except:
                    pass
                
                elements = section.find_elements(By.CLASS_NAME, "h2h__row")
                if len(elements) < 3:
                    print("Error: Not enough elements in the list.")
                    continue

                element_found = False
                
                for element in elements[:3]:
                    element.click()
                    wait.until(EC.number_of_windows_to_be(2))
                    for window_handle in driver.window_handles:
                        if window_handle != original_window:
                            driver.switch_to.window(window_handle)

                    time.sleep(3)
                    get_url = driver.current_url
                    summary_id = get_url.split("/#")[0].split("/")[-1]
                    summary_url = f"https://www.flashscore.com/match/{summary_id}/#/match-summary/match-summary"
                    driver.get(summary_url)
                    time.sleep(3)

                    league_info = driver.find_element(By.CLASS_NAME, 'tournamentHeader__sportNavWrapper')
                    soup_leg = BeautifulSoup(league_info.get_attribute('innerHTML'), 'html.parser')
                    summary_leg_name = soup_leg.find("span", {"class": "tournamentHeader__country"}).text.split(",")[0].strip()

                    if summary_leg_name == leg_name:
                        driver.close()
                        driver.switch_to.window(original_window)
                        continue  # Skip this summary and try the next one
                    
                    element_found = True

                    # Extract percentages from div elements
                    winner_elems = driver.find_elements(By.CSS_SELECTOR, ".duelParticipant__home.duelParticipant--winner")
                    if winner_elems:
                        divs = driver.find_elements(By.CLASS_NAME, '_homeValue_lgd3g_9')
                    else:
                        divs = driver.find_elements(By.CLASS_NAME, '_awayValue_lgd3g_13')
                    for i, div in enumerate(divs):
                        print(f"Div {i} HTML: {div.get_attribute('innerHTML')}")

                    if len(divs) == 3:
                        text_map = {
                            0: ("col_O", "col_R"),
                            1: ("col_P", "col_S"),
                            2: ("col_Q", "col_T")
                        }
                        col1, col2 = text_map.get(k_3, ("N/A", "N/A"))
                        col1_text, col2_text = divs[1].text, divs[2].text

                        if k_3 == 0:
                            col_O = re.search(r'(\d+)%', col1_text).group(1) if re.search(r'(\d+)%', col1_text) else "N/A"
                            col_R = re.search(r'(\d+)%', col2_text).group(1) if re.search(r'(\d+)%', col2_text) else "N/A"
                        elif k_3 == 1:
                            col_P = re.search(r'(\d+)%', col1_text).group(1) if re.search(r'(\d+)%', col1_text) else "N/A"
                            col_S = re.search(r'(\d+)%', col2_text).group(1) if re.search(r'(\d+)%', col2_text) else "N/A"
                        elif k_3 == 2:
                            col_Q = re.search(r'(\d+)%', col1_text).group(1) if re.search(r'(\d+)%', col1_text) else "N/A"
                            col_T = re.search(r'(\d+)%', col2_text).group(1) if re.search(r'(\d+)%', col2_text) else "N/A"

                    driver.close()
                    driver.switch_to.window(original_window)
                    if element_found:
                        break

            if not element_found:
                return None  # Skip if no valid element was found

            for k_4, section in enumerate(section_divs[:3]):
                try:
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
                    ).click()
                except:
                    pass

                elements = section.find_elements(By.CLASS_NAME, "h2h__row")
                if len(elements) < 3:
                    print("Error: Not enough elements in the list.")
                    continue

                element_found = False
                
                for element in elements[:3]:
                    element.click()
                    wait.until(EC.number_of_windows_to_be(2))
                    for window_handle in driver.window_handles:
                        if window_handle != original_window:
                            driver.switch_to.window(window_handle)

                    time.sleep(3)
                    get_url = driver.current_url
                    summary_id = get_url.split("/#")[0].split("/")[-1]
                    summary_url = f"https://www.flashscore.com/match/{summary_id}/#/match-summary/match-summary"
                    driver.get(summary_url)
                    time.sleep(3)

                    league_info = driver.find_element(By.CLASS_NAME, 'tournamentHeader__sportNavWrapper')
                    soup_leg = BeautifulSoup(league_info.get_attribute('innerHTML'), 'html.parser')
                    summary_leg_name = soup_leg.find("span", {"class": "tournamentHeader__country"}).text.split(",")[0].strip()

                    if summary_leg_name == leg_name:
                        driver.close()
                        driver.switch_to.window(original_window)
                        continue  # Skip this summary and try the next one
                    
                    element_found = True

                    # Extract percentages from div elements
                    winner_elems = driver.find_elements(By.CSS_SELECTOR, ".duelParticipant__home.duelParticipant--winner")
                    if winner_elems:
                        divs = driver.find_elements(By.CLASS_NAME, '_homeValue_lgd3g_9')
                    else:
                        divs = driver.find_elements(By.CLASS_NAME, '_awayValue_lgd3g_13')
                    for j, div in enumerate(divs):
                        print(f"Away Div {j} HTML: {div.get_attribute('innerHTML')}")

                    if len(divs) == 3:
                        text_map = {
                            0: ("col_W", "col_Z"),
                            1: ("col_X", "col_AA"),
                            2: ("col_Y", "col_AB")
                        }
                        col1, col2 = text_map.get(k_4, ("N/A", "N/A"))
                        col1_text, col2_text = divs[1].text, divs[2].text

                        if k_4 == 0:
                            col_W = re.search(r'(\d+)%', col1_text).group(1) if re.search(r'(\d+)%', col1_text) else "N/A"
                            col_Z = re.search(r'(\d+)%', col2_text).group(1) if re.search(r'(\d+)%', col2_text) else "N/A"
                        elif k_4 == 1:
                            col_X = re.search(r'(\d+)%', col1_text).group(1) if re.search(r'(\d+)%', col1_text) else "N/A"
                            col_AA = re.search(r'(\d+)%', col2_text).group(1) if re.search(r'(\d+)%', col2_text) else "N/A"
                        elif k_4 == 2:
                            col_Y = re.search(r'(\d+)%', col1_text).group(1) if re.search(r'(\d+)%', col1_text) else "N/A"
                            col_AB = re.search(r'(\d+)%', col2_text).group(1) if re.search(r'(\d+)%', col2_text) else "N/A"

                    driver.close()
                    driver.switch_to.window(original_window)
                    if element_found:
                        break

            if element_found:
                res = [leg_name.upper(), tm_name_h, tm_name_a, '\t', game_time, '\t', '\t', odds[0], odds[1], '\t', tm_rank_1, tm_rank_2, tm_rank_1 - tm_rank_2, '\t', col_O, col_P, col_Q, col_R, col_S, col_T, '\t', '\t', col_W, col_X, col_Y, col_Z, col_AA, col_AB]
                return res

        return None
    except Exception as e:
        print(f"Exception during get_values for match {temp_id}: {str(e)}")
        traceback.print_exc()
        return None

# Rest of the script remains the same


def get_odds_data_2():
    odds_data = {}
    browser_2 = webdriver.Chrome()
    target_url = "https://www.betexplorer.com/next/tennis/"
    browser_2.get(target_url)
    browser_2.implicitly_wait(5)
    time.sleep(5)
    
    process_key = input("do you process from this betexplorer page ? y(yes)/Enter(no) ")
    browser_2.minimize_window()
    print("\n\n*** Getting Odds Data from oddsportal.com....")
    
    wait = WebDriverWait(browser_2, 20)
    #teams_div = browser_2.find_element(By.ID, match_id)
    teams_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'table-main.js-nrbanner-t')))    
    soup_tm = BeautifulSoup(teams_div.get_attribute('innerHTML'), 'html.parser')
    
    soup_tbody_list = soup_tm.find_all("tr", {"data-def" : "1"})
    print(len(soup_tbody_list))
    
    for idx in range(len(soup_tbody_list)):
        td_name = soup_tbody_list[idx].find("td", {"class" : "table-main__tt"})
        match_id = td_name.find("a").get("href").rsplit('/', 2)[-2]
        td_odds = soup_tbody_list[idx].find_all("td", {"class" : "table-main__odds"})
        odds = [val.text.strip() for val in td_odds]
        if len(odds) == 2:
            odds_data[match_id] = odds
        else:
            odds_data[match_id] = ["", ""]
        
        print(idx, match_id, odds_data[match_id])
    
    browser_2.close()
    return odds_data


match_ids, date = get_available_match_ids(driver)
odds_data = get_odds_data_2()
#odds_data = {}
#match_ids = [["Khk7TLLp","AAA","BBB"]]
#date = "11 17"

idx = 0
data = []
interupted_ids = []
for match_data in match_ids:
    idx += 1
    print(f"\n{idx} / {len(match_ids)} : {match_data[0]}")
    try:
        match_id = match_data[0]
        if match_id in odds_data:
            odds = odds_data[match_id]
        else:
            odds = ["", ""]
        res = get_values(driver, match_data, odds)
        if res != None:
            data.append(res)
            print(res)
        else:
            print("$$$ Skipped : ", match_id)
    except Exception as e:
        print(f"\tInterrupted {match_id} due to {str(e)}")
        traceback.print_exc()
        interupted_ids.append(match_data)
        driver.close()
        driver = webdriver.Chrome()
        wait = WebDriverWait(driver, 10)
        original_window = driver.current_window_handle
k = 0       
for match_data in interupted_ids:
    k += 1
    print(f"\n {k} / {len(interupted_ids)}")
    try:
    #if 1==1:
        match_id = match_data[0]
        if match_id in odds_data:
            #odds = ['\t', '\t']
            odds = odds_data[match_id]
        else:
            odds = ["", ""]
        res = get_values(driver, match_data, odds)
        if res != None:
            data.append(res)
            print(res)
        else:
            print("$$$ Skipped : ",match_id)
    except:
    #if 1==2:
        print("\tError", match_id)
        driver.close()
        driver = webdriver.Chrome()
        wait = WebDriverWait(driver, 10)
        original_window = driver.current_window_handle
    
print(len(data))
if len(data)>0:
    output = pd.DataFrame(data,columns = None)
    output.columns = [str(val) for val in range(len(data[0]))]
    output = output.style.set_properties(subset=[str(val+1) for val in range(len(data[0])-1) if val not in [0, 1, 3, 4, 5]], **{'text-align': 'center'})  
    
    date = date.replace("/","_").replace(" ", "_")
    output_file_name = f"tennis_updated_{date}.xlsx"
    
    output.to_excel(output_file_name,index = False, header=False)
    wb = openpyxl.load_workbook(f'{output_file_name}')
    sheet = wb.active
    sheet.column_dimensions['A'].width = 70
    sheet.column_dimensions['B'].width = 25
    sheet.column_dimensions['C'].width = 25
    sheet.column_dimensions['E'].width = 10
    sheet.column_dimensions['F'].width = 10
    sheet.column_dimensions['H'].width = 10
    wb.save(f'{output_file_name}')
    
    print(f"\n\n***  Successfully Created to {output_file_name} ***\n")

else:
    print("\n\n*** There isn't any data to save!.")

driver.close()
                    
