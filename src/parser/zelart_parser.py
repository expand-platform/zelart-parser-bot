import requests
from bs4 import BeautifulSoup
import json
import os
import urllib3

class PrestaShopScraper:
    def __init__(self):
        self.email = os.environ["LOGIN"]
        self.password = os.environ["PASSWORD"]

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.login_url = "https://zelart.com.ua/user/login"

        self.session = requests.Session()

    def login(self):
        """Log in to the website and store the session."""
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": self.login_url,
            "Origin": "https://zelart.com.ua"
        }
        
        # Получаем страницу логина для извлечения CSRF-токена
        login_page = self.session.get(self.login_url, headers=headers, verify=False)
        soup = BeautifulSoup(login_page.text, "html.parser")
        
        # CSRF-токен
        csrf_token = soup.find("input", {"name": "_csrf-frontend"})["value"]
        
        # Отправляем POST-запрос с CSRF-токеном
        payload = {
            "LoginForm[login]": self.email,  # Поле для email
            "LoginForm[password]": self.password,  # Поле для пароля
            "LoginForm[rememberMe]": "1",  # Запомнить меня (опционально)
            "_csrf-frontend": csrf_token  # CSRF-токен
        }

        try:
            response = self.session.post(self.login_url, data=payload, headers=headers, verify=False)
            if response.status_code == 200 and "logout" in response.text.lower():
                print("✅ Login successful")
            else:
                print("❌ Login failed. Check your credentials or login URL.")
        except requests.exceptions.RequestException as e:
            print(f"Login error: {e}")


    def fetch_page(self, url):
        """Fetch the HTML content of a product page."""
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            response = self.session.get(url, headers=headers, verify=False)
            if response.status_code == 200:
                return response.text
            else:
                print(f"Failed to fetch {url} - Status Code: {response.status_code}")
                return None
        except requests.exceptions.SSLError as e:
            print(f"SSL error for {url}: {e}")
            return None
        

    def parse_product(self, url: str) -> dict | str:
        """Extract title, price, and description from a product page."""
        html = self.fetch_page(url)

        if not html:
            print(f"No product found for this url: {url}")
            return url

        soup = BeautifulSoup(html, "html.parser")

        app_component = soup.find(class_= 'app-component')
        json_data = f'''{app_component["data-init-data"]}'''
        data = json.loads(json_data)
        
        product_info = {
            "id": data['product']['id'],
            "title": data['model']['title'],
            "priceCur": data['product']['priceCur'],
            "priceWithDiscount": data['product']['priceWithDiscount'],
            "priceSrp": data['product']['priceSrp'],
            "isHidden": data['product']['isHidden'],
            "url": url
        }

        return product_info


    def scrape_product(self, url: str) -> dict | str:
        """ Scrape product information (Do not use this with loops, use login + parse product, only use this for a single product) """
        self.login()
        product = self.parse_product(url)
        return product