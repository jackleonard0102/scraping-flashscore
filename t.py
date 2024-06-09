# -*- coding: utf-8 -*-
# scrapping tennis score
"""
Created on Fri Jun  3 04:54:55 2022

@author: k1332
"""

from selenium import webdriver
import pandas as pd
import time
import openpyxl
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import expected_conditions

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
    temp_id = match_data[0]
    country_home = match_data[1]
    country_away = match_data[2]
    
    #####  Tenis / H2H / overall     ##################
    url_h2h = f"https://www.flashscore.com/match/{temp_id}/#/h2h/overall"
    
    driver.minimize_window()
    driver.get(url_h2h)
    time.sleep(3)
    
    league_info = driver.find_element(By.CLASS_NAME, 'tournamentHeader__sportNavWrapper')
    soup_leg = BeautifulSoup(league_info.get_attribute('innerHTML'), 'html.parser')
    leg_name = soup_leg.find("span", {"class": "tournamentHeader__country"}).text.split("- Round")[0].strip()


    teams_div = driver.find_element(By.CLASS_NAME, 'duelParticipant')
    soup_tm = BeautifulSoup(teams_div.get_attribute('innerHTML'), 'html.parser')
    match_info = soup_tm.find("div", {"class": "duelParticipant__score"}).text


    tms = soup_tm.find_all("div", {"class": "participant__participantNameWrapper"})
    game_time = soup_tm.find("div", {"class": "duelParticipant__startTime"}).text.split(" ")[-1]
    game_score = soup_tm.find("div", {"class": "detailScore__wrapper"}).text.strip()
    
    if game_score != '-':
        print("\n@@@  Finished Game, Skipped !. @@@")
        return None
    else:    
        tm_name_h = tms[0].text.strip()
        tm_name_a = tms[1].text.strip()
        
        div_home = soup_tm.find("div", {"class": "duelParticipant__home"})
        try:
            tm_rank_1 = int(div_home.find("div", {"class": "participant__participantRank"}).text.strip().split(":")[1].replace(".","").strip())
        except:
            tm_rank_1 = "9999"
        
        div_away = soup_tm.find("div", {"class": "duelParticipant__away"})
        try:
            tm_rank_2 = int(div_away.find("div", {"class": "participant__participantRank"}).text.strip().split(":")[1].replace(".","").strip())
        except:
            tm_rank_2 = "9999"
                        
        
        #### Find K L M
        section_divs = driver.find_elements(By.CLASS_NAME, 'h2h__section.section')

        if len(section_divs)<3:
            print("\n$$$ There isn't H2H game records, skipped ! $$$\n")
            return None
        
        soup_section_3 = BeautifulSoup(section_divs[2].get_attribute('innerHTML'), 'html.parser')
        soup_h2h_rows_3 = soup_section_3.find_all("div", {"class" : "h2h__row"})    
        if len(soup_h2h_rows_3)<1:
            print("\n$$$ There isn't H2H game records, skipped ! $$$\n")
            return None                    
        col_N = soup_h2h_rows_3[0].find("span", {"class" : "h2h__date"}).text.strip()
        
        soup_score_h = soup_h2h_rows_3[0].find("span", {"class" : "h2h__result"})
        score_h_1 = soup_score_h.find_all("span")[0].text
        score_h_2 = soup_score_h.find_all("span")[1].text
        col_P = score_h_1+'-'+score_h_2
        
        
        if col_P in ['1-1', '1-0', '0-1', '0-0']:
            print(f"\n### Column P (Score) : {col_P}, skipped, \n")
            return None
        
        names_div = soup_h2h_rows_3[0].find_all("span", {"class" : "h2h__participantInner"})  
        name_1 = names_div[0].text.strip()
        name_2 = names_div[1].text.strip()
        print(name_1==tm_name_h, name_2==tm_name_h)
        if name_1 == tm_name_h:
            if int(score_h_1) > int(score_h_2):
                col_O = 1
            else:
                col_O = 2
        elif name_2 == tm_name_h:
            if int(score_h_1) > int(score_h_2):
                col_O = 2
            else:
                col_O = 1
        else:
            col_O = "D"
        
        
        soup_section_1 = BeautifulSoup(section_divs[0].get_attribute('innerHTML'), 'html.parser')
        soup_h2h_rows_1 = soup_section_1.find_all("div", {"class" : "h2h__row"})
        
        for k_1 in range(len(soup_h2h_rows_1)):                
            temp_league_name = soup_h2h_rows_1[k_1].find("span", {"class" : "h2h__event"}).get('title').split("(")[0].strip().lower() 
            #print("1 : ", temp_league_name)
            if temp_league_name not in leg_name.lower():                
                ## click and get Stats for 2 Players:
                try:
                    WebDriverWait(driver, 10)
                    driver.find_element(By.XPATH, '//*[@id="onetrust-accept-btn-handler"]').click()
                    driver.minimize_window()
                except:
                    pass
                
                ##  click 1st game row
                elements = section_divs[0].find_elements(By.CLASS_NAME, "h2h__row")  

                col_R = soup_h2h_rows_1[k_1].find("span", {"class" : "h2h__icon"}).text.strip()   
                date_1 = soup_h2h_rows_1[k_1].find("span", {"class" : "h2h__date"}).text.strip()
                if date_1 == col_N:
                    print("$$$   The same game with H2H for the 1st past game, skipped !!!   $$$")
                    return None
                
                elements[k_1].click()
                driver.minimize_window()
                
                wait.until(EC.number_of_windows_to_be(2))
            
                # Loop through until we find a new window handle
                for window_handle in driver.window_handles:
                    if window_handle != original_window:
                        driver.switch_to.window(window_handle)
                
                time.sleep(3)
                get_url = str(driver.current_url)
                id_1st = get_url.split("/#")[0].split("/")[-1]
                print(f"{id_1st}")

                #url_1st = f"https://www.flashscore.com/match/{id_1st}/#/match-summary/match-statistics/0"
                url_3rd = f"https://www.flashscore.com/match/{id_1st}/#/match-summary/match-summary"
                driver.minimize_window()
                driver.get(url_3rd)
                time.sleep(3)
                
                league_info = driver.find_element(By.CLASS_NAME, 'tournamentHeader__sportNavWrapper')
                soup_leg = BeautifulSoup(league_info.get_attribute('innerHTML'), 'html.parser')
                col_S = soup_leg.find("span", {"class": "tournamentHeader__country"}).text.split(" - ")[-1].strip()
                
                leg_name_1st = soup_leg.find("span", {"class": "tournamentHeader__country"}).text.strip()
                if  'QUALIFICATION' in leg_name_1st.upper():
                    print("QUALIFICATION Game for 1st past game, Skipped !. ")
                    return None    
                
                driver.close()
                driver.switch_to.window(original_window)
                
                break
        
        
        
        soup_section_2 = BeautifulSoup(section_divs[1].get_attribute('innerHTML'), 'html.parser')
        soup_h2h_rows_2 = soup_section_2.find_all("div", {"class" : "h2h__row"}) 
        
        for k_2 in range(len(soup_h2h_rows_2)):
            temp_league_name = soup_h2h_rows_2[k_2].find("span", {"class" : "h2h__event"}).get('title').split("(")[0].strip().lower() 
            if temp_league_name not in leg_name.lower():  
                     
                elements = section_divs[1].find_elements(By.CLASS_NAME, "h2h__row")  
                
                col_U = soup_h2h_rows_2[k_2].find("span", {"class" : "h2h__icon"}).text.strip()   
                
                date_2 = soup_h2h_rows_2[k_2].find("span", {"class" : "h2h__date"}).text.strip()
                if date_2 == col_N:
                    print("$$$   The same game with H2H for the 2nd past game, skipped !!!   $$$")
                    return None
                elements[k_2].click()
                driver.minimize_window()
                
                wait.until(EC.number_of_windows_to_be(2))
            
                # Loop through until we find a new window handle
                for window_handle in driver.window_handles:
                    if window_handle != original_window:
                        driver.switch_to.window(window_handle)
                
                time.sleep(3)
                get_url = str(driver.current_url)
                id_2nd = get_url.split("/#")[0].split("/")[-1]
                print(f"{id_2nd}")
                #url_2nd = f"https://www.flashscore.com/match/{id_2nd}/#/match-summary/match-statistics/0"
                url_3rd = f"https://www.flashscore.com/match/{id_2nd}/#/match-summary/match-summary"
                driver.minimize_window()
                driver.get(url_3rd)
                time.sleep(3)
                
                league_info = driver.find_element(By.CLASS_NAME, 'tournamentHeader__sportNavWrapper')
                soup_leg = BeautifulSoup(league_info.get_attribute('innerHTML'), 'html.parser')
                col_V = soup_leg.find("span", {"class": "tournamentHeader__country"}).text.split(" - ")[-1].strip()
                leg_name_2nd = soup_leg.find("span", {"class": "tournamentHeader__country"}).text.strip()
                if  'QUALIFICATION' in leg_name_2nd.upper():
                    print("QUALIFICATION Game for 2nd past game, Skipped !. ")
                    return None    
                
                driver.close()
                driver.switch_to.window(original_window)
                
                break
        
        res = [leg_name.upper(), tm_name_h, tm_name_a, '\t', country_home, country_away, '\t', game_time, '\t', '\t', odds[0], odds[1],
               '\t', col_N, col_O, col_P, '\t', col_R, col_S, '\t', col_U, col_V,
               '\t', tm_rank_1, tm_rank_2]
            
        return res

                    
    return None


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
        print("\tInterrupted", match_id)
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
    sheet.column_dimensions['S'].width = 25
    sheet.column_dimensions['V'].width = 25
    wb.save(f'{output_file_name}')
    
    print(f"\n\n***  Successfully Created to {output_file_name} ***\n")

else:
    print("\n\n*** There isn't any data to save!.")

driver.close()
                    
