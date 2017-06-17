<?php

require_once('modules/access_manager.php');
	
$access = new AccessManager();
$filename = basename($_SERVER['PHP_SELF']);
if ($filename != "login.php") {
	$access->checkAuth();
}

include('locale.php');

header('Content-Type: text/html; charset=utf-8');

?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
        <head>
                <meta http-equiv="content-type" content="text/html; charset=utf-8" />

                <title><?=_('RAI - Rhizomatica Administration Interface')?></title>
                <style type="text/css" title="currentStyle">
                @import "css/page.css";
                @import "css/table.css";
			    @import "css/login.css";
			    @import "css/form.css";
                @import "js/fancybox/jquery.fancybox-1.3.4.css";
                </style>
                <link rel="stylesheet" href="css/jquery-ui.min.css" type="text/css" />
                <link rel="stylesheet" type="text/css" href="css/dd.css" />
                <script type="text/javascript" language="javascript" src="js/jquery.js"></script>
                <script type="text/javascript" language="javascript" src="js/jquery-ui.min.js"></script>
                <script type="text/javascript" language="javascript" src="js/jquery.dataTables.js"></script>
                <script type="text/javascript" language="javascript" src="js/jquery.dataTables.columnFilter.js"></script>
                <script type="text/javascript" language="javascript" src="js/fancybox/jquery.fancybox-1.3.4.pack.js"></script>
                <script type="text/javascript" language="javascript" src="js/jquery.dd.min.js"></script>
                <script type="text/javascript" language="javascript" src="js/rai.js"></script>
        <script type="text/javascript" language="javascript">
                 <? include("js/js_locale.php");?>
        </script>
        </head>
        <body id="dt_example">
                <div id="container">
			<? if (!isset($no_title)) { ?>
                        <div class="full_width big">
                                <img src="img/rhizomatica_logo_small.png" style="vertical-align: middle;" /> <?=_('RAI - Rhizomatica Administration Interface')?>
                        </div>
			<? } ?>
