<?php

require_once("httpful.phar");

class SubscriberException extends Exception { }

class Subscriber 
{

	private $path = "http://localhost:8085/subscriber";

	public $id = "";
	public $msisdn = "";
	public $name = "";
	public $authorized = "";
	public $balance = "";
	public $activation_date = "";

	public function set($id="", $msisdn="", $name="", $authorized="", $balance="", $activation_date="",$subscription_status="", $location="") {
		$this->id = $id;
		$this->msisdn = $msisdn;
		$this->name = $name;
		$this->authorized = $authorized;
		$this->balance = $balance;
		$this->activation_date = $activation_date;
		$this->subscription_status = $subscription_status;
		$this->location = $location;
	}

	public function get($msisdn) {
		try {
			$response = \Httpful\Request::get($this->path."/$msisdn")->expectsJson()->send();
			$data = $response->body;
		} catch (Httpful\Exception\ConnectionErrorException $e) {
			throw new SubscriberException($e->getMessage());
		}
			
		if (!is_array($data)) {
			if ($data->status == 'failed') {
				throw new SubscriberException($data->error);
			} else {
				return $data;
			}
		} else {
			$this->id = $data[0];
			$this->msisdn = $data[1];
			$this->name = $data[2];
			$this->authorized = $data[3];
			$this->balance = $data[4];
			$this->subscription_status = $data[5];
			$this->activation_date = $data[6];
			$this->location = $data[7];
		}
	}

        public function get_extension($imsi) {
                try {
                        $response = \Httpful\Request::get($this->path."/extension/$imsi")->expectsJson()->send();
                        $data = $response->body;
                } catch (Httpful\Exception\ConnectionErrorException $e) {
                        throw new SubscriberException($e->getMessage());
                }

                if (!is_array($data)) {
                        if ($data->status == 'failed') {
                                throw new SubscriberException($data->error);
                        } else {
                                return $data;
                        }
                } else {
			return $data[0];
		}
        }



	public function getAllConnected() {
		try {
			$response = \Httpful\Request::get($this->path."/all_connected")->expectsJson()->send();
			$data = $response->body;
		} catch (Httpful\Exception\ConnectionErrorException $e) {
			throw new SubscriberException($e->getMessage());
		}
			
		if (!is_array($data)) {
			if ($data->status == 'failed') {
				throw new SubscriberException($data->error);
			}
		}
	        $entries = array();
	        foreach ($data as $entry) {
        	        array_push($entries, $entry[0]);
	        }
		return $entries;
	}
		

	public function create() {
		$subscriber = array("msisdn" => $this->msisdn, "name" => $this->name, "balance" => $this->balance, "location" => $this->location);
		try {
			$response = \Httpful\Request::post($this->path)->body($subscriber)->sendsJson()->send();
		} catch (Httpful\Exception\ConnectionErrorException $e) {
			throw new SubscriberException($e->getMessage());
		}
		$data = $response->body;
		if ($data->status == 'failed') {
			throw new SubscriberException($data->error);
		} else {
			if ($data->status == 'success' && $data->error != '') {
				# the extension already existed, we got a new one
				return $data->error;
			} else {
				return "";
			}
		}
		
	}

	public function edit() {
		$subscriber = array("msisdn" => $this->msisdn, "name" => $this->name, "balance" => $this->balance, "authorized" => $this->authorized, "subscription_status" => $this->subscription_status, "location" => $this->location);
		try {
			$response = \Httpful\Request::put($this->path."/".$this->msisdn)->body($subscriber)->sendsJson()->send();
		} catch (Httpful\Exception\ConnectionErrorException $e) {
			throw new SubscriberException($e->getMessage());
		}
		$data = $response->body;
		if ($data->status == 'failed') {
			throw new SubscriberException($data->error);
		}
	}

	public function delete() {
		try {
			$response = \Httpful\Request::delete($this->path."/".$this->msisdn)->send();
		} catch (Httpful\Exception\ConnectionErrorException $e) {
                        throw new SubscriberException($e->getMessage());
                }
		$data = $response->body;
                if ($data->status == 'failed') {
                        throw new SubscriberException($data->error);
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
