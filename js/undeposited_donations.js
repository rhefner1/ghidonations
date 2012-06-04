function getCheckedRows(){
	var checked_rows = []
	$("input[type=checkbox]:checked").each(function(i){
		var id = $(this).parent().parent().attr("data-id")
		checked_rows.push(id)
	})

	return checked_rows
}

$(document).ready(function(){

	$("input[type=checkbox]").change(function(){
		var row = $(this).parent().parent()
		row.toggleClass("selectRow")
	})

	$("#select_all").click(function(){
		$(":checkbox").each(function() {
			$(this).attr('checked', true);

	    	var row = $(this).parent().parent()
			row.addClass("selectRow")
	    });
	})

	$("#deselect_all").click(function(){
		$(":checkbox").each(function() {
			$(this).attr('checked', false);

			var row = $(this).parent().parent()
			row.removeClass("selectRow")
	    });
	})


	$("#deposit").click(function(){
		var r=confirm("Do you want to deposit these donations?")
		if (r==true){
			show_flash("setting", "Marking checks as deposited...", false)
		
			var donation_keys = getCheckedRows()
			params = ["depositDonations", donation_keys]
			rpcPost(params, function(data){
				window.location.hash = "alldeposits"
			})
		}
		else{
			return
		}
		
	})

	$("#remove_deposits").click(function(){
		var r=confirm("Do you want to remove these donations from deposits?")
		if (r==true){
			show_flash("setting", "Removing checked deposits...", false)
		
			var donation_keys = getCheckedRows()
			params = ["removeFromDeposits", donation_keys]
			rpcPost(params, function(data){
				refreshPage()
			})
		}
		else{
			return
		}
		
	})

})