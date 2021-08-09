lint: bandit black flake8 isort

bandit:
	pipenv run bandit -r llama

black:
	pipenv run black --check --diff llama tests

coveralls: test
	pipenv run coveralls

flake8:
	pipenv run flake8 llama tests

isort:
	pipenv run isort llama tests --diff

test:
	pipenv run pytest --cov=llama
