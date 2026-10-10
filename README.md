# Bid Engine API

Minimalne API w FastAPI, uruchamiane w Dockerze. Aplikacja korzysta z SQLAlchemy 2, Pydantic 2 i Alembic. W Compose baza to PostgreSQL, zgodnie z konfiguracją aplikacji; SQLite jest dostępne jako lokalny fallback przez `DATABASE_URL`.

## Uruchomienie

```bash
docker compose up --build
```

Aplikacja będzie dostępna pod `http://localhost:8000`. Compose uruchamia również Redis dostępny z hosta pod portem `6380` oraz worker Celery. Wewnątrz sieci Compose Redis nadal nasłuchuje na porcie `6379`. Dokumentacja OpenAPI:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

Migracje uruchamiają się automatycznie przed startem Uvicorna. Kontener aplikacji startuje dopiero po przejściu healthchecka PostgreSQL.

Worker nasłuchuje zadań z Redis. Przykładowe zadanie `app.tasks.ping` można wysłać poleceniem:

```bash
docker compose exec app celery -A app.celery_app:celery_app call app.tasks.ping
```

Worker i API korzystają ze zmiennych `CELERY_BROKER_URL` oraz `CELERY_RESULT_BACKEND`, skonfigurowanych domyślnie na bazach Redis `0` i `1`.

## Przykładowe wywołania

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl -X POST http://localhost:8000/bids \
  -H 'Content-Type: application/json' \
  -d '{"title":"Przykładowa oferta","amount":"125.50"}'
curl http://localhost:8000/bids
```

## Podgląd danych

PostgreSQL działa z trwałym wolumenem `postgres_data`. Dane można podejrzeć przez `psql` w kontenerze:

```bash
docker compose exec db psql -U postgres -d bid_engine -c 'SELECT * FROM bids;'
```

Jeśli potrzebny jest zewnętrzny klient, można później dodać mapowanie portu `5432:5432` w Compose, o ile port jest wolny.

## SQLite lokalnie

Poza Dockerem można użyć SQLite:

```bash
DATABASE_URL=sqlite:///./bid_engine.db alembic upgrade head
DATABASE_URL=sqlite:///./bid_engine.db uvicorn app.main:app --reload
```

Plik `bid_engine.db` można otworzyć np. w rozszerzeniu SQLite dla VS Code albo przez `sqlite3`.
