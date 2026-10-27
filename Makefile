SHELL := /bin/bash
TASK := tasks/0001-stealmybitcoin
COMPOSE := docker compose -f $(TASK)/lab/compose.yaml
RUN_ID ?= $(shell date -u +%Y%m%dT%H%M%SZ)
LAB_UID ?= $(shell id -u)
LAB_GID ?= $(shell id -g)
DOCKER_CONFIG ?= $(CURDIR)/.docker
export DOCKER_CONFIG

.PHONY: lab-up lab-down lab-reset lab-status attack logs verify verify-mutation

lab-up:
	$(COMPOSE) up -d --build php nginx telemetry

lab-down:
	$(COMPOSE) down -v --remove-orphans

lab-reset: lab-down lab-up

lab-status:
	$(COMPOSE) ps

attack:
	LAB_UID=$(LAB_UID) LAB_GID=$(LAB_GID) RUN_ID=$(RUN_ID) $(COMPOSE) run --rm attacker

logs:
	$(COMPOSE) logs --no-color

verify:
	python3 $(TASK)/verify/run_verify.py

verify-mutation:
	python3 $(TASK)/verify/run_verify.py --mutation-only
