#!/usr/bin/env python3
# ============================================================
#  CASHFLOW - Installer & Terminal Analyzer
#  Cyberpunk Neon Theme | No Loading Screen
#  Checks and installs required Python packages (requests, rich)
#  Analyzes the user's terminal environment
#  Offers to launch cashflow.py immediately after setup
#  All messages are in English.
# ============================================================

import sys
import subprocess
import importlib.util
import os
import platform

# ================= ANSI FALLBACK COLORS (before rich is installed) =================
class Colors:
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_colored(text, color):
    """Print colored text using ANSI escape codes."""
    print(color + text + Colors.RESET)

# ================= PACKAGE CHECK & INSTALL =================
def check_package(package):
    """Return True if a Python package is already installed."""
    return importlib.util.find_spec(package) is not None

def install_package(package):
    """Install a Python package using pip."""
    print_colored(f"Installing {package}...", Colors.YELLOW)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print_colored(f"{package} installed successfully.", Colors.GREEN)
    except subprocess.CalledProcessError as e:
        print_colored(f"Failed to install {package}. Error: {e}", Colors.RED)
        sys.exit(1)

def ensure_dependencies():
    """Check and install required packages, then import Rich."""
    packages = ["requests", "rich"]
    missing = []
    for pkg in packages:
        if check_package(pkg):
            print_colored(f"✓ {pkg} is already installed.", Colors.CYAN)
        else:
            missing.append(pkg)
    if missing:
        print_colored("Installing missing packages...", Colors.YELLOW)
        for pkg in missing:
            install_package(pkg)

    # After installation, import Rich components
    try:
        global Console, Panel, Text, Align, box, Prompt, Table
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        from rich.align import Align
        from rich import box
        from rich.prompt import Prompt
        from rich.table import Table
        return Console()
    except ImportError:
        print_colored("Failed to import Rich after installation. Exiting.", Colors.RED)
        sys.exit(1)

# ================= TERMINAL ANALYZER =================
def analyze_terminal():
    """
    Analyze the user's terminal environment and return a dictionary of findings.
    """
    info = {}
    env = os.environ

    # Terminal emulator detection
    if "TERMUX_VERSION" in env:
        info["Terminal"] = "Termux (Android)"
    elif "TERM_PROGRAM" in env:
        term_prog = env["TERM_PROGRAM"]
        if term_prog == "Apple_Terminal":
            info["Terminal"] = "Apple Terminal"
        elif term_prog == "iTerm.app":
            info["Terminal"] = "iTerm2"
        elif term_prog == "vscode":
            info["Terminal"] = "Visual Studio Code Integrated Terminal"
        elif term_prog == "Tabby":
            info["Terminal"] = "Tabby Terminal"
        elif term_prog == "Hyper":
            info["Terminal"] = "Hyper Terminal"
        else:
            info["Terminal"] = term_prog
    elif "WT_SESSION" in env or "WT_PROFILE_ID" in env:
        info["Terminal"] = "Windows Terminal"
    elif "GNOME_TERMINAL_SERVICE" in env:
        info["Terminal"] = "GNOME Terminal"
    elif "KONSOLE_VERSION" in env:
        info["Terminal"] = "Konsole (KDE)"
    elif "XFCE_TERMINAL" in env:
        info["Terminal"] = "Xfce Terminal"
    elif "SSH_CONNECTION" in env:
        info["Terminal"] = "SSH Remote Session"
    else:
        info["Terminal"] = "Unknown / Not Detected"

    # Operating System
    if sys.platform == "win32":
        info["OS"] = "Windows"
    elif sys.platform == "darwin":
        info["OS"] = "macOS"
    elif sys.platform.startswith("linux"):
        if "ANDROID_ROOT" in env:
            info["OS"] = "Android (via Termux or similar)"
        else:
            info["OS"] = "Linux"
    else:
        info["OS"] = sys.platform

    # Terminal type ($TERM)
    info["$TERM"] = env.get("TERM", "N/A")

    # Color support
    colorterm = env.get("COLORTERM", "")
    if colorterm:
        info["Color Support"] = f"{colorterm} (True Color likely)"
    elif env.get("TERM", "").endswith("256color"):
        info["Color Support"] = "256-color palette"
    else:
        info["Color Support"] = "Basic / unknown"

    # Python version
    info["Python"] = platform.python_version()

    # Architecture
    info["Architecture"] = platform.machine()

    # Working directory
    info["Working Dir"] = os.getcwd()

    return info

# ================= MAIN INSTALLER =================
def main():
    # Ensure dependencies are installed and get Rich console
    console = ensure_dependencies()

    # Clear screen
    os.system('clear' if os.name != 'nt' else 'cls')

    # Neon color configuration (same as main program)
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

    # ================= BANNER (INSTALLER) =================
    # Different from the main cashflow.py banner
    banner_text = Text()
    banner_text.append("█ █▄░█ █▀ ▀█▀ █▀█ █░░ █░░ █▀▀ █▀█\n", style=f"bold {NEON_CYAN}")
    banner_text.append("█ █░▀█ ▄█ ░█░ █▀█ █▄▄ █▄▄ ██▄ █▀▄\n", style=f"bold {NEON_MAGENTA}")
    banner_text.append("\n")
    banner_text.append("Setup and Dependencies Checker\n", style=f"bold {NEON_YELLOW}")
    banner_text.append("Powered by Rich & Requests\n", style=f"italic {NEON_PURPLE}")

    banner_panel = Panel(
        Align.center(banner_text),
        border_style=NEON_CYAN,
        box=box.DOUBLE_EDGE,
        padding=(1, 2),
        style=f"on {BACKGROUND}",
    )
    console.print(banner_panel)
    console.print()

    # ================= CHECK CASHFLOW.PY =================
    if os.path.exists("cashflow.py"):
        console.print("[bold green]✓ cashflow.py found[/bold green]")
    else:
        console.print("[bold red]✗ cashflow.py not found in current directory![/bold red]")
        console.print("[yellow]Please place cashflow.py in the same folder as install.py[/yellow]")
    console.print()

    # ================= TERMINAL ANALYSIS =================
    console.print("[bold cyan]Terminal Environment Analysis:[/bold cyan]")
    term_info = analyze_terminal()

    # Create a table for terminal analysis
    table = Table(
        title="Terminal & System Information",
        box=box.SIMPLE_HEAVY,
        header_style=f"bold {NEON_MAGENTA} on {BACKGROUND}",
        border_style=NEON_CYAN,
        padding=(0, 1),
        expand=False,
        row_styles=[f"on {BACKGROUND}", f"on {BACKGROUND_ALT}"],
    )
    table.add_column("Property", style=f"bold {NEON_PINK}", no_wrap=True)
    table.add_column("Value", style=f"bold {NEON_GREEN}")

    for key, value in term_info.items():
        table.add_row(key, str(value))

    console.print(table)
    console.print()

    # ================= LAUNCH PROMPT =================
    launch = Prompt.ask(
        "[bold yellow]Do you want to launch CASHFLOW now?[/bold yellow]",
        choices=["y", "n"],
        default="y"
    )
    if launch.lower() == "y":
        console.print("[bold cyan]Launching CASHFLOW...[/bold cyan]")
        if os.path.exists("cashflow.py"):
            subprocess.run([sys.executable, "cashflow.py"])
        else:
            console.print("[bold red]Cannot launch: cashflow.py not found.[/bold red]")
    else:
        console.print("[bold yellow]Skipping launch. Exiting installer.[/bold yellow]")

if __name__ == "__main__":
    main()