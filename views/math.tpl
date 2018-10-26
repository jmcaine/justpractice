<html>
<body>

<div id="login">
<p id="login_detail"></p>
<p>Username: <input type="text" id="username" size="24" /> </p>
<p>Password: <input type="password" id="password" size="24" /> </p>
<p><button id="login_go">Log in</button> </p>
</div>

{{!audio_controls}}

<div id="math">

<p>{{prompt}}</p>

<p>
<span id="prompt">Original prompt:</span>
<input type="text" id="answer" size="4" autofocus />
<span id="correct_answer_flash" style="color:red; font-size:150%;"></span>
<button id="go">Go</button>
</p>

<p id="timer"></p>

<p>There's no need to logout, but if your sibling needs a turn, click here first:</p>
<p><button id="logout_go">Logout</button></p>

</div>

</body>

<script>var audio_count = {{audio_count}};</script>
<script>var ws = new WebSocket("ws://" + location.host + "/{{ws_method}}");</script>
<script src="js/math_ws.js"></script>

</html>
