<?php 
require_once('include/header.php');
require_once('include/menu.php');

?>

		<script type="text/javascript" language="javascript">
			$(document).ready(function () {
			$.ajax({
    			    url: "get_balance.php",
		            type: "GET",
		            cache: false,
			    timeout: 60000,
			    error: function() {
				$('#balance').html("<span style='font-size: 20px; color: red'><?=_('Error loading VOIP Account Balance.. please try again later') ?>");
			    },
		   	    beforeSend:function(){
			       $('#balance').html('<img src="img/loading.gif" alt="Loading..." /><br/><br/><span style="font-size: 20px"><?=_('Loading VOIP Account Balance.. please wait') ?></span>');
			    },
		            success: function (html) {
			            $('#balance').html("<span style='font-size: 20px;'><?=_('VOIP Account Balance:')?> <b>" + html + "</b> USD</span>");
		            }
			 });
			
			});
		</script>
			<? print_menu('platform'); ?>	
			<br/><br/><br/><br/><br/><br/>
			<center>
			<?php
				echo "<img src='img/account.png' width='150' height='150' /><br/><br/>";
				echo "<div id='balance'></div>";
			?>
			</center>
		</div>
	</body>

</html>
