<?php 
require_once('modules/subscriber.php');
require_once('modules/configuration.php');
require_once('include/menu.php'); 
require_once('include/header.php');

print_menu('subscribers');
 
?>	

<br/><br/><br/>

<?php


function print_form($post_data,$errors,$active_tab='0') {

	$firstname = ($_POST['firstname'] != '') ? $_POST['firstname'] : '';
	$firstname_imei = ($_POST['firstname_imei'] != '') ? $_POST['firstname_imei'] : '';
	$callerid = ($_POST['callerid'] != '') ? $_POST['callerid'] : '';
	$amount = ($_POST['amount'] != '') ? $_POST['amount'] : '0';
	$location = ($_POST['location'] != '') ? $_POST['location'] : '';
	

?>

	<div id="stylized" class="myform" style="width:500px">
		<form id="form" name="form" method="post" action="provisioning.php">
		<h1><?= _("Provision a new subscriber") ?></h1>
			<div id="tabs" class="ui-override">
			<ul>
			  <li><a href="#imsi">IMSI</a></li>
			  <li><a href="#imei">IMEI</a></li>
			</ul>
	<div id="imsi">

<?php
		// get imsi
		$imsi_script="/var/rhizomatica/bin/get_imsi.py";
		if (file_exists($imsi_script) && is_executable($imsi_script)) {
				$imsi = shell_exec("/var/rhizomatica/bin/get_imsi.py");
				if (isset($imsi) && strlen($imsi) == 16) {
					echo "&nbsp;&nbsp;Got IMSI: $imsi";
					$sub = new Subscriber();
	                try {
	                    $ext = $sub->get_extension($imsi);
					} catch (SubscriberException $e) { 
						echo "&nbsp;&nbsp;Error getting Subscriber extension";
					}
				} else {
					echo "&nbsp;&nbsp;Error getting IMSI please retry";
				}
		}

        try {
			$loc = new Configuration();
			$locations = $loc->getLocations();
				
		} catch (ConfigurationException $e) {
			echo "&nbsp;&nbsp;Error getting locations";
		}

?>

	<span style='color: red; font-size: 12px;'><?= $errors ?></span><br/>
                    <label><?= _("Name") ?>
                    <span class="small"><?= _("Subscriber Name") ?></span>
                    </label>
                    <input type="text" name="firstname" id="firstname" value="<?=$firstname?>"/>

	<label><?= _("Subscriber number or IMSI") ?>
	<span class="small"><?= _("Subscriber number") ?></span>
	</label>
	<input type="text" name="callerid" id="callerid" value="<?=$ext?>"/>

<?php
				if (count($locations) > 1) {
?>
				<label><?= _("Location") ?>
				<span class="small"><?= _("Subscriber location") ?></span>
				</label>
<?php
					echo "<select name='location' id='location'>";
					foreach ($locations as $rloc) {
						echo "<option value='".$rloc->name."'>".$rloc->name."</option>";
					}
					echo "</select>";
				}
					
?>
				<br/>
				<button type="submit" name="add_subscriber_imsi"><?= _("Add") ?></button>
				<div class="spacer"></div>
				</form>
	</div>

		<div id="imei">

		<span style='color: red; font-size: 12px;'><?= $errors ?></span><br/>
        <label><?= _("Name") ?>
        <span class="small"><?= _("Subscriber Name") ?></span>
        </label>
        <input type="text" name="firstname_imei" id="firstname_imei" value="<?=$firstname_imei?>"/>

		<label>IMEI ( *#06# )
		<span class="small"><?= _("The phone must be connected or have recently attempted to connect") ?></span>
		</label>
		<input type="text" name="imei" id="imei_text" />
		<br />
		<button type="submit" name="add_subscriber_imei"><?= _("Add") ?></button>
		<div class="spacer"></div>

<script>
  $( function() {
        $( "#tabs" ).tabs( { active: <?=$active_tab?> } );
        $( "#imei_text" ).autocomplete(
  	      {
          source: "/rai/ajax.php?service=imei",
          minLength: 3
          }
         );
  });
</script>


			</div>
		</div>
	</div>
<?
}	


	$error_txt = "";
	if (isset($_POST['add_subscriber_imei'])) {
		$active_tab=1;
		$firstname = $_POST['firstname_imei'];
		if ($firstname == "") {
			$error_txt .= _("Name is empty")."<br/>";
		}
		if (isset($_POST['imei']) && strlen($_POST['imei'])==15) {

			$imei = rtrim($_POST['imei'],'X');
			$path = "http://localhost:8085/subscriber/imei/".$imei;
			$response = \Httpful\Request::get($path)->expectsJson()->send();
			$data = $response->body;
			$callerid=$data[0][2];
			if (strlen($callerid)==11) {
				$error_txt .= _("Subscriber already exists:").' '.$callerid;
			} elseif (strlen($callerid)!=5) {
				$error_txt .= _("Subscriber not found").' '.$callerid;
			}
	    } else {
	    	$error_txt .= _("Invalid IMEI");
	    }

	} elseif (isset($_POST['add_subscriber_imsi'])) { 
		$active_tab=0;
		// form pressed verify if any data is missing

		$firstname = $_POST['firstname'];
		$callerid = $_POST['callerid'];
		$location = $_POST['location'];

		if ($firstname == "") {
			$error_txt .= _("Name is empty")."<br/>";
		}
		if ($callerid == "") {
			$error_txt .= _("Subscriber number is empty")."<br/>";
		} elseif (strlen($callerid) != 5 && strlen($callerid) != 15) {
			$error_txt .= _("Invalid number")."<br/>";
		}
	}

	if (isset($_POST['add_subscriber_imsi']) || isset($_POST['add_subscriber_imei'])) {
		if ($error_txt != "") {
			print_form(1,$error_txt,$active_tab);
		} elseif ($error_txt == "") {
			// no error process form
	                    
			$firstname = $_POST['firstname'];
	        //$callerid = $_POST['callerid'];
			$location = $_POST['location'];

			// get internal prefix
			$site = new Configuration();
			$info = $site->getSite();
			$internalprefix = $info->postcode.$info->pbxcode;

			$new_num = "$internalprefix$callerid";
		
			echo "<center>";
			$amount = 0;
			$sub = new Subscriber();
			try {
				$sub->set("",$callerid,$firstname,1,$amount,"", "", $location);
				$ret = $sub->create();
				echo "<img src='img/true.png' width='200' height='170' /><br/><br/>";
				if ($ret != "") {
					echo "<span style='font-size: 20px;'>"._("Subscriber already exists! New subscriber number").": <b>$ret</b> "._("Successfully provisioned with an initial balance of")." $amount<br/><br/>";
				} else {
					echo "<span style='font-size: 20px;'>"._("Subscriber number").": <b>$callerid</b> "._("Successfully provisioned with an initial balance of")." $amount<br/><br/>";
				}
				echo "<a href='provisioning.php'><button class='b1'>"._("Go Back")."</button></a>";
			} catch (SubscriberException $e) {
				echo "<img src='img/false.png' width='200' height='170' /><br/><br/>";
				echo "<span style='font-size: 20px; color: red;'>"._("ERROR PROVISIONING SUBSCRIBER!").
					 " ".$callerid."</span><br/>".$e->getMessage()."<br/><br/><br/>";
				echo "<a href='provisioning.php'><button class='b1'>"._("Go Back")."</button></a>";
			}
			
			echo "</center>";
		}
	} else {
		print_form(0,'');
	}

?>

	</div>

	</body>
</html>
