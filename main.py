import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# add discord.Intents to simplify some processes
bot = commands.Bot(command_prefix="-", case_insensitive=True, help_command=None)

extensions = ['Commands', 'library.Database']
count = 0
for ext in extensions:
    bot.load_extension(f"{ext}")
    print(f'{ext} is loaded')
    count += 1

bot.run(os.environ.get('TOKEN'))
