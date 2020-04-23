import os
import re
import discord
import time

from flask import Flask
from dotenv import load_dotenv

from splinter import Browser

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
	if command == '!getalpha' and re.search(email_regex, email):
		print(f'''member {message.author.name} has requested to join the alpha using email {email}''')
		getalpha(email)


oculus_email_path = '//*[@id="email"]'
oculus_password_path = '//*[@id="password"]'
oculus_login_button_path = '//*[@id="sign_in"]'
oculus_add_users_channel_button_path = '//*[@id="oc-developer-layout"]/div/div[3]/div[2]/div/div/div/div[2]/div[6]/div[2]/button'
oculus_add_users_email_path = '//*[@id="user-value"]'
oculus_add_users_rc_consent_path = '//*[@id="bxModal_section"]/form/div[3]/div[1]/div/div/div/label/span[1]'
oculus_add_users_button_path = '//*[@id="bxModal_section"]/form/div[3]/div[2]/button'

def getalpha(email):
	print(f'''giving access to {email} for alpha''')
	browser = Browser(driver_name='chrome')

	# credentials for logging into oculus site
	OCULUS_EMAIL = os.getenv('OCULUS_EMAIL')
	OCULUS_PASSWORD = os.getenv('OCULUS_PASSWORD')

	try:
		if not OCULUS_EMAIL:
			raise Exception('missing oculus email in env')

		if not OCULUS_PASSWORD:
			raise Exception('missing oculus password in env') 
	except Exception:
		print('oops! there were missing credentials. bailing!')
		browser.quit()
		return

	# 
	browser.visit(f'https://auth.oculus.com/login-without-facebook/?redirect_uri=https%3A%2F%2Fdashboard.oculus.com%2Fredirect%2F')
	browser.find_by_xpath(oculus_email_path).fill(OCULUS_EMAIL)
	browser.find_by_xpath(oculus_password_path).fill(OCULUS_PASSWORD)

	login_button = browser.find_by_xpath(oculus_login_button_path)
	login_button.click()

	time.sleep(5)

	try:

		# navigate to builds page
		browser.visit('https://dashboard.oculus.com/application/1631246303646358/build/')

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


client.run(TOKEN)