<? 

require('modules/reseller.php'); 
$no_title = 1;
require('include/header.php');


function print_form($post_data,$errors) {

	$reseller = new Reseller();
	try {
		$msisdn = $_GET['id'];
		$reseller->get($msisdn);
	} catch (ResellerException $e) {
		echo "<img src='img/false.png' width='200' height='170' /><br/><br/>";
		echo "<span style='font-size: 20px; color: red;'>"._("ERROR GETTING RESELLER INFO!")."<br/> ".$e->getMessage()." </span><br/><br/><br/><br/>";
		echo "<a href='#' onclick=\"parent.jQuery.fancybox.close()\"><button class='b1'>"._("Close")."</button></a>";

	}

?>
<br/>
			<div id="stylized" class="myform">
				<form id="form" name="form" method="post" action="reseller_delete.php">
				<h1><?= _("Delete Reseller") ?></h1><br/>

				<input type="hidden" name="msisdn" value="<?=$reseller->msisdn?>" />

				<?=_("Confirm deletion of")?>  <?=$reseller->msisdn?>

				<button type="submit" name="delete_reseller"><?= _("Delete") ?></button>
				<div class="spacer"></div>
				</form>
			</div>
<?
}	
				if (isset($_POST['delete_reseller'])) {
					// no error process form
					$msisdn = $_POST['msisdn'];

					echo "<center>";
					try {
						$reseller = new Reseller();
						$reseller->get($msisdn);
						$reseller->delete();
						
						echo "<img src='img/true.png' width='200' height='170' /><br/><br/>";
						echo "<span style='font-size: 20px;'>"._("Reseller successfully deleted!")."<br/><br/>";
						echo "<a href='#'  onclick=\"parent.jQuery.fancybox.close()\"><button class='b1'>"._("Close")."</button></a>";
					} catch (ResellerException $e) {					
						echo "<img src='img/false.png' width='200' height='170' /><br/><br/>";
						echo "<span style='font-size: 20px; color: red;'>"._("ERROR DELETING RESELLER!")." ".$e->getMessage()." </span><br/><br/><br/><br/>";
						echo "<a href='#' onclick=\"parent.jQuery.fancybox.close()\"><button class='b1'>"._("Close")."</button></a>";
					}
					
					echo "</center>";
				} else {
					print_form(0,'');
				}

			?>

	</body>

</html>
