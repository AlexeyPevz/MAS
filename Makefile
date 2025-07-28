# Makefile для управления проектом Root‑MAS

# Установка зависимостей (предполагается venv)
setup:
	pip install -r requirements.txt

# Запуск Root GroupChat с целью echo
run:
	python run.py --goal "echo"

# Развёртывание внутреннего инстанса MAS (пример)
deploy-internal:
	python -c "from tools.instance_factory import deploy_instance; deploy_instance('deploy/internal', {'POSTGRES_USER':'mas','POSTGRES_PASSWORD':'maspass','MAS_ENDPOINT':'http://localhost:8000'}, 'my_internal_instance', 'internal')"

# Тестирование LLM каскада
test-llm:
	python -c "from tools.llm_selector import pick_config, retry_with_higher_tier; print(pick_config('cheap')); print(retry_with_higher_tier('cheap', 0))"

# Аудит промптов (пример для агента meta)
audit-meta:
	python -c "from tools.prompt_builder import audit_prompt; print(audit_prompt('meta'))"