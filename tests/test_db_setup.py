import sys
import os
from dotenv import load_dotenv

# Ensure .env is loaded for DB connection
load_dotenv()

# Add scripts directory to sys.path for connectDB import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
import connectDB

def setUpModule():
    """Set up global db for all tests in this module."""
    if hasattr(connectDB, 'db'):
        globals()['db'] = connectDB.db

def tearDownModule():
    """Clean up global db after tests (optional)."""
    if 'db' in globals():
        del globals()['db']
