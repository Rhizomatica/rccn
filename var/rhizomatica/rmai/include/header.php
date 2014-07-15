<?php

require_once('modules/access_manager.php');
	
$access = new AccessManager();
$filename = basename($_SERVER['PHP_SELF']);
if ($filename != "login.php") {
	$access->checkAuth();
}


$language = $_SESSION['lang'];
putenv("LANG=$language"); 
setlocale(LC_ALL, $language);

// Set the text domain as 'messages'
$domain = 'messages';
bindtextdomain($domain, "/var/rhizomatica/rai/locale"); 
bind_textdomain_codeset($domain, 'UTF-8');
textdomain($domain);

header('Content-Type: text/html; charset=utf-8');

?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
        <head>
                <meta http-equiv="content-type" content="text/html; charset=utf-8" />
                
                <title>RAI - Rhizomatica Administration Interface</title>
                <style type="text/css" title="currentStyle">
                        @import "css/page.css";
                        @import "css/table.css";
			@import "css/login.css";
			@import "css/form.css";
                        @import "js/fancybox/jquery.fancybox-1.3.4.css";
                </style>
                <script type="text/javascript" language="javascript" src="js/jquery.js"></script>
                <script type="text/javascript" language="javascript" src="js/jquery.dataTables.js"></script>
		<script type="text/javascript" language="javascript" src="js/jquery.dataTables.columnFilter.js"></script>
                <script type="text/javascript" language="javascript" src="js/fancybox/jquery.fancybox-1.3.4.pack.js"></script>
        </head>
        <body id="dt_example">
                <div id="container">
			<? if (!isset($no_title)) { ?>
                        <div class="full_width big">
                                <img src="img/rhizomatica_logo_small.png" style="vertical-align: middle;" /> RAI - Rhizomatica Administration Interface
                        </div>
			<? } ?>
