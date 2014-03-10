<?php 

require_once('include/header.php');
require_once('include/menu.php');

?> 

                <script type="text/javascript" charset="utf-8">
                        $(document).ready(function() {
                                $('#example').dataTable( {
                                        <?
                                        /*$lang_file = 'js/'.$_SESSION['lang'].'.txt';
                                        if (file_exists($lang_file)) {
                                                echo '"oLanguage": { "sUrl": "'.$lang_file.'" },';
                                        }*/
                                        ?>

                                        "sPaginationType": "full_numbers",
                                        "bProcessing": true,
                                        "bServerSide": true,
                                        "aaSorting": [[ 1, "desc" ]],
                                        "sAjaxSource": "cdr_processing.php"
                                } ).columnFilter();
                        } );
                </script>
			<? print_menu('cdr'); ?>	


			<h1><?= _("Calls Details Records") ?></h1><br/>
			<div id="dynamic" style="margin-left: 20px;">
	<table cellpadding="0" cellspacing="0" border="0" class="display" id="example">
	<thead>
		<tr>
			<th width="2%">ID</th>
			<th align='left' width="13%"><?= _("Call Date") ?></th>
			<th align='left' width='20%'><?= _("Caller Number") ?></th>
			<th align='left' width='13%'><?= _("Called Number") ?></th>
			<th align='left' width="10%"><?= _("Context") ?></th>
			<th width="5%"><?= _("Duration") ?></th>
			<th align='left'><?= _("Hangup Cause") ?></th>
			<th align='left'><?= _("Destination") ?></th>
			<th align='left'><?= _("Cost") ?></th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td colspan="5" class="dataTables_empty"><?= _("Loading data from server") ?></td>
		</tr>
	</tbody>
	<tfoot>
		<tr>
                        <th width="2%">ID</th>
                        <th align='left' width="13%"><?= _("Call Date") ?></th>
                        <th align='left' width='20%'><?= _("Caller Number") ?></th>
                        <th align='left' width='13%'><?= _("Called Number") ?></th>
                        <th align='left' width="10%"><?= _("Context") ?></th>
                        <th width="5%"><?= _("Duration") ?></th>
                        <th align='left'><?= _("Hangup Cause") ?></th>
                        <th align='left'><?= _("Destination") ?></th>
                        <th align='left'><?= _("Cost") ?></th>
		</tr>
	</tfoot>
</table>
			</div>
			<div class="spacer"></div>
				
		</div>
	</body>

</html>
