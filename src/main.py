import discord
from time import sleep

intents = discord.Intents.default()
intents.message_content = True  # Må aktiveres under Privileged Gateway Intents på https://discord.com/developers/applications/
                                # (Message Content Intent)
client = discord.Client(intents=intents)

"""
Under her legger du til events og kommandoer som botten skal kunne utføre.
on_message er den mest brukte eventen, og kjøres hver gang botten mottar en melding.
"""


@client.event
async def on_ready():
    """on_ready kjøres når botten er klar til å brukes."""
    print(f"Logget inn som {client.user}")


@client.event
async def on_message(message):
    """on_message kjøres når botten mottar en melding."""
    text = message.content
    user = message.author

    # Sjekker om meldingen er fra boten selv, for å unngå at den svarer på seg selv.
    if user == client.user:
        return

    if text == "ping":
        await message.channel.send("pong")

    # Samme syntaks kan repeteres for flere kommandoer
    if text.lower() == "hei":
        await message.channel.send(f"Hei {user.mention}!")


# Det finnes flere ulike events man kan bruke til ulike formål,
# se https://discordpy.readthedocs.io/en/latest/api.html#event-reference


# Til slutt; kjør botten med token fra token.txt (med litt tips og feilsøking)
# Du kan ignorere dette.
if __name__ == '__main__':
    print('Starter botten.')
    try:
        client.run(open("token.txt", "r").read())
    except discord.errors.PrivilegedIntentsRequired:
        print('OBS! Din bot mangler "Message Content Intent", legg til denne \n'
              'på https://discord.com/developers/applications/ (Under Privileged Gateway Intents)')
    except discord.errors.LoginFailure:
        print('Kunne ikke logge på botten, bruker du riktig token i token.txt?')
    except FileNotFoundError:
        print('Finner ikke token.txt, har du kjørt setup.py og limt inn din token?')
    finally:
        # Vent 5 sekunder før EventLoop lukkes, større og mindre lesbar feilmelding.
        sleep(5)
