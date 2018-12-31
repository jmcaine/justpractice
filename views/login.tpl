% rebase('_base.tpl', title = 'Arithmetic')

<p><button id="login_try">Just try...</button> - if you want to just try without creating a username</p>

<p class="tilt_label">OR...</p>


<form action="login_" method="post">
<fieldset class="small_fieldset">

<legend>Log In...</legend>

<p id="login_detail">{{get('login_detail', '')}}</p>

<p>
	<input type="text" name="username" placeholder="username" autofocus />
</p>
<p>
	<input type="password" name="password" placeholder="password" />
</p>

<p><input type="submit" value="Log in!" /></p>

</fieldset>
</form>
