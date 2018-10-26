<!DOCTYPE html>
<html>

	<head>
		<meta charset="utf-8">
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		<title>Just Practice - {{get('title')}}</title>
		<script>var $ = function( id ) { return document.getElementById( id ); };</script>
		<link rel="stylesheet" href="css/main.css">
	</head>

	<body>
		<div class="content">

			% include('_flash', flash = get('flash', []))
			
			{{!base}}
			
		</div>
	</body>
	
</html>
