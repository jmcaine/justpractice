var prompt = document.getElementById("prompt");
var math_div = document.getElementById("math");
var go_button = document.getElementById("go");
var answer = document.getElementById("answer");
var login_div = document.getElementById("login");
var username = document.getElementById("username");
var password = document.getElementById("password");
var login_button = document.getElementById("login_go");
var login_detail = document.getElementById("login_detail");
var logout_button = document.getElementById("logout_go");
var timer = document.getElementById("timer");
var correct_answer_flash = document.getElementById("correct_answer_flash");
var target_time = null;
var interval;
var fail_delay = 1500;
var data = null;
var done = false;

var audio_nos = []
for(var x = 1; x <= audio_count; x++) {
	audio_nos.push(document.getElementById("audio_no_" + x));
}
var audio_yeses = []
for(var x = 1; x <= audio_count; x++) {
	audio_yeses.push(document.getElementById("audio_yes_" + x));
}

go_button.disabled = true;


function login(detail) {
	math_div.style.display = 'none';
	login_div.style.display = 'block';
	login_detail.innerHTML = detail;
	username.value = ""; // redundant
	password.value = ""; // redundant
	username.focus();
};

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

function update_timer() {
	if (Date.now() >= target_time) {
		prompt.innerHTML = "ALL DONE!";
		clearInterval(interval);
		done = true;
	}
	else {
		timer.innerHTML = ms_to_time(target_time - Date.now());
	}
};

function login_submit() {
	ws.send(JSON.stringify({"username": username.value, "password": password.value}));
	target_time = new Date();
	target_time.setMinutes(target_time.getMinutes() + 5);
	interval = setInterval(update_timer, 500);
	username.value = "";
	password.value = "";
};

login_button.onclick = function() {
	login_submit();
};

password.onkeydown = function(event) {
	if (event.keyCode == 13)
		login_submit();
};

logout_button.onclick = function() {
	ws.send('{"message": "logout"}');
	clearInterval(interval);
	start_time = 0;
};

ws.onmessage = function(event) {
	data = JSON.parse(event.data);
	if (data.message == 'login')
		login(data.detail);
	else if (data.message == 'math' && !done)
	{
		login_div.style.display = 'none';
		math_div.style.display = 'block';
		answer.value = "";
		answer.focus();
		prompt.innerHTML = data.prompt;
		go_button.disabled = false;
	}
};

function finish_correct_answer_flash() {
	correct_answer_flash.innerHTML = "";
	// Now we can send the result to the server:
	ws.send(JSON.stringify({"message": "result", "result": "incorrect", "delay": fail_delay}));
};

function submit() {
	go_button.disabled = true; // until we get the next 'math' message (problem)
	which = Math.floor(Math.random() * audio_count);
	if (data.answer == answer.value) {
		ws.send('{"message": "result", "result": "correct", "delay": "0"}');
		audio_yeses[which].play();
	}
	else {
		/* Here we need to FIRST show the correct answer for fail_delay amount of time, THEN
		send the result over the socket, along with the delay (for the server, which is
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
	if (event.keyCode == 13)
		submit();
};

go_button.onclick = function() {
	submit();
};