#!/usr/bin/env python3
# ============================================================
#  CASHFLOW - Cryptocurrency Live Monitor & Analyzer
#  Cyberpunk Neon Theme | Multi-Currency | Interactive Menu
#  For Termux (No Root) | Powered by CoinGecko API & Rich
#  All messages and prompts are in English.
#  [MODIFIED] Removed all simulation features.
#  Added Tips & Tricks menu, About and Help sections.
#  About panel uses horizontal border only.
#  Fixed clear screen and text wrapping issues.
#  Fixed fetch_market_data_for_sparkline for None coin_ids.
#  Fixed detail_analysis to show errors and handle None.
# ============================================================

import requests
import time
import argparse
import sys
import textwrap
import select
import tty
import termios
import os
from datetime import datetime
from functools import wraps

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.layout import Layout
from rich import box
from rich.prompt import Prompt, Confirm
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

# ================= NEON COLOR CONFIG =================
NEON_CYAN    = "#00ffff"
NEON_MAGENTA = "#ff00ff"
NEON_YELLOW  = "#ffff00"
NEON_GREEN   = "#39ff14"
NEON_PINK    = "#ff6ec7"
NEON_BLUE    = "#1f51ff"
NEON_PURPLE  = "#bf00ff"
NEON_RED     = "#ff3131"
NEON_ORANGE  = "#ff9933"
BACKGROUND   = "#0d0221"
BACKGROUND_ALT = "#1a0b2e"

console = Console()

# ================= COIN LIST & VISUAL SYMBOLS =================
COIN_SYMBOLS = {
    "bitcoin":        {"symbol": "₿",   "name": "Bitcoin"},
    "ethereum":       {"symbol": "Ξ",   "name": "Ethereum"},
    "binancecoin":    {"symbol": "BNB", "name": "BNB"},
    "cardano":        {"symbol": "ADA", "name": "Cardano"},
    "solana":         {"symbol": "◎",   "name": "Solana"},
    "dogecoin":       {"symbol": "Ð",   "name": "Dogecoin"},
    "ripple":         {"symbol": "✕",   "name": "XRP"},
    "polkadot":       {"symbol": "●",   "name": "Polkadot"},
    "litecoin":       {"symbol": "Ł",   "name": "Litecoin"},
    "chainlink":      {"symbol": "🔗",  "name": "Chainlink"},
    "stellar":        {"symbol": "✦",   "name": "Stellar"},
    "uniswap":        {"symbol": "🦄",  "name": "Uniswap"},
    "tron":           {"symbol": "TRX", "name": "TRON"},
    "avalanche-2":    {"symbol": "🔺",  "name": "Avalanche"},
    "cosmos":         {"symbol": "⚛",   "name": "Cosmos"},
    "monero":         {"symbol": "ɱ",   "name": "Monero"},
    "bitcoin-cash":   {"symbol": "Ƀ",   "name": "Bitcoin Cash"},
    "eos":            {"symbol": "EOS", "name": "EOS"},
    "tezos":          {"symbol": "ꜩ",   "name": "Tezos"},
    "theta-token":    {"symbol": "Θ",   "name": "Theta"},
    "shiba-inu":      {"symbol": "🐕",  "name": "Shiba Inu"},
    "polygon":        {"symbol": "MATIC","name": "Polygon"},
    "internet-computer": {"symbol": "∞", "name": "Internet Computer"},
    "near":           {"symbol": "Ⓝ",   "name": "NEAR Protocol"},
    "algorand":       {"symbol": "ALGO","name": "Algorand"},
    "vechain":        {"symbol": "VET", "name": "VeChain"},
    "fantom":         {"symbol": "FTM", "name": "Fantom"},
    "decentraland":   {"symbol": "MANA","name": "Decentraland"},
    "the-sandbox":    {"symbol": "SAND","name": "The Sandbox"},
    "axie-infinity":  {"symbol": "AXS", "name": "Axie Infinity"},
}

# ================= FIAT CURRENCY INFO =================
CURRENCY_INFO = {
    "usd": ("$", "US Dollar"),
    "idr": ("Rp", "Indonesian Rupiah"),
    "eur": ("€", "Euro"),
    "gbp": ("£", "British Pound"),
    "jpy": ("¥", "Japanese Yen"),
    "aud": ("A$", "Australian Dollar"),
    "cad": ("C$", "Canadian Dollar"),
    "chf": ("Fr", "Swiss Franc"),
    "cny": ("¥", "Chinese Yuan"),
    "inr": ("₹", "Indian Rupee"),
    "krw": ("₩", "South Korean Won"),
    "rub": ("₽", "Russian Ruble"),
    "brl": ("R$", "Brazilian Real"),
    "try": ("₺", "Turkish Lira"),
    "zar": ("R", "South African Rand"),
    "sgd": ("S$", "Singapore Dollar"),
    "myr": ("RM", "Malaysian Ringgit"),
    "thb": ("฿", "Thai Baht"),
    "php": ("₱", "Philippine Peso"),
    "vnd": ("₫", "Vietnamese Dong"),
    "ngn": ("₦", "Nigerian Naira"),
    "ars": ("$", "Argentine Peso"),
    "mxn": ("$", "Mexican Peso"),
    "sek": ("kr", "Swedish Krona"),
    "nok": ("kr", "Norwegian Krone"),
    "dkk": ("kr", "Danish Krone"),
    "pln": ("zł", "Polish Złoty"),
    "hkd": ("HK$", "Hong Kong Dollar"),
    "twd": ("NT$", "New Taiwan Dollar"),
    "aed": ("د.إ", "UAE Dirham"),
    "sar": ("﷼", "Saudi Riyal"),
    "kwd": ("د.ك", "Kuwaiti Dinar"),
    "qar": ("﷼", "Qatari Riyal"),
    "ils": ("₪", "Israeli New Shekel"),
    "clp": ("$", "Chilean Peso"),
    "cop": ("$", "Colombian Peso"),
    "pen": ("S/", "Peruvian Sol"),
    "uah": ("₴", "Ukrainian Hryvnia"),
}

# ================= API ENDPOINTS =================
BASE_URL = "https://api.coingecko.com/api/v3"
SIMPLE_PRICE_URL = f"{BASE_URL}/simple/price"
MARKET_URL = f"{BASE_URL}/coins/markets"
GLOBAL_URL = f"{BASE_URL}/global"
COIN_DETAIL_URL = f"{BASE_URL}/coins"
SEARCH_URL = f"{BASE_URL}/search"
TRENDING_URL = f"{BASE_URL}/search/trending"

# ================= FIAT RATES API =================
FIAT_RATES_URL = "https://open.er-api.com/v6/latest/{}"
FIAT_WATCH_LIST = ["USD","EUR","GBP","JPY","AUD","CAD","CHF","CNY",
                   "IDR","MYR","SGD","THB","VND","PHP","INR","KRW",
                   "RUB","BRL","TRY","ZAR","NZD","HKD","TWD"]

# ================= SIMPLE CACHE =================
_cache = {}

def cache_get(key):
    return _cache.get(key)

def cache_set(key, value):
    _cache[key] = value

# ================= RETRY & CACHE HELPERS =================
def fetch_with_retry(url, params=None, max_retries=3, timeout=15):
    last_exc = None
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_exc = e
            wait = 2 ** attempt
            time.sleep(wait)
    raise last_exc

# ================= UTILITY FUNCTIONS =================
def format_currency(value, currency_code="usd", decimals=2):
    if value is None:
        return "N/A"
    symbol = CURRENCY_INFO.get(currency_code, ("", currency_code.upper()))[0]
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        return f"{symbol}{value/1_000_000_000:.2f}B"
    elif abs_val >= 1_000_000:
        return f"{symbol}{value/1_000_000:.2f}M"
    elif abs_val >= 1_000:
        return f"{symbol}{value/1_000:.2f}K"
    else:
        return f"{symbol}{value:,.{decimals}f}"

def format_price(value, currency_code="usd"):
    if value is None:
        return Text("N/A", style="white")
    symbol = CURRENCY_INFO.get(currency_code, ("", currency_code.upper()))[0]
    if value >= 1000:
        return Text(format_currency(value, currency_code), style=f"bold {NEON_CYAN}")
    elif value >= 1:
        return Text(f"{symbol}{value:,.2f}", style=f"bold {NEON_CYAN}")
    else:
        return Text(f"{symbol}{value:.6f}", style=f"bold {NEON_CYAN}")

def format_percent(value):
    if value is None:
        return Text("N/A", style="white")
    if value > 0:
        return Text(f"▲ {value:.2f}%", style=f"bold {NEON_GREEN}")
    elif value < 0:
        return Text(f"▼ {value:.2f}%", style=f"bold {NEON_RED}")
    else:
        return Text("0.00%", style="white")

def format_supply(value):
    if value is None:
        return "N/A"
    if value >= 1_000_000_000:
        return f"{value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"{value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value/1_000:.2f}K"
    else:
        return f"{value:.2f}"

def format_fiat_rate(rate, currency_code):
    if rate is None:
        return "N/A"
    if rate >= 100:
        return f"{rate:,.2f}"
    elif rate >= 1:
        return f"{rate:,.4f}"
    else:
        return f"{rate:.6f}"

def generate_sparkline(prices, width=20):
    if not prices or len(prices) < 2:
        return Text("", style="dim")
    if len(prices) > width:
        step = len(prices) / width
        sampled = [prices[int(i * step)] for i in range(width)]
    else:
        sampled = prices
    min_p = min(sampled)
    max_p = max(sampled)
    if min_p == max_p:
        spark = "▬" * width
    else:
        blocks = "▁▂▃▄▅▆▇█"
        spark = ""
        for p in sampled:
            level = int((p - min_p) / (max_p - min_p) * (len(blocks)-1))
            spark += blocks[level]
    trend = prices[-1] - prices[0]
    if trend > 0:
        return Text(spark, style=f"bold {NEON_GREEN}")
    elif trend < 0:
        return Text(spark, style=f"bold {NEON_RED}")
    else:
        return Text(spark, style="dim")

def get_arrow(value):
    if value is None:
        return Text("", style="white")
    if value > 0:
        return Text("▲", style=f"bold {NEON_GREEN}")
    elif value < 0:
        return Text("▼", style=f"bold {NEON_RED}")
    else:
        return Text("▬", style="dim")

def generate_ascii_graph(prices, width=60, height=15):
    if not prices or len(prices) < 2:
        return Text("Not enough data", style="dim")

    max_width = console.width - 20 if console.width > 40 else 40
    width = min(width, max_width)
    height = min(height, 15)

    if len(prices) > width:
        step = len(prices) / width
        sampled = [prices[int(i * step)] for i in range(width)]
    else:
        sampled = prices
        width = len(sampled)

    min_price = min(sampled)
    max_price = max(sampled)
    if max_price == min_price:
        lines = []
        for _ in range(height):
            lines.append("─" * width)
        return Text("\n".join(lines), style="dim")

    grid = [[' ' for _ in range(width)] for _ in range(height)]

    for x, price in enumerate(sampled):
        norm = (price - min_price) / (max_price - min_price)
        bar_height = int(norm * (height - 1))
        for y in range(height):
            if y >= height - 1 - bar_height:
                grid[y][x] = '█'

    text = Text()
    max_label = format_price(max_price, "usd").plain
    min_label = format_price(min_price, "usd").plain
    text.append(f"Max: {max_label}\n", style="dim")
    for y in range(height):
        for x in range(width):
            char = grid[y][x]
            if char == '█':
                if x > 0:
                    prev_price = sampled[x-1]
                    curr_price = sampled[x]
                    if curr_price > prev_price:
                        style = f"bold {NEON_GREEN}"
                    elif curr_price < prev_price:
                        style = f"bold {NEON_RED}"
                    else:
                        style = "dim"
                else:
                    style = f"bold {NEON_GREEN}"
                text.append(char, style=style)
            else:
                text.append(char)
        text.append("\n")
    text.append(f"Min: {min_label}", style="dim")
    return text

def get_input(prompt, default=None):
    if default:
        result = Prompt.ask(prompt, default=default)
    else:
        result = Prompt.ask(prompt)
    return result.strip().lower()

def enable_raw_mode():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    return old_settings

def disable_raw_mode(old_settings):
    fd = sys.stdin.fileno()
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# ================= CLEAR SCREEN (FIXED) =================
def clear_screen():
    """Clear the terminal screen using OS-specific commands."""
    if sys.platform == "win32":
        os.system('cls')
    else:
        os.system('clear')

# ================= LOADING SCREEN =================
def loading_screen():
    clear_screen()
    text = Text()
    text.append("\n\n")
    text.append("  CASHFLOW", style=f"bold {NEON_CYAN}")
    text.append(" - Cryptocurrency Live Monitor", style=f"bold {NEON_MAGENTA}")
    text.append("\n\n")
    text.append("  Loading data and preparing environment...", style="italic")
    console.print(text)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Loading...", total=100)
        for i in range(100):
            time.sleep(0.03)
            progress.update(task, advance=1)

    clear_screen()
    console.print("✅ [bold green]System ready![/bold green]\n")
    time.sleep(0.5)

# ================= EXIT MESSAGE =================
def exit_message():
    clear_screen()
    text = Text()
    text.append("\n\n")
    text.append("  ═══════════════════════════════════════════════════════════\n", style=f"bold {NEON_MAGENTA}")
    text.append("   Thank you for using CASHFLOW!\n", style=f"bold {NEON_YELLOW}")
    text.append("   See you next time, trader! 🚀\n", style=f"bold {NEON_CYAN}")
    text.append("  ═══════════════════════════════════════════════════════════\n", style=f"bold {NEON_MAGENTA}")
    text.append("\n")
    text.append("   \"The best way to predict the future is to invent it.\"\n", style="italic")
    text.append("   - Alan Kay\n", style="italic")
    text.append("\n")
    console.print(text)
    time.sleep(2)

# ================= DATA FETCHING FUNCTIONS (with retry & cache) =================
def fetch_multi_currency_prices(coin_ids, currencies):
    cache_key = f"price_{','.join(coin_ids)}_{','.join(currencies)}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    params = {
        "ids": ",".join(coin_ids),
        "vs_currencies": ",".join(currencies),
        "include_market_cap": "true",
        "include_24hr_vol": "true",
        "include_24hr_change": "true",
        "include_last_updated_at": "true",
    }
    try:
        data = fetch_with_retry(SIMPLE_PRICE_URL, params=params)
        if not isinstance(data, dict):
            console.print(f"[bold {NEON_RED}]Invalid API response (not a dict).[/bold {NEON_RED}]")
            return None
        cache_set(cache_key, data)
        return data
    except Exception as e:
        console.print(f"[bold {NEON_RED}]Error fetching simple price: {e}[/bold {NEON_RED}]")
        return cached if cached else None

def fetch_market_data_for_sparkline(coin_ids, base_currency="usd", limit=20):
    per_page = len(coin_ids) if coin_ids else limit
    # Buat cache key yang aman untuk None
    if coin_ids:
        coin_ids_str = ",".join(coin_ids)
    else:
        coin_ids_str = "all"
    cache_key = f"market_{coin_ids_str}_{base_currency}_{per_page}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    params = {
        "vs_currency": base_currency,
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": 1,
        "sparkline": "true",
        "price_change_percentage": "24h,7d",
    }
    if coin_ids:
        params["ids"] = ",".join(coin_ids)
    try:
        data = fetch_with_retry(MARKET_URL, params=params)
        if not isinstance(data, list):
            console.print(f"[bold {NEON_RED}]Market data response is not a list.[/bold {NEON_RED}]")
            return None
        cache_set(cache_key, data)
        return data
    except Exception as e:
        console.print(f"[bold {NEON_RED}]Error fetching market data: {e}[/bold {NEON_RED}]")
        return cached if cached else None

def fetch_global_data():
    cache_key = "global"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        data = fetch_with_retry(GLOBAL_URL)
        result = data.get("data", {})
        if not result:
            return None
        cache_set(cache_key, result)
        return result
    except Exception as e:
        console.print(f"[bold {NEON_RED}]Error fetching global data: {e}[/bold {NEON_RED}]")
        return cached if cached else None

def fetch_fiat_rates(base_currency):
    cache_key = f"fiat_{base_currency.upper()}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        url = FIAT_RATES_URL.format(base_currency.upper())
        data = fetch_with_retry(url)
        if data.get("result") == "success":
            rates = data.get("rates", {})
            cache_set(cache_key, rates)
            return rates
        else:
            console.print(f"[bold {NEON_RED}]Fiat rates API failed.[/bold {NEON_RED}]")
            return None
    except Exception as e:
        console.print(f"[bold {NEON_RED}]Error fetching fiat rates: {e}[/bold {NEON_RED}]")
        return cached if cached else None

def fetch_coin_detail(coin_id, vs_currency="usd"):
    cache_key = f"detail_{coin_id}_{vs_currency}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "true",
        "vs_currency": vs_currency,
    }
    try:
        data = fetch_with_retry(f"{COIN_DETAIL_URL}/{coin_id}", params=params)
        cache_set(cache_key, data)
        return data
    except Exception as e:
        console.print(f"[bold {NEON_RED}]Error fetching detail {coin_id}: {e}[/bold {NEON_RED}]")
        return cached if cached else None

def fetch_search_results(query):
    cache_key = f"search_{query}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        data = fetch_with_retry(SEARCH_URL, params={"query": query})
        coins = data.get("coins", [])
        cache_set(cache_key, coins)
        return coins
    except Exception as e:
        console.print(f"[bold {NEON_RED}]Error searching: {e}[/bold {NEON_RED}]")
        return cached if cached else []

# ================= BANNER ASCII =================
BANNER_ART = r"""
                                                   
                                                   
▄█████  ▄▄▄   ▄▄▄▄ ▄▄ ▄▄ ▄▄▄▄▄ ▄▄     ▄▄▄  ▄▄   ▄▄ 
██     ██▀██ ███▄▄ ██▄██ ██▄▄  ██    ██▀██ ██ ▄ ██ 
▀█████ ██▀██ ▄▄██▀ ██ ██ ██    ██▄▄▄ ▀███▀  ▀█▀█▀  
                                                   
"""

def build_banner(currencies, base_currency):
    banner_lines = BANNER_ART.strip("\n").split("\n")
    colors = [NEON_CYAN, NEON_MAGENTA, NEON_YELLOW, NEON_GREEN, NEON_PINK, NEON_BLUE]
    text = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        text.append(line + "\n", style=f"bold {color}")
    text.append("\n", style="")
    text.append("LIVE CRYPTOCURRENCY MONITOR & ANALYZER", style=f"bold {NEON_YELLOW}")
    text.append("  |  ", style="white")
    text.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style=f"bold {NEON_MAGENTA}")
    text.append("\n", style="")
    text.append("Currencies: ", style=f"italic {NEON_PURPLE}")
    text.append(", ".join([f"{c.upper()} ({CURRENCY_INFO.get(c, ('', ''))[0]})" for c in currencies]), style=f"bold {NEON_CYAN}")
    text.append("  |  ", style="white")
    text.append(f"Base: {base_currency.upper()}", style=f"bold {NEON_ORANGE}")
    return Panel(
        Align.center(text),
        border_style=NEON_CYAN,
        box=box.DOUBLE_EDGE,
        padding=(1, 2),
        style=f"on {BACKGROUND}",
    )

# ================= TABLE BUILDING FUNCTIONS =================
def build_table(multi_data, market_data, currencies, base_currency, display_coin_ids=None, start_number=1):
    table = Table(
        title=None,
        box=box.SIMPLE_HEAVY,
        header_style=f"bold {NEON_MAGENTA} on {BACKGROUND}",
        border_style=NEON_CYAN,
        padding=(0, 1),
        expand=True,
        row_styles=[f"on {BACKGROUND}", f"on {BACKGROUND_ALT}"],
    )
    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("Logo", justify="center", style=f"bold {NEON_YELLOW}", no_wrap=True, width=4)
    table.add_column("Name", justify="left", style=f"bold {NEON_PINK}", no_wrap=True, min_width=12)
    for curr in currencies:
        symbol = CURRENCY_INFO.get(curr, ("", curr.upper()))[0]
        table.add_column(f"Price ({curr.upper()})", justify="right", style=f"bold {NEON_CYAN}", min_width=14)
    table.add_column("24h %", justify="center", min_width=10)
    table.add_column("7d %", justify="center", min_width=10)
    table.add_column(f"Market Cap ({base_currency.upper()})", justify="right", style=f"bold {NEON_GREEN}", min_width=12)
    table.add_column(f"Volume ({base_currency.upper()})", justify="right", style=f"bold {NEON_BLUE}", min_width=12)
    table.add_column("Supply", justify="right", style="dim", min_width=10)
    table.add_column("Sparkline 7d", justify="left", no_wrap=True, min_width=20)

    if multi_data is None:
        table.add_row("❌", "Error", "Failed to fetch data", *( [""] * (len(currencies)+6) ))
        return table

    if display_coin_ids is None:
        display_coin_ids = list(COIN_SYMBOLS.keys())

    market_by_id = {}
    if market_data:
        for coin in market_data:
            market_by_id[coin["id"]] = coin

    for local_idx, coin_id in enumerate(display_coin_ids):
        coin_entry = multi_data.get(coin_id)
        if not coin_entry:
            continue
        info = COIN_SYMBOLS.get(coin_id, {"symbol": coin_id[:4].upper(), "name": coin_id})
        visual = info["symbol"]
        idx = start_number + local_idx

        change_24h = coin_entry.get(f"{base_currency}_24h_change")
        arrow = get_arrow(change_24h)
        name_text = Text(info["name"] + " ", style=f"bold {NEON_PINK}")
        name_text.append(arrow)

        price_cells = []
        for curr in currencies:
            price = coin_entry.get(curr)
            price_cells.append(format_price(price, curr))

        base_market_cap = coin_entry.get(f"{base_currency}_market_cap")
        base_volume = coin_entry.get(f"{base_currency}_24h_vol")

        supply = None
        change_7d = None
        sparkline_prices = []
        if coin_id in market_by_id:
            m = market_by_id[coin_id]
            change_7d = m.get("price_change_percentage_7d_in_currency")
            sparkline_prices = m.get("sparkline_in_7d", {}).get("price", [])
            supply = m.get("circulating_supply")

        rank_style = "bold white"
        if idx == 1:
            rank_style = f"bold {NEON_YELLOW}"
        elif idx == 2:
            rank_style = f"bold {NEON_CYAN}"
        elif idx == 3:
            rank_style = f"bold {NEON_ORANGE}"

        row = [
            Text(str(idx), style=rank_style),
            visual,
            name_text,
        ]
        row.extend(price_cells)
        row.append(format_percent(change_24h))
        row.append(format_percent(change_7d))
        row.append(Text(format_currency(base_market_cap, base_currency), style=f"bold {NEON_GREEN}"))
        row.append(Text(format_currency(base_volume, base_currency), style=f"bold {NEON_BLUE}"))
        row.append(Text(format_supply(supply), style="dim"))
        row.append(generate_sparkline(sparkline_prices, width=20))
        table.add_row(*row)
    return table

def build_global_panel(global_data, base_currency="usd", show_hint=True):
    if not global_data:
        return Panel("Global data unavailable", border_style=NEON_RED, box=box.ROUNDED)

    total_mcap = global_data.get("total_market_cap", {}).get(base_currency, 0)
    total_vol = global_data.get("total_volume", {}).get(base_currency, 0)
    btc_dom = global_data.get("market_cap_percentage", {}).get("btc", 0)
    eth_dom = global_data.get("market_cap_percentage", {}).get("eth", 0)
    active_cryptos = global_data.get("active_cryptocurrencies", 0)
    markets = global_data.get("markets", 0)

    text = Text()
    text.append("🌐 GLOBAL MARKET", style=f"bold {NEON_YELLOW}")
    text.append("\n")
    text.append(f"Total Market Cap : {format_currency(total_mcap, base_currency)}", style=f"bold {NEON_GREEN}")
    text.append("\n")
    text.append(f"24h Volume       : {format_currency(total_vol, base_currency)}", style=f"bold {NEON_CYAN}")
    text.append("\n")
    text.append(f"BTC Dominance    : {btc_dom:.1f}%   ", style=f"bold {NEON_ORANGE}")
    text.append(f"ETH Dominance : {eth_dom:.1f}%", style=f"bold {NEON_PURPLE}")
    text.append("\n")
    text.append(f"Active Coins     : {active_cryptos}   Markets : {markets}", style="dim")
    if show_hint:
        text.append("\n")
        text.append("Enter/n: next page | p: prev page | q: menu | x: exit", style=f"italic {NEON_CYAN}")
    return Panel(
        text,
        border_style=NEON_MAGENTA,
        box=box.ROUNDED,
        padding=(0, 1),
        style=f"on {BACKGROUND}",
    )

def build_fiat_rates_panel(rates, base_currency, watch_list, title="💱 LIVE FIAT CURRENCY RATES", arrows=None):
    if not rates:
        return Panel("Exchange rate data unavailable", border_style=NEON_RED, box=box.ROUNDED)

    if arrows is None:
        arrows = {}

    table = Table(
        title=None,
        box=box.SIMPLE_HEAVY,
        header_style=f"bold {NEON_MAGENTA} on {BACKGROUND}",
        border_style=NEON_CYAN,
        padding=(0, 1),
        expand=True,
        row_styles=[f"on {BACKGROUND}", f"on {BACKGROUND_ALT}"],
    )
    table.add_column("Currency", justify="left", style=f"bold {NEON_PINK}", no_wrap=True)
    table.add_column("Trend", justify="center", style="bold", min_width=8)
    table.add_column(f"Rate (1 {base_currency.upper()})", justify="right", style=f"bold {NEON_CYAN}")
    table.add_column("Equivalent 1 Unit", justify="right", style=f"bold {NEON_GREEN}")

    for code in watch_list:
        code_upper = code.upper()
        if code_upper == base_currency.upper():
            continue
        rate = rates.get(code_upper)
        if rate is None:
            continue
        inv_rate = 1 / rate if rate else 0

        arrow = arrows.get(code_upper, "flat")
        if arrow == "up":
            arrow_text = Text("▲", style=f"bold {NEON_GREEN}")
        elif arrow == "down":
            arrow_text = Text("▼", style=f"bold {NEON_RED}")
        else:
            arrow_text = Text("▬", style="dim")

        currency_display = Text(code_upper, style=f"bold {NEON_PINK}")

        table.add_row(
            currency_display,
            arrow_text,
            format_fiat_rate(rate, code_upper),
            format_fiat_rate(inv_rate, code_upper)
        )

    return Panel(
        table,
        title=title,
        border_style=NEON_MAGENTA,
        box=box.ROUNDED,
        padding=(0, 1),
        style=f"on {BACKGROUND}",
    )

# ================= LIVE MONITOR CRYPTO =================
def live_monitor_crypto(currencies, base_currency, limit, interval, coin_ids=None):
    console.print(f"[bold {NEON_CYAN}]Starting Live Cryptocurrency Monitor...[/bold {NEON_CYAN}]")
    console.print(f"[dim]Currencies: {', '.join(currencies).upper()} | Base: {base_currency.upper()} | Refresh: {interval}s[/dim]")
    console.print("[dim]Press Enter/n for next page, p for previous, q for menu, x to exit.[/dim]")

    all_currencies = list(dict.fromkeys(currencies + [base_currency]))

    if coin_ids is None:
        full_coin_ids = list(COIN_SYMBOLS.keys())
    else:
        full_coin_ids = coin_ids

    if limit > 0 and limit < len(full_coin_ids):
        full_coin_ids = full_coin_ids[:limit]

    page_size = 13
    total_items = len(full_coin_ids)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    page = 0

    old_settings = None
    if sys.platform != "win32":
        old_settings = enable_raw_mode()

    stop_flag = False
    exit_flag = False

    clear_screen()

    try:
        with Live(console=console, screen=True, auto_refresh=False) as live:
            while not stop_flag and not exit_flag:
                if page < 0 or page >= total_pages:
                    page = 0

                try:
                    start = page * page_size
                    end = min(start + page_size, total_items)
                    coin_ids_to_use = full_coin_ids[start:end]

                    multi_data = fetch_multi_currency_prices(coin_ids_to_use, all_currencies)
                    market_data = fetch_market_data_for_sparkline(coin_ids_to_use, base_currency=base_currency, limit=len(coin_ids_to_use))

                    if multi_data is None:
                        error_text = Text()
                        error_text.append("⚠️ DATA NOT FOUND ⚠️\n", style=f"bold {NEON_RED}")
                        error_text.append("Failed to fetch data for this page.\n", style="white")
                        error_text.append("Try again later or return to menu.", style="italic")
                        layout = Layout()
                        layout.split_column(
                            Layout(name="header", size=12),
                            Layout(name="body", ratio=3),
                            Layout(name="footer", size=6),
                        )
                        layout["header"].update(build_banner(currencies, base_currency))
                        layout["body"].update(Panel(error_text, border_style=NEON_RED, box=box.ROUNDED, padding=1))
                        layout["footer"].update(build_global_panel(None, base_currency, show_hint=True))
                        live.update(layout)
                        live.refresh()
                    else:
                        layout = Layout()
                        layout.split_column(
                            Layout(name="header", size=12),
                            Layout(name="body", ratio=3),
                            Layout(name="footer", size=7),
                        )
                        layout["header"].update(build_banner(currencies, base_currency))
                        body_panel = Panel(
                            build_table(multi_data, market_data, currencies, base_currency,
                                        display_coin_ids=coin_ids_to_use,
                                        start_number=start + 1),
                            title=f"🪙 Coin List (Page {page+1}/{total_pages})",
                            border_style=NEON_MAGENTA,
                            box=box.ROUNDED,
                            padding=(0, 1),
                            style=f"on {BACKGROUND}",
                        )
                        layout["body"].update(body_panel)
                        global_data = fetch_global_data()
                        layout["footer"].update(build_global_panel(global_data, base_currency, show_hint=True))
                        live.update(layout)
                        live.refresh()
                except Exception as e:
                    error_text = Text()
                    error_text.append("⚠️ ERROR ⚠️\n", style=f"bold {NEON_RED}")
                    error_text.append(str(e), style="bold white")
                    error_text.append("\n", style="white")
                    error_text.append("Program continues...", style=f"italic {NEON_CYAN}")
                    live.update(Panel(error_text, border_style=NEON_RED, box=box.ROUNDED, padding=1))
                    live.refresh()
                    time.sleep(5)

                start_time = time.time()
                while time.time() - start_time < interval:
                    if sys.platform != "win32":
                        if select.select([sys.stdin], [], [], 0)[0]:
                            char = sys.stdin.read(1)
                            if char in ('\r', '\n', 'n', 'N'):
                                page = (page + 1) % total_pages
                                break
                            elif char in ('p', 'P'):
                                page = (page - 1) % total_pages
                                break
                            elif char == 'q':
                                stop_flag = True
                                break
                            elif char == 'x':
                                exit_flag = True
                                break
                    else:
                        import msvcrt
                        if msvcrt.kbhit():
                            char = msvcrt.getwch()
                            if char in ('\r', '\n', 'n', 'N'):
                                page = (page + 1) % total_pages
                                break
                            elif char in ('p', 'P'):
                                page = (page - 1) % total_pages
                                break
                            elif char == 'q':
                                stop_flag = True
                                break
                            elif char == 'x':
                                exit_flag = True
                                break
                    time.sleep(0.1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Ctrl+C pressed, returning to main menu...[/bold yellow]")
        return "menu"
    finally:
        if old_settings:
            disable_raw_mode(old_settings)
        clear_screen()

    if exit_flag:
        return "exit"
    else:
        return "menu"

# ================= LIVE MONITOR FIAT =================
def live_monitor_fiat(base_currency, interval, watch_list=None):
    if watch_list is None:
        watch_list = FIAT_WATCH_LIST

    console.print(f"[bold {NEON_CYAN}]Starting Live Fiat Currency Monitor...[/bold {NEON_CYAN}]")
    console.print(f"[dim]Base currency: {base_currency.upper()} | Refresh: {interval}s[/dim]")
    console.print("[dim]Press Enter/n for next page, p for previous, q for menu, x to exit.[/dim]")

    full_watch = watch_list
    page_size = 13
    total_items = len(full_watch)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    page = 0

    prev_rates = None

    old_settings = None
    if sys.platform != "win32":
        old_settings = enable_raw_mode()

    stop_flag = False
    exit_flag = False

    clear_screen()

    try:
        with Live(console=console, screen=True, auto_refresh=False) as live:
            while not stop_flag and not exit_flag:
                if page < 0 or page >= total_pages:
                    page = 0

                try:
                    start = page * page_size
                    end = min(start + page_size, total_items)
                    subset_watch = full_watch[start:end]

                    rates = fetch_fiat_rates(base_currency)

                    arrows = {}
                    if rates and prev_rates:
                        for code in subset_watch:
                            code_upper = code.upper()
                            if code_upper == base_currency.upper():
                                continue
                            current = rates.get(code_upper)
                            previous = prev_rates.get(code_upper)
                            if current is not None and previous is not None:
                                if current > previous:
                                    arrows[code_upper] = "up"
                                elif current < previous:
                                    arrows[code_upper] = "down"
                                else:
                                    arrows[code_upper] = "flat"
                            else:
                                arrows[code_upper] = "flat"
                    prev_rates = rates if rates else prev_rates

                    panel = build_fiat_rates_panel(
                        rates, base_currency, subset_watch,
                        title=f"💱 LIVE FIAT CURRENCY RATES (Page {page+1}/{total_pages})",
                        arrows=arrows
                    )

                    hint = Text()
                    hint.append("\nEnter/n: next | p: prev | q: menu | x: exit", style=f"italic {NEON_CYAN}")

                    layout = Layout()
                    layout.split_column(
                        Layout(name="main", ratio=3),
                        Layout(name="hint", size=2),
                    )
                    layout["main"].update(panel)
                    layout["hint"].update(Align.center(hint))
                    live.update(layout)
                    live.refresh()
                except Exception as e:
                    error_text = Text()
                    error_text.append("⚠️ ERROR ⚠️\n", style=f"bold {NEON_RED}")
                    error_text.append(str(e), style="bold white")
                    live.update(Panel(error_text, border_style=NEON_RED, box=box.ROUNDED, padding=1))
                    live.refresh()
                    time.sleep(5)

                start_time = time.time()
                while time.time() - start_time < interval:
                    if sys.platform != "win32":
                        if select.select([sys.stdin], [], [], 0)[0]:
                            char = sys.stdin.read(1)
                            if char in ('\r', '\n', 'n', 'N'):
                                page = (page + 1) % total_pages
                                break
                            elif char in ('p', 'P'):
                                page = (page - 1) % total_pages
                                break
                            elif char == 'q':
                                stop_flag = True
                                break
                            elif char == 'x':
                                exit_flag = True
                                break
                    else:
                        import msvcrt
                        if msvcrt.kbhit():
                            char = msvcrt.getwch()
                            if char in ('\r', '\n', 'n', 'N'):
                                page = (page + 1) % total_pages
                                break
                            elif char in ('p', 'P'):
                                page = (page - 1) % total_pages
                                break
                            elif char == 'q':
                                stop_flag = True
                                break
                            elif char == 'x':
                                exit_flag = True
                                break
                    time.sleep(0.1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Ctrl+C pressed, returning to main menu...[/bold yellow]")
        return "menu"
    finally:
        if old_settings:
            disable_raw_mode(old_settings)
        clear_screen()

    if exit_flag:
        return "exit"
    else:
        return "menu"

# ================= LIVE MONITOR GRAPH (ONE COIN PER PAGE) =================
def live_monitor_graph(base_currency, interval=5):
    console.print(f"[bold {NEON_CYAN}]Starting Live Coin Graph Monitor...[/bold {NEON_CYAN}]")
    console.print(f"[dim]Base currency: {base_currency.upper()} | Refresh: {interval}s[/dim]")
    console.print("[dim]Press Enter/n for next, p for previous, q for menu, x to exit.[/dim]")

    graph_coin_ids = ["bitcoin", "ethereum", "binancecoin", "solana", "cardano", "dogecoin"]

    page = 0
    total_items = len(graph_coin_ids)
    total_pages = total_items

    old_settings = None
    if sys.platform != "win32":
        old_settings = enable_raw_mode()

    stop_flag = False
    exit_flag = False

    clear_screen()

    try:
        with Live(console=console, screen=True, auto_refresh=False) as live:
            while not stop_flag and not exit_flag:
                if page < 0 or page >= total_pages:
                    page = 0

                try:
                    coin_id = graph_coin_ids[page]

                    multi_data = fetch_multi_currency_prices([coin_id], [base_currency])
                    if multi_data is None:
                        cached = cache_get(f"price_{coin_id}_{base_currency}")
                        if cached:
                            multi_data = cached
                        else:
                            wait_text = Text()
                            wait_text.append("⏳ Fetching data...", style=f"bold {NEON_YELLOW}")
                            layout = Layout()
                            layout.split_column(
                                Layout(name="header", size=12),
                                Layout(name="body", ratio=3),
                                Layout(name="hint", size=2),
                            )
                            layout["header"].update(build_banner([base_currency], base_currency))
                            layout["body"].update(Panel(wait_text, border_style=NEON_YELLOW, box=box.ROUNDED, padding=1))
                            hint = Text()
                            hint.append("\nEnter/n: next | p: prev | q: menu | x: exit", style=f"italic {NEON_CYAN}")
                            layout["hint"].update(Align.center(hint))
                            live.update(layout)
                            live.refresh()
                            time.sleep(2)
                            continue

                    entry = multi_data.get(coin_id)
                    if not entry:
                        raise Exception(f"Data for {coin_id} not found.")

                    current_price = entry.get(base_currency)
                    change_24h = entry.get(f"{base_currency}_24h_change")

                    market_data = fetch_market_data_for_sparkline([coin_id], base_currency=base_currency, limit=1)
                    sparkline_prices = []
                    if market_data:
                        for m in market_data:
                            if m["id"] == coin_id:
                                sparkline_prices = m.get("sparkline_in_7d", {}).get("price", [])
                                break

                    info = COIN_SYMBOLS.get(coin_id, {"symbol": coin_id[:4].upper(), "name": coin_id})
                    symbol = info["symbol"]
                    name = info["name"]

                    panel_text = Text()
                    panel_text.append(f"{symbol} {name}\n", style=f"bold {NEON_YELLOW}")
                    panel_text.append(f"Price: ", style="dim")
                    panel_text.append(format_price(current_price, base_currency).plain, style=f"bold {NEON_CYAN}")
                    panel_text.append(f"  24h: ", style="dim")
                    panel_text.append(format_percent(change_24h).plain, style=format_percent(change_24h).style)
                    panel_text.append("\n\n")
                    graph = generate_ascii_graph(sparkline_prices, width=60, height=15)
                    panel_text.append(graph)
                    panel_text.append("\n")

                    panel = Panel(
                        panel_text,
                        title=f"📈 {name} Chart (7 Days) - Page {page+1}/{total_pages}",
                        border_style=NEON_MAGENTA,
                        box=box.ROUNDED,
                        padding=(0, 1),
                        style=f"on {BACKGROUND}",
                    )

                    layout = Layout()
                    layout.split_column(
                        Layout(name="header", size=12),
                        Layout(name="body", ratio=3),
                        Layout(name="hint", size=2),
                    )
                    layout["header"].update(build_banner([base_currency], base_currency))
                    layout["body"].update(panel)
                    hint = Text()
                    hint.append("\nEnter/n: next | p: prev | q: menu | x: exit", style=f"italic {NEON_CYAN}")
                    layout["hint"].update(Align.center(hint))

                    live.update(layout)
                    live.refresh()
                except Exception as e:
                    error_text = Text()
                    error_text.append("⚠️ ERROR ⚠️\n", style=f"bold {NEON_RED}")
                    error_text.append(str(e), style="bold white")
                    error_text.append("\n", style="white")
                    error_text.append("Program continues...", style=f"italic {NEON_CYAN}")
                    live.update(Panel(error_text, border_style=NEON_RED, box=box.ROUNDED, padding=1))
                    live.refresh()
                    time.sleep(5)

                start_time = time.time()
                while time.time() - start_time < interval:
                    if sys.platform != "win32":
                        if select.select([sys.stdin], [], [], 0)[0]:
                            char = sys.stdin.read(1)
                            if char in ('\r', '\n', 'n', 'N'):
                                page = (page + 1) % total_pages
                                break
                            elif char in ('p', 'P'):
                                page = (page - 1) % total_pages
                                break
                            elif char == 'q':
                                stop_flag = True
                                break
                            elif char == 'x':
                                exit_flag = True
                                break
                    else:
                        import msvcrt
                        if msvcrt.kbhit():
                            char = msvcrt.getwch()
                            if char in ('\r', '\n', 'n', 'N'):
                                page = (page + 1) % total_pages
                                break
                            elif char in ('p', 'P'):
                                page = (page - 1) % total_pages
                                break
                            elif char == 'q':
                                stop_flag = True
                                break
                            elif char == 'x':
                                exit_flag = True
                                break
                    time.sleep(0.1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Ctrl+C pressed, returning to main menu...[/bold yellow]")
        return "menu"
    finally:
        if old_settings:
            disable_raw_mode(old_settings)
        clear_screen()

    if exit_flag:
        return "exit"
    else:
        return "menu"

# ================= DETAIL ANALYSIS (FIXED) =================
def detail_analysis(coin_id=None):
    if not coin_id:
        coin_id = get_input("Enter coin ID (e.g., bitcoin, ethereum): ")
    # Validasi coin_id tidak boleh kosong
    if not coin_id or coin_id.strip() == "":
        console.print("[red]Coin ID cannot be empty.[/red]")
        time.sleep(1)
        return
    coin_id = coin_id.strip().lower()
    
    currency = get_input("Currency for detail (default: usd): ", default="usd")
    if currency not in CURRENCY_INFO:
        console.print(f"[yellow]Warning: {currency} not recognized, using usd[/yellow]")
        currency = "usd"

    try:
        detail = fetch_coin_detail(coin_id, vs_currency=currency)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        time.sleep(2)
        return

    if not detail:
        console.print(f"[red]Failed to fetch data for '{coin_id}'. Please check the coin ID and your internet connection.[/red]")
        time.sleep(2)
        return

    # Jika data berhasil diambil, tampilkan detailnya
    name = detail.get("name", coin_id)
    symbol = detail.get("symbol", "?").upper()
    rank = detail.get("market_cap_rank", "?")
    categories = ", ".join(detail.get("categories", [])[:5])
    if not categories:
        categories = "N/A"
    description = detail.get("description", {}).get("en", "No description.")
    description = textwrap.shorten(description, width=200, placeholder="...")

    market = detail.get("market_data", {})
    current_price = market.get("current_price", {}).get(currency)
    ath = market.get("ath", {}).get(currency)
    atl = market.get("atl", {}).get(currency)
    market_cap = market.get("market_cap", {}).get(currency)
    volume = market.get("total_volume", {}).get(currency)
    change_24h = market.get("price_change_percentage_24h")
    change_7d = market.get("price_change_percentage_7d")
    change_30d = market.get("price_change_percentage_30d")
    circ_supply = market.get("circulating_supply")
    total_supply = market.get("total_supply")
    max_supply = market.get("max_supply")

    sparkline_prices = market.get("sparkline_7d", {}).get("price", [])

    panel_text = Text()
    panel_text.append(f"{name} ({symbol})", style=f"bold {NEON_YELLOW}")
    panel_text.append(f"  Rank #{rank}\n", style=f"bold {NEON_MAGENTA}")
    panel_text.append(f"Price ({currency.upper()}): ", style="white")
    panel_text.append(format_price(current_price, currency).plain, style=f"bold {NEON_CYAN}")
    panel_text.append("\n")
    panel_text.append(f"Market Cap: ", style="white")
    panel_text.append(f"{format_currency(market_cap, currency)}\n", style=f"bold {NEON_GREEN}")
    panel_text.append(f"24h Volume: ", style="white")
    panel_text.append(f"{format_currency(volume, currency)}\n", style=f"bold {NEON_BLUE}")
    panel_text.append(f"24h: ", style="white")
    panel_text.append(format_percent(change_24h).plain, style=format_percent(change_24h).style)
    panel_text.append(f"  7d: ")
    panel_text.append(format_percent(change_7d).plain, style=format_percent(change_7d).style)
    panel_text.append(f"  30d: ")
    panel_text.append(format_percent(change_30d).plain, style=format_percent(change_30d).style)
    panel_text.append("\n")
    panel_text.append(f"ATH: {format_currency(ath, currency)}   ", style=f"bold {NEON_ORANGE}")
    panel_text.append(f"ATL: {format_currency(atl, currency)}\n", style=f"bold {NEON_RED}")
    panel_text.append(f"Circulating Supply: {format_supply(circ_supply)}   ", style="dim")
    panel_text.append(f"Total Supply: {format_supply(total_supply)}   ", style="dim")
    panel_text.append(f"Max Supply: {format_supply(max_supply)}\n", style="dim")
    panel_text.append(f"Categories: {categories}\n", style="italic")
    panel_text.append(f"Description: {description}\n", style="dim")
    panel_text.append("Sparkline 7d: ", style="white")
    panel_text.append(generate_sparkline(sparkline_prices, width=40).plain, style=generate_sparkline(sparkline_prices, width=40).style)

    clear_screen()
    console.print(Panel(panel_text, title=f"[bold {NEON_CYAN}]Coin Detail[/bold {NEON_CYAN}]", border_style=NEON_MAGENTA, box=box.ROUNDED, padding=1))
    Prompt.ask("\n[bold yellow]Press Enter to return to menu[/bold yellow]")

# ================= COMPARE COINS =================
def compare_coins():
    coin_input = get_input("Enter coin IDs separated by commas (e.g., bitcoin,ethereum,cardano): ")
    coin_list = [c.strip() for c in coin_input.split(",") if c.strip()]
    if not coin_list:
        console.print("[red]No coins entered.[/red]")
        return

    currency = get_input("Currency (default: usd): ", default="usd")
    if currency not in CURRENCY_INFO:
        currency = "usd"

    all_currencies = [currency]
    multi_data = fetch_multi_currency_prices(coin_list, all_currencies)
    market_data = fetch_market_data_for_sparkline(coin_list, base_currency=currency, limit=len(coin_list))

    if not multi_data:
        console.print("[red]Failed to fetch data.[/red]")
        return

    table = Table(title=f"Coin Comparison ({currency.upper()})", border_style=NEON_CYAN, box=box.SIMPLE_HEAVY, header_style=f"bold {NEON_MAGENTA}")
    table.add_column("Name", style=f"bold {NEON_PINK}")
    table.add_column("Price", justify="right", style=f"bold {NEON_CYAN}")
    table.add_column("24h %", justify="center")
    table.add_column("7d %", justify="center")
    table.add_column("Market Cap", justify="right", style=f"bold {NEON_GREEN}")
    table.add_column("Volume", justify="right", style=f"bold {NEON_BLUE}")
    table.add_column("Sparkline", no_wrap=True)

    market_by_id = {}
    if market_data:
        for m in market_data:
            market_by_id[m["id"]] = m

    for coin_id in coin_list:
        entry = multi_data.get(coin_id)
        if not entry:
            continue
        name = COIN_SYMBOLS.get(coin_id, {}).get("name", coin_id)
        price = entry.get(currency)
        mcap = entry.get(f"{currency}_market_cap")
        vol = entry.get(f"{currency}_24h_vol")
        ch24 = entry.get(f"{currency}_24h_change")
        ch7 = market_by_id.get(coin_id, {}).get("price_change_percentage_7d_in_currency")
        spark = market_by_id.get(coin_id, {}).get("sparkline_in_7d", {}).get("price", [])
        table.add_row(
            name,
            format_price(price, currency).plain,
            format_percent(ch24).plain,
            format_percent(ch7).plain,
            format_currency(mcap, currency),
            format_currency(vol, currency),
            generate_sparkline(spark, width=25).plain,
        )

    clear_screen()
    console.print(table)
    Prompt.ask("\n[bold yellow]Press Enter to return to menu[/bold yellow]")

# ================= COMPARE FIAT CURRENCIES =================
def compare_fiat_currencies():
    from_currency = get_input("Source currency (e.g., usd): ", default="usd").upper()
    if from_currency not in CURRENCY_INFO:
        console.print(f"[yellow]Warning: {from_currency} not recognized, using USD[/yellow]")
        from_currency = "USD"

    to_currency = get_input("Target currency (e.g., idr): ", default="idr").upper()
    if to_currency not in CURRENCY_INFO:
        console.print(f"[yellow]Warning: {to_currency} not recognized, using IDR[/yellow]")
        to_currency = "IDR"

    amount_str = get_input("Amount to convert (default: 1): ", default="1")
    try:
        amount = float(amount_str)
    except:
        console.print("[red]Invalid amount, using 1.[/red]")
        amount = 1

    rates = fetch_fiat_rates(from_currency)
    if not rates:
        console.print("[red]Failed to fetch exchange rates.[/red]")
        return

    rate_to = rates.get(to_currency)
    if rate_to is None:
        console.print(f"[red]Rate for {to_currency} not available.[/red]")
        return

    converted_amount = amount * rate_to
    from_symbol = CURRENCY_INFO.get(from_currency.lower(), ("", from_currency))[0]
    to_symbol = CURRENCY_INFO.get(to_currency.lower(), ("", to_currency))[0]

    result_text = Text()
    result_text.append(f"{amount:,.2f} {from_currency} ({from_symbol})", style=f"bold {NEON_CYAN}")
    result_text.append("  =  ", style="white")
    result_text.append(f"{converted_amount:,.4f} {to_currency} ({to_symbol})", style=f"bold {NEON_GREEN}")

    panel = Panel(
        Align.center(result_text),
        title=f"💱 Conversion {from_currency} to {to_currency}",
        border_style=NEON_MAGENTA,
        box=box.ROUNDED,
        padding=1,
    )
    clear_screen()
    console.print(panel)

    rate_text = Text()
    rate_text.append(f"1 {from_currency} = {rate_to:,.6f} {to_currency}\n", style="dim")
    rate_text.append(f"1 {to_currency} = {1/rate_to:,.6f} {from_currency}", style="dim")
    console.print(Panel(rate_text, border_style=NEON_CYAN, box=box.ROUNDED, padding=(0,1)))

    Prompt.ask("\n[bold yellow]Press Enter to return to menu[/bold yellow]")

# ================= TIPS & TRICKS MENU =================
def tips_and_tricks_menu():
    while True:
        clear_screen()
        console.print(Panel.fit("[bold cyan]TIPS & TRICKS[/bold cyan]", border_style=NEON_CYAN))
        console.print("[1] Security Tips")
        console.print("[2] Trading Tips")
        console.print("[3] Investment Tips")
        console.print("[4] Mining Tips")
        console.print("[5] General Tips")
        console.print("[6] Back to Main Menu")
        choice = get_input("\nChoose (1-6): ")

        if choice == "1":
            show_tips_security()
        elif choice == "2":
            show_tips_trading()
        elif choice == "3":
            show_tips_investment()
        elif choice == "4":
            show_tips_mining()
        elif choice == "5":
            show_tips_general()
        elif choice == "6":
            break
        else:
            console.print("[red]Invalid choice.[/red]")
            time.sleep(1)

def show_tips_security():
    tips = [
        "Use a hardware wallet (Ledger, Trezor) for storing large amounts.",
        "Enable two-factor authentication (2FA) on all exchanges and email accounts.",
        "Never share your private keys or seed phrases with anyone.",
        "Beware of phishing sites; always check the URL before logging in.",
        "Use strong, unique passwords and consider a password manager.",
        "Keep your software (wallet, OS, antivirus) updated.",
        "Avoid using public Wi-Fi for crypto transactions; use a VPN if necessary.",
        "Double-check recipient addresses before sending funds.",
        "Consider using a dedicated email for crypto accounts.",
        "Regularly back up your wallet and store backups offline.",
        "Be cautious of social media giveaways and airdrops asking for private keys.",
        "Verify smart contract addresses before interacting with DeFi protocols.",
        "Use a separate wallet for daily trading and long-term holdings.",
        "Consider multi-signature wallets for business or joint accounts.",
        "Stay informed about common scams like rug pulls and pump-and-dump schemes."
    ]
    display_tips("Security Tips", tips)

def show_tips_trading():
    tips = [
        "Never invest more than you can afford to lose.",
        "Always set stop-loss orders to limit potential losses.",
        "Use dollar-cost averaging (DCA) to reduce the impact of volatility.",
        "Keep a trading journal to track your decisions and learn from mistakes.",
        "Don't chase pumps; wait for pullbacks before entering.",
        "Use both technical and fundamental analysis for better entries.",
        "Be aware of market sentiment but don't blindly follow the crowd.",
        "Diversify your portfolio across different coins and sectors.",
        "Take profits regularly; don't be greedy.",
        "Manage risk by limiting position size to 1-2% of your capital per trade.",
        "Be patient; good trades come to those who wait.",
        "Avoid emotional trading; stick to your plan.",
        "Use limit orders instead of market orders to avoid slippage.",
        "Watch for key support and resistance levels.",
        "Stay updated with news that could affect the market (regulations, partnerships)."
    ]
    display_tips("Trading Tips", tips)

def show_tips_investment():
    tips = [
        "Research the project thoroughly before investing: read whitepaper, check team, community.",
        "Focus on coins with strong fundamentals and real-world use cases.",
        "Consider long-term holding (HODL) for proven projects like Bitcoin and Ethereum.",
        "Allocate a small percentage of your net worth to crypto (5-10% is common).",
        "Rebalance your portfolio periodically to maintain desired allocation.",
        "Staking or lending can provide passive income, but understand the risks.",
        "Stay updated on regulatory developments in your country.",
        "Use cold storage for long-term holdings.",
        "Don't invest based on hype or FOMO; do your own research (DYOR).",
        "Consider market cycles: accumulate during bear markets, take profits during bulls.",
        "Set clear investment goals and time horizons.",
        "Avoid overtrading; long-term investing often outperforms frequent trading.",
        "Monitor your investments but don't check prices obsessively.",
        "Consider using index-like strategies with top 10 coins.",
        "Tax implications: keep records of all transactions for tax reporting."
    ]
    display_tips("Investment Tips", tips)

def show_tips_mining():
    tips = [
        "Calculate your electricity cost before starting mining; it can make or break profitability.",
        "Use efficient mining hardware (ASICs for Bitcoin, GPUs for altcoins).",
        "Join a mining pool to receive more consistent payouts.",
        "Monitor your hardware temperature to prevent overheating and extend lifespan.",
        "Consider cloud mining carefully; many are scams or unprofitable.",
        "Stay informed about mining difficulty adjustments and network hash rate.",
        "Mining can be noisy and generate heat; ensure proper ventilation.",
        "Explore mining alternative coins that might be more profitable than Bitcoin.",
        "Use mining profitability calculators (e.g., WhatToMine) before investing.",
        "Regularly update your mining software and firmware.",
        "Consider the environmental impact; some miners use renewable energy sources.",
        "Be prepared for hardware maintenance and potential downtime.",
        "Keep track of your mining income for tax purposes.",
        "Consider staking or masternodes as alternative ways to earn passive income.",
        "Mining profitability fluctuates with coin prices; be prepared for volatility."
    ]
    display_tips("Mining Tips", tips)

def show_tips_general():
    tips = [
        "Blockchain technology is still evolving; educate yourself continuously.",
        "Use multiple sources for news and analysis; don't rely on a single influencer.",
        "Beware of 'too good to be true' returns; they are often scams.",
        "Keep your private keys offline and secure; if you don't own the keys, you don't own the coins.",
        "Understand the difference between coins and tokens.",
        "Learn about smart contracts and how they can be exploited.",
        "Use block explorers to verify transactions and wallet balances.",
        "Participate in testnets before using mainnet for large transactions.",
        "Backup your wallet seed phrase in multiple secure locations.",
        "Consider using a dedicated device for crypto transactions.",
        "Be wary of fake mobile apps; download only from official app stores.",
        "Keep your software up to date to patch security vulnerabilities.",
        "If something goes wrong, don't panic; seek help from official channels.",
        "Remember that crypto markets are open 24/7 and highly volatile.",
        "Enjoy the journey and keep learning!"
    ]
    display_tips("General Tips", tips)

def display_tips(title, tips):
    clear_screen()
    text = Text()
    text.append(f"=== {title} ===\n\n", style=f"bold {NEON_YELLOW}")
    for i, tip in enumerate(tips, 1):
        text.append(f"{i}. {tip}\n", style="white")
    panel = Panel(
        text,
        title=f"[bold {NEON_CYAN}]{title}[/bold {NEON_CYAN}]",
        border_style=NEON_MAGENTA,
        box=box.ROUNDED,
        padding=(1, 2),
        style=f"on {BACKGROUND}",
    )
    console.print(panel)
    Prompt.ask("\n[bold yellow]Press Enter to return to Tips & Tricks menu[/bold yellow]")

# ================= ABOUT (Border Horizontal Only) =================
def show_about():
    clear_screen()
    text = Text()
    text.append("CASHFLOW - Cryptocurrency Live Monitor & Analyzer\n", style=f"bold {NEON_CYAN}")
    text.append("Version 1.0 (Real Tools Edition)\n\n", style=f"bold {NEON_MAGENTA}")
    text.append("Description:\n", style=f"bold {NEON_YELLOW}")
    text.append("A powerful terminal-based cryptocurrency monitoring and analysis tool.\n")
    text.append("Provides real-time price data, market insights, and various analytical tools.\n\n")
    text.append("Key Features:\n", style=f"bold {NEON_YELLOW}")
    text.append("  • Live Cryptocurrency Monitor with multi-currency support\n")
    text.append("  • Live Fiat Currency Rates\n")
    text.append("  • Coin Graph Monitoring\n")
    text.append("  • Detailed Coin Analysis\n")
    text.append("  • Coin Comparison\n")
    text.append("  • Global Market Overview\n")
    text.append("  • Search & Analyze\n")
    text.append("  • Fiat Currency Converter\n")
    text.append("  • Tips & Tricks for Security, Trading, Investing, Mining\n\n")
    text.append("Data Sources:\n", style=f"bold {NEON_YELLOW}")
    text.append("  • CoinGecko API (cryptocurrency data)\n")
    text.append("  • Open Exchange Rates (fiat currency rates)\n")
    text.append("  • CryptoCompare (news, if used)\n")
    text.append("  • Alternative.me (Fear & Greed Index, if used)\n\n")
    text.append("Author: CASHFLOW Team\n", style=f"italic {NEON_PINK}")
    text.append("License: MIT\n", style="dim")
    text.append("Created with ❤️ using Python and Rich library.\n", style="dim")
    panel = Panel(
        text,
        title="[bold cyan]About CASHFLOW[/bold cyan]",
        border_style=NEON_GREEN,
        box=box.HORIZONTALS,   # Hanya garis atas dan bawah
        padding=(1, 2),
        style=f"on {BACKGROUND}",
        expand=False,
    )
    console.print(panel)
    Prompt.ask("\n[bold yellow]Press Enter to return to menu[/bold yellow]")

# ================= HELP (FIXED LAYOUT) =================
def show_help():
    clear_screen()
    # Build text with manual wrapping for better readability
    help_content = []
    help_content.append(("CASHFLOW - Help & Usage Guide\n", f"bold {NEON_CYAN}"))
    help_content.append(("================================\n\n", "dim"))
    help_content.append(("MAIN MENU:\n", f"bold {NEON_YELLOW}"))
    help_content.append((textwrap.fill("[1] Live Cryptocurrency Monitor - Displays real-time coin prices, market cap, volume, sparklines.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("[2] Live Fiat Currency Monitor - Shows exchange rates for major fiat currencies.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("[3] Live Coin Graph Monitor - Visual graph for selected coins.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("[4] Detailed Coin Analysis - In-depth data for a specific coin.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("[5] Compare Coins - Compare multiple coins side by side.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("[6] Global Market Analysis - Total market cap, volume, top gainers/losers.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("[7] Search & Analyze - Search for any coin and view details.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("[8] Compare Fiat Currencies - Convert between fiat currencies.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("[9] Tips & Tricks - Useful tips for security, trading, investing, mining.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("[10] About - Information about this program.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("[11] Help - This help screen.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("[12] Exit - Quit the program.", width=70) + "\n\n", ""))
    help_content.append(("NAVIGATION:\n", f"bold {NEON_YELLOW}"))
    help_content.append((textwrap.fill("  • In menus, type the number or letter and press Enter.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("  • In live monitors:", width=70) + "\n", ""))
    help_content.append((textwrap.fill("      - Enter/n : next page", width=70) + "\n", ""))
    help_content.append((textwrap.fill("      - p       : previous page", width=70) + "\n", ""))
    help_content.append((textwrap.fill("      - q       : return to menu", width=70) + "\n", ""))
    help_content.append((textwrap.fill("      - x       : exit program", width=70) + "\n", ""))
    help_content.append((textwrap.fill("      - Ctrl+C  : interrupt and return", width=70) + "\n\n", ""))
    help_content.append(("COMMAND-LINE ARGUMENTS:\n", f"bold {NEON_YELLOW}"))
    help_content.append((textwrap.fill("  --coins bitcoin,ethereum    : Specify coin IDs to monitor.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("  --currencies usd,idr,eur    : Set fiat currencies (default: usd,idr).", width=70) + "\n", ""))
    help_content.append((textwrap.fill("  --base-currency usd         : Base currency for market cap/volume.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("  --limit 20                  : Number of coins to display.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("  --interval 30               : Refresh interval in seconds.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("  Example: python cashflow.py --coins bitcoin,ethereum --currencies usd,eur --interval 15", width=70) + "\n\n", ""))
    help_content.append(("TIPS:\n", f"bold {NEON_YELLOW}"))
    help_content.append((textwrap.fill("  • Data is cached for a short time; use 'q' and re-enter to refresh if needed.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("  • The program works best in terminal with Unicode support.", width=70) + "\n", ""))
    help_content.append((textwrap.fill("  • For Termux, ensure Python and required packages are installed:", width=70) + "\n", ""))
    help_content.append((textwrap.fill("      pkg install python && pip install rich requests", width=70) + "\n\n", ""))
    help_content.append((textwrap.fill("For more information, visit the project repository or contact support.", width=70) + "\n", "dim"))

    text = Text()
    for content, style in help_content:
        text.append(content, style=style)

    panel = Panel(
        text,
        title="[bold cyan]Help & Usage[/bold cyan]",
        border_style=NEON_BLUE,
        box=box.ROUNDED,
        padding=(1, 2),
        style=f"on {BACKGROUND}",
        expand=False,
    )
    console.print(panel)
    Prompt.ask("\n[bold yellow]Press Enter to return to menu[/bold yellow]")

# ================= GLOBAL ANALYSIS =================
def global_analysis():
    base = get_input("Base currency (default: usd): ", default="usd")
    if base not in CURRENCY_INFO:
        base = "usd"

    global_data = fetch_global_data()
    if global_data:
        clear_screen()
        console.print(build_global_panel(global_data, base, show_hint=False))

    console.print("[dim]Fetching top gainers/losers...[/dim]")
    market_all = fetch_market_data_for_sparkline(None, base_currency=base, limit=100)
    if market_all:
        sorted_gainers = sorted([m for m in market_all if m.get("price_change_percentage_24h") is not None],
                                key=lambda x: x["price_change_percentage_24h"], reverse=True)
        sorted_losers = sorted([m for m in market_all if m.get("price_change_percentage_24h") is not None],
                               key=lambda x: x["price_change_percentage_24h"])

        gainers_table = Table(title=f"Top 5 Gainers 24h ({base.upper()})", border_style=NEON_GREEN, box=box.ROUNDED)
        gainers_table.add_column("Coin", style=f"bold {NEON_PINK}")
        gainers_table.add_column("Price", justify="right", style=f"bold {NEON_CYAN}")
        gainers_table.add_column("24h %", justify="center")
        for coin in sorted_gainers[:5]:
            gainers_table.add_row(
                coin.get("name", "?"),
                format_currency(coin.get("current_price"), base),
                format_percent(coin.get("price_change_percentage_24h")).plain,
            )

        losers_table = Table(title=f"Top 5 Losers 24h ({base.upper()})", border_style=NEON_RED, box=box.ROUNDED)
        losers_table.add_column("Coin", style=f"bold {NEON_PINK}")
        losers_table.add_column("Price", justify="right", style=f"bold {NEON_CYAN}")
        losers_table.add_column("24h %", justify="center")
        for coin in sorted_losers[:5]:
            losers_table.add_row(
                coin.get("name", "?"),
                format_currency(coin.get("current_price"), base),
                format_percent(coin.get("price_change_percentage_24h")).plain,
            )

        console.print(Align.center(gainers_table))
        console.print(Align.center(losers_table))

    Prompt.ask("\n[bold yellow]Press Enter to return to menu[/bold yellow]")

# ================= SEARCH & ANALYZE =================
def search_and_analyze():
    query = get_input("Enter search keyword: ")
    if not query:
        return
    results = fetch_search_results(query)
    if not results:
        console.print("[red]No coins found.[/red]")
        return

    clear_screen()
    table = Table(title=f"Search results: '{query}'", border_style=NEON_CYAN, box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right", style="dim")
    table.add_column("ID", style=f"bold {NEON_PINK}")
    table.add_column("Name", style=f"bold {NEON_YELLOW}")
    table.add_column("Symbol", style=f"bold {NEON_MAGENTA}")
    table.add_column("Rank", justify="right", style="dim")
    for i, coin in enumerate(results[:10], 1):
        table.add_row(str(i), coin.get("id", "?"), coin.get("name", "?"), coin.get("symbol", "?").upper(), str(coin.get("market_cap_rank", "?")))
    console.print(table)

    choice = get_input("Select number for detailed analysis (Enter to cancel): ")
    if choice.isdigit() and 1 <= int(choice) <= len(results[:10]):
        selected_id = results[int(choice)-1]["id"]
        detail_analysis(selected_id)
    else:
        console.print("[dim]Cancelled.[/dim]")

# ================= MAIN MENU =================
def show_main_menu():
    clear_screen()
    console.print(build_banner(["usd"], "usd"))
    console.print("\n[bold cyan]MAIN MENU[/bold cyan]\n")
    console.print("[1] Live Cryptocurrency Monitor")
    console.print("[2] Live Fiat Currency Monitor")
    console.print("[3] Live Coin Graph Monitor")
    console.print("[4] Detailed Coin Analysis")
    console.print("[5] Compare Coins")
    console.print("[6] Global Market Analysis")
    console.print("[7] Search & Analyze")
    console.print("[8] Compare Fiat Currencies")
    console.print("[9] Tips & Tricks")
    console.print("[10] About")
    console.print("[11] Help")
    console.print("[12] Exit")
    choice = get_input("\nChoose (1-12): ")
    return choice

# ================= MAIN =================
def main():
    clear_screen()
    loading_screen()

    parser = argparse.ArgumentParser(
        description="Cashflow - Crypto Monitor & Analyzer",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Examples:\n"
               "  python cashflow.py --coins bitcoin,ethereum --currencies usd,idr --interval 15\n"
               "  python cashflow.py --currencies usd,idr,eur --limit 30"
    )
    parser.add_argument("--coins", type=str, help="Comma-separated coin ids (e.g., bitcoin,ethereum). Default: top 20 by market cap.")
    parser.add_argument("--currencies", type=str, default="usd,idr", help="Comma-separated fiat currencies (default: usd,idr).")
    parser.add_argument("--base-currency", type=str, default=None, help="Base currency for market cap, volume, global (default: first currency).")
    parser.add_argument("--limit", type=int, default=len(COIN_SYMBOLS), help="Number of coins to display (default: all).")
    parser.add_argument("--interval", type=int, default=30, help="Refresh interval in seconds (default: 30).")
    args = parser.parse_args()

    direct_mode = False
    if args.coins or args.currencies != "usd,idr" or args.base_currency or args.limit != len(COIN_SYMBOLS) or args.interval != 30:
        direct_mode = True

    if direct_mode:
        currencies = [c.strip().lower() for c in args.currencies.split(",") if c.strip()]
        if not currencies:
            console.print("[red]Error: --currencies must contain at least one currency code.[/red]")
            sys.exit(1)
        base_currency = (args.base_currency or currencies[0]).strip().lower()
        if base_currency not in currencies:
            currencies.append(base_currency)
        coin_ids = [c.strip().lower() for c in args.coins.split(",") if c.strip()] if args.coins else None
        result = live_monitor_crypto(currencies, base_currency, args.limit, args.interval, coin_ids)
        if result == "exit":
            exit_message()
        return

    currencies = ["usd", "idr"]
    base_currency = "usd"
    limit = len(COIN_SYMBOLS)
    interval = 30

    while True:
        try:
            choice = show_main_menu()
            if choice == "1":
                result = live_monitor_crypto(currencies, base_currency, limit, interval)
                if result == "exit":
                    exit_message()
                    break
            elif choice == "2":
                result = live_monitor_fiat(base_currency, interval)
                if result == "exit":
                    exit_message()
                    break
            elif choice == "3":
                result = live_monitor_graph(base_currency, interval=5)
                if result == "exit":
                    exit_message()
                    break
            elif choice == "4":
                detail_analysis()
            elif choice == "5":
                compare_coins()
            elif choice == "6":
                global_analysis()
            elif choice == "7":
                search_and_analyze()
            elif choice == "8":
                compare_fiat_currencies()
            elif choice == "9":
                tips_and_tricks_menu()
            elif choice == "10":
                show_about()
            elif choice == "11":
                show_help()
            elif choice == "12":
                exit_message()
                break
            else:
                console.print("[red]Invalid choice.[/red]")
                time.sleep(1)
        except KeyboardInterrupt:
            exit_message()
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit_message()