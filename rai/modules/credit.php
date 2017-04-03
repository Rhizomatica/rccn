<?php

require("httpful.phar");

class CreditException extends Exception { }

class Credit
{

	private $path = "http://localhost:8085/credit";

	public $msisdn = "";
	public $amount = "";

    public function get_rate() {
        $url='http://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20yahoo.finance.xchange%20where%20pair%20in%20(%22USDMXN%22)&env=store://datatables.org/alltableswithkeys';
        $xml=simplexml_load_string(file_get_contents($url));
        return $xml->results->rate->Rate;
    }

    public function get_all_credit_allocated() {
        try {
            $response = \Httpful\Request::get($this->path)->expectsJson()->send();
        } catch (Httpful\Exception\ConnectionErrorException $e) {
            throw new CreditException($e->getMessage());
        }
        $data = $response->body;
        if ($data->status == 'failed') {
            throw new CreditException($data->error);
        }
        return $data;
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
