.PHONY: check test integridade
check: test integridade
test:
	python -m pytest -q
integridade:
	python -m scripts.verificar_integridade
