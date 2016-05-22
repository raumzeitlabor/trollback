#!/usr/bin/env/python
import datetime
from payback import Payback
import xively
import sqlite3
import os
import csv

from parameters import *

dbcreate = not os.path.exists(DB_FILE)
dbcon = sqlite3.connect(DB_FILE)
dbcur = dbcon.cursor()
if dbcreate:
    dbcur.execute("""
                  CREATE TABLE history
                  (
                    date text, partner text,
                    action text, points numeric
                  );
                  """)

api = xively.XivelyAPIClient(XIVELY_API_KEY)
feed = api.feeds.get(XIVELY_FEED)
now = datetime.datetime.utcnow()

def is_payout(item):
    return 'ausgezahlt' in item['action'] or 'Wertscheckausdruck' in item['action']

payback = Payback()
if payback.login(PAYBACK_USER, PAYBACK_PIN):
    history = payback.history(pages=20)
    lastday = None
    daycount = 0
    daycount_known = 0
    deletion = False
    for i in range(len(history), 0, -1):
        item = history[i-1]
        if item['date'] != lastday:
            daycount = 1
            lastday = item['date']
            dbcur.execute('SELECT * FROM history WHERE date = ?;', (item['date'].strftime("%Y-%m-%d"),))
            daycount_known = len(dbcur.fetchall())
            if i > 10:
                dbcur.execute("DELETE FROM history WHERE date = ?", (item['date'].strftime("%Y-%m-%d"),))
                dbcon.commit()
                deletion = True
        else:
            daycount += 1
            if daycount > daycount_known or deletion:
                dbcur.execute("""
                              INSERT INTO history
                              (date, partner, action, points)
                              VALUES
                              (?, ?, ?, ?);
                              """,
                              (
                                  item['date'].strftime("%Y-%m-%d"),
                                  item['partner'],
                                  item['action'],
                                  item['points'],
                              ))

        dbcon.commit()

    dbhist = []
    data = dbcur.execute("SELECT date, partner, action, points FROM history")
    with open(CSV_FILE, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'partner', 'action', 'points'])
        for row in data:
            writer.writerow(row)
            dbhist.append({'date': row[0], 'partner': row[1], 'action': row[2], 'points': row[3]})

    dbcur.close()
    dbcon.close()

    payback.points += sum([(-1)*int(item['points']) for item in dbhist if is_payout(item) and item['points'] < 0])

    feed.datastreams = [
        xively.Datastream(id=XIVELY_ID, current_value=payback.points, at=now),
    ]
    feed.update()

else:
    print("Login failed.")
