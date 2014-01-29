<?php 

require_once('include/header.php');
require_once('include/menu.php');
require_once('modules/statistics.php');
			
print_menu('statistics'); 

?>
			<br/><br/>
			<center>
			<?php
				$stat = new CallsStatistics();

				try {
					$total_calls = $stat->getTotalCalls();
				} catch (StatisticException $e) {
					$total_calls = "ERROR $e";
				}
				
				try {
					$total_minutes = $stat->getTotalMinutes();
				} catch (StatisticException $e) {
					$total_minutes = "ERROR $e";
				}
				
				try {
					$avg_call_duration = $stat->getAverageCallDuration();
				} catch (StatisticException $e) {
					$avg_call_duration = "ERROR $e";
				}
			?>

			Total calls: <b><?=$total_calls?></b> | Total minutes: <b><?=$total_minutes?></b> | Average call duration: <b><?=$avg_call_duration?></b><br/><br/>

			<?/*Total internal calls: <b><?=$total_calls_internal?></b> | Total external calls: <b><?=$total_calls_external?></b> | Total calls from outside: <b><?=$total_calls_from_trunk?></b><br/><br/>*/?>
			<?/*Total ANSWERED: <b><?=$total_answered?></b> | Total BUSY: <b><?=$total_busy?></b> | Total NO ANSWER: <b><?=$total_noanswer?></b> <!--| Total UNSUCCESSFULL (chans full or phone off): <b><?=$total_failed?></b>--> <br/>*/?>
			<br/>
			<a href="call_stats.php?a=7d">Last 7 Days</a> | <a href="call_stats.php?a=4w">Last 4 Weeks</a> | <a href="call_stats.php?a=m">Monthly</a><br/><br/>
			<?php
				$age = (isset($_GET['a'])) ? $_GET['a'] : '7d';
				$graphs = array('total_calls','total_minutes');
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
