<?php 
require_once('include/header.php');
require_once('include/menu.php'); 
print_menu('platform');
?>

<link rel="stylesheet" href="css/leaflet.css" />
<link rel="stylesheet" href="css/localnet.css" />
<script src="js/leaflet.js"></script>

<div id="map"></div>
<div id="outsideWorld"></div>

<table id="legend">
	<thead>
		<tr>
			<th>Leyenda</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td><div class="up"></div></td>
			<td>En Linea</td>
		</tr>
		<tr>
			<td><div class="down"></div></td>
			<td>Desconectado</td>
		</tr>
		<tr>
			<td><img src="img/bts.png" alt="BTS"></td>
			<td>BTS</td>
		</tr>
		<tr>
			<td><img src="img/link.png" alt="enlace"> </td>
			<td>Enlace</td>
		</tr>
		<tr>
			<td><img src="img/bsc.png" alt="BSC"></td>
			<td>BSC</td>
		</tr>
	</tbody>
</table>

</div>
<script src="js/localnet.js"></script>
</body>

</html>
