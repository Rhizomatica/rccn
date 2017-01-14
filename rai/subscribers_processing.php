<?php
    require_once('modules/subscriber.php');
    require_once('modules/configuration.php');
    require_once('include/database.php');

    require_once('modules/access_manager.php');

    $access = new AccessManager();
    $filename = basename($_SERVER['PHP_SELF']);
    if ($filename != "login.php") {
        $access->checkAuth();
    }

    include('include/locale.php');



    /*
     * Script:    DataTables server-side script for PHP and PostgreSQL
     * Copyright: 2010 - Allan Jardine
     * License:   GPL v2 or BSD (3-point)
     */
     
    /* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
     * Easy set variables
     */
     
    /* Array of database columns which should be read and sent back to DataTables. Use a space where
     * you want to insert a non-database field (for example a counter or static image)
     */

    $aColumns = array( 'created', 'subscription_date', 'subscription_status', 'authorized', 'msisdn', 'name', 'balance', 'location' );

    /* Use a different set of columns to build the query. */
    $aqColumns = array( 'subscribers.created AS created', 'subscribers.subscription_date AS subscription_date', 'subscription_status', 'subscribers.authorized AS authorized', 'subscribers.msisdn AS msisdn', 'name', 'balance', 'location', 'hlr.created AS hlr_created', 'hlr.authorized AS hlr_auth', 'current_bts', 'home_bts' );

    /* Indexed column (used for fast and accurate table cardinality) */
    $sIndexColumn = "subscribers.id";
     
    /* DB table to use */
    $sTable = "subscribers LEFT JOIN hlr ON subscribers.msisdn = hlr.msisdn";
     
    /* Database connection information */
    $gaSql['user']       = $DB_USER;
    $gaSql['password']   = $DB_PASSWORD;
    $gaSql['db']         = $DB_DATABASE;
    $gaSql['server']     = $DB_HOST;
     
    /* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
     * If you just want to use the basic configuration for DataTables with PHP server-side, there is
     * no need to edit below this line
     */
     
    /*
     * DB connection
     */
    $gaSql['link'] = pg_connect(
        " host=".$gaSql['server'].
        " dbname=".$gaSql['db'].
        " user=".$gaSql['user'].
        " password=".$gaSql['password']
    ) or die('Could not connect: ' . pg_last_error());
    

    try {
    	$sub = new Subscriber();
	$connected_subscribers = $sub->getAllConnected();
    }
    catch (SubscriberException $e) { }

    $site = new Configuration();
    $info = $site->getSite();
    $internalprefix = $info->postcode.$info->pbxcode;
 
     
    /*
     * Paging
     */
    $sLimit = "";
    if ( isset( $_GET['iDisplayStart'] ) && $_GET['iDisplayLength'] != '-1' )
    {
        $sLimit = "LIMIT ".intval( $_GET['iDisplayLength'] )." OFFSET ".
            intval( $_GET['iDisplayStart'] );
    }
     
     
    /*
     * Ordering
     */
    if ( isset( $_GET['iSortCol_0'] ) )
    {
        $sOrder = "ORDER BY  ";
        for ( $i=0 ; $i<intval( $_GET['iSortingCols'] ) ; $i++ )
        {
            if ( $_GET[ 'bSortable_'.intval($_GET['iSortCol_'.$i]) ] == "true" )
            {
                $sOrder .= $aColumns[ intval( $_GET['iSortCol_'.$i] ) ]."
                    ".($_GET['sSortDir_'.$i]==='asc' ? 'asc' : 'desc').", ";
            }
        }
         
        $sOrder = substr_replace( $sOrder, "", -2 );
        if ( $sOrder == "ORDER BY" )
        {
            $sOrder = "";
        }
    }
     
     
    /*
     * Filtering
     * NOTE This assumes that the field that is being searched on is a string typed field (ie. one
     * on which ILIKE can be used). Boolean fields etc will need a modification here.
     */
    $sWhere = "";
    if ( $_GET['sSearch'] != "" )
    {
        $sWhere = "WHERE (";
        for ( $i=0 ; $i<count($aColumns) ; $i++ )
        {
            if ( $_GET['bSearchable_'.$i] == "true" )
            {
                $sWhere .= "CAST(".$aColumns[$i]." AS TEXT) ILIKE '%".pg_escape_string( $_GET['sSearch'] )."%' OR ";
            }
        }
        $sWhere = substr_replace( $sWhere, "", -3 );
        $sWhere .= ") AND subscribers.msisdn ILIKE '$internalprefix%' ";
    }
    if ($sWhere == "") {
	$sWhere = "WHERE subscribers.msisdn ILIKE '$internalprefix%' ";
    }
     
    /* Individual column filtering */
    for ( $i=0 ; $i<count($aColumns) ; $i++ )
    {
        if ( $_GET['bSearchable_'.$i] == "true" && $_GET['sSearch_'.$i] != '' )
        {
            if ( $sWhere == "" )
            {
                $sWhere = "WHERE ";
            }
            else
            {
                $sWhere .= " AND ";
            }
            $sWhere .= "CAST(".$aColumns[$i]." AS TEXT) ILIKE '%".pg_escape_string($_GET['sSearch_'.$i])."%' ";
        }
    }
     
     
    $sQuery = "
        SELECT ".str_replace(" , ", " ", implode(", ", $aqColumns))."
        FROM   $sTable
        $sWhere
        $sOrder
        $sLimit
    ";
    $rResult = pg_query( $gaSql['link'], $sQuery ) or die(pg_last_error());
     
    $sQuery = "
        SELECT $sIndexColumn
        FROM   $sTable WHERE subscribers.msisdn ILIKE '$internalprefix%'
    ";
    $rResultTotal = pg_query( $gaSql['link'], $sQuery ) or die(pg_last_error());
    $iTotal = pg_num_rows($rResultTotal);
    pg_free_result( $rResultTotal );
     
    if ( $sWhere != "" )
    {
        $sQuery = "
            SELECT $sIndexColumn
            FROM   $sTable
            $sWhere
        ";
        $rResultFilterTotal = pg_query( $gaSql['link'], $sQuery ) or die(pg_last_error());
        $iFilteredTotal = pg_num_rows($rResultFilterTotal);
        pg_free_result( $rResultFilterTotal );
    }
    else
    {
        $iFilteredTotal = $iTotal;
    }
     
     
     
    /*
     * Output
     */
    $output = array(
        "sEcho" => intval($_GET['sEcho']),
        "iTotalRecords" => $iTotal,
        "iTotalDisplayRecords" => $iFilteredTotal,
        "aaData" => array()
    );
     
    while ( $aRow = pg_fetch_array($rResult, null, PGSQL_ASSOC) )
    {
        $row = array();
        for ( $i=0 ; $i<count($aColumns) ; $i++ )
        {
            if ( $aColumns[$i] == "version" )
            {
                /* Special output formatting for 'version' column */
                $row[] = ($aRow[ $aColumns[$i] ]=="0") ? '-' : $aRow[ $aColumns[$i] ];
            }
	    else if ( $aColumns[$i] == "msisdn" ) {
            if ($aRow['current_bts'] == $aRow['home_bts']) {
                $content = (in_array($aRow[$aColumns[$i]],$connected_subscribers)) ? "<img src='img/led-green.gif' /> " : "<img src='img/led-red.gif' /> ";
            } else {
                $content = '<div style="position:relative;top:6px;font-weight:bold;font-size:8px;">R</div>';
                $content .= (in_array($aRow[$aColumns[$i]],$connected_subscribers)) ? "<img title='"._('Roaming on')." ".$aRow['current_bts']."' src='img/led-green.gif' /> " : "<img title='"._('Roaming on')." ".$aRow['current_bts']."' src='img/led-red.gif' /> ";

            }
            $content.= $aRow[$aColumns[$i]];
            $row[]=$content;
	    }
	    else if ( $aColumns[$i] == "authorized" ) {
		    $content=($aRow[$aColumns[$i]] == 0) ? "<img src='img/lock.png' width='16' height='16' />" : "<img src='img/unlock.png' width='16' height='16' /> ";
            $content.=($aRow[$aColumns[$i]] == 1 && $aRow['hlr_auth'] == 0 ) ? "<img title='"._('Not authorized on HLR!')."' src='img/lock.png' width='16' height='16' />" : "";
         $row[] = $content;
	    }
	    else if ( $aColumns[$i] == "created" ) {
		$row[] =  date('d-m-Y H:i:s', strtotime($aRow[$aColumns[$i]]));
	    }
	    else if ( $aColumns[$i] == "subscription_date") {
		$row[] =  date('d-m-Y H:i:s', strtotime($aRow[$aColumns[$i]]));
	    }
	    else if ( $aColumns[$i] == "subscription_status") {
		$row[] =  ($aRow[$aColumns[$i]] == 0) ? "<font color='red'>NO_PAGADAS</font>" : "<font color='green'>PAGADO</font>";
            }
            else if ( $aColumns[$i] != ' ' )
            {
                /* General output */
                $row[] = $aRow[ $aColumns[$i] ];
            }
        }
        $output['aaData'][] = $row;
    }

    echo json_encode( $output );
     
    // Free resultset
    pg_free_result( $rResult );
     
    // Closing connection
    pg_close( $gaSql['link'] );
?>
