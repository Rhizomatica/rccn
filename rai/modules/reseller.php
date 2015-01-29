<?php

require_once("httpful.phar");

class ResellerException extends Exception { }

class Reseller
{

	private $path = "http://localhost:8085/reseller";

	public $msisdn = "";
	public $pin = "";
	public $balance = "";
	public $created = "";

	public function set($msisdn="", $pin="", $balance="") {
		$this->msisdn = $msisdn;
		$this->pin = $pin;
		$this->balance = $balance;
	}

	public function get($msisdn) {
		try {
			$response = \Httpful\Request::get($this->path."/$msisdn")->expectsJson()->send();
			$data = $response->body;
		} catch (Httpful\Exception\ConnectionErrorException $e) {
			throw new ResellerException($e->getMessage());
		}
			
		if (!is_array($data)) {
			if ($data->status == 'failed') {
				throw new ResellerException($data->error);
			}
		} else {
			if ($msisdn == "messages") {
				return $data;
			} else {
				$this->id = $data[0];
				$this->created = $data[1];
				$this->msisdn = $data[2];
				$this->pin = $data[3];
				$this->balance = $data[4];
				$this->total_sales = $data[5];
			}
		}
	}


	public function getMessages() {
		try {
			$response = \Httpful\Request::get($this->path."/messages")->expectsJson()->send();
			$data = $response->body;
		} catch (Httpful\Exception\ConnectionErrorException $e) {
			throw new ResellerException($e->getMessage());
		}
			
		if (!is_array($data)) {
			if ($data->status == 'failed') {
				throw new ResellerException($data->error);
			}
		}
	        $entries = array();
	        foreach ($data as $entry) {
        	        array_push($entries, $entry[0]);
	        }
		return $entries;
	}
		
	public function create() {
		$reseller = array("msisdn" => $this->msisdn, "pin" => $this->pin, "balance" => $this->balance);
		try {
			$response = \Httpful\Request::post($this->path."/".$this->msisdn)->body($reseller)->sendsJson()->send();
		} catch (Httpful\Exception\ConnectionErrorException $e) {
			throw new ResellerException($e->getMessage());
		}
		$data = $response->body;
		if ($data->status == 'failed') {
			throw new ResellerException($data->error);
		}
	}

	public function edit() {
		$reseller = array("msisdn" => $this->msisdn, "pin" => $this->pin, "balance" => $this->balance);
		try {
			$response = \Httpful\Request::put($this->path."/".$this->msisdn)->body($reseller)->sendsJson()->send();
		} catch (Httpful\Exception\ConnectionErrorException $e) {
			throw new ResellerException($e->getMessage());
		}
		$data = $response->body;
		if ($data->status == 'failed') {
			throw new ResellerException($data->error);
		}
	}

	public function edit_messages($mess1,$mess2,$mess3,$mess4,$mess5, $mess6) {
		$messages = array("mess1" => $mess1, "mess2" => $mess2, "mess3" => $mess3, "mess4" => $mess4, "mess5" => $mess5, "mess6" => $mess6);
		try {
			$response = \Httpful\Request::put($this->path."/edit_messages")->body($messages)->sendsJson()->send();
		} catch (Httpful\Exception\ConnectionErrorException $e) {
			throw new ResellerException($e->getMessage());
		}
		$data = $response->body;
		if ($data->status == 'failed') {
			throw new ResellerException($data->error);
		}
	}


	public function delete() {
		try {
			$response = \Httpful\Request::delete($this->path."/".$this->msisdn)->send();
		} catch (Httpful\Exception\ConnectionErrorException $e) {
                        throw new ResellerException($e->getMessage());
                }
		$data = $response->body;
                if ($data->status == 'failed') {
                        throw new ResellerException($data->error);
                }
	}

}


/*$sub = new Subscriber();
try {
	#$sub->get('68820137512');
	
	#$sub->set("","37511","AntaRest4",0,"2.00","");	
	#$sub->msisdn = "68820137511";
	#$sub->add();
	#$sub->delete();
	$all = $sub->getAllConnected();
	print_r($all);
	#echo "Subscriber added successfully";
} catch (SubscriberException $e) {
	echo $e->getMessage();
}*/



?>
