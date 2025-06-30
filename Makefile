include custom.mk

# Set the user and group IDs in docker compose to the same as the host user so new files belong to the host user
# instead of root.
# This can be changed to your own user/group ID here, though these defaults should be fine for most people.
export MY_UID := 1000
export MY_GID := 1000

setup-env:
	@[ ! -f ./.env ] && cp ./.env.example ./.env || echo ".env file already exists."

start: ## Start the docker containers
	@echo "Starting the docker containers"
	@docker compose up

stop: ## Stop Containers
	@docker compose down

restart: stop start ## Restart Containers

start-bg:  ## Run containers in the background
	@docker compose up -d

build: ## Build Containers
	@docker compose build

ssh: ## SSH into running web container
	docker compose exec web bash

bash: ## Get a bash shell into the web container
	docker compose run --rm --no-deps web bash

manage: ## Run any manage.py command. E.g. `make manage ARGS='createsuperuser'`
	@docker compose run --rm web python manage.py ${ARGS}

migrations: ## Create DB migrations in the container
	@docker compose run --rm web python manage.py makemigrations

migrate: ## Run DB migrations in the container
	@docker compose run --rm web python manage.py migrate

set-defaults: ## Set the default settings
	@docker compose run --rm web python manage.py initial_setup --domain=localhost:8000 --name='ISP Billing'

set-defaults-production: ## Set the default settings
	@docker compose run --rm web python manage.py initial_setup --domain=billing.example.com --name='ISP Billing'

shell: ## Get a Django shell
	@docker compose run --rm web python manage.py shell

dbshell: ## Get a Database shell
	@docker compose exec db psql -U postgres isp_billing_system

test: ## Run Django tests
	@docker compose run --rm web python manage.py test ${ARGS}

init: setup-env start-bg migrations migrate set-defaults  ## Quickly get up and running (start containers and bootstrap DB and front end)

pip_compile_cmd = uv pip compile --no-strip-extras
pip-compile: ## Compiles your requirements.in file to requirements.txt
	@docker compose run --rm --no-deps web $(pip_compile_cmd) requirements/requirements.in -o requirements/requirements.txt
	@docker compose run --rm --no-deps web $(pip_compile_cmd) requirements/dev-requirements.in -o requirements/dev-requirements.txt
	@docker compose run --rm --no-deps web $(pip_compile_cmd) requirements/prod-requirements.in -o requirements/prod-requirements.txt

requirements: pip-compile build stop start-bg  ## Rebuild your requirements and restart your containers

ruff-format: ## Runs ruff formatter on the codebase
	@docker compose run --rm --no-deps web ruff format .

ruff-lint:  ## Runs ruff linter on the codebase
	@docker compose run --rm --no-deps web ruff check --fix  .

format: ruff-format ruff-lint ## Formatting and linting using Ruff

npm-install: ## Runs npm install in the container
	@docker compose run --rm --no-deps vite npm install $(filter-out $@,$(MAKECMDGOALS))

npm-uninstall: ## Runs npm uninstall in the container
	@docker compose run --rm --no-deps vite npm uninstall $(filter-out $@,$(MAKECMDGOALS))

npm-build: ## Runs npm build in the container (for production assets)
	@docker compose run --rm --no-deps vite npm run build

npm-dev: ## Runs npm dev in the container
	@docker compose run --rm --no-deps vite npm run dev

npm-type-check: ## Runs the type checker on the front end TypeScript code
	@docker compose run --rm --no-deps vite npm run type-check

upgrade: requirements migrations migrate npm-install npm-dev  ## Run after a Pegasus upgrade to update requirements, migrate the database, and rebuild the front end

build-api-client:  ## Update the JavaScript API client code.
	@docker run --rm --network host -v $(shell pwd)/api-client:/local openapitools/openapi-generator-cli:v7.9.0 generate \
	-i http://localhost:8000/api/schema/ \
	-g typescript-fetch \
	-o /local/

.PHONY: help
.DEFAULT_GOAL := help

help:
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# catch-all for any undefined targets - this prevents error messages
# when running things like make npm-install <package>
%:
	@:
