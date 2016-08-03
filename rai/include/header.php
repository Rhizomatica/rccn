<?php

require_once('modules/access_manager.php');
	
$access = new AccessManager();
$filename = basename($_SERVER['PHP_SELF']);
if ($filename != "login.php") {
	$access->checkAuth();
}


if (isset($_SESSION['lang'])) {
        $language = $_SESSION['lang'];
} else {
        if (isset($_SERVER['HTTP_ACCEPT_LANGUAGE'])) {
          preg_match_all('/([a-z]{1,8}(-[a-z0-9]{1,8})?)\s*(;\s*q\s*=\s*(1|0\.[0-9]+))?/i', $_SERVER['HTTP_ACCEPT_LANGUAGE'], $lang_parse);
          if (count($lang_parse[1])){
            $langs = array_combine($lang_parse[1], $lang_parse[4]);
            foreach ($langs as $lang => $val){
              if ($val === '') $langs[$lang] = "1";
            }
            $langs=array_flip($langs);
            ksort($langs, SORT_NUMERIC);
          }
          $_lang=substr(array_pop($langs),0,2);
          $language=$_lang.'_'.strtoupper($_lang);
        }
}

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

                <title><?=_('RAI - Rhizomatica Administration Interface')?></title>
                <style type="text/css" title="currentStyle">
                @import "css/page.css";
                @import "css/table.css";
			    @import "css/login.css";
			    @import "css/form.css";
                @import "js/fancybox/jquery.fancybox-1.3.4.css";
                </style>
                <link rel="stylesheet" href="css/jquery-ui.css" type="text/css" />   
                <script type="text/javascript" language="javascript" src="js/jquery.js"></script>
                <script type="text/javascript" language="javascript" src="js/jquery-ui.min.js"></script>
                <script type="text/javascript" language="javascript" src="js/jquery.dataTables.js"></script>
                <script type="text/javascript" language="javascript" src="js/jquery.dataTables.columnFilter.js"></script>
                <script type="text/javascript" language="javascript" src="js/fancybox/jquery.fancybox-1.3.4.pack.js"></script>
                <script type="text/javascript" language="javascript" src="js/rai.js"></script>
        </head>
        <body id="dt_example">
                <div id="container">
			<? if (!isset($no_title)) { ?>
                        <div class="full_width big">
                                <img src="img/rhizomatica_logo_small.png" style="vertical-align: middle;" /> <?=_('RAI - Rhizomatica Administration Interface')?>
                        </div>
			<? } ?>
