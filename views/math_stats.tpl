% rebase('_base.tpl', title = 'Stats')

<p><a href="home">Go Back Home</a> - to manage preferences, practice something, etc.</p>

<p>
Stats for {{username}}:
</p>

<p>

<table>
% for operation, data in stats.items():

% if data:
<tr>
<th colspan="6">{{operation}}</th>
</tr>

<tr>
<th>Term 1</th>
<th>Term 2</th>
<th>Trials</th>
<th>Hits</th>
<th>Early Speed (ms)</th>
<th>Recent Speed (ms)</th>
</tr>

% for datum in data:
<tr>
% for value in datum:
<td>{{value}}</td>
% end
</tr>
% end
% end
% end
</table>

</p>

