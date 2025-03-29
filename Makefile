PROJECT_NAME = openwebui-knowledge-sync
CONTAINER_NAME = $(PROJECT_NAME)-container
IMAGE_NAME = $(PROJECT_NAME)-image

# Build Docker image
build:
	docker build -t $(IMAGE_NAME) .

# Run container with restart policy
run: build
	docker run -d \
		--name $(CONTAINER_NAME) \
		--restart always \
		--env-file .env \
		--network host \
		$(IMAGE_NAME)

# Stop and remove container
stop:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

# Restart container
restart: stop run

# View container logs
logs:
	docker logs -f $(CONTAINER_NAME)

# Clean up Docker resources
clean: stop
	docker rmi $(IMAGE_NAME) || true
	docker system prune -f

# Check container status
status:
	docker ps -a | grep $(CONTAINER_NAME)

# Default target
.PHONY: all
all: build run