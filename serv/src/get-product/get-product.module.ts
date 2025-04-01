import { Module } from '@nestjs/common';
import { GetProductService } from './get-product.service';
import { GetProductController } from './get-product.controller';
import { PrismaService } from 'src/prisma.service';

@Module({
  controllers: [GetProductController],
  providers: [GetProductService, PrismaService],
})
export class GetProductModule {}
