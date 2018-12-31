var prompt = document.getElementById("prompt");
var go_button = document.getElementById("go");
var answer = document.getElementById("answer");
var timer_counter = document.getElementById("timer_counter");
var correct_answer_flash = document.getElementById("correct_answer_flash");
var target_time = null;
var interval;
var fail_delay = 1500; // parameterize?
var data = null;
var done = false; // not a really essential flag, but helps keep final message race possibilities from creating artifacts (like one last new problem prompt after the timer ran out); rare, but this safeguards

go_button.disabled = true;

var audio_nos = []
for(var x = 1; x <= audio_count; x++) {
	audio_nos.push(document.getElementById("audio_no_" + x));
}
var audio_yeses = []
for(var x = 1; x <= audio_count; x++) {
	audio_yeses.push(document.getElementById("audio_yes_" + x));
}

// Note that either counter or timer_minutes must be set, or else there will be no timing/counting!
if (counter > 0) {
	update_counter(counter);
}
else if (timer_minutes > 0) { // "else" b/c you can't (currently) use both a counter and a timer. :)
	target_time = new Date();
	target_time.setMinutes(target_time.getMinutes() + timer_minutes);
	interval = setInterval(update_timer, 500);
}


function ms_to_time(milliseconds) {
	var ms = milliseconds % 1000;
	var s = (milliseconds - ms) / 1000;
	var secs = s % 60;
	s = (s - secs) / 60;
	var mins = s % 60;
	var hrs = (s - mins) / 60;

	function pad(n) {
		return ('00' + n).slice(-2);
	};
	return hrs + ':' + pad(mins) + ':' + pad(secs);
}

function finish() {
	done = true;
	ws.send('{"message": "done"}');
	clearInterval(interval);
	answer.disabled = true;
	go_button.disabled = true;
	timer_counter.innerHTML = "ALL DONE!";
	if (trial)
		prompt.innerHTML = '<p>ALL DONE!</p> <p>Now, <a href="new_user_after">create a username</a> so you can save where you left off, here!</p>';
	else
		prompt.innerHTML = "<p>ALL DONE! Good job!</p><p><a href=" + again + ">Do it again!</a>.</p><p><a href='logout'>Log out</a> if a sibling wants to log in to play some.</p>";
}

function update_counter(value) {
	if (value > 0)
		timer_counter.innerHTML = value;
	else
		finish();
}

function update_timer() {
	if (Date.now() < target_time)
		timer_counter.innerHTML = ms_to_time(target_time - Date.now());
	else
		finish();
};

//logout_button.onclick = function() {
function logout() {
	ws.send('{"message": "done"}'); // full finish() unnecessary b/c we're immediately leaving the page...
	if (trial) {
		window.location = "new_user_after";
	} else {
		window.location = "logout";
	}
	return False;
};

ws.onmessage = function(event) {
	data = JSON.parse(event.data);
	if (data.message == 'math' && !done)
	{
		answer.disabled = false;
		answer.value = "";
		answer.focus();
		prompt.innerHTML = data.prompt;
		go_button.disabled = false;
	}
	// TODO: else error!?
};

function finish_correct_answer_flash() {
	correct_answer_flash.innerHTML = "";
	// Now we can send the result to the server:
	ws.send(JSON.stringify({"message": "result", "result": "incorrect", "delay": fail_delay}));
};

function submit() {
	answer.disabled = true;
	go_button.disabled = true; // until we get the next 'math' message (problem)
	which = Math.floor(Math.random() * audio_count);
	if (data.answer == answer.value) {
		ws.send('{"message": "result", "result": "correct", "delay": "0"}');
		audio_yeses[which].play();
		if (counter > 0)
			update_counter(--counter);
	}
	else {
		/* Here we need to FIRST show the correct answer for fail_delay amount of time, THEN
		send the result over the cet, along with the delay (for the server, which is
		responsible for timing, to subtract off.  If we just send our result message on the
		socket and then sleep, the server will push the next problem to us immediately, but
		will unknowingly be timing this fail_delay correct-answer-display time and counting it
		against the user's next answer time. */
		correct_answer_flash.innerHTML = data.answer;
		audio_nos[which].play(); // this appears to be a non-blocking call, so even if it's very long, the user will still see the next problem and his answer will be timed accurately
		setTimeout(finish_correct_answer_flash, fail_delay); // only clear the flash and send the correct answer to the server after fail_delay!
	}
};


answer.onkeydown = function(event) {
	if (event.keyCode == 13 && !go_button.disabled)
		submit();
};

go_button.onclick = function() {
	submit();
};
