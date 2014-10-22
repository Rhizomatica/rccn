<?php

class AccessManagerException extends Exception { }

class AccessManager
{
	public $userid = "";
	public $username = "";
	public $password = "";
	public $role = "";
	public $lang = "";
	
	public function login($username, $password, $lang) {
		$this->username = $username;
		$this->password = $password;
		$this->lang = $lang;
		if ($this->checkPwd($username,$password)) {
			$this->initializeSession();
			header('Location: subscribers.php');
		} else {
			header('Location: login.php');
		}
	}


	public function checkPwd($username,$password) {
		require_once(dirname(__FILE__).'/../include/database.php');
       	        $db_conn = pg_connect(
	        " host=".$DB_HOST.
	        " dbname=".$DB_DATABASE.
	        " user=".$DB_USER.
	        " password=".$DB_PASSWORD);
		$result = pg_query("SELECT * from users WHERE username='".pg_escape_string($username)."'");
		if (!$result) {
			return false;
		}
		$row = pg_fetch_row($result);
		$res = false;
		if (password_verify($password, $row[2])) {
			$res = true;
		} else {
			$res = false;
		}
                pg_free_result($result);
                pg_close($db_conn);

		return $res;
	}


	public function initializeSession() {
		session_start();
		$_SESSION['username'] = $this->username;
		$_SESSION['lang'] = $this->lang."_".strtoupper($this->lang);
		$_SESSION['is_logged'] = 1;
	}

	public function checkAuth() {
		session_start();
		if (!isset($_SESSION['username']) && !isset($_SESSION['is_logged'])) {
			header('Location: login.php');
		} 
	}

	public function logout() {
		session_destroy();
		unset($_SESSION['username']);
		unset($_SESSION['lang']);
		unset($_SESSION['is_logged']);
		header('Location: login.php');
	}
		
}


?>
