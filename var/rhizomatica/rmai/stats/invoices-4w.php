<?php
include ("../lib/jpgraph/jpgraph.php");
include ("../lib/jpgraph/jpgraph_bar.php");
include ("../lib/jpgraph/jpgraph_date.php" );

$dbh = new PDO('sqlite:../db/sqlite3.db');
$stmt = $dbh->query("select * from (select strftime('%W',date) date,round(sum(amount),2) from invoices group by strftime('%W',date) order by strftime('%W',date) DESC limit 7 ) q ORDER by date ASC");
$datax = array();
$datay = array();
while ($row = $stmt->fetch()) {
	array_push($datax,$row[0]);
	array_push($datay,$row[1]);
}

//print_r($datax);
//print_r($datay);
//$datay=array(12,8,19,3,10,5);

// Create the graph. These two calls are always required
$graph = new Graph(700,350,'auto');    
$graph->SetScale("texlin");

$graph->yaxis->scale->SetGrace(10);
$graph->xaxis->SetTickLabels($datax);
$graph->xaxis->SetLabelAngle(45);
$graph->xaxis->SetTextLabelInterval(5);

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

// Setup the titles
$graph->title->Set("Last 4 Weeks - Total pesos amount in invoices per week");
$graph->xaxis->title->Set("Week year");
$graph->yaxis->title->Set("Pesos");
$graph->yaxis->SetLabelAlign('center', 'top');

$graph->title->SetFont(FF_FONT1,FS_BOLD);
$graph->yaxis->title->SetFont(FF_FONT1,FS_BOLD);
$graph->xaxis->title->SetFont(FF_FONT1,FS_BOLD);

// Display the graph
$graph->Stroke();

?>
