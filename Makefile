.PHONY: help build up down logs restart clean test

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Construir las imágenes Docker
	docker-compose build

up: ## Levantar los servicios
	docker-compose up -d

down: ## Detener los servicios
	docker-compose down

logs: ## Ver logs de los servicios
	docker-compose logs -f

logs-api: ## Ver logs solo de la API
	docker-compose logs -f api

logs-redis: ## Ver logs solo de Redis
	docker-compose logs -f redis

restart: ## Reiniciar los servicios
	docker-compose restart

restart-api: ## Reiniciar solo la API
	docker-compose restart api

clean: ## Detener y eliminar contenedores, volúmenes e imágenes
	docker-compose down -v --rmi local

rebuild: ## Reconstruir sin caché
	docker-compose build --no-cache

ps: ## Ver estado de los contenedores
	docker-compose ps

exec: ## Ejecutar bash en el contenedor de la API
	docker-compose exec api bash

health: ## Verificar salud de los servicios
	@echo "API Health:"
	@curl -s http://localhost:8000/health | jq . || echo "API no disponible"
	@echo "\nStats:"
	@curl -s http://localhost:8000/api/v1/stats/stats | jq . || echo "Stats no disponible"

dev: ## Levantar en modo desarrollo
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

stop: ## Detener servicios sin eliminar contenedores
	docker-compose stop

start: ## Iniciar servicios detenidos
	docker-compose start
