<?php 
require_once('modules/reseller.php');
require_once('modules/configuration.php');
require_once('include/menu.php'); 
require_once('include/header.php');

print_menu('resellers');
 
?>	

<br/><br/><br/><br/>

<?php


function print_form($post_data,$errors) {

	$msisdn = ($_POST['msisdn'] != '') ? $_POST['msisdn'] : '';
	$pin = ($_POST['pin'] != '') ? $_POST['pin'] : '';
	$amount = ($_POST['amount'] != '') ? $_POST['amount'] : '0';

?>
			<div id="stylized" class="myform">
				<form id="form" name="form" method="post" action="resellers_provisioning.php">
				<h1><?= _("Provision a new Reseller") ?></h1><br/>

				<span style='color: red; font-size: 12px;'><?= $errors ?></span><br/>
                                <label><?= _("Reseller number") ?>
                                <span class="small"><?= _("Reseller number") ?></span>
                                </label>
                                <input type="text" name="msisdn" id="msisdn" value="<?=$msisdn?>"/>

				<label><?= _("PIN") ?>
				<span class="small"><?= _("Reseller code") ?></span>
				</label>
				<input type="text" name="pin" id="pin" size="4" maxlength='4' value="<?=$pin?>"/>

				<label><?= _("Initial Balance") ?>
				<span class="small"><?= _("Amount to add") ?></span>
				</label>
				<input type="text" name="amount" id="amount" value="<?=$amount?>"/><br/>
			
				<button type="submit" name="add_reseller"><?= _("Add") ?></button>
				<div class="spacer"></div>
				</form>
			</div>
<?
}	
				$error_txt = "";
				// errors check
				if (isset($_POST['add_reseller'])) {
					// form pressed verify if any data is missing
					$msisdn = $_POST['msisdn'];
					$pin = $_POST['pin'];
					$amount = $_POST['amount'];

					if ($msisdn == "") {
						$error_txt .= _("Reseller number is empty")."<br/>";
					}
					if ($pin == "" || strlen($pin) > 5 || !is_numeric($pin)) {
						$error_txt .= _("Reseller PIN is invalid")."<br/>";
					}
					if ($amount == "") {
						$error_txt .= _("Initial balance is empty")."<br/>";
					}
				} 

				if (isset($_POST['add_reseller']) && $error_txt != "") {
					print_form(1,$error_txt);
				}elseif (isset($_POST['add_reseller']) && $error_txt == "") {
					// no error process form
		                        
					$msisdn = $_POST['msisdn'];
                                        $pin = $_POST['pin'];
                                        $amount = $_POST['amount'];

					echo "<center>";
					
					$reseller = new Reseller();
					try {
						$reseller->set($msisdn,$pin,$amount);
						$reseller->create();
						echo "<img src='img/true.png' width='200' height='170' /><br/><br/>";
						echo "<span style='font-size: 20px;'>"._("Reseller number").": <b>$pin</b> "._("Successfully provisioned with an initial balance of")." $amount<br/><br/>";
						echo "<a href='resellers_provisioning.php'><button class='b1'>"._("Go Back")."</button></a>";
					} catch (ResellerException $e) {
						echo "<img src='img/false.png' width='200' height='170' /><br/><br/>";
						echo "<span style='font-size: 20px; color: red;'>"._("ERROR PROVISIONING RESELLER!")." </span><br/>".$e->getMessage()."<br/><br/><br/>";
						echo "<a href='resellers_provisioning.php'><button class='b1'>"._("Go Back")."</button></a>";
					}
					
					echo "</center>";
				} else {
					print_form(0,'');
				}

			?>

		</div>
	</body>
</html>
