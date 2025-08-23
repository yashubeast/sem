build:
	docker build -t sem . --no-cache

prod:
	docker build -t yashubeast/nerv:sem . --no-cache

push:
	docker push yashubeast/nerv:sem