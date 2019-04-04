import sqlite3

DB_NAME = "craigslist-car.db"

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)