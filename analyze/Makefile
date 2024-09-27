OPENTRONS_VERSION ?= release
export OPENTRONS_VERSION

.PHONY: build
build:
	@echo "Building docker image for opentrons-robot-server:$(OPENTRONS_VERSION)"
	@echo "Cache is always busted to ensure latest version of the code is used"
	@echo "If you want to build a different version, run 'make build OPENTRONS_VERSION=chore_release-8.0.0'"
	@echo
	docker build --build-arg OPENTRONS_VERSION=$(OPENTRONS_VERSION) --build-arg CACHEBUST=$(shell date +%s) -t opentrons-base:$(OPENTRONS_VERSION) -f Dockerfile.base .
	docker build --build-arg OPENTRONS_VERSION=$(OPENTRONS_VERSION) -t opentrons-robot-server:$(OPENTRONS_VERSION) -f Dockerfile.robot-server .

.PHONY: run-flex
run-flex:
	@echo "Running opentrons-robot-server:$(OPENTRONS_VERSION)"
	@echo
	@echo "Hope you 'make build' first!!!!!"
	@echo
	@echo "If you want to run a different version, run 'make run-flex OPENTRONS_VERSION=chore_release-8.0.0'"
	@echo
	docker run -p 31950:31950 --env-file dev-flex.env opentrons-robot-server:$(OPENTRONS_VERSION)

.PHONY: run-ot2
run-ot2:
	@echo "Running opentrons-robot-server:$(OPENTRONS_VERSION)"
	@echo
	@echo "Hope you 'make build' first!!!!!"
	@echo
	@echo "If you want to run a different version, run 'make run-ot2 OPENTRONS_VERSION=chore_release-8.0.0'"
	@echo
	docker run -p 31950:31950 --env-file dev-ot2.env opentrons-robot-server:$(OPENTRONS_VERSION)
