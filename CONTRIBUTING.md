# Contribution guidelines
Thank you for considering contributing to this project! The following are guidelines you need to follow.

## Code style
To make sure your code style is consistent with project's code style, use [pre-commit](https://pre-commit.com/) which will automatically run formatters and linting tools before any commit:
```bash
pip install -r requirements-dev.txt
pre-commit install
```
If any staged file is reformatted, you need to stage it again. If linting errors are found, you need to fix them before staging again.
