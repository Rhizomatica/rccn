<?php
include ("../lib/jpgraph/jpgraph.php");
include ("../lib/jpgraph/jpgraph_bar.php");
include ("../lib/jpgraph/jpgraph_date.php" );

$dbh = new PDO('sqlite:../db/master.db');
$stmt = $dbh->query("select strftime('%m-%Y',date(calldate)),count(*),dcontext from cdr group by strftime('%m-%Y',date(calldate)),dcontext");

$datax = array();

$internal = array();
$from_outside = array();
$external = array();

while ($row = $stmt->fetch()) {
	if (!in_array($row[0],$datax)) {
		// push dates
		array_push($datax,$row[0]);
	}
	if ($row[2] == "from-trunk")
		array_push($from_outside,$row[1]);
	if ($row[2] == "other-lines")
		array_push($external,$row[1]);
	if ($row[2] == "phones")
		array_push($internal,$row[1]);
}

// Create the graph. These two calls are always required
$graph = new Graph(700,350,'auto');    
$graph->SetScale("texlin");

$graph->yaxis->scale->SetGrace(25);
$graph->xaxis->SetTickLabels($datax);
$graph->xaxis->SetLabelAngle(45);
$graph->xaxis->SetTextLabelInterval(5);

// Add a drop shadow
$graph->SetShadow();
// Adjust the margin a bit to make more room for titles
$graph->img->SetMargin(60,30,20,80);

// Create a bar pot
$bplot = new BarPlot($external);
$bplot1 = new BarPlot($internal);
$bplot2 = new BarPlot($from_outside); 

$gbplot = new GroupBarPlot(array($bplot,$bplot1,$bplot2));

// Adjust fill color
$graph->Add($gbplot);

$bplot->SetFillColor('#C40505');
$bplot->SetColor('#C40505');
$bplot->value->Show();
$bplot->value->SetFormat('%d'); 
$bplot->SetLegend("External");

$bplot1->SetFillColor('#94D239');
$bplot1->SetColor('#94D239');
$bplot1->value->Show();
$bplot1->value->SetFormat('%d'); 
$bplot1->SetLegend("Internal");

$bplot2->SetFillColor('#3925F8');
$bplot2->SetColor('#3925F8');
$bplot2->value->Show();
$bplot2->value->SetFormat('%d');
$bplot2->SetLegend("From Outside");


// Setup the titles
$graph->title->Set("Total monthly calls breakdown by context");
$graph->xaxis->title->Set("Month");
$graph->yaxis->title->Set("Calls");
$graph->yaxis->SetLabelAlign('center', 'top');

$graph->legend->SetColumns(3);
$graph->legend->SetLayout(LEGEND_HOR);
$graph->legend->SetPos(0.5,0.14,'center','bottom');

$graph->title->SetFont(FF_FONT1,FS_BOLD);
$graph->yaxis->title->SetFont(FF_FONT1,FS_BOLD);
$graph->xaxis->title->SetFont(FF_FONT1,FS_BOLD);

// Display the graph
$graph->Stroke();

?>
