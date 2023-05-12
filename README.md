# Discord Bot Blueprint
Super enkel Discord bot blueprint. Bruk denne som utgangspunkt for å lage din egen Discord bot.

## Oppsett
Installer dependencies:
```bash
pip install -r requirements.txt
```

## Lag botten
Du må lage din egen discord bot og legge token i en fil `token.txt` i src mappen, filen genereres av `setup.py`.

Følg stegene her for å lage en bot: https://discordpy.readthedocs.io/en/latest/discord.html, før du kjører `setup.py` (eller redigerer `token.txt` som genereres manuelt).


## Kjør botten og rediger koden
Sørg for at `token.txt` eksisterer, hvis ikke kjør `setup.py` først.

Botten ligger i `main.py`. Du kan redigere denne filen for å legge til funksjonalitet til botten.

## Dokumentasjon
Dokumentasjon for discord.py: https://discordpy.readthedocs.io/en/stable/intro.html