#!/usr/bin/env python
"""
Library to get user data from Payback.
"""
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime


class Payback:
    session = None
    points = None
    points_link = None

    def login(self, user, pin):
        self.session = requests.Session()
        r = self.session.get("http://www.payback.de/pb/id/312142/")
        soup = BeautifulSoup(r.content)
        r = self.session.post(
            "https://www.payback.de/pb/ww/wf04g.login.auth.action",
            data={
                "UseHttps": "1",
                "page_id": soup.select("#inlineLoginFormBD input[name=page_id]")[0]['value'],
                "did": soup.select("#inlineLoginFormBD input[name=did]")[0]['value'],
                "pfid": soup.select("#inlineLoginFormBD input[name=pfid]")[0]['value'],
                "authAlt": "false",
                "cardNumber": user,
                "pin": pin,
                "permLoginCheckBox": "true",
                "x": 22,
                "y": 8,
            }
        )
        c = r.content.decode("windows-1252")
        soup = BeautifulSoup(c)
        if "Sie haben" in c:
            a = soup.select("p.welcome-msg a")[0]
            self.points = int(re.sub("[^0-9]", "", a.string))
            self.points_link = a['href']
            return True
        else:
            return False

    def history(self):
        i = 1
        res = []
        while True:
            r = self.session.get("https://www.payback.de/pb/punktekonto/pgn/%d/id/13598/" % i)
            soup = BeautifulSoup(r.content.decode("windows-1252"))
            trs = soup.select("table.mypoints tbody tr")
            for tr in trs:
                c = [n.string for n in list(tr.children) if n != '\n']
                res.append({
                    'date': datetime.strptime(c[0], "%d.%m.%Y"),
                    'partner': c[1],
                    'action': c[2],
                    'points': int(re.sub("[^\\-0-9]", "", c[3])),
                })
            if len(trs) == 0:
                break
            i += 1
        return res
