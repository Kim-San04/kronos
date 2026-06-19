import time
import random
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress, SpinnerColumn,
    BarColumn, TextColumn,
    TimeElapsedColumn
)
from rich import box

console = Console()

MATRIX_CHARS = (
    "アイウエオカキクケコサシスセソタチツテト"
    "ナニヌネノハヒフヘホマミムメモヤユヨラリ"
    "ルレロワヲン0123456789ABCDEF"
)

BANNER_LINES = [
    " ██╗  ██╗██████╗  ██████╗ ███╗   ██╗ ██████╗ ███████╗",
    " ██║ ██╔╝██╔══██╗██╔═══██╗████╗  ██║██╔═══██╗██╔════╝",
    " █████╔╝ ██████╔╝██║   ██║██╔██╗ ██║██║   ██║███████╗",
    " ██╔═██╗ ██╔══██╗██║   ██║██║╚██╗██║██║   ██║╚════██║",
    " ██║  ██╗██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝███████║",
    " ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝",
]

BOOT_SEQUENCE = [
    ("KRONOS Intelligence v2.1.0", "bold cyan"),
    ("", ""),
    ("[ INIT ] Chargement des modules OSINT...", "dim cyan"),
    ("[ OK   ] Moteur de profilage IA............", "green"),
    ("[ OK   ] Sherlock 300+ plateformes..........", "green"),
    ("[ OK   ] Maigret OSINT engine...............", "green"),
    ("[ OK   ] Holehe email tracker...............", "green"),
    ("[ OK   ] LeakCheck breach database..........", "green"),
    ("[ OK   ] GitHub Intelligence module.........", "green"),
    ("[ OK   ] Pivot recursif engine..............", "green"),
    ("[ OK   ] Groq AI llama-3.3-70b..............", "green"),
    ("[ OK   ] Generateur de rapport PDF..........", "green"),
    ("", ""),
    ("[ WARN ] Mode collecte passive : ACTIF", "yellow"),
    ("[ INFO ] Toutes les operations sont passives", "dim"),
    ("[ INFO ] Aucune interaction directe      ", "dim"),
    ("", ""),
    ("[ SYS  ] Systeme nominal. Pret.", "bold cyan"),
]


def matrix_rain(duration: float = 1.8):
    try:
        width = os.get_terminal_size().columns
    except Exception:
        width = 80

    height = 12
    cols = [0] * (width + 1)
    chars = [" "] * (width + 1)
    brightness = [0] * (width + 1)

    start = time.time()

    while time.time() - start < duration:
        for i in range(width):
            if random.random() < 0.05:
                cols[i] = random.randint(1, height)
                brightness[i] = random.randint(6, 10)

        lines = []
        for row in range(height):
            line = ""
            for col in range(width):
                if cols[col] > 0 and row == height - cols[col]:
                    char = random.choice(MATRIX_CHARS)
                    chars[col] = char
                    cols[col] -= 1
                    b = brightness[col]
                    if b > 8:
                        line += f"\033[97m{char}\033[0m"
                    elif b > 6:
                        line += f"\033[96m{char}\033[0m"
                    else:
                        line += f"\033[36m{char}\033[0m"
                elif chars[col] != " " and random.random() < 0.3:
                    b = brightness[col]
                    if b > 6:
                        line += f"\033[2;36m{chars[col]}\033[0m"
                    else:
                        line += f"\033[2;32m{chars[col]}\033[0m"
                else:
                    line += " "
            lines.append(line)

        sys.stdout.write("\033[H")
        for line in lines:
            sys.stdout.write(line + "\n")
        sys.stdout.flush()
        time.sleep(0.05)


def glitch_banner():
    os.system("clear")
    time.sleep(0.1)

    # Phase 1 — glitch instable
    for _ in range(3):
        for line in BANNER_LINES:
            glitched = ""
            for char in line:
                if random.random() < 0.08 and char != " ":
                    glitched += random.choice("█▓▒░▄▀■□▪▫")
                else:
                    glitched += char
            sys.stdout.write(f"\033[91m{glitched}\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.06)
        sys.stdout.write(f"\033[{len(BANNER_LINES)}A")

    # Phase 2 — stabilisation progressive
    for step in range(4):
        sys.stdout.write(f"\033[{len(BANNER_LINES)}A")
        for line in BANNER_LINES:
            glitched = ""
            glitch_prob = 0.06 - step * 0.015
            for char in line:
                if random.random() < glitch_prob and char != " ":
                    glitched += random.choice("▓▒░▄▀")
                else:
                    glitched += char
            color = "\033[96m" if step >= 2 else "\033[93m"
            sys.stdout.write(f"{color}{glitched}\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.08)

    # Phase 3 — version finale nette
    sys.stdout.write(f"\033[{len(BANNER_LINES)}A")
    for line in BANNER_LINES:
        sys.stdout.write(f"\033[96m{line}\033[0m\n")
    sys.stdout.flush()

    print()
    tagline = "  ─────────── OSINT Intelligence System v2.1 ───────────"
    for char in tagline:
        sys.stdout.write(f"\033[36m{char}\033[0m")
        sys.stdout.flush()
        time.sleep(0.01)
    print()


def boot_sequence():
    print()
    width = 60
    border = "\033[2;36m" + "─" * width + "\033[0m"
    print(border)
    print()

    for text, style in BOOT_SEQUENCE:
        if not text:
            print()
            continue

        if style == "green":
            color = "\033[92m"
        elif style == "yellow":
            color = "\033[93m"
        elif style == "bold cyan":
            color = "\033[1;96m"
        elif style == "dim":
            color = "\033[2;37m"
        else:
            color = "\033[36m"

        line = f"  {text}"
        for char in line:
            sys.stdout.write(f"{color}{char}\033[0m")
            sys.stdout.flush()
            time.sleep(0.008)
        print()
        time.sleep(0.05)

    print()
    print(border)


def scanning_animation(target: str, mode: str):
    print()

    table = Table(
        box=box.SIMPLE_HEAVY,
        show_header=False,
        border_style="cyan",
        padding=(0, 2),
        width=62
    )
    table.add_column(style="dim", width=16)
    table.add_column(style="bold white")

    table.add_row("CIBLE", f"[bold cyan]{target}[/bold cyan]")
    table.add_row("MODE", f"[yellow]{mode}[/yellow]")
    table.add_row("ENGINE", "[cyan]Groq llama-3.3-70b-versatile ●[/cyan]")
    table.add_row("PROFILER", "[cyan]TargetProfiler AI ●[/cyan]")
    table.add_row("PIVOT", "[cyan]RecursivePivot Engine ●[/cyan]")
    table.add_row("STATUS", "[bold green]ANALYSE EN COURS...[/bold green]")

    console.print(Panel(
        table,
        title="[bold cyan]◆ MISSION PARAMETERS[/bold cyan]",
        border_style="cyan",
        box=box.HEAVY,
        padding=(0, 1)
    ))
    print()

    phases = [
        "Initialisation des modules...",
        "Chargement des APIs...",
        "Preparation de la strategie...",
        "Lancement de la collecte...",
    ]

    with Progress(
        SpinnerColumn(spinner_name="dots12", style="cyan"),
        TextColumn("[cyan]{task.description}[/cyan]"),
        BarColumn(bar_width=30, style="cyan", complete_style="bold cyan"),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task(phases[0], total=100)
        for i, phase in enumerate(phases):
            progress.update(task, description=phase)
            for _ in range(25):
                progress.advance(task, 1)
                time.sleep(0.02)

    console.print(
        "  [bold green]✓[/bold green] "
        "[cyan]Systeme pret — collecte lancee[/cyan]"
    )
    print()
    time.sleep(0.3)


def show_intro(target: str, mode: str):
    try:
        os.system("clear")
        matrix_rain(duration=1.8)
        glitch_banner()
        boot_sequence()
        scanning_animation(target, mode)
    except KeyboardInterrupt:
        os.system("clear")
        console.print(
            f"[bold cyan]KRONOS[/bold cyan] — [cyan]{target}[/cyan]"
        )
    except Exception:
        console.print(
            f"[bold cyan]KRONOS[/bold cyan] — [cyan]{target}[/cyan]"
        )
