from pathlib import Path
import sqlite3

from simple_logging import Logger
from config import *


def setup_db(log):
    db_file = Path(DB_PATH).resolve()
    names_file = Path(NAMES_PATH).resolve()

    if db_file.is_file():
        log.info("Database already exists.")
        log.debug(
            "Note that the existing database expected to compatible with the program")
        return True
    log.warn("Database does not exist. Attempting to create it.")
    if not names_file.is_file():
        log.error(
            "File ({}) containing the names not found. Please create it.".format(names_file))
        return False
    log.debug("Names file exists. Opening new database.")
    # PS Errors/Exceptions aren't handled. I know. I'm not gonna do it.
    # Any error should crash the bot, which should cause it to restart (except in dev env)
    db = sqlite3.Connection(db_file)
    c = db.cursor()

    c.execute(
        '''CREATE TABLE IF NOT EXISTS names (name text PRIMARY KEY ON CONFLICT FAIL);''')
    log.debug("Created database. Adding names.")

    count = 0
    with open(names_file, 'r') as f:
        for line in f:
            if line.strip() != "":
                c.execute("INSERT INTO names VALUES(?);", [line.strip()])
                count += 1
    log.debug("Added {} names.".format(count))

    rows = c.execute("SELECT * FROM names;")
    found_count = 0
    for row in rows:
        found_count += 1
    log.debug("Found {} names.".format(found_count))

    if count != found_count:
        log.warn(
            "Looks like some names have not gotten added. Perhaps duplicates? This should be investigated.")
    log.success("Database created and set up successfully!")
    return True


if __name__ == '__main__':
    log = Logger('db_setup', log_folder=Path(LOG_FOLDER).resolve(),
                 log_level='info', output_level='debug')
    success = setup_db(log)
    if success:
        log.debug("Success!")
    else:
        log.error("Could not setup database!")
