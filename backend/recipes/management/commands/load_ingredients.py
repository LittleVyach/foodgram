import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из CSV-файла в базу данных'

    def handle(self, *args, **options):

        file_path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.csv')

        try:
            with open(file_path, encoding='utf-8') as f:
                reader = csv.reader(f)
                count = 0
                for row in reader:
                    if len(row) >= 2:
                        Ingredient.objects.get_or_create(
                            name=row[0],
                            measurement_unit=row[1]
                        )
                        count += 1
            self.stdout.write(self.style.SUCCESS(
                f'Успешно загружено ингредиентов: {count}'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                f'Файл не найден по пути: {file_path}'))
