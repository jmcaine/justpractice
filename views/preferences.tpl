% rebase('_base.tpl', title = 'Preferences')

<p>
Edit the preferences for user <b>{{ username }}</b> below....
</p>

<form action="preferences_" method="post">

<p>What kind of countdown would you like -- a simple countdown or a timer?</p>


		<fieldset class="small_fieldset">
		<legend><input type="radio" name="countdown_type" value="simple"> Simple</legend>
		<label>
			Problems to complete per session:
			<input type="number" name="count" min="0" max="200" step="10" value="{{values['count']}}" />
		</label>
		</fieldset>
		

		<fieldset class="small_fieldset">
		<legend><input type="radio" name="countdown_type" value="timer"> Timer</legend>
		<label>
			Minutes to work per session:
			<input type="number" name="time_minutes" min="0" max="60" step="1" value="{{values['time_minutes']}}" />
		</label>
		</fieldset>


<input type="submit" value="Go!" />

</form>
