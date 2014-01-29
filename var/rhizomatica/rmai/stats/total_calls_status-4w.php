<?php
include ("../lib/jpgraph/jpgraph.php");
include ("../lib/jpgraph/jpgraph_bar.php");
include ("../lib/jpgraph/jpgraph_date.php" );

$dbh = new PDO('sqlite:../db/master.db');
$stmt = $dbh->query("select * from (select strftime('%d-%m-%Y',date(calldate)) calldate,count(*),disposition from cdr group by date(calldate),disposition order by strftime('%W', calldate) DESC limit 16 ) q order by calldate asc");

$datax = array();

$answered = array();
$busy = array();
$failed = array();
$noanswer = array();

while ($row = $stmt->fetch()) {
	if (!in_array($row[0],$datax)) {
		// push dates
		array_push($datax,$row[0]);
	}
	if ($row[2] == "ANSWERED")
		array_push($answered,$row[1]);
	if ($row[2] == "BUSY")
		array_push($busy,$row[1]);
	if ($row[2] == "FAILED")
		array_push($failed,$row[1]);
	if ($row[2] == "NO ANSWER")
		array_push($noanswer,$row[1]);
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
$bplot = new BarPlot($answered);
$bplot1 = new BarPlot($busy);
//$bplot2 = new BarPlot($failed);
$bplot3 = new BarPlot($noanswer);

$gbplot = new GroupBarPlot(array($bplot,$bplot1,$bplot3));

// Adjust fill color
$graph->Add($gbplot);

$bplot->SetFillColor('#94D239');
$bplot->SetColor('#94D239');
$bplot->value->Show();
$bplot->value->SetFormat('%d'); 
$bplot->SetLegend("ANSWERED");

$bplot1->SetFillColor('#376BF6');
$bplot1->SetColor('#376BF6');
$bplot1->value->Show();
$bplot1->value->SetFormat('%d'); 
$bplot1->SetLegend("BUSY");

/*$bplot2->SetFillColor('#C40505');
$bplot2->SetColor('#C40505');
$bplot2->value->Show();
$bplot2->value->SetFormat('%d');
$bplot2->SetLegend("UNSUCCESSFULL");*/

$bplot3->SetFillColor('#A7A7A7');
$bplot3->SetColor('#A7A7A7');
$bplot3->value->Show();
$bplot3->value->SetFormat('%d');
$bplot3->SetLegend("NOANSWER");

// Setup the titles
$graph->title->Set("Last 4 Weeks - Total weekly calls breakdown by status");
$graph->xaxis->title->Set("Week year");
$graph->yaxis->title->Set("Calls");
$graph->yaxis->SetLabelAlign('center', 'top');
$graph->legend->SetColumns(4);
$graph->legend->SetLayout(LEGEND_HOR);
$graph->legend->SetPos(0.5,0.14,'center','bottom');

$graph->title->SetFont(FF_FONT1,FS_BOLD);
$graph->yaxis->title->SetFont(FF_FONT1,FS_BOLD);
$graph->xaxis->title->SetFont(FF_FONT1,FS_BOLD);

// Display the graph
$graph->Stroke();

?>
