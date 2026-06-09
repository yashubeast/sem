.PHONY: all dev
TEMPLATE ?= default
TARGET_FILE := ./default.go
BUILD_TAR := //go:build default

all: dev

dev:
	@sed -i '1s/^/\/\/ go:build $(TEMPLATE)\n\n/' $(TARGET_FILE)
	nix develop -c go build -tags $(TEMPLATE) -o app
	@sed -i '1,2d' $(TARGET_FILE)
	./app
