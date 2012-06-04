$(document).ready(function(){
	
	if ($("#var_showteam").val() == "True"){
		$("#toggle_team").attr("checked", "checked")
	}
	

    $("#members").delegate("tr", "click", function(){
        var clicked_id = $(this).attr("data-id")

        window.location.hash = "profile?i=" + clicked_id
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

	    	params = ["updateTeam", team_key, name, show_team]
	    	rpcPost(params, function(){
	    		refreshPage()
	    	})
    	}
    	
    })

    $("#delete_container").click(function(){
    	var message = "Are you sure you want to delete this team?"
    	if (confirm(message)){
    		var team_key = $("#team_key").val()

	    	params = ["deleteTeam", team_key]
	    	rpcPost(params, function(){
	    		window.location.hash = "allteams"
	    	})
    	}
    	
    	
    })
})