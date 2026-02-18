# Contributing to FinSpeak

Thank you for your interest in contributing to FinSpeak! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/aloukikjoshi/FinSpeak.git
   cd FinSpeak
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys if needed
   ```

## Running Tests

Run the full test suite:
```bash
make test
```

Or use pytest directly:
```bash
pytest tests/ -v
```

Run tests with coverage:
```bash
pytest tests/ -v --cov=fin_speak --cov-report=html
```

## Code Formatting

We use `black` for code formatting and `flake8` for linting.

**Format code:**
```bash
make format
```

**Lint code:**
```bash
make lint
```

**Manual formatting:**
```bash
black fin_speak/ tests/ --line-length 100
flake8 fin_speak/ tests/ --max-line-length 100 --ignore=E203,W503
```

## Type Checking

We use `mypy` for type checking:
```bash
mypy fin_speak/ --ignore-missing-imports
```

## Running the Application

**Local development:**
```bash
make run
# or
streamlit run fin_speak/app.py
```

**Using Docker:**
```bash
make docker-build
make docker-run
```

## Project Structure

```
FinSpeak/
├── fin_speak/          # Main package
│   ├── __init__.py
│   ├── app.py          # Streamlit application
│   ├── config.py       # Configuration
│   ├── stt.py          # Speech-to-text
│   ├── nlp.py          # NLP and intent detection
│   ├── kb.py           # Knowledge base
│   └── tts.py          # Text-to-speech
├── tests/              # Test suite
├── notebooks/          # Jupyter notebooks
├── data/               # Sample data
└── demo_assets/        # Demo audio files
```

## Adding New Features

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Add type hints
   - Follow existing code style

3. **Add tests**
   - Write unit tests for new functionality
   - Ensure all tests pass

4. **Update documentation**
   - Update README.md if needed
   - Add docstrings to new functions

5. **Submit a pull request**
   - Provide a clear description
   - Reference any related issues

## Code Style Guidelines

- Follow PEP 8 style guide
- Use type hints for function signatures
- Write descriptive docstrings (Google style)
- Keep functions focused and modular
- Add comments for complex logic
- Maximum line length: 100 characters

## Example Function Template

```python
def example_function(param1: str, param2: int) -> Dict[str, any]:
    """
    Brief description of function
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Dictionary containing results
        
    Raises:
        ValueError: If param2 is negative
    """
    if param2 < 0:
        raise ValueError("param2 must be non-negative")
    
    # Implementation
    result = {"key": "value"}
    return result
```

## Testing Guidelines

- Write tests for all new functions
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies (APIs, file I/O)
- Aim for >80% code coverage

## Reporting Issues

When reporting bugs, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/stack traces
- Screenshots if applicable

## Questions?

Feel free to open an issue for:
- Bug reports
- Feature requests
- Documentation improvements
- General questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
