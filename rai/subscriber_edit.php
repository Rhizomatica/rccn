<? 

require('modules/subscriber.php');
require('modules/configuration.php');
$no_title = 1;
require('include/header.php');


function print_form($post_data,$errors) {
	$firstname = ($_POST['firstname'] != '') ? $_POST['firstname'] : '';
	$callerid = ($_POST['callerid'] != '') ? $_POST['callerid'] : '';

	$sub = new Subscriber();
	
	try {
		$msisdn = $_GET['id'];
		$sub->get($_GET['id']);
		$name = ($_POST['firstname'] != '') ? $_POST['firstname'] : $sub->name;
		$callerid = ($_POST['callerid'] != '') ? $_POST['callerid'] : $sub->msisdn;
		$location = ($_POST['location'] != '') ? $_POST['location'] : $sub->location;
	} catch (PDOException $e) {
		echo "<img src='img/false.png' width='200' height='170' /><br/><br/>";
		echo "<span style='font-size: 20px; color: red;'>"._("ERROR GETTING SUBSCRIBER INFO!").$e->getMessage()." </span><br/><br/><br/><br/>";
		echo "<a href='provisioning.php'><button class='b1'>Go Back</button></a>";

	}

	try {
		$loc = new Configuration();
		$locations = $loc->getLocations();
	} catch (ConfigurationException $e) {
		echo "&nbsp;&nbsp;Error getting locations";
	}

?>
			<br/>
			<div id="stylized" class="myform">
				<form id="form" name="form" method="post" action="subscriber_edit.php">
				<h1><?= _("Edit Subscriber") ?></h1><br/>

				<input type="hidden" name="sip_id" value="<?=$msisdn?>" />
				<span style='color: red; font-size: 12px;'><?= $errors ?></span><br/>
                                <label><?= _("Name") ?>
                                <span class="small"><?= _("Subscriber Name") ?></span>
                                </label>
                                <input type="text" name="firstname" id="firstname" value="<?=$name?>"/>


				<label><?= _("Subscriber number") ?>
				<span class="small"><?= _("Subscriber number") ?></span>
				</label>
				<input type="text" name="callerid" id="callerid" value="<?=$callerid?>"/>
				
<?php
                                if (count($locations) > 1) {
?>
                                <label><?= _("Location") ?>
                                <span class="small"><?= _("Subscriber location") ?></span>
                                </label>
<?php
                                        echo "<select name='location' id='location'>";
                                        foreach ($locations as $rloc) {
						if ($location == $rloc->name) {
	                                                echo "<option value='".$rloc->name."' selected='selected'>".$rloc->name."</option>";
						} else {
							echo "<option value='".$rloc->name."'>".$rloc->name."</option>";
						}
                                        }
                                        echo "</select>";
                                }
?>



				<label><?= _("Subscription Paid") ?>
				<span class="small"><?= _("Check for yes uncheck for no") ?></span>
				</label><br/><br/>
				<? $checked = ($sub->subscription_status == 0) ? '' : 'checked=checked'; ?>
				<input type="checkbox" name="subscription_status" id="subscription_status" value="1" <?=$checked?>/><br/>
				
				<label><?= _("Authorized") ?>
				<span class="small"><?= _("Check for yes uncheck for no") ?></span>
				</label>
				<? $checked = ($sub->authorized == 0) ? '' : 'checked=checked'; ?>
				<input type="checkbox" name="authorized" id="authorized" value="1" <?=$checked?>/><br/>


				<button type="submit" name="edit_subscriber"><?= _("Save") ?></button>
				<div class="spacer"></div>
				</form>
			</div>
<?
}	

				$error_txt = "";
				// errors check
				if (isset($_POST['edit_subscriber'])) {
					// form pressed verify if any data is missing
					$firstname = $_POST['firstname'];
					$callerid = $_POST['callerid'];
					$authorized = $_POST['authorized'];
					$location = $_POST['location'];

					if ($firstname == "") {
						$error_txt .= _("Name is empty")."<br/>";
					}
					if ($callerid == "" || strlen($callerid) != 11) {
						$error_txt .= _("Subscriber number is invalid")."<br/>";
					}
				} 

				if (isset($_POST['edit_subscriber']) && $error_txt != "") {
					print_form(1,$error_txt);
				} elseif (isset($_POST['edit_subscriber']) && $error_txt == "") {
					echo "<center>";	
					$sub = new Subscriber();
					try {
						#$sub->get($_POST['msisdn']);
						if ($_POST['authorized'] == 1) {
							$sub->set("",$callerid,$firstname,1,"","","",$location);
						} else {
							$sub->set("",$callerid,$firstname,0,"","","",$location);
						}
						if ($_POST['subscription_status'] == 1) {
							$sub->subscription_status = 1;
						} else {
							$sub->subscription_status = 0;
						}

						$sub->edit();					
						echo "<img src='img/true.png' width='200' height='170' /><br/><br/>";
						echo "<span style='font-size: 20px;'>"._("Subscriber number").": <b>$callerid</b> "._("successfully modified")."<br/><br/>";
						echo "<a href='#'  onclick=\"parent.jQuery.fancybox.close()\"><button class='b1'>"._("Close")."</button></a>";
					} catch (SubscriberException $e) {
						echo "<img src='img/false.png' width='200' height='170' /><br/><br/>";
						echo "<span style='font-size: 20px; color: red;'>"._("ERROR SAVING SUBSCRIBER!")." ".$e->getMessage()." </span><br/><br/><br/><br/>";
						echo "<a href='#' onclick=\"parent.jQuery.fancybox.close()\"><button class='b1'>"._("Close")."</button></a>";
					}
					
					echo "</center>";
				} else {
					print_form(0,'');
				}

			?>

	</body>

</html>
