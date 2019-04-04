import argparse
import re
import sqlite3
import time
import timeit
from threading import Thread

import requests
from bs4 import BeautifulSoup


parser = argparse.ArgumentParser(description="Craiglist crawler for vehicles")
parser.add_argument('max_price', type=int, help='The maximum price for the car')
parser.add_argument('max_miles', type=int, help="The maximum amount of miles on the car")
parser.add_argument('min_year', type=int, help="The minimum year of the car")
parser.add_argument('location', type=str, help="The location for the search")

args = parser.parse_args()

MAX_PRICE = args.max_price
MAX_AUTO_MILES = args.max_miles
LOCATION = args.location
MIN_YEAR = args.min_year

DB_NAME = "craigslist-car.db"
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cur = conn.cursor()

cars_sql = """
    CREATE TABLE if not exists cars (
        "name"	        text NOT NULL,
        "price"	        real NOT NULL,
        "odometer"	    real NOT NULL,
        "url"	        text NOT NULL,
        "title_status"	text NOT NULL,
        "time_posted"	text NOT NULL,
        "location"      text,
        PRIMARY KEY(name, url)
    );
"""

cur.execute(cars_sql)


def selectAllCars():
    cur.execute("SELECT * from cars")
    rows = cur.fetchall()
    for row in rows:
        print(row)


class Crawler(Thread):
    def __init__(self, dbName, page, conn):
        Thread.__init__(self)
        self.dbName = dbName
        self.conn = conn
        self.cur = self.conn.cursor()
        self.page = page

    def insertCar(self, name, price, odometer, url, title_status, time_posted):
        try:
            car_sql = "INSERT INTO cars (name, price, odometer, url, title_status, time_posted, location) VALUES (?,?,?,?,?,?,?)"
            self.cur.execute(car_sql, (name, price, odometer,
                                       url, title_status, time_posted, LOCATION))
        except sqlite3.Error as e:
            print(e)

    def crawlUrl(self, url):
        r = requests.get(url)
        htmlBody = BeautifulSoup(r.content, "html.parser")
        titleStatus = htmlBody.find(string=re.compile(
            'title status')).parent.contents[1].string

        price = 0

        if(titleStatus.lower() != "clean"):
            print("passing this one")
            return

        name = htmlBody.select_one("#titletextonly").string

        try:
            if htmlBody.select_one(".price") is not None:
                print(htmlBody.select_one(".price").string[1:0])
                price = float(htmlBody.select_one(".price").string[1:])
        except:
            price = 0

        odometer = float(htmlBody.find(string=re.compile(
            'odometer')).parent.contents[1].string)
        timePosted = htmlBody.select_one(".date.timeago")['datetime']
        print(name, price, odometer, url)

        self.insertCar(name, price, odometer, url, titleStatus, timePosted)

    def run(self):
        try:
            url = f'https://{LOCATION}.craigslist.org/search/cta?s={self.page}&max_price={MAX_PRICE}&max_auto_miles={MAX_AUTO_MILES}&min_auto_year={MIN_YEAR}'
            r = requests.get(url)

            soup = BeautifulSoup(r.content, "html.parser")
            links = soup.findAll('a', {"class": "result-title"})

            for link in links:
                self.crawlUrl(link["href"])
            # self.crawlUrl(links[0]["href"])
            self.conn.commit()
            print("I finished my thread job")
        except requests.exceptions.RequestException as e:
            
            print(f"{self.name}I exited early")
            pass


def runThreads():
    thread1 = Crawler(DB_NAME, 0, conn)
    thread2 = Crawler(DB_NAME, 120, conn)
    thread3 = Crawler(DB_NAME, 240, conn)
    # thread4 = Crawler(DB_NAME, 360, conn)

    start = timeit.default_timer()

    thread1.start()
    thread2.start()
    thread3.start()
    # thread4.start()

    thread1.join()
    thread2.join()
    thread3.join()
    # thread4.join()

    end = timeit.default_timer()
    print(f'The process took: {end - start}')

    print("Closing connection to database")
    conn.close()
    
runThreads()


