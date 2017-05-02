#!/usr/bin/python

import db
from datetime import datetime
import random

def _practice(practicer, records, threshold, time, dbs):
	now = start = datetime.now()
	hits = trials = 0
	while (now - start).seconds < time:
		# Build batch of 10 records (problems) at a time:
		batch = build_batch(records, threshold)
		# Run this batch:
		for r in batch:
			this_start = datetime.now()
			# Execute the practice:
			correct, delay = practicer(r)
			r.trials += 1
			trials += 1
			if correct:
				r.hits += 1
				hits += 1
				# Get the elapsed time for the operation:
				now = datetime.now()
				this_elapsed = now - this_start
				this_elapsed = this_elapsed.seconds * 1000 + (this_elapsed.microseconds / 1000.0) - int(delay) # subtract off the delay that 'practicer' implemented in order to show a correct answer, e.g.
				print('time to complete: %d; delay: %s' % (this_elapsed, delay))
				# Assign the elapsed time to the proper place:
				if (r.recent_speed_ms and this_elapsed > 3 * r.recent_speed_ms) or (not r.recent_speed_ms and this_elapsed > 5 * threshold):
					print('Rejected, outlier: too slow. r.recent_speed_ms: %d, 5*threshold: %d' % (r.recent_speed_ms, 5 * threshold))
					pass # just don't process this_elapsed at all - it's an outlier... student must've just taken a break
				elif r.speed_1_ms == 0:
					r.speed_1_ms = this_elapsed
				elif r.speed_2_ms == 0:
					r.speed_2_ms = this_elapsed
				elif r.speed_3_ms == 0:
					r.speed_3_ms = this_elapsed
				elif r.speed_4_ms == 0:
					r.speed_4_ms = this_elapsed
				else:
					# Get the current average speed and then clear the 4:
					average = (r.speed_1_ms + r.speed_2_ms + r.speed_3_ms + r.speed_4_ms) / 4.0
					r.speed_2_ms = r.speed_3_ms = r.speed_4_ms = 0 # re-zero most, but....
					r.speed_1_ms = this_elapsed # speed_1 gets the new value, to start the next quad
					# Set the average to the proper place holder:
					if r.early_speed_ms == 0:
						r.early_speed_ms = r.recent_speed_ms = average
					else:
						r.recent_speed_ms = average
			# Commit the updates to r (every trial!)
			dbs.commit()
			# Finally, check our overall elapsed time - if we're done, break out:
			overall_elapsed = now - start
			if overall_elapsed.seconds > time:
				print('Got %d of the last %d correct; averaged %.2f seconds per problem' % (hits, trials, float(overall_elapsed.seconds) / trials))
				break # break out of this for loop, and, logically, out of the outer while loop


def build_batch(records, threshold):
	core = [] # core of 5 records
	olds = [] # 4 random "old" records, already mastered
	wild = random.choice(records) # 1 randomly chosen record, potentially a future/hard problem
	for r in records: # note the sort order established in the above query -- top records will be best candidates for "core"; but further tests done below:
		rec = r.recent_speed_ms # a rec of 0 indicates "never before recorded/calculated"
		recent_time_too_slow = rec == 0 or rec > threshold
		worse_than_75_percent_hit_rate = True if r.trials == 0 else 100 * r.hits / r.trials < 75
		better_than_90_percent_hit_rate = False if r.trials == 0 else 100 * r.hits / r.trials > 90
		if better_than_90_percent_hit_rate and r.recent_speed_ms < 0.75 * r.early_speed_ms: # sufficient progress
			olds.append(r) # but note that, at first, there won't be any added to olds
		elif len(core) < 5 and (recent_time_too_slow or worse_than_75_percent_hit_rate):
			core.append(r)
		elif rec > 0: # go ahead and fill this bucket more than the 4; we'll randomly choose from the contents and narrow to 4 choices only, later
			olds.append(r) # but note that, at first, there won't be any added to olds, and we'll end up with a batch of only 5 recores.  That's fine!
		if len(olds) > 15 and len(core) >= 5:
			break # we have enough now
	random.shuffle(olds)
	batch = core + olds[0:4] # + [wild,] # 5core + 4olds + 1wild = batch of 10
	random.shuffle(batch)
	return batch

def practice_input(user, min, max, time, practicer_function, dbs = None):
	if not dbs:
		dbs = session_maker()
	# Get or add pertinent plain input records:
	q = dbs.query(db.Performance).filter_by(user = user).filter(db.Performance.x >= min).filter(db.Performance.x <= max).filter(db.Performance.operation == db.Op.input).order_by(db.Performance.recent_speed_ms.desc()).order_by(db.Performance.id)
	records = q.all()
	xs = [r.x for r in records]
	for x in range(min, max+1):
		if x not in xs:
			# Add additional inputs:
			dbs.add(db.Performance(user_id = user.id, x = x, y = 0, operation = db.Op.input))
	dbs.commit()
	# Re-fetch, to get default values:
	records = q.all()
	# Now run the practice:
	_practice(practicer_function, records, 1500, time, dbs) # threshold of 1.5 seconds for input

def practice_operation(user, min_x, max_x, min_y, max_y, time, practicer_function, operation, dbs = None):
	if not dbs:
		dbs = session_maker()
	# Get or add pertinent addition records:
	#q = dbs.query(db.Performance).filter_by(user = user).filter(db.Performance.x >= min_x).filter(db.Performance.x <= max_x).filter(db.Performance.y >= min_y).filter(db.Performance.y <= max_y).filter(db.Performance.operation == operation).order_by(db.Performance.recent_speed_ms.desc()).order_by(db.Performance.id)
	q = dbs.query(db.Performance).filter_by(user = user).filter(db.Performance.x >= min_x).filter(db.Performance.x <= max_x).filter(db.Performance.y >= min_y).filter(db.Performance.y <= max_y).filter(db.Performance.operation == operation).order_by(db.Performance.id)
	records = q.all()
	existing_combos = [(r.x, r.y) for r in records]
	for combo in [(a, b) for a in range(min_x, max_x+1) for b in range(min_y, max_y+1)]: # all combos as 2-tuples
		if combo not in existing_combos:
			# Add additional combo:
			dbs.add(db.Performance(user_id = user.id, x = combo[0], y = combo[1], operation = operation))
	dbs.commit()
	# Re-fetch, to get default values:
	records = q.all()
	# Now run the practice:
	_practice(practicer_function, records, 4000, time, dbs) # threshold of 3 seconds for arithmetic operations


