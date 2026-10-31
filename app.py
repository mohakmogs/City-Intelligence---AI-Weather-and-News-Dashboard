import os
import base64
import html
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
import streamlit as st
from dotenv import load_dotenv
from tavily import TavilyClient
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain_core.messages import ToolMessage
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call

BASE_DIR = Path(__file__).resolve().parent
BACKGROUND_DIR = BASE_DIR / "assets" / "backgrounds"
load_dotenv(BASE_DIR / ".env")

st.set_page_config(
    page_title="City Intelligence | AI Weather & News",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --line:rgba(255,255,255,.16); --muted:rgba(239,244,255,.68); --text:#f6f8ff; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background-size:cover !important; background-position:center center !important; background-attachment:fixed !important; }
.stApp:before { content:""; position:fixed; inset:0; z-index:0; pointer-events:none; background:linear-gradient(115deg,rgba(5,9,24,.68),rgba(8,11,29,.36) 48%,rgba(8,7,25,.62)); }
[data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"] { background:transparent !important; }
[data-testid="stMain"] { position:relative; z-index:1; }
.block-container { max-width:1500px; padding:1.5rem 2.2rem 3rem !important; }
header[data-testid="stHeader"] { background:transparent; }
#MainMenu, footer { visibility:hidden; }
.brand { display:flex;align-items:center;gap:12px;margin:4px 0 2px; }
.brand-mark { width:42px;height:42px;border-radius:15px;display:grid;place-items:center;background:linear-gradient(135deg,rgba(84,220,255,.25),rgba(178,108,255,.28));border:1px solid rgba(255,255,255,.25);box-shadow:0 8px 30px rgba(49,185,255,.14);font-size:21px; }
.brand-name { font-family:Manrope,sans-serif;font-size:1.22rem;font-weight:800;letter-spacing:.02em;color:#fff; }
.brand-sub { color:rgba(240,244,255,.62);font-size:.76rem;margin-top:1px; }
.eyebrow { color:#9eeeff;text-transform:uppercase;letter-spacing:.18em;font-size:.68rem;font-weight:700; }
.hero-title { font-family:Manrope,sans-serif;color:#fff;font-size:clamp(2rem,4vw,3.35rem);line-height:1.08;font-weight:800;letter-spacing:-.045em;margin:.35rem 0 .45rem; }
.hero-copy { color:rgba(239,244,255,.72);font-size:.96rem;max-width:640px; }
.glass-card { box-sizing:border-box;width:100%;background:linear-gradient(135deg,rgba(22,31,55,.63),rgba(21,25,48,.43));border:1px solid var(--line);border-radius:26px;box-shadow:0 18px 55px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.08);-webkit-backdrop-filter:blur(22px);padding:22px;margin:0; }
.glass-tight { box-sizing:border-box;width:100%;background:linear-gradient(135deg,rgba(22,31,55,.66),rgba(21,25,48,.48));border:1px solid var(--line);border-radius:22px;box-shadow:0 14px 40px rgba(0,0,0,.2),inset 0 1px 0 rgba(255,255,255,.08);-webkit-backdrop-filter:blur(20px);padding:18px;margin:0; }
.section-label { color:rgba(237,243,255,.68);font-size:.72rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;margin-bottom:13px; }
.weather-city { font-family:Manrope,sans-serif;font-size:1.2rem;font-weight:700;color:#fff; }
.weather-temp { font-family:Manrope,sans-serif;font-size:clamp(3.5rem,7vw,5.4rem);line-height:1;font-weight:700;letter-spacing:-.07em;color:#fff;margin:12px 0 5px; }
.weather-condition { font-size:1.08rem;color:#e8f6ff;font-weight:600; }
.weather-meta,.chat-intro { color:rgba(239,244,255,.68);font-size:.82rem;line-height:1.55; }
.metrics-grid { display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:17px; }
.metric { border-top:1px solid rgba(255,255,255,.12);padding-top:13px;min-width:0; }
.metric-label { color:rgba(238,244,255,.58);font-size:.72rem; }
.metric-value { color:#fff;font-size:1.02rem;font-weight:700;margin-top:3px; }
.briefing-title { color:#fff;font-weight:700;font-size:1rem;margin-bottom:6px; }
.news-card { min-height:158px; }
.news-title { color:#fff;font-weight:700;font-size:.98rem;line-height:1.35;margin:6px 0 9px; }
.news-desc { color:rgba(239,244,255,.69);font-size:.82rem;line-height:1.5; }
.news-source { color:#9eeeff;font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase; }
/* Chat panel: style the actual Streamlit container, not an unclosed HTML wrapper. */
div[data-testid="stVerticalBlock"]:has(
    div[data-testid="stChatInput"]
) {
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
    border: none !important;
}
# div[data-testid="stVerticalBlock"]:has(> div [data-testid="stChatInput"]) { background:linear-gradient(135deg,rgba(22,31,55,.63),rgba(21,25,48,.43));border:1px solid var(--line);border-radius:26px;padding:22px;box-shadow:0 18px 55px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.08);backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px); }
div[data-testid="stChatMessage"] { background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.11);border-radius:18px;padding:10px 13px;margin-bottom:10px; }
div[data-testid="stChatMessage"] p { color:#f6f8ff; }
[data-testid="stChatInput"] { background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.2);border-radius:18px; }
[data-testid="stChatInput"] textarea { color:#fff !important; }
.stTextInput input { background:rgba(255,255,255,.09) !important;color:#fff !important;border:1px solid rgba(255,255,255,.2) !important;border-radius:14px !important; }
.stTextInput label,.stCheckbox label,.stToggle label { color:rgba(245,247,255,.82) !important; }
.stButton button { border-radius:13px;border:1px solid rgba(255,255,255,.22);background:rgba(255,255,255,.1);color:#fff;font-weight:600;transition:all .2s ease; }
.stButton button:hover { border-color:rgba(130,224,255,.7);background:rgba(94,190,255,.18);color:#fff; }
[data-testid="stAlert"] { background:rgba(25,34,59,.72);border:1px solid rgba(255,255,255,.14);border-radius:16px;color:#fff; }
.footer-note { color:rgba(239,244,255,.48);font-size:.72rem;text-align:center;padding:18px 0 0; }
.status-pill { display:inline-flex;align-items:center;gap:7px;padding:6px 11px;border:1px solid rgba(255,255,255,.16);border-radius:99px;background:rgba(255,255,255,.07);color:rgba(245,248,255,.85);font-size:.73rem;margin:12px 0; }
.status-dot { width:7px;height:7px;border-radius:50%;display:inline-block; }
[data-testid="column"] { min-width:0; }
@media (max-width:900px) { .block-container{padding:1rem 1rem 2rem !important}.glass-card,.glass-tight{border-radius:21px;padding:17px} }
@media (max-width:600px) {
 .block-container{padding:.75rem .7rem 1.5rem !important}.brand-name{font-size:1.05rem}.brand-mark{width:38px;height:38px;border-radius:13px}
 .hero-title{font-size:2.15rem}.hero-copy{font-size:.86rem}.glass-card,.glass-tight{border-radius:18px;padding:15px}
 .weather-temp{font-size:4rem}.news-card{min-height:unset}.metrics-grid{gap:9px}.metric-value{font-size:.9rem}
 [data-testid="stHorizontalBlock"]{gap:.65rem}
 div[data-testid="stVerticalBlock"]:has(> div [data-testid="stChatInput"]){padding:15px;border-radius:18px}
}
.stChatInput,
.stChatInput > div {
    background: linear-gradient(135deg,rgba(22,31,55,.43),rgba(21,25,48,.43));
    # background-color: rgba(0,0,0,0.25) !important;
}
.stTextInput [data-testid="stTextInputRootElement"] {
    background: transparent !important;
    background-color: transparent !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def get_secret(name: str) -> Optional[str]:
    try:
        return os.getenv(name) or st.secrets.get(name, None)
    except Exception:
        return os.getenv(name)


def image_to_data_uri(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    mime = {".webp": "image/webp", ".png": "image/png"}.get(path.suffix.lower(), "image/jpeg")
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def background_for_condition(condition: Optional[str]) -> Path:
    mapping = {
        "clear": "clear.jpg", "clouds": "cloudy.jpg", "rain": "rainy.jpg",
        "drizzle": "rainy.jpg", "thunderstorm": "storm.jpg", "snow": "snow.jpg",
        "mist": "fog.jpg", "smoke": "fog.jpg", "haze": "fog.jpg", "dust": "fog.jpg",
        "fog": "fog.jpg", "sand": "fog.jpg", "ash": "fog.jpg", "squall": "storm.jpg",
        "tornado": "storm.jpg",
    }
    candidate = BACKGROUND_DIR / mapping.get((condition or "").lower(), "default.jpg")
    return candidate if candidate.exists() else BACKGROUND_DIR / "default.jpg"


@st.cache_data(ttl=600, show_spinner=False)
def fetch_weather(city: str) -> dict:
    api_key = get_secret("OPENWEATHER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENWEATHER_API_KEY is missing. Add it to your .env file.")
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "appid": api_key, "units": "metric"}, timeout=12,
    )
    try:
        data = response.json()
    except ValueError:
        data = {}
    if response.status_code != 200:
        raise RuntimeError(data.get("message", "Could not fetch weather."))
    return data


@st.cache_data(ttl=900, show_spinner=False)
def fetch_news(query: str) -> list:
    api_key = get_secret("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is missing. Add it to your .env file.")
    client = TavilyClient(api_key=api_key)
    response = client.search(query=query, topic="news", search_depth="basic", max_results=5, include_answer=False)
    return response.get("results", [])


@tool
def get_weather(city: str) -> str:
    """Get current weather conditions for a city. Input should be a city name."""
    try:
        data = fetch_weather(city)
        weather, main, wind = data["weather"][0], data["main"], data.get("wind", {})
        return (
            f"Current weather in {data.get('name', city)}: {weather.get('description', 'Unknown').title()}. "
            f"Temperature: {main.get('temp')}°C; feels like: {main.get('feels_like')}°C; "
            f"humidity: {main.get('humidity')}%; wind speed: {wind.get('speed', 'N/A')} m/s."
        )
    except Exception as exc:
        return f"Weather lookup failed: {exc}"


@tool
def get_news(query: str) -> str:
    """Search recent news. Use a city, topic, or specific news query as input."""
    try:
        articles = fetch_news(query)
        if not articles:
            return f"No recent news results were found for: {query}"
        return "\n\n".join(
            f"Title: {item.get('title', 'Untitled')}\nSummary: {item.get('content', 'No summary available')}\nSource: {item.get('url', 'No URL')}"
            for item in articles
        )
    except Exception as exc:
        return f"News search failed: {exc}"


@wrap_tool_call
def ask_permit(request, handler):
    """Check the current Streamlit session's live-tool permission before execution."""
    # Read the current session value at call time; do not capture it when the cached agent is built.
    if not bool(st.session_state.get("approve_live_tools", False)):
        return ToolMessage(
            content=("Live tool access is currently OFF. The user must enable the live-tool toggle "
                     "before you can retrieve current weather or news. Do not claim that a tool ran."),
            tool_call_id=request.tool_call["id"],
        )
    return handler(request)


@st.cache_resource(show_spinner=False)
def build_agent():
    api_key = get_secret("GROQ_API_KEY")
    if not api_key:
        return None
    llm = ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"), api_key=api_key, temperature=0.2)
    return create_agent(
        llm, tools=[get_weather, get_news], #middleware=[ask_permit],
        system_prompt=(
            "You are City Intelligence, a concise and trustworthy city information assistant. "
            "Use get_weather for current weather and get_news for recent news or current events. "
            "For requests involving both, call both tools. Ask for a city or topic if missing. "
            "Never invent live conditions, headlines, sources, or forecasts. Weather provides current "
            "conditions only, not forecasts. Summarize results clearly and include article URLs when available. "
            "For unrelated general questions, answer normally without tools. If a tool call is denied, "
            "state that live access is off without repeatedly asking if it is already enabled."
        ),
    )


# Session state
for key, default in {
    "city": "Lucknow", "weather_data": None, "weather_error": None,
    "news_items": [], "messages": [], "approve_live_tools": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Initial / weather-dependent background
condition = None
if st.session_state.weather_data:
    condition = st.session_state.weather_data.get("weather", [{}])[0].get("main")
bg_uri = image_to_data_uri(background_for_condition(condition))
if bg_uri:
    st.markdown(f"<style>.stApp{{background-image:url('{bg_uri}') !important;}}</style>", unsafe_allow_html=True)

# Header
header_left, header_right = st.columns([1.5, 1], vertical_alignment="center")
with header_left:
    st.markdown(
        '<div class="brand"><div class="brand-mark">☁️</div><div><div class="brand-name">CITY INTELLIGENCE</div><div class="brand-sub">Background Changes with Weather.</div></div></div>',
        unsafe_allow_html=True,
    )
with header_right:
    city_col, refresh_col = st.columns([4, 1], vertical_alignment="bottom")
    with city_col:
        city_input = st.text_input("Explore a city", value=st.session_state.city, label_visibility="collapsed", placeholder="Search a city…", key="city_search")
    with refresh_col:
        refresh = st.button("↻", help="Refresh city data", use_container_width=True)

if city_input and city_input.strip() and (city_input.strip() != st.session_state.city or refresh or st.session_state.weather_data is None):
    st.session_state.city = city_input.strip()
    st.session_state.weather_error = None
    try:
        with st.spinner(f"Gathering the latest conditions for {st.session_state.city}…"):
            st.session_state.weather_data = fetch_weather(st.session_state.city)
    except Exception as exc:
        st.session_state.weather_error = str(exc)
        st.session_state.weather_data = None
    # A rerun applies the selected weather image consistently to the whole page.
    st.rerun()

# Hero
st.markdown(
    '<div style="margin:30px 0 22px"><div class="eyebrow">Live city pulse · Weather + News + AI</div>'
    '<div class="hero-title">See your city<br>in a new light.</div>'
    '<div class="hero-copy">A calm, intelligent snapshot of what\'s happening around you — powered by live data and an AI assistant.</div></div>',
    unsafe_allow_html=True,
)

# Main dashboard: preserve the existing two-column layout.
weather_col, assistant_col = st.columns([0.92, 1.08], gap="large")

with weather_col:
    if st.session_state.weather_data:
        d = st.session_state.weather_data
        main, weather, wind = d.get("main", {}), d.get("weather", [{}])[0], d.get("wind", {})
        city_name = html.escape(d.get("name", st.session_state.city))
        country = html.escape(d.get("sys", {}).get("country", ""))
        weather_html = f'''<section class="glass-card">
          <div class="section-label">◈ Current conditions</div>
          <div class="weather-city">{city_name}{", " + country if country else ""}</div>
          <div class="weather-temp">{round(main.get("temp", 0))}°</div>
          <div class="weather-condition">{html.escape(weather.get("description", "Current conditions").title())}</div>
          <div class="weather-meta">Live conditions · OpenWeather</div>
          <div class="metrics-grid">
            <div class="metric"><div class="metric-label">Feels like</div><div class="metric-value">{round(main.get("feels_like", 0))}°C</div></div>
            <div class="metric"><div class="metric-label">Humidity</div><div class="metric-value">{main.get("humidity", "—")}%</div></div>
            <div class="metric"><div class="metric-label">Wind</div><div class="metric-value">{round(wind.get("speed", 0) * 3.6)} km/h</div></div>
          </div></section>'''
    elif st.session_state.weather_error:
        weather_html = f'<section class="glass-card"><div class="section-label">◈ Current conditions</div><div class="weather-city">Weather unavailable</div><div class="weather-meta">{html.escape(st.session_state.weather_error)}</div></section>'
    else:
        weather_html = '<section class="glass-card"><div class="section-label">◈ Current conditions</div><div class="weather-city">Your city snapshot</div><div class="weather-meta">Search a city to load current conditions.</div></section>'
    st.markdown(weather_html, unsafe_allow_html=True)

    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    st.markdown(
        '<section class="glass-tight"><div class="section-label">✧ City briefing</div>'
        '<div class="briefing-title">Your daily intelligence, at a glance.</div>'
        '<div class="chat-intro">Ask the assistant to connect current conditions with the latest local developments. The briefing updates when you request fresh information.</div></section>',
        unsafe_allow_html=True,
    )
    if st.button("Get latest city headlines", use_container_width=True, key="load_news"):
        try:
            with st.spinner("Searching recent headlines…"):
                st.session_state.news_items = fetch_news(f"Latest important news in {st.session_state.city}")
        except Exception as exc:
            st.error(str(exc))

with assistant_col:
    with st.container(key="assistant_panel"):
        st.markdown('<div class="section-label">✦ AI city assistant</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-family:Manrope,sans-serif;font-size:1.35rem;font-weight:800;color:#fff;margin-bottom:4px">Ask your city anything.</div>', unsafe_allow_html=True)
        st.markdown('<div class="chat-intro">Weather, breaking news, local updates, or a quick city briefing. I’ll bring the useful details together.</div>', unsafe_allow_html=True)
        # Streamlit automatically stores the toggle value under this key.
        # Do not assign to that key again after creating the widget.
        # st.toggle(
        #     "Allow live tool calls for this conversation",
        #     key="approve_live_tools",
        #     help="When enabled, the assistant may use your Weather and Tavily APIs. Turn it off to block external tool calls.",
        # )
        # live_tools_enabled = bool(st.session_state.get("approve_live_tools", False))
        # if live_tools_enabled:
        #     st.markdown('<div class="status-pill"><span class="status-dot" style="background:#55e6a5;box-shadow:0 0 10px #55e6a5"></span>Live tools enabled</div>', unsafe_allow_html=True)
        # else:
        #     st.markdown('<div class="status-pill"><span class="status-dot" style="background:#ff777f"></span>Live tools disabled</div>', unsafe_allow_html=True)

        for msg in st.session_state.messages[-8:]:
            with st.chat_message(msg.get("role", "assistant")):
                st.markdown(msg.get("content", ""))

        prompt = st.chat_input("Ask about weather, news, or your city…")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            agent = build_agent()
            if agent is None:
                answer = "The Groq API key is missing. Add GROQ_API_KEY to your .env file and restart the app."
            else:
                try:
                    with st.spinner("Thinking…"):
                        # Pass the current session's chat history; middleware reads the same session toggle.
                        result = agent.invoke({"messages": st.session_state.messages})
                    answer = ""
                    for item in reversed(result.get("messages", [])):
                        content = getattr(item, "content", "")
                        if content and getattr(item, "type", "") == "ai":
                            answer = content if isinstance(content, str) else str(content)
                            break
                    if not answer:
                        answer = "I couldn't produce a response. Please try again."
                except Exception as exc:
                    answer = f"Something went wrong while running the agent: {exc}"
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

# Latest city news
st.markdown('<div style="height:25px"></div><div class="section-label">◉ Latest city news</div>', unsafe_allow_html=True)
if st.session_state.news_items:
    news_cols = st.columns(min(3, len(st.session_state.news_items)), gap="medium")
    for index, article in enumerate(st.session_state.news_items[:3]):
        title = html.escape(article.get("title", "Untitled"))
        summary_raw = article.get("content", "No summary available.")
        summary = html.escape(summary_raw)
        raw_url = article.get("url", "")
        parsed = urlparse(raw_url)
        safe_url = html.escape(raw_url, quote=True) if parsed.scheme in {"http", "https"} else ""
        domain = html.escape(parsed.netloc or "NEWS")
        card = f'<section class="glass-tight news-card"><div class="news-source">{domain}</div><div class="news-title">{title}</div><div class="news-desc">{summary[:190]}{"…" if len(summary) > 190 else ""}</div>'
        if safe_url:
            card += f'<div style="margin-top:12px"><a href="{safe_url}" target="_blank" rel="noopener noreferrer" style="color:#9eeeff;text-decoration:none;font-size:.8rem;font-weight:700">Read article ↗</a></div>'
        card += '</section>'
        with news_cols[index]:
            st.markdown(card, unsafe_allow_html=True)
else:
    st.markdown('<section class="glass-tight"><div class="chat-intro">Your news feed is ready when you are. Select “Get latest city headlines” to search current stories for this city.</div></section>', unsafe_allow_html=True)

st.markdown('<div class="footer-note">CITY INTELLIGENCE · Live information may vary by source and update time.</div>', unsafe_allow_html=True)
