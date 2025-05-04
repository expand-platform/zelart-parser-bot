import requests
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv
import urllib3

class PrestaShopScraper:
    def __init__(self):
        load_dotenv()
        self.email = os.getenv("LOGIN")
        self.password = os.getenv("PASSWORD")

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
            # print("payload", payload)
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
        

    def parse_product(self, url):
        """Extract title, price, and description from a product page."""
        html = self.fetch_page(url)
        if not html:
            return

        soup = BeautifulSoup(html, "html.parser")

        app_component = soup.find(class_= 'app-component')
        json_data = f'''{app_component["data-init-data"]}'''
        data = json.loads(json_data)
        
        product_info = {
            "id": data['product']['id'],
            "title": data['model']['title'],
            "priceCur": data['product']['priceCur'],
            "priceWithDiscount": data['product']['priceWithDiscount'],
            "priceBigOpt": data['product']['priceBigOpt'],
            "bigOptQuantity": data['product']['bigOptQuantity'],
            "priceSrp": data['product']['priceSrp'],
            "isHidden": data['product']['isHidden'],
            "url": url
        }

        return product_info


    def scrape_product(self, url):
        """Scrape all product pages."""
        self.login()
        product = self.parse_product(url)
        return product
        

    def product_prettify(self, product):
        product_info_prettified = ''
        for key in product:
            if key == "id":
                pass
            elif key == "title":
                product_info_prettified += f"Title: {product['title']}\n"
                # print("Title:", product['title'])
            elif key == "priceCur":
                product_info_prettified += f"Price: {product['priceCur']}\n"
                # print("Price:", product['priceCur'])
            elif key == "priceWithDiscount":
                if product['priceWithDiscount'] != product['priceCur']:
                    product_info_prettified += f"Discounted price: {product['priceWithDiscount']}\n"
                    # print("Discounted price:", product['priceWithDiscount'])
            elif key == "priceBigOpt":
                product_info_prettified += f"Opt price: {product['priceBigOpt']}\n"
                # print("Opt price:", product['priceBigOpt'])
            elif key == "bigOptQuantity":
                product_info_prettified += f"Opt quantity: {product['bigOptQuantity']}\n"
                # print("Opt quantity:", product['bigOptQuantity'])
            elif key == "priceSrp":
                product_info_prettified += f"Retail price: {product['priceSrp']}\n"
                # print("Retail price:", product['priceSrp'])
            elif key == "isHidden":
                if product['isHidden'] == True:
                    product_info_prettified += f"Product is unavailable\n"
                    # print("Product is unavailable")
                else:
                    product_info_prettified += f"Product is available\n"
                    # print("Product is available")
            elif key == "url":
                product_info_prettified += f"URL: {product['url']}\n"
                # print("URL:", product['url'])
            else:
                pass
                # print(key, product[key])
        return product_info_prettified
