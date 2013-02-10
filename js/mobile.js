var pages_retrieved = 0
var cursors_dict = {0:null}

function clickHandler(){
    $("#donations #load_more").off()
    $("#donations #load_more").one("click", function(){
        $("load_more_text").hide()
        $("#search_loading").show()

        getDonations()

        $("#search_loading").hide()
        $("load_more_text").show()
    })
}

function getDonations(){
    var i_key = $("#i_key").val()

    var query_cursor = cursors_dict[pages_retrieved]
    pages_retrieved += 1

    if (query_cursor != "end"){
        var rpc_params = {"action" : "semi_getIndividualDonations", arg0: JSON.stringify(query_cursor), arg1: JSON.stringify(i_key)}
    
        $.getJSON("/rpc?" + $.param(rpc_params), function(data){

            $.each(data[0], function(num){
                var template = $.tmpl('<li style="font-size:16px"><span>${name}</span> <small class="counter">${amount_donated}</small></a></li>', data[0][num])
                var object = template.appendTo("#donations_list");
                // object.quickfit()
            })

            // Saving query cursor for next request
            var next_cursor = data[1]

            if (next_cursor == null){
                next_cursor = "end"

                $("#donations #load_more").hide()
                $("#donations #end_of_donations").show()
            }

            cursors_dict[pages_retrieved] = next_cursor
        })
    }

    clickHandler()
}

// $(document).ready(function(){

//Team list dictionary parsed from JSON
var team_list = JSON.parse($("input[name=team_list]").val())
var team_names = ""

//Formatting team field
$.each(team_list, function(team_key, values){
    team_names += values[0] + ", "
})

$("#team_names").text(team_names.substr(0, team_names.length-2))

clickHandler()
getDonations()
    
// });