<?php

require("httpful.phar");

class StatisticException extends Exception { }

class Statistics
{

	private $path = "http://localhost:8085/statistics";

	public function get($resource) {
               try {
                        $response = \Httpful\Request::get($this->path."/$resource")->expectsJson()->send();
                        $data = $response->body;
                } catch (Httpful\Exception\ConnectionErrorException $e) {
                        throw new StatisticException($e->getMessage());
                }
                if (is_array($data)) {
			if (array_key_exists('status', $data)) {
	                        if ($data->status == 'failed') {
        	                        throw new StatisticException($data->error);
                	        }
			}
                }
                return $data;
                
	}

	public function postS($resource,$data) {
                try {
                        $response = \Httpful\Request::post($this->path."/$resource")->body($data)->sendsJson()->send();
                	$data = $response->body;
                } catch (Httpful\Exception\ConnectionErrorException $e) {
                        throw new StatisticException($e->getMessage());
                }       
                if (is_array($data)) {
                        throw new StatisticException($data->error);
                }
		return $data;
	}

	public function postM($resource,$data) {
                try {
                        $response = \Httpful\Request::post($this->path."/$resource")->body($data)->sendsJson()->expectsJson()->send();
                        $data = $response->body;
                } catch (Httpful\Exception\ConnectionErrorException $e) {
                        throw new StatisticException($e->getMessage());
                }

                if (!is_array($data)) {
                        if ($data->status == 'failed') {
                                throw new StatisticException($data->error);
                        }
                }
                $entries = array();
                foreach ($data as $entry) {
                        array_push($entries, $entry);
                }
                return $entries;
        }

}

class CallsStatistics extends Statistics {
	
	public function getTotalCalls() {
		return $this->get("calls/total_calls");
	}

	public function getTotalMinutes() {
		return $this->get("calls/total_minutes");
	}

	public function getAverageCallDuration() {
		return $this->get("calls/average_call_duration");
	}

	public function getTotalCallsByContext($context) {
		$ctx = array("context" => $context);
		return $this->postS("calls/total_calls_by_context",$ctx);
	}

	public function getCalls($period) {
		$period = array("period" => $period);
		return $this->postM("calls/calls", $period);
	}

	public function getCallsMinutes($period) {
		$period = array("period" => $period);
		return $this->postM("calls/calls_minutes", $period);
	}

	public function getCallsContext($period) {
		$period = array("period" => $period);
		return $this->postM("calls/calls_context", $period);
	}		
}

class CostsStatistics extends Statistics {

	public function getTotalSpent() {
                return $this->get("costs/total_spent");
        }

	public function getTotalSpentCredits() {
                return $this->get("costs/total_spent_credits");
        }

	public function getAverageCallCost() {
                return $this->get("costs/average_call_cost");
        }
	
	public function getTopDestinations() {
                return $this->get("costs/top_destinations");
        }

        public function getCostsStats($period) {
		$period = array("period" => $period);
                return $this->postM("costs/costs_stats", $period);
        }

        public function getCreditsStats($period) {
		$period = array("period" => $period);
                return $this->postM("costs/credits_stats", $period);
        }
}
	

/*
$stat = new CallsStatistics();
try {
	#print $stat->getTotalCalls();
	echo "Ma gheoooo: ".$stat->getTotalCallsByContext('OUTBOUND')."\n";
	$arr = $stat->getCalls('7d');
	var_dump($arr);
} catch (StatisticException $e) {
	echo $e->getMessage();
}

$stat = new CostsStatistics();
try {
	#echo $stat->getTotalSpent();
	$arr = $stat->getCostsStats('7d');
	var_dump($arr);
} catch (StatisticException $e) {
        echo $e->getMessage();
}
*/

?>
