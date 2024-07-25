import json
import numpy as np
import sys
import pandas as pd

def json_to_numpy(json_file):
    # Load the JSON file
    with open(json_file, 'r', encoding='utf-8') as f:  # specify the encoding here
        data = json.load(f)
    
    # Convert the data to a numpy array
    numpy_array = np.array(data)
    
    return numpy_array


def main():
    # Check if a filename was passed as a command line argument
    if len(sys.argv) != 2:
        print("Usage: python script.py <json_file>")
        sys.exit(1)

    # Get the filename from the command line arguments
    json_file = sys.argv[1]

    # Convert the JSON file to a numpy array
    numpy_array = json_to_numpy(json_file)

    # Convert the numpy array to a pandas DataFrame for a table view
    df = pd.DataFrame(numpy_array)

    # Print the DataFrame
    print(df.head())

if __name__ == "__main__":
    main()
