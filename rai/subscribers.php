<?php 
require_once('include/header.php');
require_once('include/menu.php');
require_once('modules/subscriber.php');
require_once('modules/configuration.php');

$site = new Configuration();
$info = $site->getSite();
$internalprefix = $info->postcode.$info->pbxcode;

?>
	<? print_menu('subscribers'); ?>

    <script type="text/javascript" charset="utf-8">
        $(document).ready(function() {
            var oTable = $('#subscribers').dataTable( {
                <?
                $lang_file = 'js/'.$_SESSION['lang'].'.txt';
                if (file_exists($lang_file)) {
                    echo '"oLanguage": { "sUrl": "'.$lang_file.'" },';
                }
                ?>
                "aLengthMenu": [ [ 10, 25, 50, -1 ], [ 10, 25, 50, "<?=_("All")?>" ] ],
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
                            if (sub[0].substr(0,6) != <?=$internalprefix?>) return '';
                            return '<a href="subscriber_edit.php?id='+sub[0]+'" class="pop"><img src="img/edit.png" alt="Edit" valign="middle" /></a> | <a href="subscriber_delete.php?id='+sub+'" class="pop"><img src="img/delete.png" alt="Delete" valign="middle" /></a>';
                        }
                    },
                    { "bSearchable": false, "aTargets": [0] },
                    { "bSearchable": false, "aTargets": [1] },
                    { "bSearchable": false, "aTargets": [2] },
                    { "bSearchable": false, "aTargets": [6] }
                ],
                "aoColumns": [
                        {},{},{"sClass": "center"},{"sClass": "center"},{},{},{},{}
                ],
                "fnDrawCallback": function () {
                        $(".pop").fancybox({
                            'width'             : '50%',
                            'height'            : '80%',
                            'autoScale'         : false,
                            'type'              : 'iframe',
                            'onClosed'          : function() {
                                  parent.location.reload(true);
                            }
                        });
                },
                "sAjaxSource": "subscribers_processing.php",
                "bStateSave": true,

                "fnInitComplete": function(oSettings, json) {
                    sVal=oSettings.oLoadedState.oSearch.sSearch
                    consel=''
                    dissel=''
                    rsel=''
                    if (sVal == 'RAI-all-connected') { consel="selected" }
                    if (sVal == 'RAI-all-disconnected') { dissel="selected" }
                    if (sVal == 'RAI-all-roaming') { rsel="selected" }
                    sel='<div style="display:table"><select id="conSelect" style="width:50px">' +
                    '<option value="">&nbsp;</option>' +
                    '<option '+consel+' value="RAI-all-connected" data-image="img/led-green.gif"></option>' +
                    '<option '+dissel+' value="RAI-all-disconnected" data-image="img/led-red.gif"></option>' +
                    '<option '+rsel+' value="RAI-all-roaming" data-image="img/led-roam.gif"></option>' +
                    '</select></div>'
                    $('#subscribers thead tr th:nth-child(5)').prepend(sel)
                    $('#conSelect').msDropDown()
                    $('#conSelect').change(function() {
                        $("#dynamic [name='subscribers_length']").val('-1')
                        $('#subscribers_filter input').val('')
                        if (this.value=='') {
                                oTable.fnSettings()._iDisplayLength = 10;
                                $("#dynamic [name='subscribers_length']").val('10')
                        } else {
                                oTable.fnSettings()._iDisplayLength = -1;
                        }
                        oTable.fnFilter (this.value, null,false,false,false)
                      })
                    sVal=oSettings.oLoadedState.aoSearchCols[3].sSearch
                    authsel=''
                    noauthsel=''
                    if (sVal == '1') { authsel="selected" }
                    if (sVal == '0') { noauthsel="selected" }
                    sel='<div style="display:table"><select id="authSelect" style="width:50px">' +
                    '<option value="">&nbsp;</option>' +
                    '<option '+authsel+' value="1" data-image="img/unlock.gif"></option>' +
                    '<option '+noauthsel+' value="0" data-image="img/lock.gif"></option> </select></div>'
                    $('#subscribers thead tr th:nth-child(4)').prepend(sel)
                    $('#authSelect').msDropDown()
                    $('#authSelect').change(function() {
                        //$("#dynamic [name='subscribers_length']").val('-1')
                        //$('#subscribers_filter input').val('')
                        oTable.fnFilter (this.value, 3,false,false,false)
                      })
                }
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
                                $roaming = $sub->get('all_roaming');

                                echo "<div>";
                                echo "<div class='left_box' style='margin-left:10px;'>"._("Unpaid subscription").": <b>$unpaid_subscribers</b></div>";
                                echo "<div class='left_box'>"._("Unauthorized").": <b>$unauthorized_subscribers</b></div>";
                                echo "<div class='left_box'>"._("Paid subscription").": <b>$paid_subscribers</b></div>";
                                echo "<div class='left_box'>"._("Online").": <b>$online</b> ("._("Roaming").": <b>$roaming</b>)</div>";
                                echo "<div class='left_box'>"._("Offline").": <b>$offline</b></div>";
                                echo "</div>";

                            }
                            catch (SubscriberException $e) { }
                        ?>


			<h1><?= _('Subscribers Phones') ?></h1><br/>
			<div id="dynamic">
<table cellpadding="0" cellspacing="0" border="0" class="display" id="subscribers">
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
