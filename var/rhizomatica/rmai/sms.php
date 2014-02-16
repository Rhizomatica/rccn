<?php 
	require_once('include/header.php');
	require_once('include/menu.php');
?>

        	        <script type="text/javascript" charset="utf-8">
                        $(document).ready(function() {
                                $('#example').dataTable( {
                                        "sPaginationType": "full_numbers",
                                        "bProcessing": true,
                                        "bServerSide": true,
                                        "aaSorting": [[ 0, "desc" ]],
                                        "sAjaxSource": "sms_processing.php"
                                } );
                        } );
	                </script>

			<? print_menu('sms'); ?>	

			<h1><?= _("SMS History") ?></h1><br/>
			<div id="dynamic" style="margin-left: 20px;">
<table cellpadding="0" cellspacing="0" border="0" class="display" id="example">
	<thead>
		<tr>
			<th align='left' width="5%"><?= _("ID") ?></th>
			<th align='left'><?= _("Date") ?></th>
			<th align='left'><?= _("Source") ?></th>
			<th align='left'><?= _("Destination") ?></th>
			<th align='left'><?= _("Context") ?></th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td colspan="5" class="dataTables_empty"><?= _("Loading data from server") ?></td>
		</tr>
	</tbody>
	<tfoot>
		<tr>
                        <th align='left' width="5%"><?= _("ID") ?></th>
                        <th align='left'><?= _("Date") ?></th>
                        <th align='left'><?= _("Source") ?></th>
                        <th align='left'><?= _("Destination") ?></th>
                        <th align='left'><?= _("Context") ?></th>
		</tr>
	</tfoot>
</table>
			</div>
			<div class="spacer"></div>
				
		</div>
	</body>

</html>
