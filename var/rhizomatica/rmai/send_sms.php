<?php 

	require_once('include/header.php');
	require_once('include/menu.php');
	require_once('modules/sms.php');

?>
			<? print_menu('send_sms'); ?>

	                </script>
			<br/><br/>
			<center>
<?
function print_form($post_data,$errors) {

	$message = ($_POST['message'] != '') ? $_POST['message'] : '';
	$number = ($_POST['number'] != '') ? $_POST['number'] : '';
	$bulk_send = ($_POST['bulk_send'] != '') ? $_POST['bulk_send'] : '';

?>

			<div id="stylized" class="myform">
				<form id="form" name="form" method="post" action="send_sms.php">
				<h1>Send SMS</h1><br/>

				<span style='color: red; font-size: 12px;'><?= $errors ?></span><br/>
				<label>Message
				<span class="small">Text of the SMS message</span>
				</label>
				<input type="text" name="message" id="message" value="<?=$message?>"/>

				<label>Number
				<span class="small">Recipient of the SMS message</span>
				</label>
				<input type="text" name="number" id="number" value="<?=$number?>"/>

				<label>Bulk send
				<span class="small">Send SMS to all subscribers</span>
				</label>
				<input type="checkbox" name="bulk_send" id="bulk_send" value="1"/>

				<button type="submit" name="send_sms">Send SMS</button>
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
						$error_txt .= "SMS text is empty<br/>";
					}
					if ($number == "" && !isset($bulk_send)) {
						$error_txt .= "SMS number is empty<br/>";
					}
				} 

				if (isset($_POST['send_sms']) && $error_txt != "") {
					print_form(1,$error_txt);
				} elseif (isset($_POST['send_sms']) && $error_txt == "") {
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
				else {
						print_form(0,'');
				}
			?>

			</center>
		</div>
	</body>

</html>
