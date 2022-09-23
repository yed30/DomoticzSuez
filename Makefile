list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs

flake8: ## Check the code 
	poetry run flake8 .

pylint: ## Lint the code 
# Had to remove somme error classes due to Domoticz python FW
	poetry run pylint plugin.py 

black: ## Run black check
	poetry run black --check  .

help: ## Display Makefile Rules
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

.AFTER :
	%if $(MAKESTATUS) != 0
	%echo Make: The final shell line exited with status: $(status)
	%endif