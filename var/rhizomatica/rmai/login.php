<?php 

require_once('include/menu.php'); 
require_once('modules/access_manager.php');
	
if(isset($_POST['access']) && $error_txt == "") {
	$access = new AccessManager();
	$access->login($_POST['username'],$_POST['password'],$_POST['language']);
}

require_once('include/header.php');

?>
	<script type="text/javascript" src="js/jquery.ddslick.js"></script>
	<script>
	$( document ).ready(function() {
		$('#language-select').ddslick({
			width: 200,
			onSelected: function(data){
				$('#language').val(data.selectedData.value);
			}
			
		});	
	});		

	</script>
			<br/><br/><br/><br/>

<?php
	function print_form($post_data, $errors) {
		$username = ($_POST['username'] != '') ? $_POST['username'] : '';
		$password = ($_POST['password'] != '') ? $_POST['password'] : '';
?>
			<form action="login.php" method="post" id="newRequestForm">
			<fieldset class="formLogin">
			    <h2></h2>
			    <span style='color: red; font-size: 12px;'><?= $errors ?></span><br/>
			    <div>
			        <label for="user_login">Username: &nbsp;</label>
				<input type='text' name='username' size='20' />
			    </div>
			    <div>
			        <label for="user_password">Password: &nbsp;</label>
				<input type='password' name='password' size='20' />
			    </div>
			    <div>
				<br/>
				<input type="hidden" name="language" id="language" value="" />
				<select id="language-select">
        				<option value="es" selected="selected" data-imagesrc="img/es_flag.png">Spanish</option>
				        <option value="en" data-imagesrc="img/en_flag.png">English</option>
				</select>
			    </div>
			    <div><br/>
			        <label>&nbsp;</label>
			        <input type="submit" name="access" class='login_button' value="Login" />
			    </div>
			</fieldset>
			</form>
<?php
	}

	$error_txt = "";
	if (isset($_POST['access'])) {
		$username = $_POST['username'];
		$password = $_POST['password'];

		if ($username == "") {
			$error_txt .= "Username is empty";	
		}
		if ($password == "") {
			$error_txt .= "Password is empty";
		}
	}

	if (isset($_POST['access']) && $error_txt != "") {
		print_form(1,$error_txt);
	} else {
		print_form(0, '');
	}

?>
	</div>
	</body>
</html>
