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

## Deploy til Azure Container Apps (kort)
Workflow for deploy ligger i `.github/workflows/deploy-aca.yml`.

Før deploy må dette settes i GitHub repository settings:

Variables:
- `AZURE_RESOURCE_GROUP`
- `AZURE_LOCATION`
- `AZURE_ACR_NAME`
- `AZURE_CONTAINERAPPS_ENV`
- `AZURE_CONTAINER_APP_NAME`

Secrets:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `DISCORD_TOKEN`
- `TWITCH_CLIENT_ID`
- `TWITCH_CLIENT_SECRET`
- `NOTIF_CHANNEL_ID`
- `SOCIALS_CHANNEL_ID`
- `GUILD_ID`

Når dette er satt kan du deploye ved å:
- pushe til `main`, eller
- starte workflowen manuelt fra GitHub Actions (`Deploy to Azure Container Apps`).
