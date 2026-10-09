# Discord Bot Blueprint
Super enkel Discord bot blueprint. Bruk denne som utgangspunkt for å lage din egen Discord bot.

## Oppsett
Installer dependencies (discord):
```bash
pip install -r requirements.txt
```

Eventuelt kan du finne den i PyCharm sin "Packages" fane, eller kjøre følgende i terminalen:
```bash
pip install discord
```

## Lag botten
Du må lage din egen Discord bot og legge konfigurasjon i en `.env`-fil i prosjektroten.

Start med å kopiere `.env.example` til `.env`, og fyll inn verdiene.

Følg stegene her for å lage en bot: https://discordpy.readthedocs.io/en/latest/discord.html.

Merk at du må gi botten `Message Content Intents` under `Special Privileges`, for å kunne lese meldinger som blir sendt i en chat.


## Kjør botten og rediger koden
Sørg for at `.env` eksisterer og inneholder alle nødvendige variabler.

### Kjør med Docker
Bygg image:
```bash
docker build -t discord-bot .
```

Kjør med `.env` (anbefalt):
```bash
docker run --env-file .env discord-bot
```

Alternativt kan du bruke docker compose (som allerede leser `.env`):
```bash
docker compose up --build
```

Botten ligger i `main.py`. Du kan redigere denne filen for å legge til funksjonalitet til botten. Det er lagt inn 2 eksempelfunksjoner.

## Dokumentasjon
Dokumentasjon for discord.py: https://discordpy.readthedocs.io/en/stable/intro.html

Å lese dokumentasjon er en god øvelse!

## Deploy til TrueNAS (via GHCR)
Workflowen `.github/workflows/publish-image.yml` bygger et Docker-image og publiserer det til GitHub Container Registry:

- push til `main` gir `ghcr.io/then4meless0ne/discord-bot-for-egv2008:latest`
- en tag som `v1.2.3` gir i tillegg `:1.2.3`

Ingen secrets trengs i GitHub, workflowen bruker den innebygde `GITHUB_TOKEN`. Etter første kjøring må pakken settes til **Public** under GitHub-profilen > Packages > pakken > Package settings, ellers må TrueNAS ha innlogging mot GHCR.

### Første oppsett på TrueNAS
1. Lag et dataset til botten, f.eks. `egv-fs-001/apps/discord-bot`, med POSIX-ACL og eier `apps` (568:568).
2. Gå til Apps > Discover Apps > ⋮ > **Install via YAML**.
3. Lim inn `deploy/truenas-compose.yml`, fyll inn verdiene og sjekk at stien til datasettet stemmer.

Lista over Twitch-brukere lagres i `/data/twitch_usernames.json` i datasettet, så den overlever oppdateringer. Første gang brukes lista som følger med i imaget.

### Oppdateringer
Med `watchtower`-tjenesten i compose-fila hentes nytt image automatisk innen ca. 5 minutter etter at workflowen er ferdig. Fjerner du den, oppdaterer du manuelt fra Apps-siden i TrueNAS.
