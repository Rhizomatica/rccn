<?php 

	require_once('include/header.php');
	require_once('include/menu.php');

?>
			<? print_menu('resellers'); ?>

		<script type="text/javascript" charset="utf-8">
			$(document).ready(function() {
				$('#example').dataTable( {
					"sPaginationType": "full_numbers",
					"bProcessing": true,
					"bServerSide": true,
					"aaSorting": [[ 0, "desc" ]],
					"aoColumnDefs": [
					   {
					        "aTargets": [5],
					        "mData": null,
					        "mRender": function (data, type, full) {
					            return '<a href="reseller_delete.php?id='+full[1]+'" class="pop"><img src="img/delete.png" alt="Delete" valign="middle" /></a>';
					        }
					    }
					],
            				"fnDrawCallback": function () {
				                $(".pop").fancybox({
			                  	    'width'             : '35%',
				                    'height'            : '40%',
				                    'autoScale'         : false,
				                    'type'              : 'iframe',
						    'onClosed'          : function() {
			                                  parent.location.reload(true);
                        		            }
			                	});
				        },
					"sAjaxSource": "resellers_processing.php"
				} );

			});
			
		</script>
			
			<h1><?= _("Resellers") ?></h1><br/>
			<div id="dynamic" style="margin-left: 20px;">
<table cellpadding="0" cellspacing="0" border="0" class="display" id="example">
	<thead>
		<tr>
			<th align='left'><?= _("Creation Date") ?></th>
			<th align='left'><?= _("Reseller Number") ?></th>
			<th align='left'>PIN</th>
			<th align='left'><?= _("Balance") ?></th>
			<th align='left'><?= _("Total Sales") ?></th>
			<th align='left'><?= _("Actions") ?></th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td colspan="5" class="dataTables_empty"><?= _("Loading data from server") ?></td>
		</tr>
	</tbody>
	<tfoot>
		<tr>
                        <th align='left'><?= _("Creation Date") ?></th>
                        <th align='left'><?= _("Reseller Number") ?></th>
                        <th align='left'>PIN</th>
                        <th align='left'><?= _("Balance") ?></th>
                        <th align='left'><?= _("Total Sales") ?></th>
                        <th align='left'><?= _("Actions") ?></th>		
		</tr>
	</tfoot>
</table>
			</div>
			<div class="spacer"></div>
				
		</div>
	</body>

</html>

