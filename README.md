# SoloDesk 4.0 — clean rebuild

A focused business workspace by Adrian Vale, rebuilt from a clean React + TypeScript + Tauri 2 foundation. The legacy application UI and Python application code are not carried into this project.

## Core workspace
- Customer records and contact notes
- Invoice register with issue/due dates and payment status
- Expense register and business totals
- Task list with completion state and due dates
- Document index for local file locations and URLs
- Simple business analytics and CSV export
- Full JSON backup export
- Classy blue and Royal gold appearance modes

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

## Data and privacy
Workspace records are stored in the app's local webview storage on this device. The app does not connect to a hosted account or upload your records. Export a JSON backup to keep a separate copy. This is a lightweight business organiser, not accounting or tax software.

## Stack
React 18 · TypeScript · Vite · Tauri 2 · Rust

Website: https://adrianvaleitl-debug.github.io/
