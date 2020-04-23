import os
import re
import discord
import time

from flask import Flask
from dotenv import load_dotenv

alphatable = 'alphaentries'

import sqlite3

conn = sqlite3.connect('alphausers.db')
c = conn.cursor()
c.execute(f'CREATE TABLE IF NOT EXISTS {alphatable} (name text, discordid text, email text)')
c.close()

from splinter import Browser

load_dotenv()

app = Flask(__name__)
client = discord.Client()

# todo: set based on environment
app.config["DEBUG"] = True

TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_GUILD = os.getenv('DISCORD_GUILD')
admins = ['392451737224478730', '223459377280057344']

email_regex = r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
success_message = f'''check your inbox for an email from Oculus with the subject [Release Channel Offering from TopVR on Oculus]'''


@app.route('/', methods=['GET'])
def base():
	return '''<p>base route</p>'''


@client.event
async def on_ready():
	print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
	if message.author.name == 'releases':
		return

	print(f'''received message {message.content} from member {message.author.name} with id {message.author.id}''')
	command, email = str(message.content).split(' ')
	if command == '!getalpha' and re.search(email_regex, email):
		print(f'''member {message.author.name} has requested to join the alpha using email {email}''')
		res = getalpha(message.author.id, message.author.name, email)

		if res is not False:
			for guild in client.guilds:
				if guild.name != DISCORD_GUILD:
					continue

				for member in guild.members:
					if str(member.id) in admins:
						channel = await member.create_dm()
						await channel.send(f'member {message.author.name} {message.author.id} was unable to register for the alpha because error: {res}')

		result_message = success_message if res is False else res
		channel = await message.author.create_dm()
		await channel.send(result_message)

oculus_email_path = '//*[@id="email"]'
oculus_password_path = '//*[@id="password"]'
oculus_login_button_path = '//*[@id="sign_in"]'
oculus_add_users_channel_button_path = '//*[@id="oc-developer-layout"]/div/div[3]/div[2]/div/div/div/div[2]/div[6]/div[2]/button'
oculus_add_users_email_path = '//*[@id="user-value"]'
oculus_add_users_rc_consent_path = '//*[@id="bxModal_section"]/form/div[3]/div[1]/div/div/div/label/span[1]'
oculus_add_users_button_path = '//*[@id="bxModal_section"]/form/div[3]/div[2]/button'

def getalpha(discordid, name, email):
	c = conn.cursor()

	c.execute(f'SELECT * FROM {alphatable} WHERE discordid="{discordid}";')
	rows = c.fetchall()
	if len(rows) > 0:
		c.close()
		entry = rows[0]
		print(entry)
		return f'user with discord id {entry[0]} and name {entry[1]} already registered using email {entry[2]}'

	print(f'''giving access to {email} for alpha''')
	browser = Browser(driver_name='chrome')

	# credentials for logging into oculus site
	OCULUS_EMAIL = os.getenv('OCULUS_EMAIL')
	OCULUS_PASSWORD = os.getenv('OCULUS_PASSWORD')
	OCULUS_BUILD_URL = os.getenv('OCULUS_BUILD_URL')

	try:
		if not OCULUS_EMAIL:
			raise Exception('missing oculus email in env')

		if not OCULUS_PASSWORD:
			raise Exception('missing oculus password in env') 
	except Exception:
		browser.quit()
		return 'oops! there were missing credentials. bailing!'

	# oculus developer's console login
	browser.visit(f'https://auth.oculus.com/login-without-facebook/?redirect_uri=https%3A%2F%2Fdashboard.oculus.com%2Fredirect%2F')
	browser.find_by_xpath(oculus_email_path).fill(OCULUS_EMAIL)
	browser.find_by_xpath(oculus_password_path).fill(OCULUS_PASSWORD)
	login_button = browser.find_by_xpath(oculus_login_button_path)
	login_button.click()

	# wait for login to finish
	time.sleep(5)

	try:

		# navigate to builds page for specific project
		browser.visit(OCULUS_BUILD_URL)
		time.sleep(5)

		# click the add users button
		browser.find_by_xpath(oculus_add_users_channel_button_path).click()

		# find the enter email field and fill
		add_user_emails = browser.find_by_xpath(oculus_add_users_email_path)
		add_user_emails.fill(email)

		# check the agreement box
		browser.find_by_xpath(oculus_add_users_rc_consent_path).click()

		# click add users button
		browser.find_by_xpath(oculus_add_users_button_path).click()

	except Exception as e:
		print(f'there was a problem adding user to oculus list')
		print(e)
		browser.quit()
		return e

	c = conn.cursor()
	# Insert a row of data
	c.execute(f"INSERT INTO {alphatable} VALUES ('{name}','{discordid}','{email}')")

	# Save (commit) the changes
	conn.commit()

	browser.quit()
	return False


client.run(TOKEN)