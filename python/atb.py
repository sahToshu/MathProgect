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
import subprocess
import re
from config import host, user, password, db_name, port

def start_browser():
    """Запускає браузер Edge у режимі віддаленого налагодження"""
    subprocess.Popen([r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe", "--remote-debugging-port=9222"], shell=True)
    time.sleep(3)
    print("🟢 Браузер успішно запущено")

def clear_database(conn):
    """Очищає базу даних перед початком роботи"""
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM atb_products")
            conn.commit()
            print("🗑️ Базу даних очищено")
        except Exception as e:
            conn.rollback()
            print(f"🔴 Помилка очищення бази даних: {e}")
        finally:
            cursor.close()

def connect_to_database():
    """Підключається до бази даних MySQL"""
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            port=port,
        )
        print("🟢 Підключено до бази даних MySQL")
        return conn
    except Exception as e:
        print(f"🔴 Помилка підключення до MySQL: {e}")
        return None

def save_to_database(conn, products):
    """Зберігає товари у базу даних"""
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS atb_products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(500) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                price_bot DECIMAL(10,2),
                discount VARCHAR(50),
                unit VARCHAR(10),
                quantity DECIMAL(10,3),
                image_url VARCHAR(512),
                category VARCHAR(100),
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_category (category),
                INDEX idx_price (price)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        for product in products:
            # Обробка знижки (якщо є)
            discount_text = product.get('discount').get_text(strip=True) if product.get('discount') else None
            # Обробка ціни price_bot (якщо є)
            price_bot = float(product['price_bot']['value']) if product.get('price_bot') and 'value' in product['price_bot'].attrs else None
            
            cursor.execute("""
                INSERT INTO atb_products 
                (name, price, price_bot, discount, unit, quantity, image_url, category)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                product.get('name'),
                product.get('price'),
                price_bot,
                discount_text,
                product.get('unit'),
                product.get('quantity'),
                product.get('image_url'),
                product.get('category')
            ))
        
        conn.commit()
        print(f"💾 Збережено {len(products)} товарів у БД")
    except Exception as e:
        conn.rollback()
        print(f"🔴 Помилка запису в БД: {e}")
        import traceback
        traceback.print_exc()  # Друкуємо повний traceback помилки
    finally:
        cursor.close()

def connect_to_existing_edge():
    """Підключається до вже запущеного браузера Edge"""
    edge_options = Options()
    edge_options.add_experimental_option("debuggerAddress", "localhost:9222")
    try:
        driver = webdriver.Edge(options=edge_options)
        print("🟢 Підключено до існуючого браузера Edge")
        return driver
    except Exception as e:
        print(f"🔴 Помилка підключення до браузера: {e}")
        return None

def human_like_delay(min=1, max=3):
    """Імітує людську затримку між діями"""
    delay = random.uniform(min, max)
    time.sleep(delay)

def extract_weight_and_unit(text):
    """Витягує вагу та одиницю виміру з тексту"""
    weight_match = re.search(r'(\d+[,.]?\d*)\s*([а-яґєіїa-z]{1,3}\b)', text, re.IGNORECASE)
    if weight_match:
        quantity = float(weight_match.group(1).replace(',', '.'))
        unit = weight_match.group(2).lower()
        return quantity, unit
    return None, None

def extract_products(driver):
    """Витягує дані про товари з поточної сторінки"""
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article.catalog-item"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        products = soup.find_all('article', class_='catalog-item')
        extracted = []
        
        for product in products:
            try:
                # Назва товару
                name_tag = product.find('div', class_='catalog-item__title')
                name = name_tag.get_text(strip=True) if name_tag else None
                if not name:
                    continue
                
                # Ціна
                price_data = product.find('data', class_='product-price__top')
                price = float(price_data['value']) if price_data and 'value' in price_data.attrs else None
                if price is None:
                    continue
                # Скидочка
                price_bot = product.find('data', class_='product-price__bottom')
                discount = product.find('span', class_='custom-product-label')
                # Одиниця виміру
                unit_span = product.find('span', class_='product-price__unit')
                unit = unit_span.get_text(strip=True)[1:] if unit_span else None
                
                # Витягуємо вагу/кількість з назви
                quantity, extracted_unit = extract_weight_and_unit(name)
                if extracted_unit:
                    unit = extracted_unit
                elif unit == "шт":
                    quantity = 1
                else:
                    quantity = None
                
                # Зображення
                img_tag = product.find('img', class_='catalog-item__img')
                image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
                if image_url and not image_url.startswith(('http', '//')):
                    image_url = f"https://www.atbmarket.com{image_url}"
                
                extracted.append({
                    'name': name,
                    'price': price,
                    'price_bot': price_bot,
                    'discount': discount,
                    'unit': unit,
                    'quantity': quantity,
                    'image_url': image_url
                })
                
            except Exception as e:
                print(f"⚠️ Помилка парсингу товару: {e}")
                continue
                
        print(f"🔍 Знайдено товарів на сторінці: {len(extracted)}")
        return extracted
        
    except Exception as e:
        print(f"🔴 Помилка витягування товарів: {e}")
        return []

def process_category(driver, base_url, category_name, min_products=36, max_pages=17):
    """Обробляє всі сторінки вказаної категорії"""
    all_products = []
    current_page = 1
    has_next_page = True
    
    while has_next_page and current_page <= max_pages:
        url = f"{base_url}?page={current_page}" if current_page > 1 else base_url
        print(f"\n📄 Обробляємо сторінку {current_page}: {url}")
        
        try:
            driver.get(url)
            human_like_delay(2, 4)
            
            # Обробка підтвердження віку (якщо є)
            try:
                age_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.custom-blue-btn"))
                )
                age_btn.click()
                print("🔞 Підтверджено вік")
                human_like_delay()
            except:
                pass
                
            products = extract_products(driver)
            if not products:
                print("⚠️ Товари не знайдено")
                break
                
            all_products.extend(products)
            
            if len(products) < min_products:
                print(f"⚠️ На сторінці лише {len(products)} товарів")
                break
                
            current_page += 1
            human_like_delay(3, 5)
            
        except Exception as e:
            print(f"🔴 Помилка обробки сторінки: {e}")
            break
    
    for product in all_products:
        product['category'] = category_name
    
    print(f"✅ Всього зібрано товарів у категорії '{category_name}': {len(all_products)}")
    return all_products

def main():
    """Головна функція парсингу"""
    categories = [
        ("Овочі та фрукти", "https://www.atbmarket.com/catalog/287-ovochi-ta-frukti"),
        ("Бакалія", "https://www.atbmarket.com/catalog/285-bakaliya"),
        ("Молочні продукти", "https://www.atbmarket.com/catalog/molocni-produkti-ta-ajca"),
        ("М'ясо", "https://www.atbmarket.com/catalog/maso"),
        ("Сири", "https://www.atbmarket.com/catalog/siri"),
        ("Риба та морепродукти", "https://www.atbmarket.com/catalog/353-riba-i-moreprodukti"),
        ("Хлібобулочні вироби", "https://www.atbmarket.com/catalog/325-khlibobulochni-virobi"),
        ("Заморожені продукти", "https://www.atbmarket.com/catalog/322-zamorozheni-produkti"),
        ("Ковбаси та м'ясні делікатеси", "https://www.atbmarket.com/catalog/360-kovbasa-i-m-yasni-delikatesi"),
    ]
    
    # Підключення до БД
    start_browser()
    db_conn = connect_to_database()
    if db_conn:
        clear_database(db_conn)
    
    driver = connect_to_existing_edge()
    if not driver:
        return
    
    try:
        all_products = []
        
        for category_name, url in categories:
            products = process_category(driver, url, category_name)
            if products:
                all_products.extend(products)
                # Збереження в БД
                if db_conn:
                    save_to_database(db_conn, products)
            
            human_like_delay(5, 8)
        
        # Збереження в CSV
        if all_products:
            info_folder = os.path.join(os.path.dirname(__file__), 'info')
            os.makedirs(info_folder, exist_ok=True)
            csv_path = os.path.join(info_folder, 'atb_products.csv')
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'category', 'name', 'price', 'unit', 
                    'quantity', 'image_url'
                ])
                writer.writeheader()
                writer.writerows(all_products)
            
            print(f"💾 Дані збережено у файл: {csv_path}")
            
    except Exception as e:
        print(f"🔴 Критична помилка: {e}")
    finally:
        driver.quit()
        print("🛑 Браузер закрито")
        if db_conn:
            db_conn.close()
            print("🛑 З'єднання з БД закрито")

if __name__ == "__main__":
    print("🚀 Запуск парсера ATB Market")
    main()
    print("🏁 Роботу завершено")
