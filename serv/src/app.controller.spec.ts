// app.controller.spec.ts
import { AppController } from './app.controller';
import { ProductService } from './app.service';

describe('AppController', () => {
  let appController: AppController;

  beforeEach(() => {
    const productService = {} as ProductService; // Мок для ProductService
    appController = new AppController(productService);  // Передаем мок
  });

  it('should be defined', () => {
    expect(appController).toBeDefined();
  });
});
