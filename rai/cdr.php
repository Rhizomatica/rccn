<?php 

require_once('include/header.php');
require_once('include/menu.php');

?> 

    <script type="text/javascript" charset="utf-8">
            $(document).ready(function() {
                    var dT = $('#example').dataTable( {
                            <?
                            $lang_file = 'js/'.$_SESSION['lang'].'.txt';
                            if (file_exists($lang_file)) {
                                    echo '"oLanguage": { "sUrl": "'.$lang_file.'" },';
                            }
                            ?>
                            "sPaginationType": "full_numbers",
                            "bProcessing": true,
                            "bServerSide": true,
                            "aaSorting": [[ 0, "desc" ]],
                            "sAjaxSource": "cdr_processing.php",
                            "fnServerParams": function ( aoData ) {
				co = $("#cost_only_check").attr('checked');
		                aoData.push( { "name": "cost_only", "value": co } );
                            },
                            "fnInitComplete": function (oSettings, json) {
                                html='<span id="cost_only" style="margin-right:20px"><label>'+ tr.call_cost_txt + '</label><input style="vertical-align:middle;padding:1px" type="checkbox" name="cost_only" id="cost_only_check">'
                                $("#example_filter").prepend(html);
                                $("#cost_only_check").change(function () {
                                        dT.fnFilter('');
                                })
                            },
                            "aoColumnDefs": [
			                    { "bSearchable": false, "aTargets": [0] },
			                    { "bSearchable": false, "aTargets": [1] },
			                    { "bSearchable": false, "aTargets": [5] },
			                    { "bSearchable": false, "aTargets": [8] } ]
                                } ).columnFilter();
                        } );
    </script>
			<? print_menu('cdr'); ?>	


			<h1><?= _("Calls Details Records") ?></h1><br/>
			<div id="dynamic">
	<table cellpadding="0" cellspacing="0" border="0" class="display" id="example">
	<thead>
		<tr>
			<th width="2%">ID</th>
			<th align='left' width="16%"><?= _("Call Date") ?></th>
			<th align='left' width='12%'><?= _("Caller Number") ?></th>
			<th align='left' width='12%'><?= _("Called Number") ?></th>
			<th align='left' width="8%"><?= _("Context") ?></th>
			<th width="5%"><?= _("Duration") ?></th>
			<th align='left' width="18%"><?= _("Hangup Cause") ?></th>
			<th align='left' width="22%"><?= _("Destination") ?></th>
			<th align='left' width="5%"><?= _("Cost") ?></th>
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
                        <th align='left' width="16%"><?= _("Call Date") ?></th>
                        <th align='left' width='12%'><?= _("Caller Number") ?></th>
                        <th align='left' width='12%'><?= _("Called Number") ?></th>
                        <th align='left' width="8%"><?= _("Context") ?></th>
                        <th width="5%"><?= _("Duration") ?></th>
                        <th align='left' width="18%"><?= _("Hangup Cause") ?></th>
                        <th align='left' width="22%"><?= _("Destination") ?></th>
                        <th align='left' width="5%"><?= _("Cost") ?></th>
		</tr>
	</tfoot>
</table>
			</div>
			<div class="spacer"></div>
				
		</div>
	</body>

</html>
