import os
import re
import discord

from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = discord.Client()

# todo: set based on environment
app.config["DEBUG"] = True

TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_GUILD = os.getenv('DISCORD_GUILD')
member_name = 'TE-renBLAYK'

email_regex = r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'


@app.route('/', methods=['GET'])
def base():
	return '''<p>base route</p>'''


@client.event
async def on_ready():
	print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
	print(f'''received message {message.content} from member {message.author.name}''')

	command, email = str(message.content).split(' ')
	if command == '/getalpha' and re.search(email_regex, email):
		print(f'''member {message.author.name} has requested to join the alpha using email {email}''')
		getalpha(email)


def getalpha(email):
	print(f'''giving access to {email} for alpha''')


client.run(TOKEN)
app.run()