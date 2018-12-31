% rebase('_base.tpl', title = 'Home')

<p>
% if username:
Hi <b>{{ username }}</b>,
% else:
Hi,
% end
what would you like to practice?
</p>

<p>
% if not username:
<ul>
<li><a href="new_user">I'm a new user; sign me up first!</a></li>
</ul>
% end

<ul>
<li><a href="multiply">Addition</a></li>
<li><a href="multiply">Multiplication</a></li>
</ul>

% if username:
<ul>
<li><a href="preferences">Edit My Preferences</a></li>
<li><a href="logout">Log Out</a></li>
</ul>
% end

</p>

