# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 09:11:42 2021

@author: k1332
"""

from selenium import webdriver
import pandas as pd
import time
import os
import openpyxl
from openpyxl.styles import Alignment, Font
from openpyxl.styles import numbers
import re
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import expected_conditions

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

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
    
    unroll_elements = driver.find_elements(By.CLASS_NAME, "event__expander--close") 
    print(len(unroll_elements))
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

#driver.close()

def scrape_team_1_2(driver, temp_id, odds):
    #temp_id = "fiyntA89"
    url_overall = f"https://www.flashscore.com/match/{temp_id}/#/standings/table/overall"
    #url_overall = f"https://www.flashscore.com/match/{temp_id}/#/standings/form/overall/5"
        
    driver.minimize_window()
    driver.get(url_overall)
    time.sleep(3)
    
    league_info = driver.find_element(By.CLASS_NAME, 'tournamentHeader__sportNavWrapper')
    soup_leg = BeautifulSoup(league_info.get_attribute('innerHTML'), 'html.parser')
    
    ## find women game and skip
    if 'women' in soup_leg.find("span", {"class": "tournamentHeader__country"}).text.lower():
        print("\n*** Skipped, WOMEN game...")
        return None
    
    else:
        leg_name = soup_leg.find("span", {"class": "tournamentHeader__country"}).text.split("- Round")[0].strip()
         
        teams_div = driver.find_element(By.CLASS_NAME, 'duelParticipant')
        soup_tm = BeautifulSoup(teams_div.get_attribute('innerHTML'), 'html.parser')
        tms = soup_tm.find_all("div", {"class": "participant__participantNameWrapper"})
        game_time = soup_tm.find("div", {"class": "duelParticipant__startTime"}).text.split(" ")[-1]
    
        #detailScore__wrapper
        game_score = soup_tm.find("div", {"class": "detailScore__wrapper"}).text.strip()
        
        if game_score != '-':
            print("\n### Finished Game, Skipped !. ###")
            return None
        else:
            tm_name_h = tms[0].text.strip()
            tm_name_a = tms[1].text.strip()
            
            table_divs = driver.find_element(By.ID, 'tournament-table-tabs-and-content')
            soup_table = BeautifulSoup(table_divs.get_attribute('innerHTML'), 'html.parser')  
            
            rows_h_a = soup_table.find_all("div", {"class": "table__row--selected"})
            

            F_1 = int(rows_h_a[0].find_all("span", {"class" : "table__cell--value"})[0].text)
            F_2 = int(rows_h_a[1].find_all("span", {"class" : "table__cell--value"})[0].text)
        
            #col_K = min(int(F_1), int(F_2))
            if (F_1 < 8) | (F_2 < 8):
                print(f"\n###  Q or R < 8, Skipped  ###\n")
                return None
            
            else:
                #ui-table__row  
                rank_all = len(soup_table.find_all("div", {"class": "ui-table__row"}))
                rows_h_a = soup_table.find_all("div", {"class": "table__row--selected"})
                tm_1_h = rows_h_a[0].find("div", {"class" : "tableCellParticipant"}).text.strip()
                #F_1_h = int(rows_h_a[0].find_all("span", {"class" : "table__cell--value"})[0].text)
                G_1_h  = rows_h_a[0].find("span", {"class" : "table__cell--score"}).text.split(":")
                #P_1  = rows_h_a[0].find("span", {"class" : "table__cell--points"}).text.strip()
                rank_1  = rows_h_a[0].find("div", {"class" : "tableCellRank"}).text.strip().replace(".", "")
                
                tm_2_a = rows_h_a[1].find("div", {"class" : "tableCellParticipant"}).text.strip()
                #F_2_a = int(rows_h_a[1].find_all("span", {"class" : "table__cell--value"})[0].text)
                G_2_a  = rows_h_a[1].find("span", {"class" : "table__cell--score"}).text.split(":")
                #P_2  = rows_h_a[1].find("span", {"class" : "table__cell--points"}).text.strip()
                rank_2  = rows_h_a[1].find("div", {"class" : "tableCellRank"}).text.strip().replace(".", "")
                
                if tm_1_h == tm_name_h:
                    rank_h = rank_1
                    rank_a = rank_2
                    
                elif tm_2_a == tm_name_h:            
                    rank_a = rank_1
                    rank_h = rank_2

                try:
                    val = int(rank_1)
                    val = int(rank_2)
                except:
                    print("*** Invalid Ranking Number, Skipped !  ***")
                    return None
                
                url_home = f"https://www.flashscore.com/match/{temp_id}/#/standings/table/home"
                driver.get(url_home)
                time.sleep(3)
                
                table_divs = driver.find_element(By.ID, 'tournament-table-tabs-and-content')
                soup_table = BeautifulSoup(table_divs.get_attribute('innerHTML'), 'html.parser')  
                
                rows_h_a = soup_table.find_all("div", {"class": "table__row--selected"})
                tm_1_h = rows_h_a[0].find("div", {"class" : "tableCellParticipant"}).text.strip()
                G_1_h  = rows_h_a[0].find("span", {"class" : "table__cell--score"}).text.split(":")
                tm_2_a = rows_h_a[1].find("div", {"class" : "tableCellParticipant"}).text.strip()
                G_2_a  = rows_h_a[1].find("span", {"class" : "table__cell--score"}).text.split(":") 
                #table__cell--value
                MP_home_1  = rows_h_a[0].find_all("span", {"class" : "table__cell--value"})[0].text.strip()
                MP_home_2  = rows_h_a[1].find_all("span", {"class" : "table__cell--value"})[0].text.strip()
                if tm_name_h == tm_1_h:
                    new_S = int(G_1_h[0])
                    new_T = int(G_1_h[1])
                    MP_home = int(MP_home_1)
                else:
                    new_S = int(G_2_a[0])
                    new_T = int(G_2_a[1])
                    MP_home = int(MP_home_2)

                url_away = f"https://www.flashscore.com/match/{temp_id}/#/standings/table/away"
                driver.get(url_away)
                time.sleep(3)
                
                table_divs = driver.find_element(By.ID, 'tournament-table-tabs-and-content')
                soup_table = BeautifulSoup(table_divs.get_attribute('innerHTML'), 'html.parser')  
                
                rows_h_a = soup_table.find_all("div", {"class": "table__row--selected"})
                tm_1_h = rows_h_a[0].find("div", {"class" : "tableCellParticipant"}).text.strip()
                G_1_h  = rows_h_a[0].find("span", {"class" : "table__cell--score"}).text.split(":")
                tm_2_a = rows_h_a[1].find("div", {"class" : "tableCellParticipant"}).text.strip()
                G_2_a  = rows_h_a[1].find("span", {"class" : "table__cell--score"}).text.split(":")     
                MP_away_1  = rows_h_a[0].find_all("span", {"class" : "table__cell--value"})[0].text.strip()
                MP_away_2  = rows_h_a[1].find_all("span", {"class" : "table__cell--value"})[0].text.strip()
                if tm_name_a == tm_1_h:
                    new_U = int(G_1_h[0])
                    new_V = int(G_1_h[1])
                    MP_away = int(MP_away_1)
                else:
                    new_U = int(G_2_a[0])
                    new_V = int(G_2_a[1])
                    MP_away = int(MP_away_2)

                W_Y = round(int(new_S)/int(new_U), 2)
                X_Z = round(int(new_T)/int(new_V), 2)
                
                AD_AA = round(new_S/MP_home, 2)
                AE_AA = round(new_T/MP_home, 2)
                AF_AB = round(new_U/MP_away, 2)
                AG_AB = round(new_V/MP_away, 2)
                res = [leg_name, tm_name_h, tm_name_a, game_time, '\t', '\t', odds[0], odds[1], odds[2],
                       '\t', W_Y, X_Z, '\t', AD_AA, AE_AA, AF_AB, AG_AB, '\t', '\t', rank_all, rank_h, rank_a, 
                       '\t', F_1, F_2, '\t', MP_home, MP_away, '\t', new_S, new_T, new_U, new_V]
                
                
                print(res)
                

                return res
                
    return None

    


def get_odds_data_2():
    odds_data = {}
    browser_2 = webdriver.Chrome()
    target_url = "https://www.betexplorer.com/next/soccer/"
    browser_2.get(target_url)
    browser_2.implicitly_wait(5)
    time.sleep(5)
    
    process_key = input("do you process from this oddsportal page ? y(yes)/Enter(no) ")
    browser_2.minimize_window()
    print("\n\n*** Getting Odds Data from betexplorer.com....")
    
    wait = WebDriverWait(browser_2, 40)
    #teams_div = browser_2.find_element(By.ID, match_id)
    teams_div = wait.until(EC.presence_of_element_located((By.ID, 'nr-ko-all')))    
    soup_tm = BeautifulSoup(teams_div.get_attribute('innerHTML'), 'html.parser')
    
    soup_tbody_list = soup_tm.find_all("ul", {"class" : "table-main__matchInfo"})
    print(len(soup_tbody_list))
    
    for idx in range(len(soup_tbody_list)):
        if 'data-def' in soup_tbody_list[idx].attrs.keys():
            td_name = soup_tbody_list[idx].find("li", {"class" : "table-main__participants"})
            match_id = td_name.find("a").get("href").rsplit('/', 2)[-2]            
            
            #match_id = soup_tbody_list[idx].attrs['data-live']
            td_odds = soup_tbody_list[idx].find("div", {"class" : "table-main__oddsLi"})
            #odds = [val.text.strip() for val in td_odds]
            #if len(odds) == 3:
            odds_data[match_id] = td_odds.text.strip().split("\n")
            #else:
            #odds_data[match_id] = ["", "", ""]
            
            print(idx, match_id, odds_data[match_id])
    
    browser_2.close()
    return odds_data

date, match_ids = get_match_ids(driver)
#if 'ANaK02C8' in match_ids:
#    print("\nOKKKKK\n")
odds_data = get_odds_data_2()
#odds_data = {}
#date = "09 09"
idx = 0
data = []
#match_ids = ['xvclTFHa']
for match_id in match_ids:
    idx += 1
    print(f"\n{idx} / {len(match_ids)} : {match_id}")
    try:
    #if 1==1:
        if match_id in odds_data:
            odds = odds_data[match_id]
            res = scrape_team_1_2(driver, match_id, odds)
        else:
            res = scrape_team_1_2(driver, match_id, ["\t", "\t", "\t"])
        if res !=  None:      
            data.append(res)
        #print(res)
    except:
        print("\tSkipped !.")
    
print(len(data))
if len(data) > 0:
    output = pd.DataFrame(data,columns = None)
    output.columns = [str(val) for val in range(len(data[0]))]
    output = output.style.set_properties(subset=[str(val+3) for val in range(len(data[0])-3)], **{'text-align': 'center'})
    
    date = date.replace("/","_").replace(" ", "_")
    output_file_name = f"soccor_{date}.xlsx"
    
    output.to_excel(output_file_name,index = False, header=False)
    wb = openpyxl.load_workbook(f'{output_file_name}')
    sheet = wb.active
    sheet.column_dimensions['A'].width = 40
    sheet.column_dimensions['B'].width = 25
    sheet.column_dimensions['C'].width = 25
    sheet.column_dimensions['D'].width = 10
    wb.save(f'{output_file_name}')
    
    print(f"\n\n***  Successfully Created to {output_file_name} ***\n")
else:
    print("\n ***  There is no result  \n")
driver.close()

