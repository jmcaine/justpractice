% rebase('_base.tpl', title = 'Preferences')

<p><a href="home">Go Back Home</a> - to practice something, view stats, etc.</p>

<p>
Edit the preferences for user <b>{{ username }}</b> below....
</p>

<form action="preferences_" method="post">

<p>What kind of countdown would you like -- a simple countdown or a timer?</p>


		<fieldset class="small_fieldset">
		<legend><input type="radio" name="countdown_type" id="simple_radio" value="simple" onclick="radio_changed()"> Simple </legend>
		<label>
			Problems to complete per session:
			<input type="number" name="count" min="0" max="200" step="10" id="simple_value" value="{{values['count']}}" oninput="simple_value_changed()" />
		</label>
		</fieldset>
		

		<fieldset class="small_fieldset">
		<legend><input type="radio" name="countdown_type" id="timer_radio" value="timer" onclick="radio_changed()"> Timer </legend>
		<label>
			Minutes to work per session:
			<input type="number" name="time_minutes" min="0" max="60" step="1" id="timer_value" value="{{values['time_minutes']}}" oninput="timer_value_changed()" />
		</label>
		</fieldset>


<input type="submit" value="Go!" />

</form>

<script>
var simple_radio = document.getElementById("simple_radio");
var timer_radio = document.getElementById("timer_radio");

// Animate changes:

function simple_value_changed() {
	simple_radio.checked = true;
	timer_value.value = 0;
};

function timer_value_changed() {
	timer_radio.checked = true;
	simple_value.value = 0;
}

function radio_changed() {
	if (simple_radio.checked == true)
		timer_value.value = 0;
	else
		simple_value.value = 0;
}

// Initialize:
if ({{values['count']}} > 0)
	simple_value_changed();
else // ({{values['time_minutes']}} > 0)
	timer_value_changed();


</script>
