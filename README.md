# E-commerce API (Django)

A **Django-based E-commerce API** with order management, product handling, and stock tracking. Uses **Docker, Docker Compose**, and **PostgreSQL** for easy local development.

---

## Features

- Product CRUD
- Order creation and management
- Order status history tracking
- Automatic stock updates on order creation/cancellation
- Dockerized for development

---

## Project Structure

```
project/
├── project/
├── api/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env
```

---

## Quick Start

1. **Clone repository and set up environment**

```bash
git clone https://github.com/prakashtaz0091/e-commerce-api-task
cd e-commerce-api-task
```

Create a `.env` file:

```env
SECRET_KEY=<your_secret_key>
DEBUG=True
JWT_SIGNING_KEY=<your_jwt_secret_key>


DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

2. **Build and start containers**

```bash
docker-compose up --build -d
```

3. **Generate secret key**

```bash
docker-compose exec web python -c "
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
"
# paste the generated key into the .env file
```

4. **Run migrations**

```bash
docker-compose exec web python manage.py migrate
```

5. **Create superuser**

```bash
docker-compose exec web python manage.py createsuperuser
```

6. **Seed test data (optional)**

```bash
docker-compose exec web python manage.py seed_categories --realistic
docker-compose exec web python manage.py seed_products --realistic
docker-compose exec web python manage.py seed_orders --realistic
docker-compose exec web python manage.py seed_order_history --realistic

# for other commands, look at the `seed_categories`, `seed_products`, and `seed_orders` commands
```

---

## Notes

- API runs at `http://localhost:8000/`
- All management commands run inside the `web` container:

```bash
docker-compose exec web python manage.py <command>
```
