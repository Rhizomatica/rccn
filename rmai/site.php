<?php 

	require_once('include/header.php');
	require_once('include/menu.php');
	require_once('modules/configuration.php');

?>
			<? print_menu('platform'); ?>

	                </script>
			<br/><br/>
			<center>
			<?php
				
				try {
					$site = new Configuration();
					$info = $site->getSite();
			?>
			<style>

 dl {
    border: 1px solid #666;
    padding: 0.5em;
    width: 500px;
    font-size: 15px;
  }
  dt {
    float: left;
    clear: left;
    width: 200px;
    text-align: right;
    font-weight: bold;
  }
  dd {
    padding: 0 0 10px 0;
  }

</style>
    			<dl>
        			<dt><?= _('Site name') ?>:</dt>
        			<dd><?= $info->site_name ?></dd>
        			<dt><?=_ ('Network name') ?>:</dt>
        			<dd><?= $info->network_name ?></dd>
        			<dt><?= _('Prefix') ?>:</dt>
        			<dd><?=$info->postcode.$info->pbxcode?></dd>
    			</dl>
			<?	
				} catch (ConfigurationException $e) {
					echo $e->getMessage();
				}
				
			?>
		</div>
	</body>

</html>
