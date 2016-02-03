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
})