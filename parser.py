import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def fetch_cryptocurrencies(output_file="cryptos-1.json"):
    # Настройки браузера (чтобы он не открывался визуально)
    options = Options()  # Запуск в фоновом режиме (убрать, если хотите видеть браузер)
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")  # Отключает лишние логи

    # Запускаем Chrome через Selenium
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        cryptocurrencies = []
        for i in range(1, 50):
            url = f"https://www.coinbase.com/ru/explore?page={i}"
            print(f"Открываем страницу {url}")
            driver.get(url)

            time.sleep(1)
            # Парсим HTML-код с помощью BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Ищем список криптовалют (обычно в таблице или в карточках)
            crypto_cards = soup.find_all("tr")  # Используем строки таблицы

            for card in crypto_cards:
                image_tag = card.find("img")
                name_tag = card.find("h2", {"class": "cds-typographyResets-t6muwls"})
                ticker_tag = card.find("p", {"class": "cds-typographyResets-t6muwls"})

                image_url = image_tag["src"] if image_tag else ""
                name = name_tag.get_text(strip=True) if name_tag else ""
                ticker = ticker_tag.get_text(strip=True) if ticker_tag else ""

                if name and ticker:
                    cryptocurrencies.append({
                        "image_url": image_url,
                        "name": name,
                        "ticker": ticker
                    })

            print(f"Получены данные о {len(cryptocurrencies)} криптовалютах")

        # Сохраняем в JSON-файл
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(cryptocurrencies, f, ensure_ascii=False, indent=4)

        print(f"✅ Данные о {len(cryptocurrencies)} криптовалютах сохранены в {output_file}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

    finally:
        driver.quit()  # Закрываем браузер после завершения работы

if __name__ == "__main__":
    fetch_cryptocurrencies()
