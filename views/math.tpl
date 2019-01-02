% rebase('_base.tpl', title = 'Arithmetic')

{{!audio_controls}}

<p>{{intro}}</p>

<fieldset class="small_fieldset">
<legend>Solve...</legend>

<span id="prompt">Loading, please wait...:</span> <span id="correct_answer_flash"></span>
<input type="text" id="answer" autofocus />
<button id="go">Go</button>

</fieldset>

<p id="timer_counter"></p>

% if trial == 0:
<p><a href="home">Go Home</a> - to manage preferences, practice something else, etc.</p>
<p><a href="math_stats">View Stats</a> - to view your stats and progress.</p>
<p><a href="logout" onclick="return logout();">Log Out</a> - to let a sibling log in and play, for example.</p>
% end

<script>
	var audio_count = {{audio_count}};
	var timer_minutes = {{timer_minutes}};
	var counter = {{counter}};
	var trial = {{trial}};
	var again = "{{again}}";
	var ws = new WebSocket("{{ws_protocol}}://" + location.host + "{{ws_url_prefix}}/{{ws_method}}");
</script>
<script src="js/math_ws.js"></script>

