<?php

require("httpful.phar");

class CreditException extends Exception { }

class Credit
{

	private $path = "http://localhost:8085/credit";

	public $receipt_id = "";
	public $msisdn = "";
	public $amount = "";

	public function set($msisdn, $amount) {
		$this->msisdn = $msisdn;
		$this->authorized = $credit;
	}

	public function add($msisdn,$amount) {
		$data = array("msisdn" => $msisdn, "amount" => $amount);
		try {
			$response = \Httpful\Request::post($this->path)->body($data)->sendsJson()->send();
		} catch (Httpful\Exception\ConnectionErrorException $e) {
			throw new CreditException($e->getMessage());
		}
			
                $data = $response->body;
                if ($data->status == 'failed') {
                        throw new CreditException($data->error);
                }
	}
}


/*$credit = new Credit();
try {
	$credit->add('INV002','68820123991',2.00);
} catch (CreditException $e) {
	echo $e->getMessage();
}*/


?>
