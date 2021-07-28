linting: bandit black flake8 isort
	
testing: coveralls pytest

bandit:
	pipenv run bandit -r alma_api_cli

black:
	pipenv run black --check --diff .
	
coveralls: 
	pipenv run coveralls

flake8:
	pipenv run flake8 .

isort:
	pipenv run isort . --diff
	
pytest:
	pipenv run pytest
