<?php 

	require_once('include/header.php');
	require_once('include/menu.php');
	require_once('modules/reseller.php');

?>
			<? print_menu('resellers'); ?>

	                </script>
			<br/><br/>
			<center>
<?
function print_form($post_data,$errors) {


	try {
		$reseller = new Reseller();
		$messages = $reseller->get('messages');
	} catch (ResellerException $e) {
		echo "<img src='img/false.png' width='200' height='170' /><br/><br/>";
		echo "<span style='font-size: 20px; color: red;'>"._("ERROR GETTING INFO!").$e->getMessage()." </span><br/><br/><br/><br/>";
		echo "<a href='resellers_configuration.php'><button class='b1'>"._("Go Back")."</button></a>";
	}


	$message1 = ($_POST['message1'] != '') ? $_POST['message1'] : $messages[0];
	$message2 = ($_POST['message2'] != '') ? $_POST['message2'] : $messages[1];
	$message3 = ($_POST['message3'] != '') ? $_POST['message3'] : $messages[2];
	$message4 = ($_POST['message4'] != '') ? $_POST['message4'] : $messages[3];
	$message5 = ($_POST['message5'] != '') ? $_POST['message5'] : $messages[4];
	$message6 = ($_POST['message6'] != '') ? $_POST['message6'] : $messages[5];



?>

			<div id="stylized" class="myform" style='width: 520px;'>
				<form id="form" name="form" method="post" action="resellers_configuration.php">
				<h1><?=_("Configure reseller notification messages") ?></h1><br/>

				<span style='color: red; font-size: 12px;'><?= $errors ?></span><br/>
				<label><?=_("Invalid data") ?>
				<span class="small"><?=_("Invalid data sent to the shortcode")?></span>
				</label>
				<textarea style='margin-left: -15px;' rows="6" cols="23" name="message1" id="message1"><?=$message1?></textarea>

				<label><?=_("Reseller not enough credit1") ?>
				<span class="small"><?=_("Message sent to the subscriber")?></span>
				</label>
				<textarea style='margin-left: -15px;' rows="6" cols="23" name="message2" id="message2"><?=$message2?></textarea>

				<label><?=_("Reseller not enough credit2 ") ?>
				<span class="small"><?=_("Message sent to the reseller")?></span>
				</label>
				<textarea style='margin-left: -15px;' rows="6" cols="23" name="message3" id="message3"><?=$message3?></textarea>

				<label><?=_("Credit added successfully to subscriber account") ?>
				<span class="small"><?=_("Message sent to the subscriber")?></span>
				</label>
				<textarea style='margin-left: -15px;' rows="6" cols="23" name="message4" id="message4"><?=$message4?></textarea>

				<label><?=_("Credit added successfully to subscriber account") ?>
				<span class="small"><?=_("Message sent to the Reseller")?></span>
				</label>
				<textarea style='margin-left: -15px;' rows="6" cols="23" name="message5" id="message5"><?=$message5?></textarea>

				<label><?=_("General error") ?>
				<span class="small"><?=_("General error notice message")?></span>
				</label>
				<textarea style='margin-left: -15px;' rows="6" cols="23" name="message6" id="message6"><?=$message6?></textarea>

				<button type="submit" name="save_messages"><?=_("Save")?></button>
				<div class="spacer"></div>
				</form>
			</div>
<?
}	
				$errors = 0;
				$error_txt = "";
				// errors check
				if (isset($_POST['save_messages'])) {
					// form pressed verify if any data is missing
					$message1 = $_POST['message1'];
					$message2 = $_POST['message2'];
					$message3 = $_POST['message3'];
					$message4 = $_POST['message4'];
					$message5 = $_POST['message5'];
					$message6 = $_POST['message6'];


				} 

				if (isset($_POST['save_messages']) && $error_txt != "") {
					print_form(1,$error_txt);
				} elseif (isset($_POST['save_messages']) && $error_txt == "") {
	
					try {
						$reseller = new Reseller();
						$reseller->edit_messages($message1,$message2,$message3,$message4,$message5,$message6);
						echo "<img src='img/true.png' width='150' height='150' /><br/><br/>";
						echo "<span style='font-size: 20px;'>"._("MESSAGES SAVED!")."</span><br/><br/><br/><br/>";
						echo "<a href='resellers_configuration.php'><button class='b1'>"._("Go Back")."</button></a>";
					} catch (ResellerException $e) {
						echo "<img src='img/false.png' width='200' height='170' /><br/><br/>";
						echo "<span style='font-size: 20px; color: red;'>"._("ERROR SAVING MESSAGES!")."</br>".$e->getMessage()." </span><br/><br/><br/><br/>";
						echo "<a href='resellers_configuration.php'><button class='b1'>"._("Go Back")."</button></a>";
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
