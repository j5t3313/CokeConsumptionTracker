# Diet Coke Tracker 2026

A Streamlit dashboard for tracking Diet Coke (and inferior product) consumption between friends, powered by Google Sheets.

![Diet Coke Tracker]

## Features

- **Live Leaderboard** — Real-time ranking with leader highlight and margin tracking
- **Trend Analysis** — Daily consumption charts and cumulative "Race to 1000 Ounces"
- **Consumption Patterns** — Breakdown by hour, day of week, format, and drink type
- **Player Stats** — Individual metrics including streaks, predictions, loyalty percentage, and peak drinking hours
- **Recent Activity Feed** — Latest entries from the Google Form
- **Auto-refresh** — Data updates every 5 minutes with manual refresh option

## Tech Stack

- **Frontend**: Streamlit
- **Visualization**: Plotly
- **Data Source**: Google Sheets (via Google Forms)
- **Authentication**: Google Service Account

## Setup

### 1. Google Cloud Configuration

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable the **Google Sheets API** and **Google Drive API**
3. Create a Service Account:
   - Go to IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Name it (e.g., "sheets-reader") and click through the prompts
4. Generate a key:
   - Click on the service account
   - Go to Keys → Add Key → Create new key → JSON
   - Save the downloaded JSON file

### 2. Google Sheet Setup

1. Create a Google Form with the following fields:
   - Who are you (dropdown)
   - DC or inferior product? (dropdown)
   - Date & time (datetime)
   - Format (dropdown: Can, Bottle, Fountain, etc.)
   - Ounces (number)
   - Additional notes (text)
   - AM only: is this the first beverage you've had today? (dropdown)

2. Link the form to a Google Sheet

3. Share the sheet with your service account email (found in the JSON file as `client_email`) with Viewer access

### 3. Local Configuration

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/diet-coke-tracker.git
   cd diet-coke-tracker
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.streamlit/secrets.toml` from the template:
   ```bash
   cp .streamlit/secrets.toml.template .streamlit/secrets.toml
   ```

4. Populate `secrets.toml` with values from your Google service account JSON file

5. Update `app.py`:
   - Set `SHEET_ID` to your Google Sheet ID (from the URL: `docs.google.com/spreadsheets/d/{SHEET_ID}/edit`)
   - Set `SHEET_NAME` to match your responses tab name

### 4. Run Locally

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## Deployment

### Streamlit Cloud (Recommended)

1. Push your repo to GitHub (exclude `secrets.toml`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Add your secrets in Settings → Secrets (paste the contents of `secrets.toml`)
5. Deploy

### Other Platforms

The app can also be deployed on:
- Heroku
- Railway
- Google Cloud Run
- AWS App Runner

## Configuration

### Adding Players

Update the `PERSON_COLORS` dictionary in `app.py` to add or modify player colors:

```python
PERSON_COLORS = {
    "Cain": "#E61A27",    # Diet Coke Red
    "Shiv": "#8A8A8A"     # Silver
}
```

### Adjusting the Race Goal

Modify the goal line in the cumulative chart section:

```python
fig_cumulative.add_hline(y=1000, ...)  # Change 1000 to your target
```

## Project Structure

```
diet-coke-tracker/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── README.md
└── .streamlit/
    ├── secrets.toml            # Your secrets (git-ignored)
    └── secrets.toml.template   # Template for secrets
```

## License

MIT

## Acknowledgments

- Powered by caffeine and questionable life choices
- Diet Coke branding colors used for aesthetic purposes only
