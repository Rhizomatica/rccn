$(function() {
	var support_popup = 'width=780,height=460,toolbar=0,menubar=0,location=0,status=1,scrollbars=1,resizable=0';
	$('.support_popup').click(function() {
			//Get the destination URL and the class popup specs
			var popurl = $(this).attr('href');
			var popupSpecs = $(this).attr('class');
			//Create a "unique" name for the window using a random number
			var popupName = Math.floor(Math.random()*10000001);
			//Opens the pop-up window according to the specified specs
			newwindow=window.open(popurl,popupName,eval(popupSpecs));
			return false;
	});
	$('.credit_status').change(function() {
		y=$('#cs_year').val()
		m=$('#cs_month').val()
		$('#credit_report').html(tr.spinner)
		$.getJSON("/rai/ajax.php", {'service': 'credit', 'year': y}, function(data) {
			$('#credit_report').html('')
			$.each( data, function( i,p ) {
				var date = new Date(p[1]+"/01/2000")
				locale=navigator.language
				month = date.toLocaleString(locale, { month: "long" });
				html='<div>'+
				'<span class="cyear" style="display:none">'+p[0]+
				'</span><span class="cmonth">'+month+'</span>' +
				'<span class="camount">$'+
				parseInt(p[2]).toFixed(2).replace(/(\d)(?=(\d{3})+\.)/g, '$1,') +
				'</span><span class="camount">$'+
				parseInt(p[3]).toFixed(2).replace(/(\d)(?=(\d{3})+\.)/g, '$1,') +
				'</span>'
				'</span></div>'
				$('#credit_report').append(html)
			})
		});
	});
})