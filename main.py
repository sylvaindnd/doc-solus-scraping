import json
import os
import requests
import datetime
import pdfkit
from bs4 import BeautifulSoup
from requests_html import HTMLSession


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
ACCOUNT = json.load(open(f"{CURRENT_DIR}/account.json", "r"))
BASE_URL = "https://www.doc-solus.fr"


class DocSolus:
    def __init__(self, search_keys=[]):
        self.cookies = None
        self.session = HTMLSession()
        self.authenticate()
        self.search_keys = search_keys
        self.urls = self.retrieve_urls()

    def retrieve_urls(self):
        """
        Retrieve the urls from the json file

        URLS as the following format:
        [{
            "sector": "PC",
            "school": "Polytechnique",
            "title": "Polytechnique PC 2023",
            "url": "https://www.doc-solus.fr/prepa/sci/adc/bin/view.corrige.html?q=Polytechnique%20PC%202023",
            "open": False,
            "search_keys": f"{filiere}-{concours}"
        }]

        If the url is not open then we will scrape the pages

        :return:
        """
        if not os.path.exists(f"{CURRENT_DIR}/urls.json"):
            json.dump([], open(f"{CURRENT_DIR}/urls.json", "w"))
            return []
        urls = json.load(open(f"{CURRENT_DIR}/urls.json", "r"))
        return urls

    def get_headers(self):
        cookies = ""
        if self.cookies:
            cookies = f"ck_id={self.cookies.get('cookies', {}).get('ck_id', '')}"
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Cookie": cookies,
            "Host": "www.doc-solus.fr",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "macOS",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        }

    def check_cookies(self):
        """
        Check if the cookies are still valid

        :return:
        """
        if not "cookies" in ACCOUNT:
            return False
        if ACCOUNT["cookies"].get("expiry_date") < datetime.datetime.now().timestamp():
            return False
        return True

    def authenticate(self):
        """
        Authenticate the user to the website

        :return:
        """
        if not self.check_cookies():
            response = requests.post(
                f"{BASE_URL}/bin/users/connexion.html",
                data={
                    "email": ACCOUNT["email"],
                    "password": ACCOUNT["password"],
                },
                headers=self.get_headers()
            )
            self.cookies = response.cookies.get_dict()
            ACCOUNT["cookies"] = {
                "expiry_date": datetime.datetime.now().timestamp() + 0,
                "cookies": self.cookies
            }
            json.dump(ACCOUNT, open(f"{CURRENT_DIR}/account.json", "w"))
        else:
            self.cookies = ACCOUNT["cookies"]["cookies"]

    def searchs(self):
        """
        Search the urls for the given search keys

        :return:
        """
        for k in self.search_keys:
            search_key_text = f"{k.get('filiere', '')}-{k.get('concours', '')}"
            if search_key_text in [u.get('search_keys') for u in self.urls]:
                print(f"Search for {k.get('filiere', '')} {k.get('concours', '')} already done")
                continue
            search_url = (f"{BASE_URL}/main.html?"
                   f"filiere={k.get('filiere', '')}&"
                   f"concours={k.get('concours', '')}")
            response = requests.get(search_url, headers=self.get_headers())
            soup = BeautifulSoup(response.text, "html.parser")
            for u in soup.select('.center.maincolumn ul li a'):
                link_url = f"{BASE_URL}{u.get('href')}"
                link_text = u.text
                if not link_url in [u.get('url') for u in self.urls]:
                    self.urls.append({
                        "sector": k.get('filiere', ''),
                        "school": k.get('concours', ''),
                        "title": link_text,
                        "url": link_url,
                        "open": False,
                        "search_keys": f"{k.get('filiere', '')}-{k.get('concours', '')}"
                    })
            print(f"Search for {k.get('filiere', '')} {k.get('concours', '')} done")
        json.dump(self.urls, open(f"{CURRENT_DIR}/urls.json", "w"))
        print("Searchs done")

    def get_tables(self, url):
        r = self.session.get(url, headers=self.get_headers())
        self.cookies = r.cookies.get_dict()
        print("Cookies", self.cookies)
        r.html.render()
        # print(r.html.html)
        soup = BeautifulSoup(r.html.html, "html.parser")
        table = soup.get('.center.maincolumn center .puzzle > div > table')
        print(table)
        return table

    def downloads(self):
        for u in self.urls:
            if not u.get('open', False):
                print(f"Opening {u.get('url')}")
                tables = []
                r = self.session.get(u.get('url'), headers=self.get_headers())
                r.html.render()
                soup = BeautifulSoup(r.html.html, "html.parser")
                for l in soup.select('.center.maincolumn > section > span > a'):
                    link = l.get('href')
                    tables.append(self.get_tables(f"{BASE_URL}{link}"))
                u['open'] = True





if __name__ == '__main__':
    doc_solus = DocSolus(search_keys=[
        {
            "filiere": "PC",
            "concours": "Polytechnique",
        },
        {
            "filiere": "MP",
            "concours": "Polytechnique",
        },
        {
            "filiere": "PSI",
            "concours": "Polytechnique",
        },
        {
            "filiere": "PC",
            "concours": "Mines",
        },
        {
            "filiere": "PSI",
            "concours": "Mines",
        },
        {
            "filiere": "MP",
            "concours": "Mines",
        },
        {
            "filiere": "PC",
            "concours": "Centrale",
        },
        {
            "filiere": "MP",
            "concours": "Centrale",
        },
        {
            "filiere": "PSI",
            "concours": "Centrale",
        }
    ])
    doc_solus.searchs()
    doc_solus.downloads()
