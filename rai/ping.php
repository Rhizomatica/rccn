<?php

// starting point for tests to devices 

// future: icinga, mtr, jitter etc....

if (!empty($_GET['ip'])) {
	$ip = $_GET['ip'];
	$pingReply = ping($ip);

	if ($pingReply){
		$reply = "up";
	} else {
		$reply = "down";
	} 
}else {
	$ip = null; 
}

echo $reply;

// functions to play with

function ping($host)
{
    exec(sprintf('ping -c 1 -W 5 %s', escapeshellarg($host)), $res, $rval);
    return $rval === 0;
}
?>