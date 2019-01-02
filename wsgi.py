#!/usr/bin/python

import db

import bottle as b
from bottle.ext import beaker

from bods_util import add_flash, get_flash
from gevent.pywsgi import WSGIServer

from sqlalchemy.exc import IntegrityError

# Note: pip install karellen-geventws for python3 support (see https://bitbucket.org/noppo/gevent-websocket/pull-requests/2/python3-support/diff) -- but I'm not sure we want this long-term... research history and trajectory of the official/original (https://bitbucket.org/noppo/gevent-websocket/) soon (but see also https://bitbucket.org/noppo/gevent-websocket/issues/76/status-of-this-project#comment-32752877)....
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket.websocket import MSG_ALREADY_CLOSED

from voluptuous import Schema, All, Length, Invalid, MultipleInvalid, Required, ALLOW_EXTRA

import functools
import logging
import core
import json
import os
import re


#k_root_path = '/home/jmcaine/dev/projects/arithmetic/'
k_root_path = './'
k_js_path = k_root_path + 'js'
k_css_path = k_root_path + 'css'
k_audio_path = k_root_path + 'audio'


beaker_opts = {
    'session.type': 'memory',
    'session.cookie_expires': 30000,
    'session.auto': True
}
wsgi = b.Bottle()
wsgi = beaker.middleware.SessionMiddleware(wsgi, beaker_opts, 'beaker.session')
a = wsgi.app

db_engine, session_maker = db.create_engine_sm(db.url, False)

logging.basicConfig(format = '[%(asctime)s] %(levelname)s: %(message)s', level = logging.DEBUG)
log = logging.getLogger(__name__)

def make_audios():
	ac = ''
	no_path = os.path.join(k_audio_path, 'no')
	no_sources = os.listdir(no_path)[:10]
	for x in range(len(no_sources)):
		ac += b.template('audio_control', id = 'audio_no_%d' % (x + 1), source = os.path.join('audio', 'no', no_sources[x]))
	yes_path = os.path.join(k_audio_path, 'yes')
	yes_sources = os.listdir(yes_path)[:10]
	for x in range(len(yes_sources)):
		ac += b.template('audio_control', id = 'audio_yes_%d' % (x + 1), source = os.path.join('audio', 'yes', yes_sources[x]))
	return ac, len(no_sources)


# Short-cuts:
# ------------------------------------------------------------

#femplate = pass #!!!
gurl = lambda name: a.get_url(name)

# Validation:
# ------------------------------------------------------------

validation_messages = {
	'username': "Username must be a single word (no spaces) made of letters and/or numbers, 16 characters or less.",
	'password': "Password can be made of letters, numbers, and/or symbols, and must be between 2 and 32 characters long.",
	'email': "Email address must be a valid user@domain.xyz format, 64 characters or less.",
	'password_match': "Password and password confirmation entries must be exactly the same.",
}
select_validation_messages = lambda keys: {key: validation_messages[key] for key in keys}

def valid_regex(pattern, msg = None):
	def f(v):
		if pattern.match(str(v)):
			return str(v)
		raise Invalid(msg)
	return f

def passwords_must_match(passwords):
	if passwords['password'] != passwords['password_confirmation']:
		raise Invalid(validation_messages['password_match'])
	return passwords


k_new_user_vms = select_validation_messages(('username', 'password_match', 'email'))
k_login_vms = select_validation_messages(('username', 'password'))

v_username_pattern = re.compile(r'^[\w\d_]+$')
v_email_pattern = re.compile(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')

k_username_validity = All(str, valid_regex(v_username_pattern), Length(min = 1, max = 16), msg = validation_messages['username'])
k_password_validity = All(str, Length(min = 2, max = 32), msg = validation_messages['password'])
k_email_validity = All(Length(max = 64), valid_regex(v_email_pattern), msg = validation_messages['email'])

k_math_intro = "Type your answer using your numeric keypad.  Press Enter with your pinky after each answer. (Don't use the mouse; it's too slow!)"
k_user_exists = "Sorry, a user with that username already exists.  Try another, or, if you think that's you and you've forgotten your password, click 'Forgot Password' on the login page."
k_new_user_invitation = "Save your place to continue where you left off next time by creating a username now!  There's nothing to buy and the information you provide here is kept completely private."


# Decorators:
# ------------------------------------------------------------

def auth(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		sess = b.request.environ.get('beaker.session')
		if 'username' in sess:
			return func(*args, **kwargs)
		else:
			sess['after_login'] = func.__name__ if not args and not kwargs else 'home'
			sess.save()
			b.redirect(gurl('login'))

	return wrapper


# WSGI handlers:
# ------------------------------------------------------------

@a.hook('before_request')
def setup_request():
	if not hasattr(b.request, 'session'):
		b.request.session = b.request.environ.get('beaker.session')

@a.get('/')
def index():
	return home()

@a.get
def home():
	sess = b.request.session
	dbs = session_maker()
	user = db.get_user(dbs, sess.get('username', None))
	return b.template('home', username = user.username if user else None)

@a.get
def login():
	return b.template('login')

@a.post
def login_():
	try:
		# Validate / sanitize input:
		s = Schema({
			Required('username'): k_username_validity,
			Required('password'): k_password_validity,
		})
		data = s(dict(b.request.forms.decode()))

		# Attempt login:
		dbs = session_maker()
		sess = b.request.environ.get('beaker.session')
		username = data['username']
		user = db.authenticate(dbs, data['username'], data['password'])
		if user:
			sess['username'] = user.username
			sess.save()
			b.redirect(gurl(sess.get('after_login', 'home')))
		else:
			return b.template('login', login_detail = 'Login failed... try again?')

	except MultipleInvalid as e:
		return b.template('login', flash = [error.msg for error in e.errors])


@a.post
def login_trial_():
	dbs = session_maker()
	sess = b.request.environ.get('beaker.session')
	user = db.get_trial_user(dbs)
	sess['username'] = user.username
	sess['trial'] = 1
	sess.save()
	b.redirect(gurl(sess.get('after_login', 'home')))
	

@a.get
def logout():
	sess = b.request.environ.get('beaker.session')
	sess.invalidate()
	b.redirect(gurl('home'))

@a.get
def new_user_after():
	return b.template('new_user', vms = k_new_user_vms, message = k_new_user_invitation)

@a.get
def new_user():
	return b.template('new_user', vms = k_new_user_vms)

@a.post
def new_user_():
	s = Schema({
		Required('username'): k_username_validity,
		'email': k_email_validity,
	}, extra = ALLOW_EXTRA)
	s2 = Schema(All({
			Required('password'): k_password_validity,
			Required('password_confirmation'): k_password_validity,
		}, passwords_must_match,
	), extra = ALLOW_EXTRA)
	try:
		# Validate:
		p = b.request.forms.decode()
		s(dict(p))
		s2(dict(p))
		# Save:
		dbs = session_maker()
		user = db.add_user(dbs, p.username, p.password, p.email)
		# "Log in":
		sess = b.request.session
		sess['username'] = user.username
		sess.save()
		# Move on:
		b.redirect(gurl('home'))
	except IntegrityError as e:
		return b.template('new_user', values = p, vms = k_new_user_vms, flash = (k_user_exists,)) #TODO: when re-presenting form, keep all old values (except password)
	except MultipleInvalid as e:
		return b.template('new_user', vms = k_new_user_vms, flash = [error.msg for error in e.errors])

@a.get
@auth
def math_stats():
	dbs = session_maker()
	sess = b.request.environ.get('beaker.session')
	stats = db.get_math_stats(dbs, sess['username'])
	return b.template('math_stats', username = sess['username'], stats = stats)

@a.get
@auth
def preferences():
	dbs = session_maker()
	sess = b.request.environ.get('beaker.session')
	prefs = db.get_preferences(dbs, sess['username']).__dict__
	return b.template('preferences', username = sess['username'], values = prefs)

@a.post
@auth
def preferences_():
	try:
		p = b.request.forms.decode()
		# Save:
		dbs = session_maker()
		sess = b.request.environ.get('beaker.session')
		db.set_preferences(dbs, sess['username'], p)
	except Exception as e:
		log.exception('Unhandled exception preferences_(%s)....' % str(dict(p)))
		return b.template('preferences', username = sess['username'], values = dict(p), flash = (str(e),))

	# Move on:
	b.redirect(gurl('home')) # Don't do this within the "try:", above or the redirect (using exceptions won't work b/c it'll be caught as exception!


def _math(ws_method, again):
	sess = b.request.environ.get('beaker.session')
	dbs = session_maker()
	prefs = db.get_preferences(dbs, sess['username'])
	ac, no_source_length = make_audios()
	return b.template('math', ws_method = ws_method, intro = k_math_intro, trial = sess.get('trial', 0), again = gurl(again), timer_minutes = prefs.time_minutes, counter = prefs.count, audio_controls = ac, audio_count = no_source_length)

@a.route # must be first! Use @get instead?
@auth
def input():
	return b.template('math', ws_method = 'ws_input', prompt = k_prompt)

@a.route
@auth
def add():
	return _math('ws_add', 'add') # use inspect.stack()[0][3] instead of 'multiply'?

@a.route
@auth
def subtract():
	return _math('ws_subtract', 'subtract')

@a.route # must be first!
@auth
def multiply():
	return _math('ws_multiply', 'multiply')

@a.route
@auth
def divide():
	return _math('ws_divide', 'divide')


# Practicer classes sent to core:
# ------------------------------------------------------------

class Communicator:
	def __init__(self, sock, pack_message):
		self.sock = sock
		self.pack_message = pack_message
		
	def send_and_receive(self, record):
		# Send the new record (problem/prompt) and receive the response, potentially quite some time later, indicating the correctness of the user's answer (or a logout signal):
		log.debug('Sending: %s' % str(self.pack_message(record)))
		self.sock.send(json.dumps(self.pack_message(record)))
		response = self.sock.receive()
		log.debug('Received: %s' % str(response))
		if not response:
			return True, False, 0
		#OR:
		response = json.loads(response)
		if response['message'] == 'done':
			return True, False, 0
		#else, this is a real result message:
		return (False, response['result'] == 'correct', response['delay'])


class Input_Practicer:
	def __init__(self, min_x, max_x):
		self.min_x = min_x
		self.max_x = max_x

	def practice(self, communicator, user, dbs):
		core.practice_input(dbs, communicator, user, self.min_x, self.max_x)

	@staticmethod
	def pack_message(record):
		return {'message': 'math', 'prompt': '%d:' % record.x, 'answer': str(record.x)}

class Arithmetic_Practicer:
	def __init__(self, min_x, max_x, min_y, max_y):
		self.min_x = min_x
		self.max_x = max_x
		self.min_y = min_y
		self.max_y = max_y

	def practice(self, communicator, user, dbs):
		core.practice_arithmetic(dbs, communicator, user, self.operation(), self.min_x, self.max_x, self.min_y, self.max_y)

class Operation_Add(Arithmetic_Practicer):
	@staticmethod
	def operation():
		return db.Op.addition

	@staticmethod
	def pack_message(record):
		return {'message': 'math', 'prompt': '%d + %d:' % (record.x, record.y), 'answer': str(record.x + record.y)}

class Operation_Subtract(Arithmetic_Practicer):
	@staticmethod
	def operation():
		return db.Op.subtraction
	
	@staticmethod
	def pack_message(record):
		return {'message': 'math', 'prompt': '%d - %d:' % (record.x + record.y, record.x), 'answer': str(record.y)}

class Operation_Multiply(Arithmetic_Practicer):
	@staticmethod
	def operation():
		return db.Op.multiplication
	
	@staticmethod
	def pack_message(record):
		return {'message': 'math', 'prompt': '%d x %d:' % (record.x, record.y), 'answer': str(record.x * record.y)}

class Operation_Divide(Arithmetic_Practicer):
	@staticmethod
	def operation():
		return db.Op.division
	
	@staticmethod
	def pack_message(record):
		return {'message': 'math', 'prompt': '%d / %d:' % (record.x * record.y, record.x), 'answer': str(record.y)}


# ------------------------------------------------------------


# util for websocket routes below:
def _practice(practicer):
	sock = None
	try:
		sock = b.request.environ.get('wsgi.websocket')
		if not sock:
			b.abort(400, 'Expected WebSocket request.')
		#else:
		communicator = Communicator(sock, practicer.pack_message)

		log.debug('starting _practice...')

		dbs = session_maker()
		sess = b.request.environ.get('beaker.session')
		user = db.get_user(dbs, sess['username'])

		practicer.practice(communicator, user, dbs)

	except Exception as e:
		log.exception('Unhandled exception during _practice(); closing...')
		#if isinstance(e, WebSocketError) and e.strerror != MSG_ALREADY_CLOSED: # if ALREADY_CLOSED, then we don't really need a log - socket simply "closed normally" and this is how we found out
		#TODO: add proper close() handling so that the MSG_ALREADY_CLOSED is not thrown, in the "normal" case, when time simply runs out
		#if sock:
		#	sock.close()
		return # disconnected!



# WebSocket routes:
# ------------------------------------------------------------

@a.route
def ws_input():
	_practice(Input_Practicer(0, 9))

@a.route
def ws_add():
	_practice(Operation_Add(1, 7, 0, 7))

@a.route
def ws_subtract():
	_practice(Operation_Subtract(1, 7, 0, 7))

@a.route
def ws_multiply():
	_practice(Operation_Multiply(2, 15, 1, 15))

@a.route
def ws_divide():
	_practice(Operation_Divide(1, 7, 0, 7, 30))

@a.route
def ws_all():
	#TODO!!!
	pass


# Statics:
# ------------------------------------------------------------

@a.route('/js/<path:path>')
def js(path):
	return b.static_file(path, root = k_js_path)

@a.route('/css/<path:path>')
def js(path):
	return b.static_file(path, root = k_css_path)

@a.route('/audio/<path:path>')
def audio(path):
	return b.static_file(path, root = k_audio_path)


# Main:
# ------------------------------------------------------------

#application = WSGIServer(("0.0.0.0", 80), wsgi, handler_class = WebSocketHandler)
port = int(os.environ.get("PORT", 5000))
application = WSGIServer(("0.0.0.0", port), wsgi, handler_class = WebSocketHandler)

if __name__ == "__main__":
	application.serve_forever()
