[![Foodgram workflow](https://github.com/LittleVyach/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/LittleVyach/foodgram/actions/workflows/main.yml)


# Foodgram (<<Продуктовый помощник>>)
Онлайн сервис для публикации рецептов, поиска кулинарного вдохновения и автоматического формирования списка покупок для похода в магазин.

## Технологии и стек:
<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/DRF-092E20?style=for-the-badge&logo=django&logoColor=white" alt="DRF">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white" alt="Nginx">
  <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white" alt="GitHub Actions">
  <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React">
</p>

## Основные возможности:
Рецепты: Создание, редактирования, просмотр и удаление.
Интерактив: Добавление рецептов в Избранное.
Список покупок: Возможность собрать ингредиенты из выбранных рецептов в один список и выгрузить/скачать его.
Теги: Фильтрация рецептов по тегам.
Безопасность: Система JWT-Токенов

## Локальный запуск проекта:
Чтобы развернуть проект на локальном компьютере, выполните следующие шаги:

1. Клонируйте репозиторий:
```
git clone https://github.com/LittleVyach/foodgram.git
cd foodgram
```
2. Создайте файл .env.
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=your_password
DB_HOST=db
DB_PORT=5432
SECRET_KEY='ваш_секретный_ключ_django'
DEBUG=False
ALLOWED_HOSTS=127.0.0.1, localhost
```
3. Запустите контейнеры через Docker Compose:
```
docker compose up -d --build
```
4. Выполните миграции и соберите статику:
```
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --no-input
```
## Деплой на удаленный сервер.
1. Проверяет код линтером.
2. Собирает и публикует Docker образы.
3. Автоматически подключается к удаленному серверу.

## Примеры API-запросов:
1 Получение списка рецептов:
* **URL:** /api/recipes/
* **Метод:** GET
* **Описание:** Возвращает пагинированный список всех рецептов.
* **Пример ответа (200 OK):**
```
{
  "count": 15,
  "next": "http://localhost/api/recipes/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "tags": [
        {
          "id": 1,
          "name": "Завтрак",
          "color": "#E26C2D",
          "slug": "breakfast"
        }
      ],
      "author": {
        "email": "chef@foodgram.ru",
        "id": 1,
        "username": "SuperChef",
        "first_name": "Иван",
        "last_name": "Иванов"
      },
      "ingredients": [
        {
          "id": 42,
          "name": "Яйцо куриное",
          "measurement_unit": "шт.",
          "amount": 2
        }
      ],
      "is_favorited": false,
      "is_in_shopping_cart": false,
      "name": "Омлет классический",
      "image": "http://localhost/media/recipes/omlet.jpg",
      "text": "Взбить яйца с молоком и вылить на разогретую сковороду...",
      "cooking_time": 15
    }
  ]
}
```
2 Добавление рецепта в избранное:
* **URL:** /api/recipes/1/favorite/
* **Метод:** POST
* **Описание:** Добавляет рецепт с id=1 в список избранного текущего пользователя.
* **Пример ответа (201 Created):**
```
{
  "id": 1,
  "name": "Омлет классический",
  "image": "http://localhost/media/recipes/omlet.jpg",
  "cooking_time": 15
}
```


