<?php

require("httpful.phar");

class CreditException extends Exception { }

class Credit
{

	private $path = "http://localhost:8085/credit";

	public $msisdn = "";
	public $amount = "";

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

        public function add_to_reseller($msisdn, $amount) {
                $data = array("msisdn" => $msisdn, "amount" => $amount);
                try {
                        $response = \Httpful\Request::post($this->path."/reseller")->body($data)->sendsJson()->send();
                } catch (Httpful\Exception\ConnectionErrorException $e) {
                        throw new CreditException($e->getMessage());
                }

                $data = $response->body;
                if ($data->status == 'failed') {
                        throw new CreditException($data->error);
                }
        }

}



?>
