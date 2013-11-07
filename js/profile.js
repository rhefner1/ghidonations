//Global variables
var team_list = ""
var individual_key

function dataTableWriter(data_table, d){
    data_table.fnAddData([
        d.key,
        d.formatted_donation_date,
        d.name,
        d.amount_donated,
        d.payment_type,
        d.team_name
    ])

    data_table.fnAdjustColumnSizing()
}

function getTeamTotals(){
	var params = {'individual_key':individual_key}
	var request = ghiapi.get.team_totals(params)

	request.execute(function(response){

		$.each(response.team_totals, function(index, tt){
			html = '<li style="margin-bottom:5px"><strong>%t</strong> - %d</li>'
			html = html.replace("%t", tt.team_name)
			html = html.replace("%d", tt.donation_total)

			$("#team_totals_div").append(html)
		})
		
	})
}

function refreshCurrentTeams(){
	$("#current_teams").html("")

	$.each(team_list, function(team_key, values){
	    var new_div = '<div data-id="key" class="current_team" style="clear:both; margin-top:10px"></div>'
	    var insert_name = '<strong>name</strong> <br> Fundraise amount:'
	    var fundraise = '<input type="text" class="small" style="margin-left:15px" value="amount" />'
	    var input = '<input type="button" class="button small" style="margin-left:15px" value="Remove" />'
	            
		$("#current_teams").append(new_div.replace("key", team_key))
		$("#current_teams div[data-id=" + team_key + "]").append(insert_name.replace("name", values[0]))
		$("#current_teams div[data-id=" + team_key + "]").append(fundraise.replace("amount", parseFloat(values[1]).toFixed(2)))
		$("#current_teams div[data-id=" + team_key + "]").append(input)
	})
}

$(document).ready(function(){
	individual_key = $("#individual_key").val()
	var donate_parent = $("input[name=donate_parent]").val()

    var rpc_params = {'individual_key':individual_key}
    var rpc_request = ghiapi.semi.get.individual_donations

    var data_table = initializeTable(5, rpc_request, rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
    })

	//Team list dictionary parsed from JSON
	team_list = JSON.parse(htmlDecode($("input[name=team_list]").val()))
	var team_names = ""

	var show_donation_page = $("#var_show_donation_page").val()
	if (show_donation_page == "True"){
		$("input[name=show_donation_page]").attr("checked", "checked")
	}

	//Formatting team fields
	$.each(team_list, function(team_key, values){
		team_names += values[0] + ", "

        var support_url = '<a href="donate_parent?t=team_key&i=individual_key" target="_blank">team_name</a><br><br>'
        support_url = support_url.replace("donate_parent", donate_parent)
        support_url = support_url.replace("team_key", team_key)
        support_url = support_url.replace("individual_key", individual_key)
        support_url = support_url.replace("team_name", values[0])

        $("#support_urls").append(support_url)
	})

	//Populate current teams
	refreshCurrentTeams()

	getTeamTotals()

	$("form").validationEngine()

	$("#team_display input").val(team_names.substr(0, team_names.length-2))

	$("#edit_profile").click(function(){
		//Change the page to edit mode
		$("#edit_profile").hide()
		$("#team_display").hide()
		$(".hidden").fadeIn()

		$(".unlockable").removeAttr("disabled")	
	})

    //Set the team selector to current team
    $("#team_selector select").val($("#current_team").val())

    $("#all_teams").delegate("#add_team", "click", function(){
    	var team_key = $("#all_teams select").val()
    	var team_name = $("#all_teams option[value=" + team_key + "]").text()

    	//Add team to dictionary
		team_list[team_key] = [team_name, 2800]

		refreshCurrentTeams()
	})

    $(".current_team input[type=button]").live("click", function(){
        var team_key = $(this).parent().attr("data-id")

        //Remove team from dictionary
        delete team_list[team_key]

        refreshCurrentTeams()
    })

    $("form input[name=delete_individual]").click(function(){
    	var r=confirm("Do you want to delete this person?")
		if (r==true){
	    	var params = {'individual_key':individual_key}
	    	var request = ghiapi.individual.delete(params)

		    request.execute(function(response){
		    	rpcSuccessMessage(response)
		    	
		    	var home_page = $("#home_page").val()
	            if (home_page == "dashboard"){
	            	window.location.hash = "allteams"
	            }
	            else{
	            	window.location = "/login"
	            }
		    })
		}
		else{
			return
		}	
    })

	$("form input[type=submit]").click(function(){
		$("#current_teams input[type=text]").each(function(){
			var team_key = $(this).parent().attr("data-id")

			var number = $(this).val().replace(/[^\d.]/g, "")
			var amount = parseFloat(number)

			if (amount == 0){
				amount = 0.01
			}

			team_list[team_key][1] = amount
		})

		json_list = $.toJSON(team_list)
		$("form input[name=team_list]").val(json_list)

		var validation_result = $("form").validationEngine('validate')
		if (validation_result == true){
			$("form").submit()
		}	
	})

    $("#donations").delegate("tr", "click", function(){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        var url = "/ajax/reviewdetails?id=" + clicked_id
        loadColorbox(url, "donation_container")
    });
	
})