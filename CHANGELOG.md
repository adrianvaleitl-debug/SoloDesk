# Changelog

## V2.9 — 11 November 2026
- Fixed accent-colour spotlight rendering with a multi-layer, softly blurred nebula effect that redraws on resize.
- Improved Windows 11 acrylic/transient backdrop handling and retained a legacy acrylic fallback.
- Kept the app content crisp by avoiding whole-window opacity changes for transparency adjustments.
- Deferred fragile accent refresh work so theme changes do not immediately tear down the interface.
- Preserved existing business records, settings and workflows.

## V2.8 — 11 November 2026
- Added persistent Adrian Vale website and Donate · Ko-fi links to the desktop sidebar.
- Added a soft, blurred spotlight that follows the selected accent colour.
- Reapplied Windows acrylic blur whenever the transparency slider changes.
- Kept existing business records, settings and workflows intact.


## V2.7 — 11 November 2026
- Fixed a startup crash caused by an invalid fallback accent-theme lookup (`KeyError: 'Euro'`).
- Made accent colour lookup safely fall back to Black when a saved theme is missing or invalid.
- Kept existing saved business data and the six accent choices intact.


## V2.6 — 11 November 2026
- Made global search more compact to prevent the search icon and field from colliding with the surrounding outline.
- Restored six optional accent choices, with Black as the default while retaining neutral dark glass surfaces.
- Refined spacing around text, controls and panel borders for clearer layouts.


## V1.4 — 11 November 2026
- Introduced a dedicated SoloDesk icon for the app, installer, taskbar, website and desktop shortcuts.
- Established an independent navy-and-blue interface identity rather than copying Market Insight's green theme.
- Added five new colour themes: Ocean, Sage, Violet, Coral and Teal, while migrating existing saved theme choices.
- Improved automatic updates so the app can download and launch the latest Windows installer after user confirmation.
- Updated the website so its download buttons follow the latest Windows installer automatically.
- Added a first-run desktop shortcut prompt and branded shortcut icon.
- Updated the Windows installer and build process to package the new icon assets.

## V1.3 — 10 November 2026
- Rebuilt the desktop interface around a shared quality standard with Market Insight: rounded cards and controls, consistent spacing and bold typography, with its own product layout.
- Added five colour themes, five font families, bold/regular text and Dark, Light and System appearance modes.
- Added searchable customer, invoice, expense, task and document workspaces.
- Added document links, a business analytics view, first-launch quick-start guide and in-app What's New page.
- Added creator links and project support links in the app and website.
- Rebuilt the website to match the app's visual identity and added creator attribution.

## V1.2 — 10 November 2026
- Added invoice and expense editing, improved dashboard summary and refreshed the product website.
- Refined the Windows build and release workflow.

## V1.1 — 10 November 2026
- Refreshed the desktop interface and added invoice and expense editing.
- Improved Windows packaging and portable builds.

## V1.0
- Initial local-first business organiser release.
- Customer, invoice, expense and task management, CSV exports, settings and database backup.
