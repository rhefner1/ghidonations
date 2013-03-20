function dataTableWriter(data_table, d){
    data_table.fnAddData([
        d.key,
        d.name,
        d.email,
        d.raised,
    ])

    data_table.fnAdjustColumnSizing()
}

$(document).ready(function(){

    //Initializing data table
    var team_key = $("#team_key").val()

    var rpc_params = {'team_key':team_key}
    var rpc_request = ghiapi.get.teammembers

    var data_table = initializeTable(3, rpc_request, rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
    })
	
	if ($("#var_showteam").val() == "True"){
		$("#toggle_team").attr("checked", "checked")
	}
	

    $("#members").delegate("tr", "click", function(e){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        change_hash(e, "profile?i=" + clicked_id)
    })
    
    $("#edit_team").click(function(){
    	if ($("#edit_team").attr("data-state") == "edit"){
			$("#edit_team").attr("data-state", "save")
    		$(this).removeClass("black").addClass("blue")
	    	$(this).val("Save Team")

	    	$("#edit_container").slideDown()
	    	$("#delete_container").slideDown()
    	}
    	else{
    		var team_key = $("#team_key").val()
	    	var name = $("#team_name").val()
	    	var show_team = $("#toggle_team").is(":checked")

            //Flash message
            show_flash("setting", "Updating team...", false)

	    	var params = {'team_key':team_key, 'name':name, 'show_team':show_team}
            var request = ghiapi.team.update(params)

	    	request.execute(function(response){
                rpcSuccessMessage(response)
	    		refreshPage()
	    	})
    	}
    	
    })

    $("#delete_container").click(function(){
    	var message = "Are you sure you want to delete this team?"
    	if (confirm(message)){
    		var team_key = $("#team_key").val()

	    	var params = {'team_key':team_key}
            var request = ghiapi.team.delete(params)

	    	request.execute(function(response){
                rpcSuccessMessage(response)
	    		window.location.hash = "allteams"
	    	})
    	}
    	
    	
    })
})