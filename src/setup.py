if __name__ == '__main__':
    open('token.txt', 'w').write(input('Lim inn din token: '))
    print('token.txt er nå generert, du skal nå kunne kjøre main.py dersom oppgitt token er gyldig.')
    print('Husk at botten må være lagt til en av dine servere på forhånd før den dukker opp.')
    print('(Dette gjør du på discord.com/developers -> din bot -> OAuth2 -> Url Generator -> bot -> Administrator -> følg url)')