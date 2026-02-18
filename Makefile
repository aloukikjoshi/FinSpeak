.PHONY: install run test clean format lint docker-build docker-run

install:
	pip install -r requirements.txt

run:
	streamlit run fin_speak/app.py

test:
	pytest tests/ -v --cov=fin_speak --cov-report=html

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov/

format:
	black fin_speak/ tests/ --line-length 100
	
lint:
	flake8 fin_speak/ tests/ --max-line-length 100 --ignore=E203,W503
	mypy fin_speak/ --ignore-missing-imports

docker-build:
	docker build -t finspeak:latest .

docker-run:
	docker run -p 8501:8501 finspeak:latest

help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies"
	@echo "  run          - Run Streamlit app"
	@echo "  test         - Run tests with coverage"
	@echo "  clean        - Clean up temporary files"
	@echo "  format       - Format code with black"
	@echo "  lint         - Lint code with flake8 and mypy"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"
