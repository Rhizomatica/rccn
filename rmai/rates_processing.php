<?php
	
	$rates = file_get_contents('db/ratesUSD.csv');
	
	//$array = array_map("str_getcsv", explode("\n", $rates));
	//print json_encode($array);
	$csvarr = array();


	function csvToJson($csv) {
	    $rows = explode("\n", trim($csv));
	    $csvarr["aaData"] = array_map(function ($row) {
        	//$keys = array('destination','areacode','price');
	        //return array_combine($keys, str_getcsv($row));
		return str_getcsv($row);
	    }, $rows);
	    $json = json_encode($csvarr);

	    return $json;
	}

	echo csvToJson($rates);

/*if (($handle = fopen('db/ratesUSD.csv', 'r')) === false) {
    die('Error opening file');
}

$headers = fgetcsv($handle, 1024, ',');
$complete = array();

while ($row = fgetcsv($handle, 1024, ',')) {
    $complete[] = array_combine($headers, $row);
}

fclose($handle);

echo json_encode($complete);*/

?>
