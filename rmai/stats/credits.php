<?php
include ("../lib/jpgraph/jpgraph.php");
include ("../lib/jpgraph/jpgraph_bar.php");
include ("../lib/jpgraph/jpgraph_date.php" );

require ('../modules/statistics.php');
require_once('../modules/access_manager.php');

$access = new AccessManager();
$filename = basename($_SERVER['PHP_SELF']);
if ($filename != "login.php") {
        $access->checkAuth();
}


$period=$_GET['p'];

try {
        $stat = new CostsStatistics();
        $data = $stat->getCreditsStats($period);
} catch (StatisticException $e) {
        echo "Error generating statistic: $e";
        exit;
}

$datax = array();
$datay = array();
foreach ($data as $entry) {
        array_push($datax,$entry[0]);
        array_push($datay,$entry[1]);
}

$tickint = (count($datax) > 1 && count($datax) < 5) ? 5 : 2;

// Create the graph. These two calls are always required
$graph = new Graph(700,350,'auto');    
$graph->SetScale("texlin");

$graph->yaxis->scale->SetGrace(10);
$graph->xaxis->SetTickLabels($datax);
$graph->xaxis->SetLabelAngle(45);
$graph->xaxis->SetTextLabelInterval($tickint);

// Add a drop shadow
$graph->SetShadow();
// Adjust the margin a bit to make more room for titles
$graph->img->SetMargin(60,30,20,80);

// Create a bar pot
$bplot = new BarPlot($datay);

// Adjust fill color
$graph->Add($bplot);
//$bplot->SetFillColor('orange');
$bplot->value->Show();
$bplot->value->SetFormat('%01.2f'); 
//$bplot->SetShadow();
//$graph ->xaxis->scale-> SetDateFormat( 'Y-m-d');

$map = array('7d' => array(_('Last 7 Days').' - '._('Total pesos amount in credits per day'),_('Day')),
	     '4w' => array(_('Last 4 Weeks').' - '._('Total pesos amount in credits per week'),_('Week year')),
	     'm' =>  array(_('Total pesos amount in credits per month'),_('Month')));

// Setup the titles
$graph->title->Set($map[$period][0]);
$graph->xaxis->title->Set($map[$period][1]);
$graph->yaxis->title->Set("Pesos");
$graph->yaxis->SetLabelAlign('center', 'top');

$graph->title->SetFont(FF_FONT1,FS_BOLD);
$graph->yaxis->title->SetFont(FF_FONT1,FS_BOLD);
$graph->xaxis->title->SetFont(FF_FONT1,FS_BOLD);

// Display the graph
$graph->Stroke();

?>
