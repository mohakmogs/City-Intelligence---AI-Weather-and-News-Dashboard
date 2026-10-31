# City Intelligence — AI Weather & News Dashboard

A responsive Streamlit dashboard that combines current city weather, recent news search, and a LangChain AI assistant in a glassmorphism interface.

live link :https://city-intelligence---ai-weather-and-news-dashboard.streamlit.app/

## Features

- Current weather lookup through OpenWeather.
- Recent news search through Tavily.
- Groq-powered LangChain agent with weather and news tools.
- Middleware-based approval gate for live tool calls.
- Session-based chat history during the active Streamlit session.
- Weather-aware background switching using local image assets.
- Responsive layout for desktop, tablet, and mobile screens.

## 1. Project structure

```text
city-intelligence/
├── app.py
├── requirements.txt
├── .env.example
├── .env                  # Create this locally; do not commit it
├── README.md
└── assets/
    └── backgrounds/
        ├── default.jpg
        ├── clear.jpg
        ├── cloudy.jpg
        ├── rainy.jpg
        ├── storm.jpg
        ├── snow.jpg
        └── fog.jpg
```

## 2. Add your background images

Save your images in `assets/backgrounds/` using these exact names:

| Filename | Weather condition |
|---|---|
| `default.jpg` | Initial nebula / cosmic background |
| `clear.jpg` | Clear sky / sunny |
| `cloudy.jpg` | Cloudy |
| `rainy.jpg` | Rain / drizzle |
| `storm.jpg` | Thunderstorm / squall |
| `snow.jpg` | Snow |
| `fog.jpg` | Mist / haze / fog |

Recommended: 1920×1080 or larger, 16:9, JPG or WebP. The current uploaded nebula image is included as `default.jpg`. If a condition-specific image is missing, the app falls back to `default.jpg`.

## 3. Configure API keys

Copy `.env.example` to `.env` and add your keys:

```env
GROQ_API_KEY=...
OPENWEATHER_API_KEY=...
TAVILY_API_KEY=...
GROQ_MODEL=openai/gpt-oss-120b
```

Never commit `.env` or expose API keys in screenshots or public repositories.

## 4. Install and run

Python 3.10 or 3.11 is recommended.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 5. Tool approval

The assistant's **Allow live tool calls for this conversation** toggle controls whether the middleware permits the agent to execute external Weather and Tavily tools. Keep it disabled to prevent tool execution.

## Notes and current limitations

- The weather card shows current conditions, not a forecast. Tomorrow-specific planning requires adding the OpenWeather forecast endpoint.
- Chat history is retained in Streamlit session state for the active browser session; it is not yet persisted across server restarts or separate sessions.
- The approval toggle is a session-level permission gate. It is not a per-tool confirmation dialog.
- For production deployment, add authentication, rate limiting, structured logging, API usage controls, and persistent per-user conversation storage.
