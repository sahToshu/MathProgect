import { Controller, Get, Query } from '@nestjs/common';
import { ProductService } from './app.service';
import { IPro, ISilpoPro } from './app.service';

@Controller('products')
export class AppController {
  constructor(private readonly productService: ProductService) {}

  @Get('atb')
  async getProductsFromATB(
    @Query('grams') grams: number,
    @Query('name') name: string,
    @Query('category') category: string,
    @Query('sortOrder') sortOrder: 'asc' | 'desc' = 'asc',
  ): Promise<IPro[]> {
    const filteredProducts = await this.productService.getFilteredATBProducts(name, category);
    const withCalculatedPrices = await this.productService.calculateATBPriceForGrams(filteredProducts, grams || 100);
    return this.productService.sortByPrice(withCalculatedPrices, sortOrder);
  }

  @Get('silpo')
  async getProductsFromSilpo(
    @Query('grams') grams: number,
    @Query('name') name: string,
    @Query('category') category: string,
    @Query('sortOrder') sortOrder: 'asc' | 'desc' = 'asc',
  ): Promise<ISilpoPro[]> {
    const filteredProducts = await this.productService.getFilteredSilpoProducts(name, category);
    const withCalculatedPrices = await this.productService.calculateSilpoPriceForGrams(filteredProducts, grams || 100);
    return this.productService.sortByPrice(withCalculatedPrices, sortOrder);
  }

  @Get('compare')
  async compareProducts(
    @Query('name') name: string,
    @Query('grams') grams: number,
    @Query('category') category: string,
    @Query('sortOrder') sortOrder: 'asc' | 'desc' = 'asc',
  ) {
    return this.productService.compareProducts(name, grams || 100, category, sortOrder);
  }
}
