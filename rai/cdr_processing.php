<?php

    require_once('include/database.php');

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
    $aColumns = array( 'id', 'start_stamp', 'caller_id_number', 'destination_number',
                       'context', 'billsec', 'hangup_cause', 'destination_name', 'cost', 'accountcode' );
     
    /* Indexed column (used for fast and accurate table cardinality) */
    $sIndexColumn = "id";
     
    /* DB table to use */
    $sTable = "cdr";
     
     
     
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
    if ( $_GET['sSearch'] != "" && strlen($_GET['sSearch']) > 3)
    {
        // Do something to make these queries a little more realistic
        if ( is_numeric($_GET['sSearch']) ) {
            $_GET['bSearchable_4'] = "false";
            $_GET['bSearchable_6'] = "false";
            $_GET['bSearchable_7'] = "false";
        } else {
            $_GET['bSearchable_2'] = "false";
            $_GET['bSearchable_3'] = "false";
        }
        $sWhere = "WHERE (";
        for ( $i=0 ; $i<count($aColumns) ; $i++ )
        {
            if ( $_GET['bSearchable_'.$i] == "true" )
            {
                if ( is_numeric($_GET['sSearch']) ) {
                    $sWhere .= $aColumns[$i]." LIKE '%".pg_escape_string( $_GET['sSearch'] )."%' OR ";
                } else {
                    #loose the first % - we can assume tpying a search has to start from beginning.
                    $sWhere .= "CAST(".$aColumns[$i]." AS TEXT) ILIKE '".pg_escape_string( $_GET['sSearch'] )."%' OR ";
                }
            }
        }
        $sWhere = substr_replace( $sWhere, "", -3 );
        $sWhere .= ")";
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

    if ( isset($_GET['cost_only']) && $_GET['cost_only'] == 'checked')
    {
        if ($sWhere == "") {
            $sWhere = "WHERE cost IS NOT NULL";
        } else {
            $sWhere .= " AND cost IS NOT NULL";
        }
    }

    $sQuery = "
        SELECT ".str_replace(" , ", " ", implode(", ", $aColumns))."
        FROM   $sTable
        $sWhere
        $sOrder
        $sLimit
    ";
    $rResult = pg_query( $gaSql['link'], $sQuery ) or die(pg_last_error());
     
    $sQuery = "
        SELECT count($sIndexColumn)
        FROM   $sTable
    ";
    $rResultTotal = pg_query( $gaSql['link'], $sQuery ) or die(pg_last_error());
    $iTotal = pg_fetch_row($rResultTotal)[0];
    pg_free_result( $rResultTotal );
     
    if ( $sWhere != "" )
    {
        $sQuery = "
            SELECT count($sIndexColumn)
            FROM   $sTable
            $sWhere
        ";
        $rResultFilterTotal = pg_query( $gaSql['link'], $sQuery ) or die(pg_last_error());
        $iFilteredTotal = pg_fetch_row($rResultFilterTotal)[0];
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
            if ( $aColumns[$i] == "version" ) {
		      $row[] =  date('d-m-Y H:i:s', strtotime($aRow[$aColumns[$i]]));
            }

            if ( $aColumns[$i] == "billsec") {
                $row[] = gmdate("H:i:s", $aRow[ $aColumns[$i] ]);
            } else if ( $aColumns[$i] == "start_stamp" ) {
                $row[] =  date('d-m-Y H:i:s', strtotime($aRow[$aColumns[$i]]));
            } else if ( $aColumns[$i] == "destination_number" ) {
                if ($aRow["accountcode"] != null) {
                    $row[] = '<span class="inbound_thru" title="'.$aRow["accountcode"].'">'.$aRow["destination_number"] . '</span>';
                } else {
                    $row[] = $aRow[ $aColumns[$i] ];
                }
            } else if ( $aColumns[$i] == "accountcode" ) {
                // Skip
            } else if ( $aColumns[$i] != ' ' ) {
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
