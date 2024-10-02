import os
import json
import time

import requests
import slugify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
ACCOUNT = json.load(open(f"{CURRENT_DIR}/account.json", "r"))
BASE_URL = "https://www.doc-solus.fr"


class Docsolus:
    def __init__(self, search_keys=[]):
        self.driver = webdriver.Firefox()
        self.search_keys = search_keys
        self.urls = self.retrieve_urls()
        self.cookies = {}

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

    def authenticate(self):
        try:
            self.driver.get(f"{BASE_URL}/bin/users/connexion.html")
            wait = WebDriverWait(self.driver, 10)
            login = wait.until(EC.presence_of_element_located((By.NAME, "login")))
            password = wait.until(EC.presence_of_element_located((By.NAME, "passwd")))
            submit = wait.until(EC.element_to_be_clickable((By.NAME, "save")))
            login.send_keys(ACCOUNT['email'])
            password.send_keys(ACCOUNT['password'])
            submit.click()
            return True
        except Exception as e:
            print(f"Authenticate error: {str(e)}")
        return False

    def searchs(self):
        try:
            for k in self.search_keys:
                search_key_text = f"{k.get('filiere', '')}-{k.get('concours', '')}"
                if search_key_text in [u.get('search_keys') for u in self.urls]:
                    print(f"Search for {k.get('filiere', '')} {k.get('concours', '')} already done")
                    continue
                search_url = (f"{BASE_URL}/main.html?"
                       f"filiere={k.get('filiere', '')}&"
                       f"concours={k.get('concours', '')}")
                self.driver.get(search_url)
                for u in self.driver.find_elements(By.CSS_SELECTOR, '.center.maincolumn ul li a'):
                    link_url = u.get_attribute('href')
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
            return True
        except Exception as e:
            print(f"Searchs error: {str(e)}")
        return False

    def _check_exists_by_css(self, css):
        try:
            self.driver.find_element(By.CSS_SELECTOR, css)
        except NoSuchElementException:
            return False
        return True

    def _get_image(self, url):
        self.driver.get(url)
        wait = WebDriverWait(self.driver, 1)

        has_puzzle = self._check_exists_by_css('.center.maincolumn > center > .puzzle')
        has_image = self._check_exists_by_css('.center.maincolumn > img')

        table = None
        if has_puzzle:
            while True:
                try:
                    table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.center.maincolumn > center > .puzzle > div > table')))
                    break
                except Exception:
                    self.driver.refresh()
                    time.sleep(1)
        elif has_image:
            table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.center.maincolumn > img')))
        else:
            table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.center.maincolumn')))
        url_name = slugify.slugify(url)
        if not os.path.exists(f"{CURRENT_DIR}/screenshots"):
            os.makedirs(f"{CURRENT_DIR}/screenshots")
        self.driver.implicitly_wait(2)
        table.screenshot(f"{CURRENT_DIR}/screenshots/{url_name}.png")
        return f"{CURRENT_DIR}/screenshots/{url_name}.png"

    def downloads(self):
        for u in self.urls:
            if not u.get('open', False):
                print(f"Opening {u.get('url')}")
                self.driver.get(u.get('url'))
                self.driver.implicitly_wait(.5)
                elements = self.driver.find_elements(By.CSS_SELECTOR, '.center.maincolumn > section > span > a')
                images = []
                links = []
                for e in elements:
                    if not e.get_attribute('href'):
                        continue
                    links.append(e.get_attribute('href'))
                for l in links:
                    images.append(self._get_image(l))
                u['open'] = True
        json.dump(self.urls, open(f"{CURRENT_DIR}/urls.json", "w"))


if __name__ == '__main__':
    doc = Docsolus(search_keys=[
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
    if not doc.authenticate():
        print("Failed to authenticate")

    if not doc.searchs():
        print("Failed to search")

    if not doc.downloads():
        print("Failed to download")

