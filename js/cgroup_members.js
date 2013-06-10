function dataTableWriter(data_table, d){
    data_table.fnAddData([
        d.key,
        d.name,
        d.email
    ])

    data_table.fnAdjustColumnSizing()
}

$(document).ready(function(){

    //Initializing data table
    var group_key = $("#group_key").val()

    var rpc_params = {'group_key':group_key}
    var rpc_request = ghiapi.get.contactgroupmembers

    var data_table = initializeTable(2, rpc_request, rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
    })
	
	if ($("#var_showteam").val() == "True"){
		$("#toggle_team").attr("checked", "checked")
	}
	

    $("#members").delegate("tr", "click", function(e){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        change_hash(e, "contact?c=" + clicked_id)
    })
    
    $("#edit_group").click(function(){
    	if ($("#edit_group").attr("data-state") == "edit"){
			$("#edit_group").attr("data-state", "save")
    		$(this).removeClass("black").addClass("blue")
	    	$(this).val("Save Group")

	    	$("#edit_container").slideDown()
	    	$("#delete_container").slideDown()
    	}
    	else{
    		var group_key = $("#group_key").val()
	    	var name = $("#group_name").val()

            //Flash message
            show_flash("setting", "Updating group...", false)

	    	var params = {'group_key':group_key, 'name':name}
            var request = ghiapi.update.contactgroup(params)

	    	request.execute(function(response){
                rpcSuccessMessage(response)
	    		refreshPage()
	    	})
    	}
    	
    })

    $("#delete_container").click(function(){
    	var message = "Are you sure you want to delete this group?"
    	if (confirm(message)){
    		var team_key = $("#group_key").val()

	    	var params = {'group_key':group_key}
            var request = ghiapi.contactgroup.delete(params)

	    	request.execute(function(response){
                rpcSuccessMessage(response)
	    		window.location.hash = "allcontactgroups"
	    	})
    	}
    	
    	
    })
})