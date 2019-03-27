<?
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
putenv("LANGUAGE=$language");
setlocale(LC_ALL, $language);

// Set the text domain as 'messages'
$domain = 'messages';
bindtextdomain($domain, "/var/rhizomatica/rai/locale"); 
bind_textdomain_codeset($domain, 'UTF-8');
textdomain($domain);
?>