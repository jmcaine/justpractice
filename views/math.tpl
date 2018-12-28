% rebase('_base.tpl', title = 'Arithmetic')

<div id="login">

<p id="login_detail"></p>

<p><button id="login_try">Just try...</button> - if you want to just try without creating a username</p>

<p class="tilt_label">OR...</p>


<fieldset class="small_fieldset">
<legend>Log In...</legend>
<p><input type="text" id="username" placeholder="username" /> </p>
<p><input type="password" id="password" placeholder="password" /> </p>
<p><button id="login_go">Log in</button> </p>
</fieldset>



</div>

{{!audio_controls}}

<div id="math">

<p>{{prompt}}</p>

<fieldset class="small_fieldset">
<legend>Solve...</legend>

<span id="prompt">Original prompt:</span> <span id="correct_answer_flash"></span>
<input type="text" id="answer" autofocus />
<button id="go">Go</button>

</fieldset>

<p id="timer_counter"></p>

<p>There's no need to logout, but if your sibling needs a turn, click here first:</p>
<p><button id="logout_go">Logout</button></p>

</div>


<script>var audio_count = {{audio_count}};</script>
<script>var ws = new WebSocket("ws://" + location.host + "/{{ws_method}}");</script>
<script src="js/math_ws.js"></script>

