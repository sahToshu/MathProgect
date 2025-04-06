"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProductService = void 0;
const common_1 = require("@nestjs/common");
const prisma_service_1 = require("./prisma.service");
let ProductService = class ProductService {
    prisma;
    constructor(prisma) {
        this.prisma = prisma;
    }
    filterATBByName(products, name = '') {
        return products.filter(product => product.name.toLowerCase().includes(name.toLowerCase()));
    }
    filterATBByCategory(products, category = '') {
        return products.filter(product => product.category && product.category.toLowerCase() === category.toLowerCase());
    }
    async getBaseATBProducts() {
        return this.prisma.atb_products.findMany();
    }
    async getFilteredATBProducts(name, category) {
        const products = await this.getBaseATBProducts();
        const filteredByName = this.filterATBByName(products, name || '');
        return this.filterATBByCategory(filteredByName, category || '');
    }
    filterSilpoByName(products, name = '') {
        return products.filter(product => product.name.toLowerCase().includes(name.toLowerCase()));
    }
    filterSilpoByCategory(products, category = '') {
        return products.filter(product => product.category && product.category.toLowerCase() === category.toLowerCase());
    }
    async getBaseSilpoProducts() {
        return this.prisma.silpo_products.findMany();
    }
    async getFilteredSilpoProducts(name, category) {
        const products = await this.getBaseSilpoProducts();
        const filteredByName = this.filterSilpoByName(products, name || '');
        return this.filterSilpoByCategory(filteredByName, category || '');
    }
    async calculateATBPriceForGrams(products, grams) {
        return products.map(product => {
            let quantity = 1000;
            if (product.unit == "г") {
                quantity = Number(product.quantity);
            }
            else if (product.unit == "кг" && product.quantity) {
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
    async calculateSilpoPriceForGrams(products, grams) {
        return products.map(product => {
            let quantity = product.quantity != null ? product.quantity.toNumber() : 1000;
            if (product.unit === "кг" || product.unit === "л") {
                quantity = product.quantity ? product.quantity.toNumber() * 1000 : 1000;
            }
            else if (product.unit === "шт") {
                quantity = 1;
            }
            else if (product.unit === "г") {
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
    sortByPrice(products, sortOrder = 'asc') {
        return [...products].sort((a, b) => {
            return sortOrder === 'asc'
                ? a.priceforx - b.priceforx
                : b.priceforx - a.priceforx;
        });
    }
    async compareProducts(name, grams = 100, category, sortOrder = 'asc') {
        const atbProducts = await this.getFilteredATBProducts(name, category);
        const silpoProducts = await this.getFilteredSilpoProducts(name, category);
        const atbWithPrices = await this.calculateATBPriceForGrams(atbProducts, grams);
        const silpoWithPrices = await this.calculateSilpoPriceForGrams(silpoProducts, grams);
        const combined = [
            ...atbWithPrices.map(p => ({
                ...p,
                pricePerUnit: p.priceforx / grams
            })),
            ...silpoWithPrices.map(p => ({
                ...p,
                pricePerUnit: p.priceforx / grams
            }))
        ];
        return combined.sort((a, b) => {
            return sortOrder === 'asc'
                ? a.pricePerUnit - b.pricePerUnit
                : b.pricePerUnit - a.pricePerUnit;
        });
    }
};
exports.ProductService = ProductService;
exports.ProductService = ProductService = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [prisma_service_1.PrismaService])
], ProductService);
//# sourceMappingURL=app.service.js.map