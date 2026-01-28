NOW = $(shell date --utc +%FT%H%M%SZ)
ROOT := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
TOOLS ?= $(ROOT)/tools
PLANS ?= $(ROOT)/.plans

invoke: .env
	poetry run -- $(TOOLS)/lambda reconfigure
	poetry run -- $(TOOLS)/lambda invoke

.env:
	poetry run -- $(TOOLS)/lambda env >$@

deps.zip: pyproject.toml poetry.lock
	$(TOOLS)/bundle $@

app.zip: FORCE
	$(TOOLS)/bundle $@

install:
	pipx install --force ".[cli]"

plan: $(PLANS) .terraform.flag deps.zip app.zip
	terraform plan -out $(PLANS)/plan-$(NOW)
	echo -n "terraform apply $(PLANS)/plan-$(NOW)" | xclip

destroy: $(PLANS) .terraform.flag
	terraform plan -destroy -out "$(PLANS)/destroy-$(NOW)"
	echo -n "terraform apply $(PLANS)/destroy-$(NOW)" | xclip

$(PLANS):
	@mkdir -p "$@"

init: .terraform.flag .poetry.flag
.terraform.flag:
	terraform init
	touch "$@"

poetry.lock .poetry.flag:
	poetry install -E cli
	touch "$@"

reinit:
	rm -f .*.flag
	$(MAKE) init

update:
	terraform init -upgrade && touch .terraform.flag
	poetry update && touch .poetry.flag

clean:
	rm -f deps.zip app.zip
	rm -f src/schema/{terraform.py,build_info.py}
	rm -rf "$(PLANS)"

deepclean: clean
	rm -rf .venv
	rm -rf .terraform

FORCE:
.PHONY: invoke call
.PHONY: install
.PHONY: init update reinit
.PHONY: plan destroy
.PHONY: clean deepclean
