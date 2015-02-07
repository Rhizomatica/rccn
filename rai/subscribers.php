<?php 

	require_once('include/header.php');
	require_once('include/menu.php');
	require_once('modules/subscriber.php');

?>
			<? print_menu('subscribers'); ?>

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
                                        "aaSorting": [[ 0, "desc" ]],
                                        "aoColumnDefs": [
                                           {
                                                "aTargets": [8],
                                                "mData": null,
                                                "mRender": function (data, type, full) {
                                                    sub = full[4].match(/\d\d\d\d\d\d\d\d\d\d\d/);
                                                    return '<a href="subscriber_edit.php?id='+sub+'" class="pop"><img src="img/edit.png" alt="Edit" valign="middle" /></a> | <a href="subscriber_delete.php?id='+sub+'" class="pop"><img src="img/delete.png" alt="Delete" valign="middle" /></a>';
                                                }
                                            }
                                        ],
                                        "aoColumns": [
                                                {},{},{"sClass": "center"},{"sClass": "center"},{},{},{}
                                        ],
                                        "fnDrawCallback": function () {
                                                $(".pop").fancybox({
                                                    'width'             : '50%',
                                                    'height'            : '70%',
                                                    'autoScale'         : false,
                                                    'type'              : 'iframe',
                                                    'onClosed'          : function() {
                                                          parent.location.reload(true);
                                                    }
                                                });
                                        },
                                        "sAjaxSource": "subscribers_processing.php"
                                } );

                        });
                        
	                </script><br/>
                        <?php
                            try {
                                $sub = new Subscriber();
                                $unpaid_subscribers = $sub->get('unpaid_subscription');
                                $unauthorized_subscribers = $sub->get('unauthorized');
                                $paid_subscribers = $sub->get('paid_subscription');
                                $online = $sub->get('online');
                                $offline = $sub->get('offline');
                                echo "<div>";
                                echo "<div class='left_box' style='margin-left:10px;'>"._("Unpaid subscription").": <b>$unpaid_subscribers</b></div>";
                                echo "<div class='left_box'>"._("Unauthorized").": <b>$unauthorized_subscribers</b></div>";
                                echo "<div class='left_box'>"._("Paid subscription").": <b>$paid_subscribers</b></div>";
                                echo "<div class='left_box'>"._("Online").": <b>$online</b></div>";
                                echo "<div class='left_box'>"._("Offline").": <b>$offline</b></div>";
                                echo "</div>";

                            }
                            catch (SubscriberException $e) { }
                        ?>


			<h1><?= _('Subscribers Phones') ?></h1><br/>
			<div id="dynamic" style="margin-left: 20px;">
<table cellpadding="0" cellspacing="0" border="0" class="display" id="example">
	<thead>
		<tr>
			<th align='left' width='12%'><?= _("Activation date") ?></th>
                        <th align='left' width='14%'><?= _('Subscription date') ?></th>
                        <th width='12%'><?= _("Subscription Status") ?></th>
			<th width="7%"> <?= _("Authorized") ?></th>
			<th align='left' width='12%'><?= _("Number") ?></th>
			<th align='left'><?= _("Name") ?></th>
			<th align='left'><?= _("Balance") ?></th>
			<th align='left'><?= _("Location") ?></th>
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
                        <th align='left' width='12%'><?= _("Activation date") ?></th>
                        <th align='left' width='14%'><?= _('Subscription date') ?></th>
                        <th width='12%'><?= _("Subscription Status") ?></th>
                        <th width="7%"><?= _("Authorized") ?></th>
                        <th align='left' width='12%'><?= _("Number") ?></th>
                        <th align='left'><?= _("Name") ?></th>
                        <th align='left'><?= _("Balance") ?></th>
			<th align='left'><?= _("Location") ?></th>
                        <th align='left'><?= _("Actions") ?></th>
		</tr>
	</tfoot>
</table>
			</div>
			<div class="spacer"></div>
				
		</div>
	</body>

</html>
