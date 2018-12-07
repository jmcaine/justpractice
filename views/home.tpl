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
<ul>
% if not username:
<li><a href="new_user">I'm a new user; sign me up first!</a></li>
% end

<li><a href="multiply">Addition</a></li>
<li><a href="multiply">Multiplication</a></li>
</ul>
</p>

