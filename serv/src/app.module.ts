// app.module.ts
import { Module } from '@nestjs/common';
import { AppController } from './app.controller'; // Импортируем AppController
import { ProductService } from './app.service'; // Импортируем ProductService из app.service
import { PrismaService } from './prisma.service'; // Импортируем PrismaService

@Module({
  controllers: [AppController], // Только контроллеры в этом списке
  providers: [ProductService, PrismaService], // Сервисы в providers
})
export class AppModule {}
