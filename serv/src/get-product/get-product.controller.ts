import { Controller, Get } from '@nestjs/common'; // Добавлен импорт Get
import { GetProductService } from './get-product.service';

@Controller('get-product')
export class GetProductController {
  constructor(private readonly getProductService: GetProductService) {}

  @Get()
  async getAllProducts(): Promise<Array<{ name: string; isDone: boolean }>> {
    // Исправлен возвращаемый тип
    return [
      {
        name: 'daasa',
        isDone: false,
      },
    ];
  }
}
