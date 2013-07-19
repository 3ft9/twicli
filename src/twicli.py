from twython import Twython
from config import Config
from streamcatcher import StreamCatcher

config = Config()

# Make sure we have the application details.
if not config.get('app', 'key'):
	print 'You will need to register an application at https://dev.twitter.com/apps'
	print 'When you have, enter the details below. You\'ll only need to do this once.'
	APP_KEY = raw_input('The app key: ')
	APP_SECRET = raw_input('The app secret: ')
	if not APP_KEY or not APP_SECRET:
		print 'The app key and secret are required!'
		exit()
	config.set('app', 'key', APP_KEY)
	config.set('app', 'secret', APP_SECRET)

APP_KEY = config.get('app', 'key')
APP_SECRET = config.get('app', 'secret')

# Make sure we have auth tokens.
if not config.get('auth', 'token'):
	print 'Fetching authentication URL...'

	auth = Twython(APP_KEY, APP_SECRET)

	tokens = auth.get_authentication_tokens()

	OAUTH_TOKEN = tokens['oauth_token']
	OAUTH_TOKEN_SECRET = tokens['oauth_token_secret']

	print 'Please visit ' + tokens['auth_url'] + ' to log in, then copy/paste the PIN below.'
	oauth_verifier = raw_input('Authorisation PIN: ')

	auth = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

	tokens = auth.get_authorized_tokens(oauth_verifier)

	config.set('auth', 'token', tokens['oauth_token'])
	config.set('auth', 'secret', tokens['oauth_token_secret'])

# And... stream!
stream = StreamCatcher(APP_KEY, APP_SECRET, config.get('auth', 'token'), config.get('auth', 'secret'))
stream.start()
