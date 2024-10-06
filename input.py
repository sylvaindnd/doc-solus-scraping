import os
import time
import json
import slugify
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
ACCOUNT = json.load(open(f"{CURRENT_DIR}/account.json", "r"))
BASE_URL = "https://www.doc-solus.fr"


class Docsolus:
    def __init__(self):
        self.driver = webdriver.Firefox()
        self.cookies = {}

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

    def _check_exists_by_css(self, css):
        try:
            self.driver.find_element(By.CSS_SELECTOR, css)
        except NoSuchElementException:
            return False
        return True

    def _get_image(self, url):
        self.driver.get(url)
        wait = WebDriverWait(self.driver, 2)

        has_puzzle = self._check_exists_by_css('.center.maincolumn > center > .puzzle')
        has_image = self._check_exists_by_css('.center.maincolumn > img')

        table = None
        if has_puzzle:
            while True:
                try:
                    table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.center.maincolumn > center > .puzzle > div > table')))
                    break
                except Exception:
                    print(f"Refreshing {url}...")
                    self.driver.refresh()
                    time.sleep(2)
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

    def _images_to_pdf(self, i, title):
        print("Creating PDF...")

        images = [
            Image.open(i) for i in i
        ]

        for i, img in enumerate(images):
            img.thumbnail((800, 800))

        if not os.path.exists(f"{CURRENT_DIR}/pdfs"):
            os.makedirs(f"{CURRENT_DIR}/pdfs")
        images[0].save(f"{CURRENT_DIR}/pdfs/{title}.pdf", save_all=True, append_images=images[1:])
        print(f"PDF created: {title}.pdf")

    def download(self, url):
        self.driver.get(url)
        print(f"Opening {url}...")
        time.sleep(3)
        title = self.driver.find_element(By.CSS_SELECTOR, 'h1').text
        title = slugify.slugify(title)

        if os.path.exists(f"{CURRENT_DIR}/screenshots"):
            for file in os.listdir(f"{CURRENT_DIR}/screenshots"):
                os.remove(f"{CURRENT_DIR}/screenshots/{file}")

        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, '.center.maincolumn > section > span > a')
            images = []
            links = []
            for e in elements:
                if not e.get_attribute('href'):
                    continue
                links.append(e.get_attribute('href'))
            for i, l in enumerate(links):
                print(f"Downloading {i+1}/{len(links)}...")
                images.append(self._get_image(l))
            self._images_to_pdf(images, title)
            return True
        except Exception:
            print(f"Download error: {str(e)}")
            return False
        return True


if __name__ == '__main__':
    docsolus = Docsolus()

    if not docsolus.authenticate():
        print("Authentication failed")
        exit()

    url = input("Enter the url: ")
    if not docsolus.download(url):
        print("Download failed")
        exit()

