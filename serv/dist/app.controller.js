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
var __param = (this && this.__param) || function (paramIndex, decorator) {
    return function (target, key) { decorator(target, key, paramIndex); }
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AppController = void 0;
const common_1 = require("@nestjs/common");
const app_service_1 = require("./app.service");
let AppController = class AppController {
    productService;
    constructor(productService) {
        this.productService = productService;
    }
    async getProductsFromATB(grams, name, category, sortOrder = 'asc') {
        const filteredProducts = await this.productService.getFilteredATBProducts(name, category);
        const withCalculatedPrices = await this.productService.calculateATBPriceForGrams(filteredProducts, grams || 100);
        return this.productService.sortByPrice(withCalculatedPrices, sortOrder);
    }
    async getProductsFromSilpo(grams, name, category, sortOrder = 'asc') {
        const filteredProducts = await this.productService.getFilteredSilpoProducts(name, category);
        const withCalculatedPrices = await this.productService.calculateSilpoPriceForGrams(filteredProducts, grams || 100);
        return this.productService.sortByPrice(withCalculatedPrices, sortOrder);
    }
    async compareProducts(name, grams, category, sortOrder = 'asc') {
        return this.productService.compareProducts(name, grams || 100, category, sortOrder);
    }
};
exports.AppController = AppController;
__decorate([
    (0, common_1.Get)('atb'),
    __param(0, (0, common_1.Query)('grams')),
    __param(1, (0, common_1.Query)('name')),
    __param(2, (0, common_1.Query)('category')),
    __param(3, (0, common_1.Query)('sortOrder')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Number, String, String, String]),
    __metadata("design:returntype", Promise)
], AppController.prototype, "getProductsFromATB", null);
__decorate([
    (0, common_1.Get)('silpo'),
    __param(0, (0, common_1.Query)('grams')),
    __param(1, (0, common_1.Query)('name')),
    __param(2, (0, common_1.Query)('category')),
    __param(3, (0, common_1.Query)('sortOrder')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Number, String, String, String]),
    __metadata("design:returntype", Promise)
], AppController.prototype, "getProductsFromSilpo", null);
__decorate([
    (0, common_1.Get)('compare'),
    __param(0, (0, common_1.Query)('name')),
    __param(1, (0, common_1.Query)('grams')),
    __param(2, (0, common_1.Query)('category')),
    __param(3, (0, common_1.Query)('sortOrder')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, Number, String, String]),
    __metadata("design:returntype", Promise)
], AppController.prototype, "compareProducts", null);
exports.AppController = AppController = __decorate([
    (0, common_1.Controller)('products'),
    __metadata("design:paramtypes", [app_service_1.ProductService])
], AppController);
//# sourceMappingURL=app.controller.js.map