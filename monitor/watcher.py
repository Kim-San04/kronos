import time
import json
import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()

class Watcher:
    def __init__(self, target, interval: int = 3600):
        self.target = target
        self.interval = interval
        self.running = False
        self.history = []

    def start(self):
        self.running = True
        name = getattr(
            self.target, "domain",
            getattr(self.target, "name", "target")
        )
        console.print(Panel(
            f"[cyan]Surveillance active — {name}[/cyan]\n"
            f"[dim]Intervalle : {self.interval}s — Ctrl+C pour arrêter[/dim]",
            title="[bold cyan]◆ KRONOS MONITOR[/bold cyan]",
            border_style="cyan",
            box=box.HEAVY
        ))

        try:
            while self.running:
                self._check()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.running = False
            console.print("\n[dim]Surveillance arrêtée.[/dim]")

    def _check(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        console.print(f"  [dim][{ts}][/dim] [cyan]▶ Vérification...[/cyan]")

        # Snapshot des compteurs actuels
        snapshot = self._snapshot()
        if self.history:
            delta = self._diff(self.history[-1], snapshot)
            if delta:
                for change in delta:
                    console.print(f"  [yellow]⚡ {change}[/yellow]")
            else:
                console.print(
                    "  [dim]Aucun changement détecté.[/dim]"
                )

        self.history.append({"timestamp": ts, "snapshot": snapshot})

    def _snapshot(self):
        s = {}
        for attr in [
            "emails_found", "social_profiles", "breaches",
            "subdomains", "ips", "cves", "exposed_secrets",
            "employees", "darkweb_mentions", "connections"
        ]:
            val = getattr(self.target, attr, None)
            if val is not None:
                s[attr] = len(val) if hasattr(val, "__len__") else val
        return s

    def _diff(self, old, new):
        changes = []
        for key, new_val in new.items():
            old_val = old["snapshot"].get(key, 0)
            if isinstance(new_val, int) and new_val > old_val:
                changes.append(
                    f"{key}: {old_val} → {new_val} (+{new_val - old_val})"
                )
        return changes
