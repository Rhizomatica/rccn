<?php 

	require_once('include/header.php');
	require_once('include/menu.php');
	require_once('modules/sms.php');
	require_once('modules/subscriber.php');

?>
			<? print_menu('sms'); ?>

	                </script>
			<br/><br/><br/><br/>
			<center>
<?
function print_form($post_data,$errors) {

	$message = ($_POST['message'] != '') ? $_POST['message'] : '';
	$number = ($_POST['number'] != '') ? $_POST['number'] : '';
	$bulk_send = ($_POST['bulk_send'] != '') ? $_POST['bulk_send'] : '';

?>

			<div id="stylized" class="myform">
				<form id="form" name="form" method="post" action="send_sms.php">
				<h1><?=_("Send SMS") ?></h1><br/>

				<span style='color: red; font-size: 12px;'><?= $errors ?></span><br/>
				<label><?=_("Message") ?>
				<span class="small"><?=_("Text of the SMS message")?></span>
				</label>
				<textarea style='margin-left: -15px;' rows="6" cols="23" name="message" id="message"><?=$message?></textarea>

				<label><?=_("Number")?>
				<span class="small"><?=_("Recipient of the SMS message")?></span>
				</label>
				<input type="text" name="number" id="number" value="<?=$number?>"/>
			
                                <label><?=_("All registered")?></label>
                                <input type="checkbox" name="bulk_send" id="bulk_send" value="all"/><br/>

                                <label><?=_("All not registered (5 digits)")?></label>
                                <input type="checkbox" name="bulk_send" id="bulk_send" value="extension"/><br/>

                                <label><?=_("All subscription not paid")?></label>
                                <input type="checkbox" name="bulk_send" id="bulk_send" value="notpaid"/><br/>

                                <label><?=_("All not authorized")?></label>
                                <input type="checkbox" name="bulk_send" id="bulk_send" value="unauthorized"/><br/>
				
				<button type="submit" name="send_sms"><?=_("Send SMS")?></button>
				<div class="spacer"></div>
				</form>
			</div>
<?
}	
				$errors = 0;
				$error_txt = "";
				// errors check
				if (isset($_POST['send_sms'])) {
					// form pressed verify if any data is missing
					$message = $_POST['message'];
					$number = $_POST['number'];
					$bulk_send = $_POST['bulk_send'];

					if ($message == "") {
						$error_txt .= _("SMS text is empty")."<br/>";
					}
					if ($number == "" && !isset($bulk_send)) {
						$error_txt .= _("SMS number is empty")."<br/>";
					}
				} 

				if (isset($_POST['send_sms']) && $error_txt != "") {
					print_form(1,$error_txt);
				} elseif (isset($_POST['send_sms']) && $error_txt == "") {
					$sub = new Subscriber();
	
					$ret = 0;
					try {
						$sub->get($_POST['number']);
					} catch (SubscriberException $e) {
						echo "<img src='img/false.png' width='200' height='170' /><br/><br/>";
						echo "<span style='font-size: 20px; color: red;'>"._("ERROR SENDING SMS!")."</br>".$e->getMessage()." </span><br/><br/><br/><br/>";
						echo "<a href='send_sms.php'><button class='b1'>"._("Go Back")."</button></a>";
						$ret = 1;
					}

					if ($ret == 0) {
						if (isset($_POST['bulk_send'])) {
							try {
								$sms = new SMS();
								$sms->send_broadcast($_POST['message'], $_POST['bulk_send']);
								echo "<img src='img/true.png' width='150' height='150' /><br/><br/>";
								echo "<span style='font-size: 20px;'>"._("BROADCAST MESSAGE IS BEING SENT!")."</span><br/><br/><br/><br/>";
								echo "<a href='send_sms.php'><button class='b1'>"._("Go Back")."</button></a>";
							} catch (SMSException $e) {
                                        	        	echo "<img src='img/false.png' width='200' height='170' /><br/><br/>";
	                                                	echo "<span style='font-size: 20px; color: red;'>"._("ERROR SENDING MASS SMS!")."<br/>".$e->getMessage()." </span><br/><br/><br/><br/>";
		                                                echo "<a href='send_sms.php'><button class='b1'>"._("Go Back")."</button></a>";
							}
						} else {
							try {
								$sms = new SMS();
								$sms->send('10000',$_POST['number'],$_POST['message']);
								echo "<img src='img/true.png' width='150' height='150' /><br/><br/>";
								echo "<span style='font-size: 20px;'>"._("MESSAGE SENT!")."</span><br/><br/><br/><br/>";
								echo "<a href='send_sms.php'><button class='b1'>"._("Go Back")."</button></a>";
							} catch (SMSException $e) {
                                        	        	echo "<img src='img/false.png' width='200' height='170' /><br/><br/>";
	                                                	echo "<span style='font-size: 20px; color: red;'>"._("ERROR SENDING SMS!")."<br/>".$e->getMessage()." </span><br/><br/><br/><br/>";
		                                                echo "<a href='send_sms.php'><button class='b1'>"._("Go Back")."</button></a>";
							}
						}
					}
				}					
				else {
						print_form(0,'');
				}
			?>

			</center>
		</div>
	</body>

</html>
