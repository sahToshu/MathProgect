from selenium import webdriver
from selenium.webdriver.edge.options import Options
import os

def save_page_html(url, output_file="page.html"):
    """Зберігає HTML сторінки у файл"""
    try:
        # Налаштування драйвера
        edge_options = Options()
        edge_options.add_argument("--headless")  # Режим без відображення браузера
        driver = webdriver.Edge(options=edge_options)
        
        # Отримання сторінки
        driver.get(url)
        
        # Очікування завантаження (можна змінити за необхідності)
        driver.implicitly_wait(10)
        
        # Збереження HTML у файл
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
            
        print(f"HTML успішно збережено у файл: {os.path.abspath(output_file)}")
        
    except Exception as e:
        print(f"Помилка: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

# Приклад використання:
if __name__ == "__main__":
    url = "https://silpo.ua/category/frukty-ovochi-4788"  # Можна змінити на будь-яку URL-адресу
    save_page_html(url)