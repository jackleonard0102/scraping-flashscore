from selenium import webdriver
import pandas as pd
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import openpyxl
from selenium.webdriver.chrome.options import Options

# Set Chrome options to disable the search engine choice screen
chrome_options = Options()
chrome_options.add_argument("--disable-search-engine-choice-screen")

# Initialize WebDriver with the specified options
driver = webdriver.Chrome(options=chrome_options)

def get_match_ids(driver):
    search_url = "https://www.flashscore.com"
    driver.get(search_url)
    input('Are you ready? Press Enter to run the scraper...')
    print('Scraper is running, please wait...\n')
    
    date_elem = driver.find_element(By.CLASS_NAME, 'calendar__datepicker')
    date = date_elem.text        
    print("\n\n**** Date : ", date, "  ****\n\n")
    
    # Unroll all hidden games
    WebDriverWait(driver, 20)
    driver.find_element('xpath', '//*[@id="onetrust-accept-btn-handler"]').click()
    
    unroll_elements = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='wcl-icon-action-navigation-arrow-down']")))

    print("Unroll elements number --------> ", len(unroll_elements))
    i = 0
    for element in unroll_elements:
        while True:
            try:
                element.click()
                i += 1
                print('Clicked : ', i)
                break
            except:
                driver.execute_script("window.scrollBy(0,100)", "")
                print(i, "...")
                              
    matches = driver.find_elements(By.CLASS_NAME, 'event__match--twoLine')
    matches_number = len(matches)   
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


def scrape_team_1_2(driver, temp_id, odds):
    url_overall = f"https://www.flashscore.com/match/{temp_id}/#/standings/table/overall"
    driver.get(url_overall)
    time.sleep(3)
    
    league_info = driver.find_element(By.CLASS_NAME, 'tournamentHeader__sportNavWrapper')
    soup_leg = BeautifulSoup(league_info.get_attribute('innerHTML'), 'html.parser')
    
    if 'women' in soup_leg.find("span", {"class": "tournamentHeader__country"}).text.lower():
        print("\n*** Skipped, WOMEN game...")
        return None
    
    leg_name = soup_leg.find("span", {"class": "tournamentHeader__country"}).text.split("- Round")[0].strip()

    teams_div = driver.find_element(By.CLASS_NAME, 'duelParticipant')
    soup_tm = BeautifulSoup(teams_div.get_attribute('innerHTML'), 'html.parser')
    tms = soup_tm.find_all("div", {"class": "participant__participantNameWrapper"})
    game_time = soup_tm.find("div", {"class": "duelParticipant__startTime"}).text.split(" ")[-1]
    game_score = soup_tm.find("div", {"class": "detailScore__wrapper"}).text.strip()
    
    tm_name_h = tms[0].text.strip()
    tm_name_a = tms[1].text.strip()

    if game_score != '-':
        print("\n### Skipped because the game is finished! ###")
        return None

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
        
        if idx == 1:
            if team_name == tm_name_h:
                form_icons_G_H = form_icons_text
            else:
                form_icons_J_K = form_icons_text
    
    if min_value_span < 5:
        print(f"\n### Skipped because min_value_span ({min_value_span}) is less than 5! ###")
        return None
    
    # Switch to the standings table URL
    url_table = f"https://www.flashscore.com/match/{temp_id}/#/standings/top_scorers"
    driver.get(url_table)
    time.sleep(3)
    
    scores_div = driver.find_element(By.ID, 'tournament-table-tabs-and-content')
    soup_score = BeautifulSoup(scores_div.get_attribute('innerHTML'), 'html.parser')
    top_score_teams = soup_score.find_all("div", {"class": "ui-table__row topScorers__row topScorers__row--selected"})

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
            if (score_team == tm_name_h):
                team_number = 1
            else:
                team_number = 2
            team_info.append([score_team, team_number, score])

    for _ in range(4 - len(team_info)):
        team_info.append(['\t', '\t', '\t'])

    print(team_info)

    res = [leg_name, tm_name_h, tm_name_a, game_time, '\t', '\t', min_value_span, '\t', form_icons_G_H[0], form_icons_G_H[1], '\t', form_icons_J_K[0], form_icons_J_K[1], '\t', team_info[0][1], team_info[0][2], '\t', team_info[1][1], team_info[1][2], '\t', team_info[2][1], team_info[2][2], '\t', team_info[3][1], team_info[3][2], '\t', '\t', odds[0], odds[1], odds[2]]
    
    print(res)
    return res


def get_odds_data_2():
    odds_data = {}
    browser_2 = webdriver.Chrome(options=chrome_options)
    target_url = "https://www.betexplorer.com/next/soccer/"
    browser_2.get(target_url)

    WebDriverWait(browser_2, 10).until(
        EC.presence_of_element_located((By.ID, 'nr-ko-all'))
    )

    input("Are you ready? Press Enter to run the scraper...")
    
    print("Scrolling down the page...")
    last_height = browser_2.execute_script("return document.body.scrollHeight")
    
    while True:
        browser_2.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = browser_2.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            time.sleep(2)
            new_height = browser_2.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                break

        last_height = new_height

    print("Page fully scrolled.\n")
    
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
