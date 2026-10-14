IMAGE ?= registry.internal.example/ai/daily-ai-briefing
TAG ?= $(shell git rev-parse --short HEAD)

.PHONY: image push

image:
	docker build --tag $(IMAGE):$(TAG) .

push: image
	docker push $(IMAGE):$(TAG)
