# Ledger 3.9 4.0 — Adrian Vale

A focused business workspace, rebuilt with React, TypeScript and Tauri 2. This is a clean desktop application foundation; the previous Python UI and application implementation are not included.

## Core features
- Customer directory with company and contact details, notes, search, editing and CSV export
- Invoice register with invoice number, customer, dates, amounts and payment status
- Expense register with category, supplier, date and amount
- Business task manager with due dates, priorities, completion and recurring daily, weekly or monthly tasks
- Document index for local file locations and external URLs
- Overview of customers, paid income, outstanding invoices, expenses and tasks
- Analytics for total invoiced, outstanding balances, expenses and net recorded amounts
- Full JSON backup export, per-section CSV export and a confirmed local-data deletion control
- Website-matched Classy blue and Royal gold themes

## Run locally
```bash
npm install
npm run tauri dev
```

## Test and build
```bash
npm test
npm run build
npm run tauri build
```

## Data and limitations
Records are saved in local app storage on this device. No hosted account, payment processor, cloud sync or tax filing service is connected. Export a JSON backup regularly. Ledger is an organiser, not accounting, bookkeeping, tax or legal advice software. Check records and exported information before relying on them.

## Technology
React 18 · TypeScript · Vite · Tauri 2 · Rust

Website: https://adrianvaleitl-debug.github.io/Adrian-Vales-Projects/

## Ledger 3.9.0

- Added a first-launch business-use and data-loss acknowledgement.
- Renamed the product Ledger and introduced a matching royal-gold L app icon.
