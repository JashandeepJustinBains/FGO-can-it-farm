from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import sys
import subprocess
import re
import WebpageAsJson  # replace with the name of your existing script

def getID(link, location, dir, regex, search):
    # List of URLs to visit
    # url_segment = [8088,8091,8096,8097,8098,8109,8113,8123,8156,8161,8183,8188,8196,8200,8208,8225,8230,8238,8240,8273,8290,
    #                8308,8313,8335,8346,8347,8348,8349,8350,8351,8352,8353,8354,8355,8356,8357,8358,8359,8360,8361,8362,8363,
    #                8364,8365,8366,8367,8368,8369,8370,8371,8372,8373,8374,8375,8376,8377,8378,8379,8380,8381,8382,8383,8384,
    #                8385,8386,8387,8388,8389,9001,9002,9003,9004,9005,9006,9007,9008,9009,9010,9013,9014,9015,9018,9021,9022,
    #                9029,9031,9032,9033,9035,9040,9046,9048,9049,9050,9051,9052,9053,9056,9057,9058,9068,9069,9071,9072,9073,
    #                9074,9075,9076,9077,9080,9087,9088,9091,9097,9098,9099,9101,9107,9109,9111,9112,9113,9119,9120,9124,9125,
    #                9127,9128,9130,9131,9133,9134,9135,9136,9143,9144,9145,9151,9152,9160,9163,9164,9166,9168,9169,9170]

    # TODO hunting quests have not been included yet, I would also like to automate this script better and maybe run it every morning at 5 or 6am EST to always have updated quest list
    url_segment = [9999]
    phrase = "Mana Prism"

    # Start the Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=chrome_options)

    for url in url_segment:
        cur_url = re.sub(regex, str(url), link)
        print(f"Current URL: {cur_url}")


        # Visit the URL
        driver.get(cur_url)

        driver.implicitly_wait(10) # seconds

        # Find all tables
        tables = driver.find_elements(By.TAG_NAME, "table")
        
        for table in tables:
            # Get the table text
            table_text = table.text

            # Check if the table text contains the search phrase
            if phrase in table_text:
                # If the search phrase is found, find all IDs in the table
                print("Searching for IDs...")
                elements = table.find_elements(By.XPATH, ".//tr/td/a")

                for element in elements:
                    # If the element is found and it matches the regex 'search' string, print it
                    if re.match(search, element.text):
                        print(f"Found ID: {element.text}")
                        loc_url = re.sub(search, str(element.text), location)
                        # Call the function from your existing script to download the webpage
                        print("Starting new subprocess...")
                        subprocess.run(['python', 'WebpageAsJson.py', dir, loc_url], cwd='F:/FGO-opensource/FGO-can-it-farm/')
                        print("Subprocess finished.")
    
    # Close the Chrome driver
    driver.quit()

def main():
    # Check if there are command line arguments
    # if len(sys.argv) != 6:
        # print("Usage:")
        # print("./GetQuests.py <directory> <link> <regex>")
        # print("Example:\n ./GetQuests.py  ")
        # return
    # if len(sys.argv) == 6:
    directory = './Quests'
    link = 'https://apps.atlasacademy.io/db/JP/war/9124'
    location = 'https://api.atlasacademy.io/nice/JP/quest/94062608/1?lang=en'
    regex = '[0-9]{4}'
    search = '[0-9]{8}'
    getID(link, location, directory, regex, search)

if __name__ == "__main__":
    main()
