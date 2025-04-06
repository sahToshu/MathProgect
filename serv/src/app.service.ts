import { Injectable } from '@nestjs/common';
import { PrismaService } from './prisma.service';
import { atb_products, silpo_products } from '@prisma/client';

export interface IPro extends atb_products {
  priceforx: number;
  priceforxbot: number;
  x: number;
  store: 'ATB';
}

export interface ISilpoPro extends silpo_products {
  priceforx: number;
  priceforxbot: number;
  x: number;
  store: 'Silpo';
}

type CombinedProduct = (IPro | ISilpoPro) & { pricePerUnit: number };

@Injectable()
export class ProductService {
  constructor(private readonly prisma: PrismaService) {}

  // ATB functions
  private filterATBByName(products: atb_products[], name: string = ''): atb_products[] {
    return products.filter(product => 
      product.name.toLowerCase().includes(name.toLowerCase())
    );
  }

  private filterATBByCategory(products: atb_products[], category: string = ''): atb_products[] {
    return products.filter(product => 
      product.category && product.category.toLowerCase() === category.toLowerCase()
    );
  }

  private async getBaseATBProducts(): Promise<atb_products[]> {
    return this.prisma.atb_products.findMany();
  }

  async getFilteredATBProducts(name?: string, category?: string): Promise<atb_products[]> {
    const products = await this.getBaseATBProducts();
    const filteredByName = this.filterATBByName(products, name || '');
    return this.filterATBByCategory(filteredByName, category || '');
  }

  // Silpo functions
  private filterSilpoByName(products: silpo_products[], name: string = ''): silpo_products[] {
    return products.filter(product => 
      product.name.toLowerCase().includes(name.toLowerCase())
    );
  }

  private filterSilpoByCategory(products: silpo_products[], category: string = ''): silpo_products[] {
    return products.filter(product => 
      product.category && product.category.toLowerCase() === category.toLowerCase()
    );
  }

  private async getBaseSilpoProducts(): Promise<silpo_products[]> {
    return this.prisma.silpo_products.findMany();
  }

  async getFilteredSilpoProducts(name?: string, category?: string): Promise<silpo_products[]> {
    const products = await this.getBaseSilpoProducts();
    const filteredByName = this.filterSilpoByName(products, name || '');
    return this.filterSilpoByCategory(filteredByName, category || '');
  }

  // Common functions
  async calculateATBPriceForGrams(products: atb_products[], grams: number): Promise<IPro[]> {
    return products.map(product => {
      let quantity = 1000
      if (product.unit == "г") {
        quantity = Number(product.quantity);
      }else if (product.unit == "кг" && product.quantity) {
        quantity = Number(product.quantity) * 1000; 
      }
      const price = Number(product.price);
      const price_bot = product.price_bot ? Number(product.price_bot) : 0;

      return {
        ...product,
        priceforx: (price / quantity) * grams,
        priceforxbot: price_bot ? (price_bot / quantity) * grams : 0,
        x: grams,
        store: 'ATB'
      };
    });
  }

  async calculateSilpoPriceForGrams(products: silpo_products[], grams: number): Promise<ISilpoPro[]> {
    return products.map(product => {
      let quantity = product.quantity != null ? product.quantity.toNumber() : 1000;

      if (product.unit === "кг" || product.unit === "л") {
        quantity = product.quantity ? product.quantity.toNumber() * 1000 : 1000;
      } else if (product.unit === "шт") {
        quantity = 1;
      } else if (product.unit === "г") {
        quantity = product.quantity != null ? product.quantity.toNumber() : 1000;
      }

      const price = Number(product.price);
      const price_bot = product.price_bot ? Number(product.price_bot) : 0;

      return {
        ...product,
        priceforx: (price / quantity) * grams,
        priceforxbot: price_bot ? (price_bot / quantity) * grams : 0,
        x: grams,
        store: 'Silpo'
      };
    });
  }

  sortByPrice<T extends { priceforx: number }>(products: T[], sortOrder: 'asc' | 'desc' = 'asc'): T[] {
    return [...products].sort((a, b) => {
      return sortOrder === 'asc' 
        ? a.priceforx - b.priceforx 
        : b.priceforx - a.priceforx;
    });
  }

  // Comparison function
  async compareProducts(
    name: string,
    grams: number = 100,
    category?: string,
    sortOrder: 'asc' | 'desc' = 'asc'
  ): Promise<CombinedProduct[]> {
    // Get products from both stores
    const atbProducts = await this.getFilteredATBProducts(name, category);
    const silpoProducts = await this.getFilteredSilpoProducts(name, category);

    // Calculate prices
    const atbWithPrices = await this.calculateATBPriceForGrams(atbProducts, grams);
    const silpoWithPrices = await this.calculateSilpoPriceForGrams(silpoProducts, grams);

    // Combine and add price per unit for better comparison
    const combined: CombinedProduct[] = [
      ...atbWithPrices.map(p => ({ 
        ...p, 
        pricePerUnit: p.priceforx / grams 
      })),
      ...silpoWithPrices.map(p => ({ 
        ...p, 
        pricePerUnit: p.priceforx / grams 
      }))
    ];

    // Sort by price per unit
    return combined.sort((a, b) => {
      return sortOrder === 'asc' 
        ? a.pricePerUnit - b.pricePerUnit 
        : b.pricePerUnit - a.pricePerUnit;
    });
  }
}
