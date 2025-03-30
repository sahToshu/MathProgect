from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import mysql.connector
import time
import random
import csv
import os
from config import host, user, password, db_name, port

def connect_to_database():
    """Підключення до бази даних MAMP"""
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            port=port,
        )
        print("Підключено до бази даних MAMP")
        return conn
    except Exception as e:
        print(f"Помилка підключення до MySQL: {e}")
        return None

def save_to_database(conn, products):
    """Збереження товарів у базу даних"""
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS silpo_products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(255),
                name VARCHAR(500),
                price VARCHAR(100),
                image_url VARCHAR(512),
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        for product in products:
            cursor.execute("""
                INSERT INTO silpo_products (category, name, price, image_url)
                VALUES (%s, %s, %s, %s)
            """, (
                product['category'],
                product['name'],
                product['price'],
                product['image_url']
            ))
        
        conn.commit()
        print(f"Збережено {len(products)} товарів у БД")
    except Exception as e:
        conn.rollback()
        print(f"Помилка запису в БД: {e}")
    finally:
        cursor.close()

def connect_to_existing_edge():
    """Підключення до браузера"""
    edge_options = Options()
    edge_options.add_experimental_option("debuggerAddress", "localhost:9222")
    driver = webdriver.Edge(options=edge_options)
    return driver

def human_like_delay(min=1, max=3):
    """Імітація людської затримки"""
    time.sleep(random.uniform(min, max))

def extract_products(driver):
    """Витяг даних про продукти"""
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.products-list"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        products_container = soup.find('div', class_='products-list')
        
        if not products_container:
            print("Не знайдено контейнер з товарами")
            return []
            
        products = products_container.find_all('shop-silpo-common-product-card')
        extracted = []
        
        for product in products:
            try:
                product_card = product.find('a', class_='product-card')
                if not product_card:
                    continue
                
                name = product_card.find('div', class_='product-card__title').get_text(strip=True)
                price = product_card.find('div', class_='product-card-price__displayPrice').get_text(strip=True)
                weight = product_card.find('div', class_='ft-typo-14-semibold').get_text(strip=True)
                full_price = f"{price}/{weight}"
                
                img_tag = product_card.find('img', class_='product-card__product-img')
                image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
                if image_url and not image_url.startswith('http'):
                    image_url = f"https://silpo.ua{image_url}"
                
                is_available = product_card.find('button', class_='product-card-quantity__add') is not None
                
                if name and full_price and is_available:
                    extracted.append({
                        'name': name,
                        'price': full_price,
                        'image_url': image_url
                    })
            except Exception as e:
                print(f"Помилка парсингу товару: {e}")
                continue
                
        print(f"Знайдено товарів на сторінці: {len(extracted)}")
        return extracted
        
    except Exception as e:
        print(f"Помилка витягування товарів: {e}")
        return []

def process_category(driver, base_url, category_name, min_products=47, max_pages=70):
    """Обробка категорії"""
    all_products = []
    current_page = 1
    has_next_page = True
    
    while has_next_page and current_page <= max_pages:
        url = f"{base_url}?page={current_page}" if current_page > 1 else base_url
        print(f"\nОбробка сторінки {current_page}: {url}")
        
        try:
            driver.get(url)
            human_like_delay(2, 4)
            
            if "Доступ обмежений" in driver.page_source:
                print("Блокування доступу! Перехід до наступної категорії")
                break
                
            products = extract_products(driver)
            if not products:
                print("Товари не знайдені")
                break
                
            all_products.extend(products)
            
            if len(products) < min_products:
                print(f"На сторінці лише {len(products)} товарів")
                break
                
            current_page += 1
            human_like_delay(3, 5)
            
        except Exception as e:
            print(f"Помилка обробки сторінки: {e}")
            break
    
    for product in all_products:
        product['category'] = category_name
    
    print(f"Всього товарів у категорії {category_name}: {len(all_products)}")
    return all_products

def main():
    """Головна функція"""
    categories = [
        ("М'ясо", "https://silpo.ua/category/m-iaso-4411"),
        ("Риба", "https://silpo.ua/category/ryba-4430"),
        ("Ковбасні вироби", "https://silpo.ua/category/kovbasni-vyroby-i-m-iasni-delikatesy-4731"),
        ("Сири", "https://silpo.ua/category/syry-1468"),
        ("Хліб та випічка", "https://silpo.ua/category/khlib-ta-vypichka-5121"),
        ("Молочні продукти", "https://silpo.ua/category/molochni-produkty-ta-iaitsia-234"),
        ("Бакалія", "https://silpo.ua/category/bakaliia-i-konservy-4870"),
        ("Соуси та спеції", "https://silpo.ua/category/sousy-i-spetsii-4938"),
        ("Заморожені продукти", "https://silpo.ua/category/zamorozhena-produktsiia-264"),
        ("Овочі та фрукти", "https://silpo.ua/category/frukty-ovochi-4788")
    ]
    
    # Підключення до БД
    db_conn = connect_to_database()
    
    try:
        # Підключення до браузера
        driver = connect_to_existing_edge()
        all_products = []
        
        for category_name, url in categories:
            products = process_category(driver, url, category_name)
            if products:
                all_products.extend(products)
                # Збереження у БД
                if db_conn:
                    save_to_database(db_conn, products)
            
            human_like_delay(5, 8)
        
        # Збереження в CSV
        if all_products:
            info_folder = os.path.join(os.path.dirname(__file__), 'info')
            os.makedirs(info_folder, exist_ok=True)
            csv_path = os.path.join(info_folder, 'silpo_products.csv')
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['category', 'name', 'price', 'image_url'])
                writer.writeheader()
                writer.writerows(all_products)
            
            print(f"Дані збережено у {csv_path}")
            
    except Exception as e:
        print(f"Критична помилка: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()
        if db_conn:
            db_conn.close()

if __name__ == "__main__":
    main()
