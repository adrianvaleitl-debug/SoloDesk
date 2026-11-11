# SoloDesk V2.8
**Your business, in one place.**  
**Created by Adrian Vale.**

## What's new in V2.8
- Persistent sidebar shortcuts to the Adrian Vale website and Donate · Ko-fi.
- Accent-colour blurred spotlight and responsive acrylic transparency.
- **Startup crash fixed:** corrected the invalid Euro accent-theme fallback that could stop SoloDesk opening.
- **Safer accent settings:** missing or outdated saved accent values now fall back safely to Black.
- **Accent choices retained:** Black, Amber, Azure, Lavender, Rose and Teal remain available.
- Existing customers, invoices, expenses, tasks and other local business data are preserved.

## What's new in V2.6
- **Compact global search:** reduced the search control so its icon and field fit cleanly inside the top bar.
- **Six optional accent choices:** Black remains the default while charcoal glass surfaces stay neutral.
- **Clearer spacing:** refined text, controls and panel borders to avoid collisions.


**Your business, in one place.**  
**Created by Adrian Vale.**

SoloDesk is a local-first Windows desktop workspace for freelancers and small businesses.
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
