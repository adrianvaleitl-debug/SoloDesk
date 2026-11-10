# SoloDesk V1.2
**Your business, in one place.**

SoloDesk is a local-first Windows desktop organiser for freelancers and small businesses.

## Features
- Business overview with financial summary cards, recent invoices and quick actions
- Customer directory with editing and CSV export
- Invoice creation, payment status and CSV export
- Expense tracking and CSV export
- Task list with priorities and completion state
- Business name and display-currency settings
- SQLite local database and manual backup

## Run from source
Install Python 3.11 or newer, then run `python solodesk.py`. No third-party packages are required.

## Build for Windows
Run `build_windows.bat` on Windows to create a standalone app in `dist\SoloDesk\`. The installer configuration is in `installer.iss`. GitHub Actions can build the installer manually or when a `V*` tag is pushed.

## Data and limitations
Windows data is stored in `%LOCALAPPDATA%\SoloDesk\solodesk.db`; other platforms use `~/.solodesk/solodesk.db`. Back it up regularly. Currency selection changes the displayed symbol only; it does not convert amounts. V1.2 is not accounting or tax software and does not provide VAT returns, payment processing, cloud sync or legally compliant invoice templates. Review invoices and tax records with an appropriate professional.


## Releases and updates

- Download the latest Windows installer from [GitHub Releases](https://github.com/adrianvaleitl-debug/SoloDesk/releases/latest).
- In the app, open **Settings → Check for updates** to open the latest release page.
- GitHub Actions creates build artifacts when run manually. Pushing a version tag such as `V1.2` builds the installer and publishes a GitHub Release automatically.
- Before installing an update, close SoloDesk and back up your database from Settings. The installer does not intentionally remove your local database.

## Project quality and support

Please report reproducible problems through [GitHub Issues](https://github.com/adrianvaleitl-debug/SoloDesk/issues). Do not include customer records, passwords, payment details, or database backups in bug reports.
