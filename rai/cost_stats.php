<?php 

require_once('include/header.php');
require_once('include/menu.php');
require_once('modules/statistics.php');

print_menu('statistics'); 

?>
			<br/><br/>
			<center>
			<br/>
			<?php
				$stat = new CostsStatistics();
				try {
					$total_cost = $stat->getTotalSpent();
				} catch (StatisticException $e) {
					$total_cost = "ERROR $e";
				}
 
				try {
					$total_credits = $stat->getTotalSpentCredits();
				} catch (StatisticException $e) {
					$total_credits = "ERROR $e";
				}
 
				try {
					$avg_call_cost = $stat->getAverageCallCost();
				} catch (StatisticException $e) {
					$avg_call_cost = "ERROR $e";
				}


			?>

			Total spent on calls: <b><?=$total_cost?></b> | Total on credits: <b><?=$total_credits?></b> | Average call cost: <b><?=$avg_call_cost?></b><br/><br/>
			Top 10 destinations and cost<br/><br/>
			<div style="text-align:left; border: 1px solid #bbb; padding: 5px; width: 400px;">
			<?php
				try {
					$top_destinations = $stat->getTopDestinations();
				} catch (StatisticException $e) {
					echo "Error: ".$e->getMessage();
				}
				
				foreach($top_destinations as $dest) {
					echo $dest[0].": <b>".$dest[1]."</b><br/>";
				}
			?>
			</div><br/>
			<a href="cost_stats.php?a=7d">Last 7 Days</a> | <a href="cost_stats.php?a=4w">Last 4 Weeks</a> | <a href="cost_stats.php?a=m">Monthly</a><br/><br/>

			<?php
				$age = (isset($_GET['a'])) ? $_GET['a'] : '7d';
				$graphs = array('cost','credits');
				foreach ($graphs as &$g) {
					echo "<img src='stats/$g.php?p=$age' style='border: 1px solid #bbb;'/>&nbsp;&nbsp;";
				}
				echo "<br/>";
			?>
			<br/><br/>
			</center>
		</div>
	</body>

</html>
