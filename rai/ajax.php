<?

switch ($_REQUEST['service']) {

	case "imei":
		require_once("modules/httpful.phar");
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
	break;
	case "credit":
		require_once("modules/credit.php");
		$cred = new Credit();
		print $cred->get_credit_records($_REQUEST['year']);
	break;
}

?>