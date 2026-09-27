.PHONY: all dev

all: dev

dev:
	nix develop -c go build -o app
	./app

build:
	docker build -t sem . --no-cache

rebuild:
	docker compose down
	docker build -t sem . --no-cache
	docker compose up -d
