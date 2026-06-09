# Stage 1: Build.
FROM golang:1.26-alpine AS build
WORKDIR /build
# Copy files.
COPY bot bot
COPY commands commands
COPY default.go .
COPY main.go .
COPY go.mod .
COPY go.sum .
# Get go packages.
RUN go mod download
# Build.
RUN go build -o app

# STAGE 2: Run.
FROM alpine:3 AS run
WORKDIR /app
# Copy build artifacts from Build stage.
COPY --from=build /build/app .
# Run
CMD [ "/app/app" ]
