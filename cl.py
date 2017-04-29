#!/usr/bin/python

import core
import db

import getpass
from datetime import datetime, timedelta
import random


db_engine = None
session_maker = None
verbose = False


def get_user(username, dbs = None):
	if not dbs:
		dbs = session_maker()
	return dbs.query(db.User).filter_by(username = username).one_or_none()

def authenticate(user):
	pw = getpass.getpass("Enter your password:")
	if not db.authenticate(user, pw):
		raise db.Bad_User_Auth()


def practice_input(record):
	result = int(input('%d: ' % record.x))
	ret = result == record.x
	if not ret:
		print('Oops!')
	return ret

def practice_addition(record):
	result = int(input('%d + %d = ' % (record.x, record.y)))
	ret = result == (record.x + record.y)
	if not ret:
		print('Oops! %d + %d = %d' % (record.x, record.y, record.x + record.y))
	return ret

def practice_subtraction(record):
	result = int(input('%d - %d = ' % (record.x + record.y, record.x)))
	ret = result == record.y
	if not ret:
		print('Oops! %d - %d = %d' % (record.x + record.y, record.x, record.y))
	return ret

def practice_multiplication(record):
	result = int(input('%d x %d = ' % (record.x, record.y)))
	ret = result == (record.x * record.y)
	if not ret:
		print('Oops! %d x %d = %d' % (record.x, record.y, record.x * record.y))
	return ret

def practice_division(record):
	result = int(input('%d / %d = ' % (record.x * record.y, record.x)))
	ret = result == record.y
	if not ret:
		print('Oops! %d / %d = %d' % (record.x * record.y, record.x, record.y))
	return ret


def add_user(username, password = None, dbs = None):
	if not dbs:
		dbs = session_maker()
	exists = dbs.query(db.User).filter_by(username = username).one_or_none()
	if exists:
		raise db.User_Exists(username)
	#else, get password if necessary:
	if not password:
		pw1 = ''
		pw2 = 'invalid'
		while pw1 != pw2:
			pw1 = getpass.getpass("Enter user's password:")
			pw2 = getpass.getpass("Enter user's password again for confirmation:")
		password = pw1
	try:
		db.add_user(dbs, username, password)
	except IntegrityError: # double-check; in case somehow user was created since we last checked
		dbs.rollback()
		raise User_Exists(username)

def get_users(dbs = None):
	if not dbs:
		dbs = session_maker()
	return dbs.query(User).all()
	

if __name__ == "__main__":
	import sys, getopt
	
	options = (
		('h', 'help', None, 'Print help information'),
		('c', 'create-db', None, 'Create a new (file-based) database (use -d to specify database file name); e.g.: python test.py -d test.db -c'),
		('d', 'db', 'dbname', 'Name of the database (file) to attach to'),
		('v', 'verbose', None, 'Display verbose output'),
		('a', 'adduser', 'username', 'Add a user with <username> to the system; e.g.: python cl.py -d test.db -a test1'),
		('l', 'listusers', None, 'List users'),
		('u', 'user', 'username', 'Set user for the given practice / operation'),
		('I', 'practice-input', None, 'Practice input speed; e.g.: python cl.py -d test.db -u testuser -t 60 -I -x 0 -X 9'),
		('A', 'practice-addition', None, 'Practice input speed; e.g.: python cl.py -d test.db -u testuser -t 60 -A -x 1 -X 12 -y 0 -Y 12'),
		('S', 'practice-subtraction', None, 'Practice input speed; e.g.: python cl.py -d test.db -u testuser -t 60 -S -x 1 -X 12 -y 0 -Y 12'),
		('M', 'practice-multiplication', None, 'Practice input speed; e.g.: python cl.py -d test.db -u testuser -t 60 -M -x 1 -X 12 -y 0 -Y 12'),
		('D', 'practice-division', None, 'Practice input speed; e.g.: python cl.py -d test.db -u testuser -t 60 -D -x 1 -X 12 -y 0 -Y 12'),
		('t', 'time', 'time', 'Set time to practice in seconds; e.g.: python cl.py -d test.db -u testuser -t 120 -I -x 0 -X 9'),
		('x', 'x-minimum', 'minimum', 'Set minimum value for x; e.g.: python cl.py -d test.db -u testuser -t 60 -I -x 0 -X 9'),
		('X', 'x-maximum', 'maximum', 'Set maximum value for x; e.g.: python cl.py -d test.db -u testuser -t 60 -I -x 0 -X 9'),
		('y', 'y-minimum', 'minimum', 'Set minimum value for y; e.g.: python cl.py -d test.db -u testuser -t 60 -A -x 0 -X 12 -y 0 -Y 12'),
		('Y', 'y-maximum', 'maximum', 'Set maximum value for y; e.g.: python cl.py -d test.db -u testuser -t 60 -A -x 0 -X 12 -y 0 -Y 12'),
	)
	go_options = ''.join([o[0] + (':' if o[2] else '') for o in options])
	go_long_options = ''.join([o[1] + ('=' if o[2] else '') for o in options])
	helpstrings = ('test.py <options> ...',) #  add options lines!!!

	global db_engine
	global session_maker
	global verbose

	try:
		opts, args = getopt.getopt(sys.argv[1:], go_options, go_long_options)
	except getopt.GetoptError:
		print('\n'.join(helpstrings))
		sys.exit(2)
	try:
		x_min = 0
		x_max = 12
		y_min = 0
		y_max = 12
		time = 60
		user = None
		dbs = None
		for opt, arg in opts:
			if opt in ('-h', '--help'):
				print(helpstrings[0])
				sys.exit()
			elif opt in ('-v', '--verbose'):
				verbose = True
			elif opt in ('-d', '--db'):
				db_engine, session_maker = db.create_engine_sm('sqlite:///' + arg, verbose)
			elif opt in ('-c', '--create-db'):
				db.create_db(db_engine)
			elif opt in ('-a', '--adduser'):
				print('adding user:', arg)
				add_user(arg)
			elif opt in ('-l', '--listusers'):
				print('Users:', ', '.join([r.username for r in get_users()]))
			elif opt in ('-u', '--user'):
				dbs = session_maker()
				user = get_user(arg, dbs)
				authenticate(user)
			elif opt in ('-t', '--time'):
				time = int(arg)
			elif opt in ('-x', '--x-minimum'):
				x_min = int(arg)
			elif opt in ('-X', '--x-maximum'):
				x_max = int(arg)
			elif opt in ('-y', '--y-minimum'):
				y_min = int(arg)
			elif opt in ('-Y', '--y-maximum'):
				y_max = int(arg)
			elif opt in ('-I', '--practice-input'):
				core.practice_input(user, x_min, x_max, time, practice_input, dbs)
			elif opt in ('-A', '--practice-addition'):
				core.practice_operation(user, x_min, x_max, y_min, y_max, time, practice_addition, db.Op.addition, dbs)
			elif opt in ('-S', '--practice-subtraction'):
				core.practice_operation(user, x_min, x_max, y_min, y_max, time, practice_subtraction, db.Op.subtraction, dbs)
			elif opt in ('-M', '--practice-multiplication'):
				core.practice_operation(user, x_min, x_max, y_min, y_max, time, practice_multiplication, db.Op.multiplication, dbs)
			elif opt in ('-D', '--practice-division'):
				core.practice_operation(user, x_min, x_max, y_min, y_max, time, practice_division, db.Op.division, dbs)
	except db.Descriptive_Exception as e:
		print(e.description)
		if verbose:
			raise
	
#user, range(s), operation(s), count, easy/medium/hard