import { Injectable } from '@nestjs/common';
import { PrismaService } from './prisma.service';
import { atb_products, silpo_products } from '@prisma/client';

/**
 * Типы единиц измерения цены:
 * - per100g - цена за 100 грамм
 * - perKg - цена за килограмм
 * - perPiece - цена за штуку
 * - perCustom - пользовательская единица измерения
 */
export type PriceUnitType = 'per100g' | 'perKg' | 'perPiece' | 'perCustom';

/**
 * Интерфейс данных о цене продукта:
 * - originalPrice - оригинальная строка цены из магазина
 * - numericPrice - числовое значение цены
 * - pricePer100g - цена за 100 грамм (если применимо)
 * - unitType - тип единицы измерения
 */
export interface PriceData {
  originalPrice: string;
  numericPrice: number;
  pricePer100g?: number;
  unitType: PriceUnitType | null;
}

/**
 * Интерфейс продукта ATB с расширенными данными о цене
 */
export interface ProductWithPriceData extends atb_products {
  priceData: PriceData;
}

/**
 * Интерфейс продукта Silpo с расширенными данными о цене
 */
export interface SilpoProductWithPriceData extends silpo_products {
  priceData: PriceData;
}

@Injectable()
export class ProductService {
  constructor(private readonly prisma: PrismaService) {}

  /**
   * Парсит данные о цене из строки цены и названия продукта
   * @param priceString - строка с ценой (например: "89.99 грн/кг")
   * @param productName - название продукта (например: "Молоко 1л")
   * @returns Объект с разобранными данными о цене
   */
  public parseProductPriceData(
    priceString: string,
    productName: string
  ): PriceData {
    // Извлекаем числовое значение цены
    const numericPrice = parseFloat(
      priceString.replace(/[^\d.,]/g, '').replace(',', '.')
    );
  
    const result: PriceData = {
      originalPrice: priceString,
      numericPrice,
      unitType: 'perPiece' // По умолчанию считаем штучным товаром
    };
  
    // Ищем любой вес в формате: /<число>г, /<число>кг и т.д.
    const weightMatch = priceString.match(/\/(\d+[,.]?\d*)\s*(г|грам|грамм|g|кг|kg|мл|ml|л|l)\b/i);
  
    if (weightMatch) {
      const weightValue = parseFloat(weightMatch[1].replace(',', '.'));
      const weightUnit = weightMatch[2].toLowerCase();
  
      // Конвертируем в граммы
      let grams = weightValue;
      if (weightUnit.includes('кг') || weightUnit.includes('kg')) grams = weightValue * 1000;
      if (weightUnit.includes('л') || weightUnit.includes('l')) grams = weightValue * 1000;
  
      if (grams > 0) {
        // Рассчитываем цену за 100г
        result.pricePer100g = (numericPrice * 100) / grams;
        result.unitType = grams === 100 ? 'per100g' : 
                         grams === 1000 ? 'perKg' : 'perCustom';
        return result;
      }
    }
  
    // Если вес не указан в цене, проверяем название
    const nameWeightMatch = productName.match(/(\d+[,.]?\d*)\s*(г|грам|грамм|g|кг|kg|мл|ml|л|l)\b/i);
    if (nameWeightMatch) {
      const weightValue = parseFloat(nameWeightMatch[1].replace(',', '.'));
      const weightUnit = nameWeightMatch[2].toLowerCase();
  
      let grams = weightValue;
      if (weightUnit.includes('кг') || weightUnit.includes('kg')) grams = weightValue * 1000;
  
      if (grams > 0) {
        result.pricePer100g = (numericPrice * 100) / grams;
        result.unitType = grams === 100 ? 'per100g' : 
                         grams === 1000 ? 'perKg' : 'perCustom';
        return result;
      }
    }
  
    // Если явного веса нет, проверяем стандартные форматы
    if (priceString.includes('/100г')) {
      result.pricePer100g = numericPrice;
      result.unitType = 'per100g';
    } else if (priceString.includes('/кг')) {
      result.pricePer100g = numericPrice / 10;
      result.unitType = 'perKg';
    } else {
      // Если не весовой товар
      result.pricePer100g = numericPrice;
      result.unitType = 'perPiece';
    }
  
    return result;
  }

  /**
   * Получает продукты ATB, отсортированные по цене
   * @param direction - направление сортировки (по возрастанию или убыванию)
   * @returns Массив продуктов с данными о цене
   */
  async getSortedATBProducts(direction: 'asc' | 'desc' = 'asc'): Promise<ProductWithPriceData[]> {
    // Получаем все продукты ATB с ненулевыми ценой и названием
    const products = await this.prisma.atb_products.findMany({
      where: {
        price: { not: null },
        name: { not: null }
      }
    });

    // Добавляем разобранные данные о цене и сортируем
    return products
      .map(product => ({
        ...product,
        priceData: this.parseProductPriceData(product.price!, product.name!)
      }))
      .sort((a, b) => {
        // Для сортировки используем цену за 100г или общую цену
        const aPrice = a.priceData.pricePer100g ?? a.priceData.numericPrice;
        const bPrice = b.priceData.pricePer100g ?? b.priceData.numericPrice;
        return direction === 'asc' ? aPrice - bPrice : bPrice - aPrice;
      });
  }

  /**
   * Получает продукты Silpo, отсортированные по цене
   * @param direction - направление сортировки (по возрастанию или убыванию)
   * @returns Массив продуктов с данными о цене
   */
  async getSortedSilpoProducts(direction: 'asc' | 'desc' = 'asc'): Promise<SilpoProductWithPriceData[]> {
    // Аналогично для продуктов Silpo
    const products = await this.prisma.silpo_products.findMany({
      where: {
        price: { not: null },
        name: { not: null }
      }
    });

    return products
      .map(product => ({
        ...product,
        priceData: this.parseProductPriceData(product.price!, product.name!)
      }))
      .sort((a, b) => {
        const aPrice = a.priceData.pricePer100g ?? a.priceData.numericPrice;
        const bPrice = b.priceData.pricePer100g ?? b.priceData.numericPrice;
        return direction === 'asc' ? aPrice - bPrice : bPrice - aPrice;
      });
  }

  /**
   * Получает все продукты (ATB и Silpo), отсортированные по цене
   * @param direction - направление сортировки
   * @returns Объект с двумя массивами: ATB и Silpo продукты
   */
  async getAllSortedProducts(direction: 'asc' | 'desc' = 'asc') {
    // Параллельно получаем продукты обоих магазинов
    const [atb, silpo] = await Promise.all([
      this.getSortedATBProducts(direction),
      this.getSortedSilpoProducts(direction)
    ]);
    
    return { atb, silpo };
  }

  /**
   * Ищет продукты ATB по названию и/или категории
   * @param name - часть названия для поиска
   * @param category - часть категории для поиска
   * @returns Массив найденных продуктов
   /**/

   async findATBProducts(name?: string, category?: string): Promise<atb_products[]> {
    return this.prisma.atb_products.findMany({
      where: {
        name: name ? { contains: name.toLowerCase() } : undefined,
        category: category ? { contains: category.toLowerCase() } : undefined
      }
    });
  }
  
  async findSilpoProducts(name?: string, category?: string): Promise<silpo_products[]> {
    return this.prisma.silpo_products.findMany({
      where: {
        name: name ? { contains: name.toLowerCase() } : undefined,
        category: category ? { contains: category.toLowerCase() } : undefined
      }
    });
  }
  

}
