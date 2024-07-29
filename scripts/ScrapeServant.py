from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

def scrape_website(url):
    # Specify the path to your ChromeDriver
    chromedriver_path = 'F:\\Program Files\\ChromeWebDriver\\chromedriver.exe'
    driver = webdriver.Chrome()

    # Open the website
    driver.get(url)

    # Wait for the page to load
    time.sleep(5)

    # Click on the tabs and scrape the data
    tabs = ['servant-tabs-tab-skill-1', 'servant-tabs-tab-skill-2', 'servant-tabs-tab-skill-3', 'servant-tabs-tab-noble-phantasm', 'servant-tabs-tab-passives', 'servant-tabs-tab-traits']
    for tab in tabs:
        # Wait until the tab is present
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, tab)))

        # Click on the tab
        driver.find_element(By.ID, tab).click()

        # Wait for the content of the tab to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'tab-content')))

        # Scrape the data
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tab_content = soup.find('div', {'class': 'tab-content'})

        print(f"\n{tab}:\n")
        print(tab_content.prettify().encode('utf-8'))


    # Close the browser
    driver.quit()

if __name__ == "__main__":
    url = 'https://apps.atlasacademy.io/db/JP/servant/416'
    scrape_website(url)
