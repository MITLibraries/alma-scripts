lint: bandit black flake8 isort
	
test: coveralls 

bandit:
	pipenv run bandit -r alma_api_cli

black:
	pipenv run black --check --diff .
	
coveralls: test
	pipenv run coveralls

flake8:
	pipenv run flake8 .

isort:
	pipenv run isort . --diff
	
test:
	pipenv run pytest --cov=alma_api_cli
