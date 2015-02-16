<?php

require_once("httpful.phar");

class ConfigurationException extends Exception { }

class Configuration
{

	private $path = "http://localhost:8085/configuration";

	public function getSite() {
		try {
			$response = \Httpful\Request::get($this->path."/site")->expectsJson()->send();
			$data = $response->body;
		} catch (Httpful\Exception\ConnectionErrorException $e) {
			throw new SubscriberException($e->getMessage());
		}
		if (!is_array((array) $data)) {
			if ($data->status == 'failed') {
				throw new SubscriberException($data->error);
			}
		} else {
			return $data;
		}
	}
	
	public function getConfig() {
		try {
			$response = \Httpful\Request::get($this->path."/config")->expectsJson()->send();
			$data = $response->body;
		} catch (Httpful\Exception\ConnectionErrorException $e) {
			throw new SubscriberException($e->getMessage());
		}
			
		if (!is_array((array) $data)) {
			if ($data->status == 'failed') {
				throw new SubscriberException($data->error);
			}
		} else {
			return $data;
		}
	}

        public function getLocations() {
                try {
                        $response = \Httpful\Request::get($this->path."/locations")->expectsJson()->send();
                        $data = $response->body;
                } catch (Httpful\Exception\ConnectionErrorException $e) {
                        throw new SubscriberException($e->getMessage());
                }

                if (!is_array((array) $data)) {
                        if ($data->status == 'failed') {
                                throw new SubscriberException($data->error);
                        }
                } else {
                        return $data;
                }
        }


}

/*$config = new Configuration();
try {
	print_r($config->getConfig());
} catch (ConfigurationException $e) {
	echo $e->getMessage();
}*/


?>
