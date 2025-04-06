import { ProductService } from './app.service';
import { IPro, ISilpoPro } from './app.service';
export declare class AppController {
    private readonly productService;
    constructor(productService: ProductService);
    getProductsFromATB(grams: number, name: string, category: string, sortOrder?: 'asc' | 'desc'): Promise<IPro[]>;
    getProductsFromSilpo(grams: number, name: string, category: string, sortOrder?: 'asc' | 'desc'): Promise<ISilpoPro[]>;
    compareProducts(name: string, grams: number, category: string, sortOrder?: 'asc' | 'desc'): Promise<((IPro | ISilpoPro) & {
        pricePerUnit: number;
    })[]>;
}
