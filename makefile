.PHONY: all dev
TEMPLATE ?= default

all: dev

dev:
	nix develop -c go build -tags $(TEMPLATE) -o app && ./app
