.PHONY: install
install: ## Install the virtual environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync
	@uv run pre-commit install

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Running quality checks via pre-commit hooks"
	@uv run pre-commit run -a

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@uv run python -m pytest --cov --cov-config=pyproject.toml --cov-report=xml

.PHONY: build
build: clean-build ## Build wheel file
	@echo "🚀 Creating wheel file"
	@uvx --from build pyproject-build --installer uv

.PHONY: clean-build
clean-build: ## Clean build artifacts
	@echo "🚀 Removing build artifacts"
	@uv run python -c "import shutil; import os; shutil.rmtree('dist') if os.path.exists('dist') else None"

.PHONY: publish
publish: ## Publish a release to PyPI.
	@echo "🚀 Publishing."
	@uvx twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@uv run mkdocs build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@uv run mkdocs serve

.PHONY: jm
jm: ## Run Jean-Michel CLI (usage: make jm ARGS="list messages")
	@uv run jm $(ARGS)

.PHONY: jm-help
jm-help: ## Show Jean-Michel CLI help
	@uv run jm --help

.PHONY: jm-send
jm-send: ## Send a message (usage: make jm-send MSG="hello")
	@uv run jm send "$(MSG)"

.PHONY: jm-list
jm-list: ## List messages (usage: make jm-list LIMIT=100)
	@uv run jm list messages --limit $(or $(LIMIT),100)

.PHONY: jm-mcp
jm-mcp: ## Run MCP server (usage: make jm-mcp TRANSPORT=stdio HOST=127.0.0.1 PORT=8001)
	@uv run jm mcp --transport $(or $(TRANSPORT),stdio) --host $(or $(HOST),127.0.0.1) --port $(or $(PORT),8001)

.PHONY: api
api: ## Run FastAPI server (usage: make api HOST=127.0.0.1 PORT=<repo-default|override> RELOAD=true)
	@PORT_VALUE="$(or $(PORT),$$(uv run python -c 'from jean_michel.settings import get_default_api_port; print(get_default_api_port())'))"; \
	uv run uvicorn jean_michel.api.app:app --host $(or $(HOST),127.0.0.1) --port $$PORT_VALUE $(if $(filter true,$(RELOAD)),--reload,)

.PHONY: help
help:
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
