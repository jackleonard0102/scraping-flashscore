# -*- coding: utf-8 -*-
"""
Created on Thu Dec 23 10:06:11 2021

@author: k1332
"""


from selenium import webdriver
import pandas as pd
import time
import openpyxl
from openpyxl.styles import Alignment, Font
from openpyxl.styles import numbers
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import expected_conditions

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

output_file_name = "output.xlsx"

try:
    raw_df = pd.read_excel(output_file_name, header=None)
    flag = True
except:
    print(f"\n\n*** {output_file_name} file doesn't exist now, please run first program to get output.xlsx file!.\n")
    flag = False


driver = webdriver.Chrome()

def get_match_results(driver):
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
    # WebDriverWait(driver, 20)
    # driver.find_element('xpath', '//*[@id="onetrust-accept-btn-handler"]').click()
    
    # unroll_elements = driver.find_elements(By.CLASS_NAME, "event__expander--close") 
    # print(len(unroll_elements))
    # i = 0
    # for element in unroll_elements:
    #     while True:
    #         try:
    #             #driver.execute_script("window.scrollBy(0,100)","")
    #             element.click()
    #             i  += 1
    #             print('clicked : ', i)
    #             break
    #         except:
    #             driver.execute_script("window.scrollBy(0,100)","")
    #             print(i, "...")
                              
    ## get all match ids
    matches = driver.find_elements(By.CLASS_NAME, 'event__match--twoLine')
    matches_number = len(matches)   # the number of matches of specific day
    print("\n**** Total Matches Number : ", matches_number, "  ****\n")
    
    score_results = {}

    for match in matches:
        # event__score
        soup_sc = BeautifulSoup(match.get_attribute('innerHTML'), 'html.parser')
        
        # Check if the stage element exists
        stage_elem = soup_sc.find("div", {"class": "event__stage--block"})
        if stage_elem:
            stage = stage_elem.text.strip()
            if stage == "Finished":
                row_id = match.get_attribute('id')
                print ("this is row_id ================> ", row_id)
                row_id = row_id[4:]
                print ("this is row_id from index 3 ================> ", row_id)
                
                # Get team names
                tm_name_h_elem = soup_sc.find("div", {"class": "event__participant--home"})
                tm_name_a_elem = soup_sc.find("div", {"class": "event__participant--away"})
                
                if tm_name_h_elem and tm_name_a_elem:
                    tm_name_h = tm_name_h_elem.text.strip().lower()
                    tm_name_a = tm_name_a_elem.text.strip().lower()
                    
                    # Get scores
                    score_h_elem = soup_sc.find("div", {"class": "event__score--home"})
                    score_a_elem = soup_sc.find("div", {"class": "event__score--away"})
                    
                    if score_h_elem and score_a_elem:
                        score_h = int(score_h_elem.text)
                        score_a = int(score_a_elem.text)
                        
                        col_D = f"{score_h}-{score_a}"
                        col_E = 1 if score_h > score_a else 2 if score_h < score_a else "D"

                        print(f"Storing result for {tm_name_h} vs {tm_name_a}: {col_D}, {col_E}")
                        
                        score_results[(tm_name_h, tm_name_a)] = [col_D, col_E]
                    else:
                        print("Scores not found for match")
                else:
                    print("Team names not found for match")
        # else:
        #     print("Stage element not found for match")

    return date, score_results



date, match_results = get_match_results(driver)
#print(match_results)

def normalize_name(name):
    return name.strip().lower()

for idx in range(len(raw_df)):
    name_h = raw_df[1][idx]
    name_a = raw_df[2][idx]
    
    if (name_h, name_a) in match_results.keys():
        res = match_results[(name_h, name_a)]
        print(name_h, name_a, res)
        raw_df.loc[idx, 3] = res[0]
        raw_df.loc[idx, 4] = res[1]
    else:
        print(f"No match found for {name_h} vs {name_a}")
        raw_df = raw_df.drop([idx])

        
if len(raw_df) > 0:
    print(raw_df.shape)    
    #raw_df = raw_df.reset_index()
    raw_df.columns = [str(val) for val in range(raw_df.shape[1])]
    raw_df = raw_df.style.set_properties(subset=[str(val+3) for val in range(raw_df.shape[1]-3)], **{'text-align': 'center'})
    raw_df.to_excel(output_file_name, index = False, header=False)
    wb = openpyxl.load_workbook(f'{output_file_name}')
    sheet = wb.active
    sheet.column_dimensions['A'].width = 35
    sheet.column_dimensions['B'].width = 22
    sheet.column_dimensions['C'].width = 22
    sheet.column_dimensions['D'].width = 10
    wb.save(f'{output_file_name}')
    #raw_df.to_excel("output.xlsx",header=False,index=False)
    print(f"\n\n*** Successfully updated output file as {output_file_name} *** \n")
else:
    print(f"\n\n****  {output_file_name} data is very old, You please get output.csv file again at first.")
driver.close()