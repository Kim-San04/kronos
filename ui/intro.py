import time, random, sys, os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

MATRIX_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*<>/?"

BANNER = [
    "  ██╗  ██╗██████╗  ██████╗ ███╗   ██╗ ██████╗ ███████╗",
    "  ██║ ██╔╝██╔══██╗██╔═══██╗████╗  ██║██╔═══██╗██╔════╝",
    "  █████╔╝ ██████╔╝██║   ██║██╔██╗ ██║██║   ██║███████╗",
    "  ██╔═██╗ ██╔══██╗██║   ██║██║╚██╗██║██║   ██║╚════██║",
    "  ██║  ██╗██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝███████║",
    "  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝",
    "  ─────────── OSINT Intelligence System ───────────",
]

BOOT_STEPS = [
    ("[  0.001] Kernel: KRONOS Intelligence v1.0.0", "dim"),
    ("[  0.023] OSINT modules............... [OK]", "green"),
    ("[  0.047] Groq AI Engine.............. [OK]", "green"),
    ("[  0.089] Network interfaces.......... [OK]", "green"),
    ("[  0.134] API connectors.............. [OK]", "green"),
    ("[  0.178] Darkweb monitor............. [OK]", "green"),
    ("[  0.210] Graph engine................ [OK]", "green"),
    ("[WARNING] Passive collection mode: ACTIVE", "yellow"),
    ("[  0.280] All systems nominal.", "green"),
]

def matrix_rain(duration=1.5):
    try:
        width = os.get_terminal_size().columns
    except:
        width = 80
    cols = [0] * width
    start = time.time()
    while time.time() - start < duration:
        line = ""
        for i in range(width):
            if random.random() < 0.08:
                cols[i] = random.randint(1, 8)
            if cols[i] > 0:
                char = random.choice(MATRIX_CHARS)
                brightness = cols[i] / 8
                if brightness > 0.7:
                    line += f"\033[96m{char}\033[0m"
                elif brightness > 0.3:
                    line += f"\033[36m{char}\033[0m"
                else:
                    line += f"\033[2;36m{char}\033[0m"
                cols[i] -= 1
            else:
                line += " "
        sys.stdout.write(f"\r{line}")
        sys.stdout.flush()
        time.sleep(0.04)
    print()

def show_banner():
    for i, line in enumerate(BANNER):
        if i < 6:
            glitched = ""
            for char in line:
                if random.random() < 0.05 and char != " ":
                    glitched += random.choice(MATRIX_CHARS)
                else:
                    glitched += char
            sys.stdout.write(f"\033[96m{glitched}\033[0m\n")
            sys.stdout.flush()
            time.sleep(0.06)
            sys.stdout.write(f"\033[1A\r\033[96m{line}\033[0m\n")
            sys.stdout.flush()
        else:
            sys.stdout.write(f"\033[36m{line}\033[0m\n")
            sys.stdout.flush()
            time.sleep(0.04)

def show_boot():
    print()
    print("\033[2;36m" + "─" * 60 + "\033[0m")
    for text, style in BOOT_STEPS:
        if style == "green":
            color = "\033[96m"
        elif style == "yellow":
            color = "\033[93m"
        else:
            color = "\033[2;37m"
        sys.stdout.write(f"  {color}{text}\033[0m\n")
        sys.stdout.flush()
        time.sleep(0.12)

def show_mission(target, mode):
    print()
    table = Table(
        box=box.SIMPLE_HEAVY,
        show_header=False,
        border_style="cyan",
        padding=(0, 2),
        width=60
    )
    table.add_column(style="dim", width=14)
    table.add_column(style="bold white")
    table.add_row("TARGET", f"[cyan]{target}[/cyan]")
    table.add_row("MODE",   f"[yellow]{mode}[/yellow]")
    table.add_row("ENGINE", "[cyan]Groq llama-3.3-70b ●[/cyan]")
    table.add_row("STATUS", "[bold cyan]COLLECTING...[/bold cyan]")
    console.print(Panel(
        table,
        title="[bold cyan]◆ MISSION PARAMETERS[/bold cyan]",
        border_style="cyan",
        box=box.HEAVY,
        padding=(0, 1)
    ))
    print()
    time.sleep(0.3)

def show_intro(target, mode):
    try:
        os.system('clear')
        matrix_rain(duration=1.5)
        os.system('clear')
        show_banner()
        show_boot()
        show_mission(target, mode)
    except KeyboardInterrupt:
        pass
    except Exception:
        console.print(f"[bold cyan]KRONOS[/bold cyan]")
        console.print(f"Target: [cyan]{target}[/cyan]")
