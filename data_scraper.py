import csv
from datetime import date
import pandas as pd
import chkMarketConditions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from pathlib import Path
from selenium.webdriver.firefox.options import Options


import time
options = Options()
options.add_argument('--disable-blink-features=AutomationControlled')
# global driver
#my workaround for not opening a ton of windows.

driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
driver.implicitly_wait(40)
# driver = webdriver.Firefox()

class DataScraper:
    global driver
    #use to instantiate a selenium browser?
    def __init__(self):
        chkMrkt = chkMarketConditions.MarketCondition()
        if chkMrkt.is_market_open_today() == False:
            print("Market Closed")
            exit()


    def get_mpdata(self, ticker):
        error = 0
        ticker = ticker.upper()
        print(ticker)
        a = "/html/body/app-root/div/div[1]/div/app-options/div/div[8]/div/app-straddle/table/caption/b"
        b = By.TAG_NAME, "app-maxpain"
        c = "/html/body/app-root/div/div[1]/div/app-options/div/div[4]/div/app-chart/div/div[2]/div[2]/label/input"
        # htmlDateGeneratedline = By.XPATH, "/html/body/app-root/div/div[1]/div/app-options/div/div[3]/div/app-summary/table/tbody/tr/td[1]"

        driver.get(f'https://maximum-pain.com/options/{ticker}')
        element_dropdown = driver.find_element(By.TAG_NAME, "select")
        all_options = element_dropdown.find_elements(By.TAG_NAME, "option")

        ### Some unused web objects if needed to adjust for load times.

        dateGenerated1 = driver.find_element(By.XPATH, "/html/body/app-root/div/div[1]/div/app-options/div/div[3]/div/app-summary/table/tbody/tr/td[1]").get_attribute("innerHTML")
        dateGenerated = pd.to_datetime(dateGenerated1).strftime("%m/%d/%y")
        repeat_date_check_list = [0]
        data_list = []
        data_dict = {"maturitydate": dateGenerated}
        todayinweirdformat = date.today()
        today = pd.to_datetime(todayinweirdformat).strftime("%m-%d-%y")
        todayasYYMMDD = todayinweirdformat.strftime("%Y_%m_%d")
        pd.to_datetime(date.today()).strftime("%Y_%m_%d")


        for option in all_options:
            WebDriverWait(driver, 40).until(EC.element_to_be_clickable((By.XPATH, c)))
            option.click()
            WebDriverWait(driver, 40).until(EC.element_to_be_clickable((By.TAG_NAME, "option")))
            WebDriverWait(driver, 40).until(EC.element_to_be_clickable((By.XPATH,a)))
            # may be needied for timeout?  implicit wait after global driver may have fixed.
            time.sleep(.5)
            #website posts as mm/dd/yyyy, need to convert so it parses correctly when concatenated in pandas later.
            maturitydate1 = driver.find_element(By.XPATH, "/html/body/app-root/div/div[1]/div/app-options/div/div[10]/div/app-maxpain/table/caption/b[1]").get_attribute("innerHTML").removeprefix(f"{ticker} maturity ")
            maturitydate1.removeprefix(f"{ticker} maturity ")
            maturitydate = pd.to_datetime(maturitydate1).strftime("%m/%d/%y")
            WebDriverWait(driver, 40).until(EC.element_to_be_clickable((By.TAG_NAME, "option")))
            WebDriverWait(driver, 40).until(EC.element_to_be_clickable((By.XPATH, a)))

            if maturitydate != repeat_date_check_list[-1]:
                maxpainstring = (driver.find_element(By.XPATH,  "/html/body/app-root/div/div[1]/div/app-options/div/div[10]/div/app-maxpain/table/caption/b[2]").get_attribute("innerHTML")).removeprefix("Max Pain $")
                maxpain = '{:,.2f}'.format(float(maxpainstring))
                data_list.append(maxpain)
                data_dict[maturitydate] = maxpain
                repeat_date_check_list.append(maturitydate)
                WebDriverWait(driver, 40).until(EC.element_to_be_clickable((By.TAG_NAME, "option")))
                WebDriverWait(driver, 40).until(EC.element_to_be_clickable((By.XPATH, a)))
# """maybe i should change this so that instead of quitting, it just deletes duplicates and
# continues. that ways it would be easier to automate ... actually i
# should just be pulling OI data and comoputeing this stuff myself."""
            else:
                print("Error: Webdriver has timed out.")
                todayasYYMMDD = f"Timeout Error {today}"
                error = 1
                break

###TODO clean up diff dir problem and move files manually to reflect.


        # .teardown(){}
        print(data_dict)
        if error == 0:
            output_dir = Path(f'dataOutput/{ticker}_Daily_CSVs')

            output_dir.mkdir(mode=0o755,parents=True, exist_ok=True)

            with open(f"dataOutput/daily_selenium_scrapedMP/{ticker}_Daily_CSVs/{todayasYYMMDD} {ticker} MaxPain.csv", 'w') as file:
                writer = csv.DictWriter(file, data_dict.keys())
                writer.writeheader()
                writer.writerow(data_dict)
    def closedriver(self):
        driver.close()
    def quitdriver(self):
        driver.quit()