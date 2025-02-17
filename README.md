NOTICE: I sincerely apologize for revealing this forbidden knowledge.

This is a program that attempts to test each and every (realistically) servant in 90, 90+, 90++, 90* and 90** nodes. 

These are the parts to this program 
    1. /scripts/
        GetNiceFormatQuests.py
            scrapes atlas academy for all recommendedLv: 90 or higher nodes.
        GetUpdatesAndUpsert.py
            running this script uploads new Servant and Quest data to the mongodb
        mongodb_startup_script.sh
            logs into mongodb for shell scripting
        connectDB.py
            python script to log into mongodb
    2. MiscJsons/
        Contains data about CE, Events, MysticCode Ids, servant ids, trait ids
        largly unnecessary
    3. MysticCodes/
        contains the reasonable mystic codes that can be used while farming
        TODO needs to be updated with new MCs
    4. Main Codebase
        units/: 
            a
        managers/:
            a
        