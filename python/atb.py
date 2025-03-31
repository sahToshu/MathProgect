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
    """Підключення до MAMP MySQL"""
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
            CREATE TABLE IF NOT EXISTS atb_products (
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
                INSERT INTO atb_products (category, name, price, image_url)
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
    """Підключення до браузера (без змін)"""
    edge_options = Options()
    edge_options.add_experimental_option("debuggerAddress", "localhost:9222")
    driver = webdriver.Edge(options=edge_options)
    return driver

def human_like_delay(min=1, max=3):
    """Імітація людської затримки (без змін)"""
    time.sleep(random.uniform(min, max))

def extract_products(driver):
    """Витяг даних про продукти з ATB (без змін)"""
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article.catalog-item"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        products = soup.find_all('article', class_='catalog-item')
        extracted = []
        
        for product in products:
            try:
                name = product.find('div', class_='catalog-item__title').get_text(strip=True)
                price = product.find('data', class_='product-price__top').get_text(strip=True)
                
                img_tag = product.find('img', class_='catalog-item__img')
                image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
                
                if image_url and not image_url.startswith('http'):
                    image_url = f"https://www.atbmarket.com{image_url}"
                
                if name and price:
                    extracted.append({
                        'name': name,
                        'price': price,
                        'image_url': image_url
                    })
            except Exception as e:
                print(f"Помилка парсингу товару: {e}")
                continue
                
        print(f"Знайдено товарів ATB на сторінці: {len(extracted)}")
        return extracted
        
    except Exception as e:
        print(f"Помилка витягування товарів ATB: {e}")
        return []

def process_category(driver, base_url, category_name, min_products=36, max_pages=17):
    """Обробка категорії ATB (без змін)"""
    all_products = []
    current_page = 1
    has_next_page = True
    
    while has_next_page and current_page <= max_pages:
        url = f"{base_url}?page={current_page}" if current_page > 1 else base_url
        print(f"\nОбробка сторінки {current_page} ATB: {url}")
        
        try:
            driver.get(url)
            human_like_delay(2, 4)
            
            # Обробка підтвердження віку
            try:
                age_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.custom-blue-btn"))
                )
                age_btn.click()
                print("Підтверджено вік для ATB")
                human_like_delay()
            except:
                pass
                
            products = extract_products(driver)
            if not products:
                print("Товари ATB не знайдені")
                break
                
            all_products.extend(products)
            
            if len(products) < min_products:
                print(f"На сторінці ATB лише {len(products)} товарів")
                break
                
            current_page += 1
            human_like_delay(3, 5)
            
        except Exception as e:
            print(f"Помилка обробки сторінки ATB: {e}")
            break
    
    for product in all_products:
        product['category'] = category_name
    
    print(f"Всього зібрано товарів ATB у категорії {category_name}: {len(all_products)}")
    return all_products

def main():
    """Головна функція для ATB"""
    categories = [
        ("Овочі та фрукти", "https://www.atbmarket.com/catalog/287-ovochi-ta-frukti"),
        ("Бакалія", "https://www.atbmarket.com/catalog/285-bakaliya"),
        ("Молочні продукти", "https://www.atbmarket.com/catalog/molocni-produkti-ta-ajca"),
        ("М'ясо", "https://www.atbmarket.com/catalog/maso"),
        ("Сири", "https://www.atbmarket.com/catalog/siri"),
        ("Риба і Морепродукти", "https://www.atbmarket.com/catalog/353-riba-i-moreprodukti"),
        ("Хлібобулочні вироби", "https://www.atbmarket.com/catalog/325-khlibobulochni-virobi"),
        ("Заморожені продукти", "https://www.atbmarket.com/catalog/322-zamorozheni-produkti"),
        ("Ковбаса і м'ясні делікатеси", "https://www.atbmarket.com/catalog/360-kovbasa-i-m-yasni-delikatesi"),
    ]
    
    # Підключення до БД
    db_conn = connect_to_database()
    
    try:
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
        
        # Збереження в CSV (оригінальний функціонал)
        if all_products:
            info_folder = os.path.join(os.path.dirname(__file__), 'info')
            os.makedirs(info_folder, exist_ok=True)
            csv_path = os.path.join(info_folder, 'atb_products.csv')
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['category', 'name', 'price', 'image_url'])
                writer.writeheader()
                writer.writerows(all_products)
            
            print(f"Дані ATB збережено у {csv_path}")
            
    except Exception as e:
        print(f"Критична помилка ATB: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()
        if db_conn:
            db_conn.close()

if __name__ == "__main__":
    main()
