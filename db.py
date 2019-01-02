#!/usr/bin/python

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy import UniqueConstraint, ForeignKey
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, relationship

from enum import Enum as PyEnum
from os import urandom
import hashlib
from datetime import datetime
import string
import random
from collections import OrderedDict

url = 'sqlite:///test.db' # deport!
Base = declarative_base()

class SABaseMixin(object):
	id = Column(Integer, primary_key=True)

	@declared_attr
	def __tablename__(cls):
		return cls.__name__.lower()

# Alembic/migration note: used:
#	alembic revision --autogenerate -m "initial tables"
# as first pass in order to import the following tables as initial state
# Then, for a new feature...
#	export PYTHONPATH="/home/av2/dev/justpractice"
#	alembic revision --autogenerate -m "new feature"
# Then, of course:
#	alembic upgrade head


class User(SABaseMixin, Base):
	username = Column(String, unique = True)
	salt = Column(String)
	password = Column(String)
	email = Column(String)

class Op(PyEnum):
	input = 'input'
	addition = '+'
	subtraction = '-'
	multiplication = 'x'
	division = '/'

class Performance(SABaseMixin, Base):
	timestamp = Column(DateTime, default=datetime.utcnow)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship('User', back_populates = 'performance') # necessary?  in addition to the above?
	x = Column(Integer)
	y = Column(Integer, default = 0)
	operation = Column(Enum(Op))
	speed_1_ms = Column(Integer, default = 0)
	speed_2_ms = Column(Integer, default = 0)
	speed_3_ms = Column(Integer, default = 0)
	speed_4_ms = Column(Integer, default = 0)
	trials = Column(Integer, default = 0)
	hits = Column(Integer, default = 0)
	early_speed_ms = Column(Integer, default = 0)
	recent_speed_ms = Column(Integer, default = 0)
	UniqueConstraint('user_id', 'x', 'y', 'operation', name='uix_user_operation') # add user!!!
User.performance = relationship('Performance', order_by = Performance.id, back_populates = 'user')

class Preferences(SABaseMixin, Base):
	user_id = Column(Integer, ForeignKey('user.id'))
	time_minutes = Column(Integer, default = 0)
	count = Column(Integer, default = 30)
	

class Descriptive_Exception(Exception):
	def __init__(self, description):
		super().__init__()
		self.description = description

class User_Exists(Descriptive_Exception):
	def __init__(self, username):
		super().__init__('User with username "%s" already exists.' % username)

class Bad_User_Auth(Descriptive_Exception):
	def __init__(self, username):
		super().__init__('Cannot authenticate - username or password is incorrect.')

def create_db(engine):
	Base.metadata.create_all(engine)

def create_engine_sm(url = url, echo = True):
	db_engine = create_engine(url, echo = echo)
	session_maker = sessionmaker(bind = db_engine)
	return (db_engine, session_maker)

_hash = lambda password, salt: hashlib.pbkdf2_hmac('sha256', bytes(password, 'UTF-8'), salt, 100000)

def add_user(dbs, username, password, email = None, commit = True):
	salt = urandom(32)
	user = User(username = username, salt = salt, email = email, password = _hash(password, salt))
	dbs.add(user)
	if commit:
		dbs.commit() # consider making sure autoflush is on, or calling flush(), or read http://skien.cc/blog/2014/02/06/sqlalchemy-and-race-conditions-follow-up/
		dbs.refresh(user)
	return user

def update_user(dbs, temp_username, new_username, password, email):
	user = get_user(dbs, temp_username)
	user.username = new_username
	salt = urandom(32)
	user.salt = salt
	user.password = _hash(password, salt)
	dbs.commit()
	dbs.refresh(user)
	return user

def get_user(dbs, username):
	return dbs.query(User).filter_by(username = username).one_or_none()

def get_preferences(dbs, username):
	assert(username != None)
	prefs = dbs.query(Preferences).join(User).filter(User.username == username).all()
	if len(prefs) == 1:
		prefs = prefs[0]
	elif len(prefs) > 1:
		raise Exception("Multiple Preferences records for user (id = %d); only one allowed" % user_id);
	elif len(prefs) == 0:
		# Create record w/ defaults:
		user = get_user(dbs, username)
		prefs = Preferences(user_id = user.id)
		dbs.add(prefs)
		dbs.commit()
		dbs.refresh(prefs)
	return prefs

def set_preferences(dbs, username, preferences):
	# Ugly!  Make this better!
	p = get_preferences(dbs, username)
	p.time_minutes = preferences.time_minutes
	p.count = preferences.count
	dbs.commit()

def get_trial_user(dbs):
	username = 'tria!!' + ''.join(random.choice(string.ascii_letters + string.digits) for i in range(20)) # really no chance of collision
	return add_user(dbs, username, '')

def authenticate(dbs, username, password):
	user = get_user(dbs, username)
	if user and _hash(password, user.salt) == user.password:
		return user
	else:
		return None

def print_users_performance(user):
	for p in user.performance:
		print('x:%d\ty:%d\top:%s\ts1:%4.0f\ts2:%4.0f\ts3:%4.0f\ts4:%4.0f\ttrials:%s\thits:%s\tesms:%4.0f\trsms:%4.0f' % (p.x, p.y, p.operation, p.speed_1_ms, p.speed_2_ms, p.speed_3_ms, p.speed_4_ms, p.trials, p.hits, p.early_speed_ms, p.recent_speed_ms))


def get_math_stats(dbs, username):
	user = get_user(dbs, username)
	result = OrderedDict({
		Op.input: [],
		Op.addition: [],
		Op.subtraction: [],
		Op.multiplication: [],
		Op.division: [],
	})
	
	for p in user.performance:
		result[p.operation].append((p.x, p.y, p.trials, p.hits, int(p.early_speed_ms), int(p.recent_speed_ms)))
	
	return result

'''
records = dbs.query(Performance).filter_by(user = user).filter(Performance.x >= min).filter(Performance.x <= max).filter(Performance.operation == Op.input).order_by(Performance.recent_speed_ms.desc()).order_by(Performance.id).all()
#records = dict([(r[Performance.x], r) for r in records])
xs = [r[Performance.x] for r in records]
for x in range(min, max+1):
	if x not in xs:
		# Add additional inputs:
		p = Performance(user_id = user.id, x = x, y = 0, operation = Op.input)
		dbs.add(p)
		records.append(p)
dbs.commit()
'''
