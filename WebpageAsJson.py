import requests
import json
import os
import sys
import re

def download_json(url, directory):
    # Send a GET request to the URL
    response = requests.get(url)

    # Check that the request was successful
    if response.status_code == 200:
        # Parse the response as JSON
        try:
            data = response.json()

            # Extract the desired name from the data
            name = f'{str(data['spotName']) + '-' + str(data['warId'])}'
            filename = ""
            banned = ["&",["\'"],"\"","?", "<", ">", "#","{", "}","%","~","/","\\","."]
            for i, c in enumerate(name):
                if c in banned:
                    filename += ""
                else:
                    filename += c
            
            print(filename)
            # Create the filename
            filename = os.path.join(directory, f'{filename}.json')

            # Save the data to a file
            with open(filename,  'w', encoding='utf-8') as f:
                json.dump(data, f)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            print(f"Response content: {response.content}")
    else:
        print(f"Failed to download data from {url}")


def replaceString(regex_str, link, curNum):
    # use regex expression to find the part of the link that would require find any numbers in link and replace them with curNum
    return re.sub(regex_str, str(curNum), link)

# Example usage:
#   py ./script.py <directory> <link> <rangeStart> <regex_str>

def main():
    # Check if there are command line arguments
    if len(sys.argv) != 3:
        print("Usage:")
        print("./GetNiceFormat.py <directory> <link>")
        print("Example:\n ./GetNiceFormat.py ./Quests 'https://api.atlasacademy.io/nice/JP/quest/94062608/1?lang=en' ")
        return
    if len(sys.argv) == 3:
        directory = sys.argv[1]
        link = sys.argv[2]
        download_json(link, directory)



if __name__ == '__main__':
    main()