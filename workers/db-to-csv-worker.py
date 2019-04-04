import csv
import sys
sys.path.append(".")

import db
database = db.Database()

def worker():
    with database.conn:
        with open('./cars.csv', 'w', encoding='utf-8') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(['Name', 'Price', 'Odometer', 'Link', 'Status', 'Date', 'Location'])
            
            for row in database.conn.execute("SELECT * from cars order by time_posted desc"):
                writer.writerow(row)

worker()