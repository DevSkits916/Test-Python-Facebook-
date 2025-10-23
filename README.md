# Browser Automation Platform

This repository contains a Flask-based automation service that simulates human social-media posting and exposes a control dashboard suitable for deployment on Render or other container-friendly platforms.

## Features

- **Campaign orchestration service** – Flask routes start and stop automation jobs, stream Server-Sent Events (SSE) updates, and expose dashboard views for monitoring automation state.【F:browser-automation-platform/app.py†L20-L145】
- **Stealth browser automation** – A Selenium engine configures a headless Chrome session with anti-detection flags, randomized viewports, mobile user-agent rotation, and resilient navigation/posting workflows with recovery helpers.【F:browser-automation-platform/browser_engine.py†L35-L189】【F:browser-automation-platform/browser_engine.py†L189-L272】
- **Content rotation management** – CSV-backed content manager loads 50+ post variations, prevents duplicates, and tracks campaign progress during automated posting.【F:browser-automation-platform/content_manager.py†L10-L73】【F:browser-automation-platform/data/post_variations.csv†L1-L61】
- **Live web dashboard** – Templates and JavaScript widgets render campaign status, control forms, and live logs via SSE feeds.【F:browser-automation-platform/templates/dashboard.html†L1-L54】【F:browser-automation-platform/static/script.js†L1-L120】
- **Render-ready deployment scripts** – Build script installs Google Chrome and a matching ChromeDriver, while Procfile, requirements, and runtime metadata enable one-click deployment.【F:browser-automation-platform/build.sh†L1-L25】【F:browser-automation-platform/Procfile†L1-L1】【F:browser-automation-platform/requirements.txt†L1-L4】【F:browser-automation-platform/runtime.txt†L1-L1】

## Project Layout

```
.
├── Procfile
├── README.md
├── browser-automation-platform/
│   ├── Procfile
│   ├── app.py
│   ├── browser_engine.py
│   ├── build.sh
│   ├── content_manager.py
│   ├── data/
│   │   └── post_variations.csv
│   ├── requirements.txt
│   ├── runtime.txt
│   ├── static/
│   │   ├── post_variations_sample.csv
│   │   ├── script.js
│   │   └── style.css
│   └── templates/
│       ├── configuration.html
│       ├── dashboard.html
│       └── results.html
├── build.sh
├── requirements.txt
└── runtime.txt
```

The root-level files duplicate the deployment artefacts so Render can detect them whether you deploy from the project root or the nested `browser-automation-platform/` folder.

## Prerequisites

- Python 3.11 (specified in `runtime.txt`).【F:browser-automation-platform/runtime.txt†L1-L1】
- Google Chrome and a compatible ChromeDriver. Render installs them by executing `build.sh` during the build phase.【F:browser-automation-platform/build.sh†L1-L25】

For local development, install Google Chrome manually or adjust `build.sh` to target your environment.

## Local Development

1. **Create and activate a virtual environment** using Python 3.11.
2. **Install dependencies:**
   ```bash
   pip install -r browser-automation-platform/requirements.txt
   ```
3. **Prepare content data:** edit `browser-automation-platform/data/post_variations.csv` or supply your own CSV matching the `identifier,title,body,target_group` schema.【F:browser-automation-platform/content_manager.py†L45-L63】
4. **Run the Flask app:**
   ```bash
   python browser-automation-platform/app.py
   ```
5. Visit `http://localhost:5000` to access the dashboard. Use the configuration and control forms to provide credentials and platform settings.

### Environment Variables

- `CONTENT_SOURCE` – Override the default CSV path when running the automation service.【F:browser-automation-platform/app.py†L33-L35】
- `GOOGLE_CHROME_BIN` / `CHROMEDRIVER_PATH` – Custom Chrome or ChromeDriver locations if they are not installed system-wide.【F:browser-automation-platform/app.py†L15-L17】【F:browser-automation-platform/browser_engine.py†L75-L105】

## Render Deployment

1. Push this repository to a GitHub project connected to Render.
2. Create a new **Web Service** in Render and select the repository.
3. Set the **build command** to `./build.sh` (either root-level or `browser-automation-platform/build.sh`).【F:browser-automation-platform/build.sh†L1-L25】
4. Set the **start command** to `gunicorn app:app` and the working directory to `browser-automation-platform/` (or adjust to match your chosen Procfile).【F:browser-automation-platform/Procfile†L1-L1】
5. Define required environment variables for platform credentials (Render Secret Files are recommended).
6. Deploy. Render executes the build script to install Chrome/ChromeDriver and launches Gunicorn with the Flask application.

## CSV Content Schema

Each row in `post_variations.csv` should supply:

| Column        | Description                                      |
|---------------|--------------------------------------------------|
| `identifier`  | Unique handle for the variation.                  |
| `title`       | Display title shown in dashboards/logs.           |
| `body`        | Post content text shared with the target group.   |
| `target_group`| Search keywords or group names to target.         |

The `ContentManager` enforces these columns and raises an error if any are missing or empty.【F:browser-automation-platform/content_manager.py†L45-L63】

## Monitoring and Debugging

- **Live updates:** The dashboard subscribes to `/automation-status` SSE feed to show log entries, status text, and progress metrics in real time.【F:browser-automation-platform/app.py†L92-L137】【F:browser-automation-platform/static/script.js†L1-L52】
- **Emergency stop:** POST `/emergency-stop` to cancel the current campaign gracefully.【F:browser-automation-platform/app.py†L138-L150】
- **Debug artefacts:** When errors occur, the automation engine captures screenshots and browser console logs under a `debug/` directory to aid investigation.【F:browser-automation-platform/browser_engine.py†L223-L246】

## Testing

A lightweight smoke check compiles all Python modules:

```bash
python -m compileall browser-automation-platform
```

This ensures syntax validity before deploying to Render.

