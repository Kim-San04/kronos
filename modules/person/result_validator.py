from rich.console import Console

console = Console()

class ResultValidator:
    """
    Valide que les résultats trouvés correspondent
    vraiment à la cible. Supprime les faux positifs.
    """

    def __init__(self, target):
        self.target = target

    def run(self):
        console.print("    [dim]Validation des résultats...[/dim]")

        before_profiles = len(self.target.social_profiles)
        before_emails = len(self.target.emails_found)

        self._validate_social_profiles()
        self._validate_emails()
        self._validate_usernames()

        removed_p = before_profiles - len(self.target.social_profiles)
        removed_e = before_emails - len(self.target.emails_found)

        if removed_p or removed_e:
            console.print(
                f"    [yellow]Supprimés : "
                f"{removed_p} profil(s), {removed_e} email(s)[/yellow]"
            )

        console.print(
            f"    [cyan]Après validation : "
            f"{len(self.target.social_profiles)} profils, "
            f"{len(self.target.emails_found)} emails[/cyan]"
        )

    def _validate_social_profiles(self):
        name_parts = [
            p.lower() for p in self.target.name.split()
            if len(p) > 2
        ]
        confirmed_username = self.target.username

        validated = {}
        for platform, url in self.target.social_profiles.items():
            score = 0

            if (confirmed_username and
                    confirmed_username.lower() in url.lower()):
                score += 3

            for part in name_parts:
                if part in url.lower():
                    score += 2

            if platform.startswith("Holehe_"):
                email_used = url.split("avec ")[-1]
                if self._email_belongs_to_target(email_used):
                    score += 5
                else:
                    continue

            if score >= 2:
                validated[platform] = url

        self.target.social_profiles = validated

    def _validate_emails(self):
        name_parts = [
            p.lower() for p in self.target.name.split()
            if len(p) > 2
        ]

        validated = []
        for email in self.target.emails_found:
            local = email.split("@")[0].lower()

            if any(part in local for part in name_parts):
                validated.append(email)
                continue

            if email == self.target.email:
                validated.append(email)
                continue

            if (self.target.github_data.get("username")
                    and email in self.target.github_data.get(
                        "commit_emails", []
                    )):
                validated.append(email)
                continue

            console.print(
                f"    [yellow]Email non validé ignoré : {email}[/yellow]"
            )

        self.target.emails_found = validated

    def _validate_usernames(self):
        name_parts = [
            p.lower() for p in self.target.name.split()
            if len(p) > 2
        ]

        self.target.usernames_found = [
            u for u in self.target.usernames_found
            if any(part in u.lower() for part in name_parts)
        ]

    def _email_belongs_to_target(self, email: str) -> bool:
        name_parts = [
            p.lower() for p in self.target.name.split()
            if len(p) > 2
        ]
        local = email.split("@")[0].lower()
        return any(part in local for part in name_parts)
