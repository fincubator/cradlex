# Cradlex

[![License](https://img.shields.io/github/license/fincubator/cradlex)][LICENSE]
[![Dependabot Status](https://api.dependabot.com/badges/status?host=github&repo=fincubator/cradlex)](https://dependabot.com)
[![pre-commit](https://github.com/fincubator/cradlex/workflows/pre-commit/badge.svg)](https://github.com/fincubator/cradlex/actions?query=workflow%3Apre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

[Cradlex](https://t.me/cradlexbot) is an asynchronous ERP Telegram bot for small builder groups.

## Requirements
* [Python](https://www.python.org/) >= 3.9
* [PostgreSQL](https://www.postgresql.org/) - relational database management system
* [asyncpg](https://github.com/MagicStack/asyncpg) - asynchronous PostgreSQL database client library for Python
* [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and Object Relational Mapper for Python
* [Alembic](https://alembic.sqlalchemy.org/) - database migration tool for usage with the SQLAlchemy

## Installation and launch
1. Clone the repository:
```bash
git clone https://github.com/fincubator/cradlex
cd cradlex
```
2. Install Python version no less than 3.9 with [pip](https://pip.pypa.io/en/stable/installing/).
3. Install requirements:
```bash
pip install -r requirements.txt
```
4. Create environment file from example:
```bash
cp .env.example .env
```
5. Personalize settings by modifying ```.env``` with your preferable text editor. Remove ```INTERNAL_HOST``` and ```DATABASE_HOST``` if you want bot and database running on localhost.
6. Create a new Telegram bot by talking to [@BotFather](https://t.me/BotFather) and get its API token.
7. Create a file containing Telegram bot's API token with filename specified in ```TOKEN_FILENAME``` from ```.env``` (example in [secrets/tbtoken](secrets/tbtoken)).
8. Create a file containing database password with filename specified in ```DATABASE_PASSWORD_FILENAME``` from ```.env``` (example in [secrets/dbpassword](secrets/dbpassword)).
9. Install and start [PostgreSQL server](https://www.postgresql.org/download/).
10. Set environment variables:
```bash
export $(sed 's/#.*//' .env | xargs)
```
11. Create database user.
12. Launch Cradlex:
```bash
python -m cradlex
```

## Contributing
You can help by working on opened issues, fixing bugs, creating new features or improving documentation.

Before contributing, please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## License
Cradlex is released under the GNU Affero General Public License v3.0. See [LICENSE] for the full licensing condition.

[LICENSE]: LICENSE
