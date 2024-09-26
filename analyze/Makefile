OPENTRONS_VERSION ?= edge
export OPENTRONS_VERSION

.PHONY: build-rs
build-rs:
	@echo "Building docker image for opentrons-robot-server:$(OPENTRONS_VERSION)"
	@echo "Cache is always busted to ensure latest version of the code is used"
	@echo "If you want to build a different version, run 'make build-rs OPENTRONS_VERSION=chore_release-8.0.0'"
	docker build --build-arg OPENTRONS_VERSION=$(OPENTRONS_VERSION) --build-arg CACHEBUST=$(CACHEBUST) -t opentrons-robot-server:$(OPENTRONS_VERSION) -f Dockerfile.robot-server .

.PHONY: run-flex
run-flex:
	@echo "Running opentrons-robot-server:$(OPENTRONS_VERSION)"
	@echo "If you want to run a different version, run 'make run-flex OPENTRONS_VERSION=chore_release-8.0.0'"
	docker run -p 31950:31950 --env-file dev-flex.env opentrons-robot-server:$(OPENTRONS_VERSION)

.PHONY: run-ot2
run-ot2:
	@echo "Running opentrons-robot-server:$(OPENTRONS_VERSION)"
	@echo "If you want to run a different version, run 'make run-ot2 OPENTRONS_VERSION=chore_release-8.0.0'"
	docker run -p 31950:31950 --env-file dev-ot2.env opentrons-robot-server:$(OPENTRONS_VERSION)

.PHONY: build-analyze-app
build-analyze-app:
	@echo "Building docker image for opentrons-analyze-app"
	docker build -t opentrons-analyze-app -f Dockerfile.analyze-app .

.PHONY: run-analyze-app
run-analyze-app:
	@echo "Running opentrons-analyze-app"
	docker run -p 5000:5000 opentrons-analyze-app

.PHONY: run
run:
	@echo "Running Flex and OT2 robot-server and Analyze App"
	@echo "If you want to run a different version, run 'make run OPENTRONS_VERSION=chore_release-8.0.0'"
	OPENTRONS_VERSION=$(OPENTRONS_VERSION) docker-compose up --build
