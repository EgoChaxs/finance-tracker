# Finance Tracker

A self-hosted finance tracker intended for personal or family use on a private network.  
It provides a simple web interface for manually tracking transactions, budgets, categories, savings goals, and contributions across multiple users,  
without trying to enforce how users should manage their money.

The project is designed around a simple principle:  
> Store facts, calculate statistics.

## Features

* Multiple users
* Access-key based authentication
* Income and expense tracking
* Custom transaction categories
* Monthly budgets
* Personal and shared savings goals
* Goal contributions
* SQLite database
* Database migrations with Alembic
* Responsive web interface
* Optional systemd service for always-on Linux installations

## Tech Stack

### Backend

* Python
* Flask
* SQLAlchemy
* Alembic
* SQLite
* Argon2 password hashing

### Frontend

* HTML
* CSS
* JavaScript

### Testing

* pytest
* pytest-cov

## Requirements

* Python 3.12 or newer
* Git

Linux is the primary target environment, although the application can also be run on other platforms supported by Python.

## Installation

Clone the repository:

```bash
git clone https://github.com/EgoChaxs/finance-tracker
cd finance-tracker
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Install the project:

```bash
pip install -e .
```

For development, including the test dependencies:

```bash
pip install -e ".[dev]"
```

## Running Finance Tracker

Make the startup script executable (you can skip this on Windows):

```bash
chmod +x start.sh
```

Then run:

```bash
./start.sh
```
*Use the `start.ps1` script on Windows.*

The startup script:

1. Creates the `data/` directory if it does not already exist.
2. Applies pending Alembic database migrations.
3. Starts the finance tracker.

By default, the application is available on port `5000`.

For example:

```text
http://localhost:5000
```

From another device on the same network, use the server's local IP address:

```text
http://SERVER_IP:5000
```

## Creating Users

Users are created through the provided user creation utility:

```bash
python -m src.create_user
```

Follow the prompts to create the user and their access key.

Access keys are not recoverable from the database because only their Argon2 hashes are stored.

If users are unlikely to retain their own access keys, store a recovery copy somewhere appropriately protected and separate from the application database and repository.

## Database

**Finance Tracker** uses SQLite.

The database is stored under:

```text
data/finance_tracker.db
```

Database schema changes are managed through Alembic.

To manually apply migrations:

```bash
python -m alembic upgrade head
```

The **start** scripts also apply pending migrations automatically before starting the application.

## Running Tests

Install the development dependencies:

```bash
pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest
```

Run the tests with coverage:

```bash
pytest --cov
```

## Running with systemd

An example systemd service is included in:

```text
deploy/finance-tracker.service
```

The service is optional. Finance Tracker does not depend on systemd and may be run using any suitable process manager.  
Before installing the service, edit it and replace the example username and paths with those used on your server.

Copy it to the systemd service directory:

```bash
sudo cp deploy/finance-tracker.service /etc/systemd/system/finance-tracker.service
```

Reload systemd and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now finance-tracker.service
```

Check its status:

```bash
systemctl status finance-tracker.service
```

View logs:

```bash
journalctl -u finance-tracker.service -f
```

Restart:

```bash
sudo systemctl restart finance-tracker.service
```

## Updating

Pull the latest changes:

```bash
git pull
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

Update the installed project and dependencies:

```bash
pip install -e .
```

Apply any new database migrations:

```bash
python -m alembic upgrade head
```

If **Finance Tracker** is running through systemd:

```bash
sudo systemctl restart finance-tracker.service
```

When using the provided startup script through systemd, pending migrations are also applied automatically when the service starts.

## Security

Primarily intended for use on a trusted private network.  
User access keys are hashed using Argon2, and authentication sessions are stored separately from the raw session tokens.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
