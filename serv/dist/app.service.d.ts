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
type CombinedProduct = (IPro | ISilpoPro) & {
    pricePerUnit: number;
};
export declare class ProductService {
    private readonly prisma;
    constructor(prisma: PrismaService);
    private filterATBByName;
    private filterATBByCategory;
    private getBaseATBProducts;
    getFilteredATBProducts(name?: string, category?: string): Promise<atb_products[]>;
    private filterSilpoByName;
    private filterSilpoByCategory;
    private getBaseSilpoProducts;
    getFilteredSilpoProducts(name?: string, category?: string): Promise<silpo_products[]>;
    calculateATBPriceForGrams(products: atb_products[], grams: number): Promise<IPro[]>;
    calculateSilpoPriceForGrams(products: silpo_products[], grams: number): Promise<ISilpoPro[]>;
    sortByPrice<T extends {
        priceforx: number;
    }>(products: T[], sortOrder?: 'asc' | 'desc'): T[];
    compareProducts(name: string, grams?: number, category?: string, sortOrder?: 'asc' | 'desc'): Promise<CombinedProduct[]>;
}
export {};
