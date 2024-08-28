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

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

output_file_name = "s.xlsx"

try:
    raw_df = pd.read_excel(output_file_name, header=None)
    print("this is excel data =============> ", raw_df)
    flag = True
except:
    print(f"\n\n*** {output_file_name} file doesn't exist now, please run first program to get output.xlsx file!.\n")
    flag = False

# Configurer les options Chrome pour désactiver l'écran de choix du moteur de recherche
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--disable-search-engine-choice-screen")

# Initialiser WebDriver avec les options configurées
driver = webdriver.Chrome(options=chrome_options)

def get_match_results(driver):
    search_url = "https://www.flashscore.com"
    driver.get(search_url)
    time.sleep(1)
    answer = input('are you ready to run scraper ?..Y/N>>')
    if answer.lower() == "n":
        exit()
    print('scraper is running please wait..\n')

    date_elem = driver.find_element(By.CLASS_NAME, 'calendar__datepicker')
    date = date_elem.text  # chosen specific day
    print("\n\n**** Date : ", date, "  ****\n\n")

    # unroll all hidden games
    WebDriverWait(driver, 20)
    driver.find_element('xpath', '//*[@id="onetrust-accept-btn-handler"]').click()

    unroll_elements = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='wcl-icon-action-navigation-arrow-down']"))
    )
    print(len(unroll_elements))
    i = 0
    for element in unroll_elements:
        while True:
            try:
                element.click()
                i += 1
                print('clicked : ', i)
                break
            except:
                driver.execute_script("window.scrollBy(0,100)", "")
                print(i, "...")

    # get all match ids
    matches = driver.find_elements(By.CLASS_NAME, 'event__match--twoLine')
    matches_number = len(matches)  # the number of matches of specific day
    print("\n**** Total Matches Number : ", matches_number, "  ****\n")

    score_results = {}

    for match in matches:
        soup_sc = BeautifulSoup(match.get_attribute('innerHTML'), 'html.parser')
        stage_elem = soup_sc.find("div", {"class": "event__stage--block"})
        if stage_elem:
            stage = stage_elem.text.strip()
            if stage == "Finished":
                row_id = match.get_attribute('id')[4:]

                # Get team names
                tm_name_h_elem = soup_sc.find("div", {"class": "_participant_j0qo9_4 event__homeParticipant"})
                tm_name_a_elem = soup_sc.find("div", {"class": "_participant_j0qo9_4 event__awayParticipant"})

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

    return date, score_results

date, match_results = get_match_results(driver)

def normalize_name(name):
    return name.strip().lower()

for idx in range(len(raw_df)):
    name_h = normalize_name(raw_df[1][idx])
    name_a = normalize_name(raw_df[2][idx])

    if (name_h, name_a) in match_results.keys():
        res = match_results[(name_h, name_a)]
        print(f"Match found: {name_h} vs {name_a} - {res}")
        raw_df.loc[idx, 3] = res[0]
        raw_df.loc[idx, 4] = res[1]
    else:
        print(f"No match found for {name_h} vs {name_a}")
        raw_df = raw_df.drop([idx])

raw_df = raw_df.reset_index(drop=True)

if len(raw_df) > 0:
    print(raw_df.shape)
    raw_df.columns = [str(val) for val in range(raw_df.shape[1])]
    raw_df = raw_df.style.set_properties(subset=[str(val+3) for val in range(raw_df.shape[1]-3)], **{'text-align': 'center'})
    raw_df.to_excel(output_file_name, index=False, header=False)
    wb = openpyxl.load_workbook(output_file_name)
    sheet = wb.active
    sheet.column_dimensions['A'].width = 35
    sheet.column_dimensions['B'].width = 22
    sheet.column_dimensions['C'].width = 22
    sheet.column_dimensions['D'].width = 10
    wb.save(output_file_name)
    print(f"\n\n*** Successfully updated output file as {output_file_name} *** \n")
else:
    print(f"\n\n****  {output_file_name} data is very old, You please get output.csv file again at first.")

driver.close()
