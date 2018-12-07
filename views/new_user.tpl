% rebase('_base.tpl', title = 'New User')

% message = get('message')
% if message:
<div class="flash">{{message}}</div>
% end

<form action="new_user_" method="post">

<ol class="step_numbers">
<li>

<p>First, create a one-word username for yourself (lowercase, no spaces)...</p>
<label>New username:
<input name="username" id="username" type="text" required autofocus placeholder="Enter new username" pattern="[a-z0-9_]+" />
<span class="invalid_message">{{vms['username']}}</span>
</label>

</li>
<li>

<p>Next, invent a password; type it in twice to make sure you've got it...</p>
<label>New password:
<input name="password" id="password" type="password" required placeholder="Enter new password" />
<input name="password_confirmation" id="password_confirmation" type="password" required placeholder="Enter password again for confirmation" />
<span class="invalid_message" id="password_match_message">{{vms['password_match']}}</span>
</label>

</li>
<li>

<p>Finally, enter an email address that can be used if you ever need a password reset (optional, but this may be very useful someday!)...</p>
<label>Email address:
<input name="email" id="email" type="email" placeholder="Enter email address" />
<span class="invalid_message">{{vms['email']}}</span>
</label>

</li>

<input type="submit" value="Go!" />

</form>


<script>

$('username').addEventListener('input', validate);
$('email').addEventListener('blur', validate);
$('password').addEventListener('blur', validate_passwords);
$('password_confirmation').addEventListener('blur', validate_passwords);

function validate(evt) {
	var e = evt.currentTarget;
	e.nextElementSibling.style.display = e.checkValidity() ? "none" : "block";
}

function validate_passwords(evt) {
	var e = evt.currentTarget; // "password_confirmation"
	$('password_match_message').style.display = $('password_confirmation').value == "" || $('password').value == $('password_confirmation').value ? "none" : "block";
}

</script>
