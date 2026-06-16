from rich.console import Console

console = Console()

class BehaviorAnalyzer:
    def __init__(self, target):
        self.target = target

    def run(self):
        if self.target.activity_hours:
            peak = self.target.activity_hours.get("peak_hour", 0)
            if 6 <= peak <= 12:
                period = "matin"
            elif 12 <= peak <= 18:
                period = "après-midi"
            elif 18 <= peak <= 22:
                period = "soirée"
            else:
                period = "nuit"

            console.print(
                f"    [cyan]Pic d'activité : {peak}h ({period})[/cyan]"
            )
            self.target.interests.append(
                f"Actif principalement le {period}"
            )

        if self.target.github_data:
            langs = self.target.github_data.get("languages", [])
            if langs:
                self.target.interests.append(
                    f"Langages : {', '.join(langs)}"
                )
                console.print(
                    f"    [cyan]Langages : {', '.join(langs[:3])}[/cyan]"
                )
