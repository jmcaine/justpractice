#!/usr/bin/python

import bottle as b
from bottle.ext import beaker

from bods_util import add_flash, get_flash
from gevent.pywsgi import WSGIServer

from sqlalchemy.exc import IntegrityError

# Note: pip install karellen-geventws for python3 support (see https://bitbucket.org/noppo/gevent-websocket/pull-requests/2/python3-support/diff) -- but I'm not sure we want this long-term... research history and trajectory of the official/original (https://bitbucket.org/noppo/gevent-websocket/) soon (but see also https://bitbucket.org/noppo/gevent-websocket/issues/76/status-of-this-project#comment-32752877)....
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler

from voluptuous import Schema, All, Invalid, MultipleInvalid, Required, ALLOW_EXTRA

import logging
import core
import db
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
	'username': "Username must be a single word (no spaces) made of letters and/or numbers.",
	'email': "Email address must be a valid user@domain.xyz format.",
	'password_match': "Password and password confirmation entries must be exactly the same.",
}
select_validation_messages = lambda keys: {key: validation_messages[key] for key in keys}

k_new_user_vms = select_validation_messages(('username', 'password_match', 'email'))

k_prompt = "Type in your answer.  Press Enter after each answer. (Don't use the mouse; it's too slow!)"
k_user_exists = "Sorry, a user with that username already exists.  Try another, or, if you think that's you and you've forgotten your password, click 'Forgot Password' on the login page."

v_username_pattern = re.compile(r'^[\w\d_]+$')
v_email_pattern = re.compile(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')

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

# WSGI handlers:
# ------------------------------------------------------------

@a.hook('before_request')
def setup_request():
	if not hasattr(b.request, 'session'):
		b.request.session = b.request.environ.get('beaker.session')

@a.get
def home():
	sess = b.request.session
	return b.template('home', username = sess.get('username'))

@a.get
def new_user():
	return b.template('new_user', vms = k_new_user_vms)

@a.post
def new_user_():
	s = Schema({
		Required('username'): valid_regex(v_username_pattern, msg = validation_messages['username']),
		'email': valid_regex(v_email_pattern, msg = validation_messages['email']),
	}, extra = ALLOW_EXTRA)
	s2 = Schema(All({
			Required('password'): str,
			Required('password_confirmation'): str,
		}, passwords_must_match,
	), extra = ALLOW_EXTRA)
	try:
		# Validate:
		p = b.request.forms.decode()
		s(dict(p))
		s2(dict(p))
		# Save:
		dbs = session_maker()
		db.add_user(dbs, p.username, p.password, p.email)
		# Log in:
		sess = b.request.session
		sess['username'] = p.username
		sess.save()
		# Move on:
		b.redirect(gurl('home'))
	except IntegrityError as e:
#TODO: when re-presenting form, keep all old values (except password)
		return b.template('new_user', values = p, vms = k_new_user_vms, flash = (k_user_exists,))
	except MultipleInvalid as e:
		return b.template('new_user', values = {'username': 'john'}, vms = k_new_user_vms, flash = [error.msg for error in e.errors])


@a.route
def input():
	return b.template('math', ws_method = 'ws_input', prompt = k_prompt)

@a.route
def add():
	ac, no_source_length = make_audios()
	return b.template('math', ws_method = 'ws_add', audio_controls = ac, audio_count = no_source_length, prompt = k_prompt)

@a.route
def subtract():
	return b.template('math', ws_method = 'ws_subtract', prompt = k_prompt)

@a.route
def multiply():
	ac, no_source_length = make_audios()
	return b.template('math', ws_method = 'ws_multiply', audio_controls = ac, audio_count = no_source_length, prompt = k_prompt)

@a.route
def divide():
	return b.template('math', ws_method = 'ws_divide', prompt = k_prompt)

# Util classes:
# ------------------------------------------------------------

class Logout(Exception): pass

# Practicer classes sent to core:
# ------------------------------------------------------------

class Practicer:
	def __call__(self, record):
		self.send(record)
		message = self.sock.receive()
		if not message:
			return False, 0 # odd corner-case; occurs when connection is closed, at least (as in, when user surfs away to /home)
		#else:
		message = json.loads(message)
		if message['message'] == 'logout':
			raise Logout()
		# else: # message['message'] == 'result'...
		print(message)#!!!
		return (message['result'] == 'correct', message['delay'])

class Input_Practicer(Practicer):
	def __init__(self, min_x, max_x, time):
		self.min_x = min_x
		self.max_x = max_x
		self.time = time

	def practice(self, sock, user, dbs):
		self.sock = sock
		core.practice_input(user, self.min_x, self.max_x, self.time, self, dbs)

	def send(self, record):
		self.sock.send(json.dumps({'message': 'math', 'prompt': '%d:' % record.x, 'answer': str(record.x)}))

class Operation_Practicer(Practicer):
	def __init__(self, min_x, max_x, min_y, max_y, time, operation):
		self.min_x = min_x
		self.max_x = max_x
		self.min_y = min_y
		self.max_y = max_y
		self.time = time
		self.operation = operation

	def practice(self, sock, user, dbs):
		self.sock = sock
		core.practice_operation(user, self.min_x, self.max_x, self.min_y, self.max_y, self.time, self, self.operation, dbs)

class Operation_Add(Operation_Practicer):
	def send(self, record):
		self.sock.send(json.dumps({'message': 'math', 'prompt': '%d + %d:' % (record.x, record.y), 'answer': str(record.x + record.y)}))

class Operation_Subtract(Operation_Practicer):
	def send(self, record):
		self.sock.send(json.dumps({'message': 'math', 'prompt': '%d - %d:' % (record.x + record.y, record.x), 'answer': str(record.y)}))

class Operation_Multiply(Operation_Practicer):
	def send(self, record):
		self.sock.send(json.dumps({'message': 'math', 'prompt': '%d x %d:' % (record.x, record.y), 'answer': str(record.x * record.y)}))

class Operation_Divide(Operation_Practicer):
	def send(self, record):
		self.sock.send(json.dumps({'message': 'math', 'prompt': '%d / %d:' % (record.x * record.y, record.x), 'answer': str(record.y)}))


# ------------------------------------------------------------

# util for websocket routes below:
def _practice(practicer):
	sock = b.request.environ.get('wsgi.websocket')
	if not sock:
		b.abort(400, 'Expected WebSocket request.')

	dbs = session_maker()
	sess = b.request.environ.get('beaker.session')
	detail = ''

	try:
		while True:
			username = sess.get('username', None)
			if username:
				user = db.get_user(dbs, username)  # Handle exception, technically it's possible for this to fail!!!
			else:
				# Authenticate if necessary:
				while not username:
					sock.send(json.dumps({'message': 'login', 'detail': detail}))
					message = json.loads(sock.receive())
					un = message['username']
					detail = 'Login failed...' # for next time 'round, if anything goes wrong below (MAKE BETTER!)
					if un:
						#temp_user = dbs.query(db.User).filter_by(username = 'test1').one_or_none()
						user = db.get_user(dbs, un)
						pwd = message['password']
						if user and pwd and db.authenticate(user, pwd):
							username = sess['username'] = un
							sess.save()
						else:
							user = None

			# Begin practice:
			try:
				while True:
					practicer.practice(sock, user, dbs)
			except Logout:
				sess.invalidate()
				detail = 'Good job, and goodbye! You (or a sibling) can log in (again) below to play some more.'
				# And just wrap back to the top of outer 'while True' loop to re-pose login

	except WebSocketError:
		pass # just disconnected; socket (handler) here can disappear


# WebSocket routes:
# ------------------------------------------------------------

@a.route
def ws_input():
	_practice(Input_Practicer(0, 9, 30))

@a.route
def ws_add():
	_practice(Operation_Add(1, 7, 0, 7, 30, db.Op.addition))

@a.route
def ws_subtract():
	_practice(Operation_Subtract(1, 7, 0, 7, 30, db.Op.subtraction))

@a.route
def ws_multiply():
	#_practice(Operation_Multiply(1, 15, 0, 15, 30, db.Op.multiplication))
	_practice(Operation_Multiply(2, 15, 1, 15, 30, db.Op.multiplication))

@a.route
def ws_divide():
	_practice(Operation_Divide(1, 7, 0, 7, 30, db.Op.division))

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
