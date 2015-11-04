<?php 
require_once('include/header.php');
require_once('include/menu.php'); 
print_menu('platform');

 $VProxy = exec('grep "voip_proxy" /var/rhizomatica/rccn/config_values.py');
 $VoipProxy = preg_match('/".*?"/', $VProxy, $matches);
 $VoipIP=trim(($matches[0]), '"');
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
<script>
        // standard things to check
        standardChecks = {
            "Servidor": "10.23.0.2",
            "Google": "8.8.8.8",
            "VOIP": "<?php print ($VoipIP); ?>"

        };

    for (var key in standardChecks) {
        ip = standardChecks[key];

        pingIt(ip, key);
    }

    function pingIt(ip, key) {
        $.ajax({
            method: "POST",
            url: "ping.php",
            data: {
                ip
            }
        }).done(function(status) {
            console.log("key: " + key + " ip: " + ip + " status: " + status);
            $("#outsideWorld").append('<div class="' + status + '"><p>' + key + '<br/>' + ip + '</p></div>');
        });
    }
</script>
</body>

</html>