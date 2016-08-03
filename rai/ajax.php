<?

require_once("modules/httpful.phar");

switch ($_REQUEST['service']) {

	case "imei":
		$path = "http://localhost:8085/subscriber/imei/".$_REQUEST['term'];
		$response = \Httpful\Request::get($path)->expectsJson()->send();
		$data = $response->body;
		//print json_encode($data);
		print '[ ';
		foreach ($data as $key => $value) {
			$s.='"'.substr($value[0],0,14).'X",';
			
		}
		print rtrim($s,',');
		print ' ]';
}

?>