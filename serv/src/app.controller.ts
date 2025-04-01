import { Controller, Get, Query } from '@nestjs/common';
import { 
  ProductService,
  ProductWithPriceData,
  SilpoProductWithPriceData 
} from './app.service';

@Controller('products')
export class ProductController {
  constructor(private readonly productService: ProductService) {}

  /**
   * Получает отсортированные продукты ATB с возможностью фильтрации
   * @param direction - направление сортировки по цене
   * @param name - часть названия для поиска (не строгое соответствие)
   * @param category - часть категории для поиска (не строгое соответствие)
   */
  @Get('atb/sorted')
  async getSortedATBProducts(
    @Query('direction') direction: 'asc' | 'desc' = 'asc',
    @Query('name') name?: string,
    @Query('category') category?: string
  ): Promise<ProductWithPriceData[]> {
    // Сначала фильтруем по названию и категории
    const filtered = await this.productService.findATBProducts(name, category);
    // Затем добавляем расчет цены и сортируем
    return filtered
      .filter(p => p.price && p.name) // Фильтруем продукты с ценой и названием
      .map(p => ({
        ...p,
        priceData: this.productService.parseProductPriceData(p.price!, p.name!)
      }))
      .sort((a, b) => {
        const aPrice = a.priceData.pricePer100g ?? a.priceData.numericPrice;
        const bPrice = b.priceData.pricePer100g ?? b.priceData.numericPrice;
        return direction === 'asc' ? aPrice - bPrice : bPrice - aPrice;
      });
  }

  /**
   * Получает отсортированные продукты Silpo с возможностью фильтрации
   * @param direction - направление сортировки по цене
   * @param name - часть названия для поиска (не строгое соответствие)
   * @param category - часть категории для поиска (не строгое соответствие)
   */
  @Get('silpo/sorted')
  async getSortedSilpoProducts(
    @Query('direction') direction: 'asc' | 'desc' = 'asc',
    @Query('name') name?: string,
    @Query('category') category?: string
  ): Promise<SilpoProductWithPriceData[]> {
    const filtered = await this.productService.findSilpoProducts(name, category);
    return filtered
      .filter(p => p.price && p.name)
      .map(p => ({
        ...p,
        priceData: this.productService.parseProductPriceData(p.price!, p.name!)
      }))
      .sort((a, b) => {
        const aPrice = a.priceData.pricePer100g ?? a.priceData.numericPrice;
        const bPrice = b.priceData.pricePer100g ?? b.priceData.numericPrice;
        return direction === 'asc' ? aPrice - bPrice : bPrice - aPrice;
      });
  }

  /**
   * Получает все отсортированные продукты с возможностью фильтрации
   * @param direction - направление сортировки по цене
   * @param name - часть названия для поиска (не строгое соответствие)
   * @param category - часть категории для поиска (не строгое соответствие)
   */
  @Get('all/sorted')
  async getAllSortedProducts(
    @Query('direction') direction: 'asc' | 'desc' = 'asc',
    @Query('name') name?: string,
    @Query('category') category?: string
  ): Promise<{
    atb: ProductWithPriceData[];
    silpo: SilpoProductWithPriceData[];
  }> {
    const [atb, silpo] = await Promise.all([
      this.getSortedATBProducts(direction, name, category),
      this.getSortedSilpoProducts(direction, name, category)
    ]);
    return { atb, silpo };
  }

  // Оригинальные методы поиска без сортировки
  @Get('atb')
  async getATBProducts(
    @Query('name') name?: string,
    @Query('category') category?: string
  ) {
    return this.productService.findATBProducts(name, category);
  }

  @Get('silpo')
  async getSilpoProducts(
    @Query('name') name?: string,
    @Query('category') category?: string
  ) {
    return this.productService.findSilpoProducts(name, category);
  }
}
