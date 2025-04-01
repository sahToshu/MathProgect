import { Module } from '@nestjs/common';
import { ProductController } from './app.controller';
import { ProductService } from './app.service';
import { PrismaService } from './prisma.service';

@Module({
  controllers: [ProductController],
  providers: [ProductService, PrismaService],
})
export class AppModule {}
