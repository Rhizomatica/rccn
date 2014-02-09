<?php

require_once("httpful.phar");

class SMSException extends Exception { }

class SMS
{

	private $path = "http://localhost:8085/sms";

	public function send($source,$destination,$text) {
		$data = array("source" => $source, "destination" => $destination, "text" => $text);
		try {
			$response = \Httpful\Request::post($this->path."/send")->body($data)->sendsJson()->send();
		} catch (Httpful\Exception\ConnectionErrorException $e) {
			throw new SMSException($e->getMessage());
		}
			
                $data = $response->body;
                if ($data->status == 'failed') {
                        throw new SMSException($data->error);
                }
	}
}


?>
