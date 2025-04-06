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
import re
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
    """Зберігає список продуктів у базу даних"""
    if not conn:
        print("Відсутнє з'єднання з базою даних.")
        return

    cursor = conn.cursor()

    try:
        # Створення таблиці, якщо вона не існує
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS silpo_products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(255) NOT NULL,
                name VARCHAR(500) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                price_bot DECIMAL(10,2),
                discount VARCHAR(50),
                unit VARCHAR(10),
                quantity DECIMAL(10,3),
                image_url VARCHAR(512),
                is_available BOOLEAN DEFAULT TRUE,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_category (category),
                INDEX idx_price (price),
                INDEX idx_availability (is_available)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)

        insert_query = """
            INSERT INTO silpo_products 
            (category, name, price, price_bot, discount, unit, quantity, image_url, is_available)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        inserted_count = 0

        for product in products:
            try:
                # Конвертація значень до правильних типів з перевіркою
                price = float(product.get('price', '0').replace(' ', '').replace(',', '.'))
                price_bot = product.get('price_bot')
                price_bot = float(price_bot.replace(' ', '').replace(',', '.')) if price_bot else None

                quantity = product.get('quantity')
                quantity = float(quantity) if quantity is not None else None

                values = (
                    product.get('category'),
                    product.get('name'),
                    price,
                    price_bot,
                    product.get('discount'),
                    product.get('unit'),
                    quantity,
                    product.get('image_url'),
                    product.get('is_available', True)
                )

                cursor.execute(insert_query, values)
                inserted_count += 1

            except Exception as inner_e:
                print(f"Не вдалося зберегти товар: {product.get('name')}")
                print(f"Помилка: {inner_e}")
                continue

        conn.commit()
        print(f"Успішно збережено {inserted_count} товарів у базу даних.")

    except Exception as e:
        conn.rollback()
        print("Помилка під час збереження до БД:")
        print(e)
        import traceback
        traceback.print_exc()

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
    """Витяг даних про продукти з урахуванням перевірки ваги"""
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
                price = price.replace(' ', '')[:-3]  # Видаляємо пробіли та "₴"
                
                # Обробка опціональних полів
                price_bot_elem = product_card.find('div', class_='product-card-price__displayOldPrice')
                price_bot = price_bot_elem.get_text(strip=True).replace(' ', '')[:-3] if price_bot_elem else None
                
                discount_elem = product_card.find('div', class_='product-card-price__sale')
                discount = discount_elem.get_text(strip=True) if discount_elem else None
                
                # Удосконалена обробка ваги
                weight_elem = product_card.find('div', class_='ft-typo-14-semibold')
                unit, quantity = None, None
                
                if weight_elem:
                    weight_text = weight_elem.get_text(strip=True)
                    # Регулярний вираз для знаходження ваги (число + одиниця)
                    weight_match = re.match(r'^(\d+[,.]?\d*)\s*([а-яґєіїa-z]*)$', weight_text, re.IGNORECASE)
                    if weight_match:
                        quantity = float(weight_match.group(1).replace(',', '.'))
                        unit = weight_match.group(2).lower() if weight_match.group(2) else None
                
                # Если unit = "шт", ищем вес в названии
                if unit == 'шт' or (unit is None and weight_elem is None):
                    # Ищем в названии паттерны типа "100г", "0.5кг" и т.д.
                    name_weight_match = re.search(r'(\d+[,.]?\d*)\s*(г|кг|мл|л|шт)', name, re.IGNORECASE)
                    if name_weight_match:
                        quantity = float(name_weight_match.group(1).replace(',', '.'))
                        unit = name_weight_match.group(2).lower()
                    else:
                        # Если не нашли в названии, оставляем unit = "шт", quantity = NULL
                        unit = 'шт'
                        quantity = None
                
                img_tag = product_card.find('img', class_='product-card__product-img')
                image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
                if image_url and not image_url.startswith('http'):
                    image_url = f"https://silpo.ua{image_url}"
                
                is_available = product_card.find('div', class_='cart-soldout')
                if is_available == "Товар закінчився":
                    continue
                
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
                print(f"Помилка парсингу товару: {e}")
                continue
                
        print(f"Знайдено товарів на сторінці: {len(extracted)}")
        return extracted
        
    except Exception as e:
        print(f"Помилка витягування товарів: {e}")
        return []

def process_category(driver, base_url, category_name, min_products=47, max_pages=100):
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
