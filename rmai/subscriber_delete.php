<? 

require('modules/subscriber.php'); 
$no_title = 1;
require('include/header.php');


function print_form($post_data,$errors) {

	$sub = new Subscriber();
	try {
		$msisdn = $_GET['id'];
		$sub->get($msisdn);	
	} catch (SubscriberException $e) {
		echo "<img src='img/false.png' width='200' height='170' /><br/><br/>";
		echo "<span style='font-size: 20px; color: red;'>"._("ERROR GETTING SUBSCRIBER INFO!")."<br/> ".$e->getMessage()." </span><br/><br/><br/><br/>";
		echo "<a href='#' onclick=\"parent.jQuery.fancybox.close()\"><button class='b1'>"._("Close")."</button></a>";

	}

?>
<br/>
			<div id="stylized" class="myform">
				<form id="form" name="form" method="post" action="subscriber_delete.php">
				<h1><?= _("Delete Subscriber") ?></h1><br/>

				<input type="hidden" name="msisdn" value="<?=$sub->msisdn?>" />

				<?=_("Confirm deletion of")?>  <?=$sub->name?> <?=$sub->msisdn?>

				<button type="submit" name="delete_subscriber"><?= _("Delete") ?></button>
				<div class="spacer"></div>
				</form>
			</div>
<?
}	
				if (isset($_POST['delete_subscriber'])) {
					// no error process form
					$msisdn = $_POST['msisdn'];

					echo "<center>";
					try {
						$sub = new Subscriber();
						$sub->get($msisdn);
						$sub->delete();
						echo "<img src='img/true.png' width='200' height='170' /><br/><br/>";
						echo "<span style='font-size: 20px;'>"._("Subscriber successfully deleted!")."<br/><br/>";
						echo "<a href='#'  onclick=\"parent.jQuery.fancybox.close()\"><button class='b1'>"._("Close")."</button></a>";
					} catch (SubscriberException $e) {					
						echo "<img src='img/false.png' width='200' height='170' /><br/><br/>";
						echo "<span style='font-size: 20px; color: red;'>"._("ERROR DELETING SUBSCRIBER!")." ".$e->getMessage()." </span><br/><br/><br/><br/>";
						echo "<a href='#' onclick=\"parent.jQuery.fancybox.close()\"><button class='b1'>"._("Close")."</button></a>";
					}
					
					echo "</center>";
				} else {
					print_form(0,'');
				}

			?>

	</body>

</html>
