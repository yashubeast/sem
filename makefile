.PHONY: all dev

all: dev

dev:
	nix develop -c go build -o app
	./app
