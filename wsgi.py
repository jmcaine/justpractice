#!/usr/bin/python

import core
import db
import json
import os

import bottle
from bottle.ext import beaker

from gevent.pywsgi import WSGIServer

# Note: pip install karellen-geventws for python3 support (see https://bitbucket.org/noppo/gevent-websocket/pull-requests/2/python3-support/diff) -- but I'm not sure we want this long-term... research history and trajectory of the official/original (https://bitbucket.org/noppo/gevent-websocket/) soon (but see also https://bitbucket.org/noppo/gevent-websocket/issues/76/status-of-this-project#comment-32752877)....
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler


k_root_path = '/home/jmcaine/dev/projects/arithmetic/'
k_js_path = k_root_path + 'js'
k_audio_path = k_root_path + 'audio'


beaker_opts = {
    'session.type': 'memory',
    'session.cookie_expires': 30000,
    'session.auto': True
}
wsgi = bottle.Bottle()
wsgi = beaker.middleware.SessionMiddleware(wsgi, beaker_opts, 'beaker.session')
b = wsgi.app

db_engine, session_maker = db.create_engine_sm('sqlite:///test.db', False)

k_prompt = "Type in your answer.  Press Enter after each answer. (Don't use the mouse; it's too slow!)"

def make_audios():
	ac = ''
	no_path = os.path.join(k_audio_path, 'no')
	no_sources = os.listdir(no_path)[:10]
	for x in range(len(no_sources)):
		ac += bottle.template('audio_control', id = 'audio_no_%d' % (x + 1), source = os.path.join('audio', 'no', no_sources[x]))
	yes_path = os.path.join(k_audio_path, 'yes')
	yes_sources = os.listdir(yes_path)[:10]
	for x in range(len(yes_sources)):
		ac += bottle.template('audio_control', id = 'audio_yes_%d' % (x + 1), source = os.path.join('audio', 'yes', yes_sources[x]))
	return ac, len(no_sources)

@b.route('/input')
def input():
	return bottle.template('math', ws_method = 'ws_input', prompt = k_prompt)

@b.route('/add')
def add():
	ac, no_source_length = make_audios()
	return bottle.template('math', ws_method = 'ws_add', audio_controls = ac, audio_count = no_source_length, prompt = k_prompt)

@b.route('/subtract')
def subtract():
	return bottle.template('math', ws_method = 'ws_subtract', prompt = k_prompt)

@b.route('/multiply')
def multiply():
	ac, no_source_length = make_audios()
	return bottle.template('math', ws_method = 'ws_multiply', audio_controls = ac, audio_count = no_source_length, prompt = k_prompt)

@b.route('/divide')
def divide():
	return bottle.template('math', ws_method = 'ws_divide', prompt = k_prompt)


class Logout(Exception): pass

class Practicer:
	def __call__(self, record):
		self.send(record)
		message = json.loads(self.sock.receive())
		if message['message'] == 'logout':
			raise Logout()
		# else:
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


def _practice(practicer):
	sock = bottle.request.environ.get('wsgi.websocket')
	if not sock:
		bottle.abort(400, 'Expected WebSocket request.')

	dbs = session_maker()
	sess = bottle.request.environ.get('beaker.session')
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

@b.route('/ws_input')
def ws_input():
	_practice(Input_Practicer(0, 9, 30))

@b.route('/ws_add')
def ws_add():
	_practice(Operation_Add(1, 7, 0, 7, 30, db.Op.addition))

@b.route('/ws_subtract')
def ws_subtract():
	_practice(Operation_Subtract(1, 7, 0, 7, 30, db.Op.subtraction))

@b.route('/ws_multiply')
def ws_multiply():
	#_practice(Operation_Multiply(1, 15, 0, 15, 30, db.Op.multiplication))
	_practice(Operation_Multiply(2, 15, 1, 15, 30, db.Op.multiplication))

@b.route('/ws_divide')
def ws_divide():
	_practice(Operation_Divide(1, 7, 0, 7, 30, db.Op.division))

@b.route('/ws_all')
def ws_all():
	#TODO!!!
	pass


# Statics:

@b.route('/js/<path:path>')
def js(path):
	return bottle.static_file(path, root = k_js_path)

@b.route('/audio/<path:path>')
def audio(path):
	return bottle.static_file(path, root = k_audio_path)


# Main:
application = WSGIServer(("0.0.0.0", 8080), wsgi, handler_class = WebSocketHandler)

if __name__ == "__main__":
	application.serve_forever()
