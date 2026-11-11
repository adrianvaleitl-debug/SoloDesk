# SoloDesk V3.0
**Your business, in one place.**  
**Created by Adrian Vale.**

## What's new in V3.0
- Rebuilt the Windows glass host using colour-key transparency so the acrylic backdrop can show through without fading text or controls.
- Expanded the transparency slider's acrylic tint range and apply timing.
- Moved the accent-colour nebula spotlight onto the transparent host layer.
- Redesigned the in-app release history with a featured latest release and a previous-version timeline.
- Existing customers, invoices, expenses, tasks, documents and settings are preserved.

## Previous release highlights
- **V2.8:** Added persistent Adrian Vale website and Donate · Ko-fi shortcuts.
- **V2.7:** Improved saved accent compatibility and safe fallback handling.
- **V2.6:** Refined global search, spacing and optional accent colours.


## Features
- Business overview with paid income, outstanding invoices, expenses and customer totals.
- Customer directory with searchable contact records, editing and CSV export.
- Invoice creation, editing, payment status and CSV export.
- Expense tracking, editing, supplier records and CSV export.
- Task manager with priorities, completion status and recurrence options.
- Business document library with links to files stored on your computer.
- Analytics summary for paid income, outstanding invoices and expenses.
- Five SoloDesk colour themes: Ocean, Sage, Violet, Coral and Teal.
- Five font choices: Segoe UI, Arial, Verdana, Trebuchet MS and Georgia.
- Bold or regular typography throughout the app.
- Dark, Light and System appearance modes.
- First-launch seven-step quick-start guide, one-time desktop shortcut prompt and in-app What's New release notes.
- Optional Windows startup launch and desktop shortcut create/remove controls.
- Automatic and manual GitHub release checks, automatic installer download and launch, manual database backups and in-app update controls.
- YouTube, TikTok and Ko-fi creator links.

## Creator

- **Adrian Vale — personal website:** https://adrianvaleitl-debug.github.io/
SoloDesk is created by **Adrian Vale**.
- YouTube: https://www.youtube.com/@Adrianvaleitl
- TikTok: https://www.tiktok.com/@adrianvaleitl
- Ko-fi: https://ko-fi.com/marketinsight

## Run from source
Install Python 3.11 or newer, then run:
`python -m pip install -r requirements.txt`
`python solodesk.py`

## Build for Windows
Run `build_windows.bat` on Windows. GitHub Actions builds the Windows installer and portable package on pushes to main and version tags.

## Data and limitations
Windows data is stored in `%LOCALAPPDATA%\\SoloDesk\\solodesk.db`; other platforms use `~/.solodesk/solodesk.db`. Back up regularly. Currency selection changes the displayed symbol only; it does not convert amounts. SoloDesk is not accounting or tax software and does not provide VAT returns, payment processing, cloud sync or legally compliant invoice templates. Document entries link to files at their current local paths.

## Releases and support
- [Latest Windows release](https://github.com/adrianvaleitl-debug/SoloDesk/releases/latest)
- [Website](https://adrianvaleitl-debug.github.io/SoloDesk/)
- [Report a problem](https://github.com/adrianvaleitl-debug/SoloDesk/issues)
