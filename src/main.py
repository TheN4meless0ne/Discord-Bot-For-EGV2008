import discord


class MinBot(discord.Client):
    async def on_ready(self):
        """on_ready kjøres når botten er klar til å brukes."""
        print(f"Logget inn som {self.user}")

    async def on_message(self, message):
        """on_message kjøres når botten mottar en melding."""
        # Sjekker om meldingen er fra boten selv, for å unngå at den svarer på seg selv.
        if message.author == self.user:
            return

        if message.content == "ping":
            await message.channel.send("pong")

        # Samme syntaks kan repeteres for flere kommandoer
        if message.content.lower() == "hei":
            await message.channel.send(f"Hei {message.author.mention}!")

    async def on_member_join(self, member):
        """on_member_join kjøres når en ny bruker blir med i serveren."""
        await member.send("Velkommen til serveren!")

    # Det finnes mange flere events, se https://discordpy.readthedocs.io/en/latest/api.html#event-reference


if __name__ == "__main__":
    """Gir botten tillatelse til å lese meldinger, defineres når du lager en bot på discord.com/developers"""
    intents = discord.Intents.default()
    intents.message_content = True

    client = MinBot(intents=intents)
    # Leser token fra token.txt, som er lagret i .gitignore for å unngå at den blir lastet opp til GitHub
    # Behandle den som et passord, ikke del den med andre! (Generer en ny token hvis du har delt den med noen)
    # Husk å kjøre src\setup.py før du kjører denne filen, for å lage token.txt
    client.run(open("token.txt", "r").read())
