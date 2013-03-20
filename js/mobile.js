var pages_retrieved = 0
var cursors_dict = {0:null}

function clickHandler(){
    $("#donations #load_more").off()
    $("#donations #load_more").one("click", function(){
        $("#load_more_text").hide()
        $("#search_loading").show()

        getDonations()

        $("#search_loading").hide()
        $("#load_more_text").show()
    })
}

function getDonations(){
    var i_key = $("#i_key").val()

    var query_cursor = cursors_dict[pages_retrieved]
    pages_retrieved += 1

    if (query_cursor != "end"){
        var params = {'individual_key':i_key, 'query_cursor':null}
        var request = ghiapi.semi.get.individualdonations(params)
    
        request.execute(function(response){

            $.each(response.objects, function(index, d){
                var template = $.tmpl('<li style="font-size:16px"><span>${name}</span> <small class="counter">${amount_donated}</small></a></li>', d)
                template.appendTo("#donations_list");
            })

            // Saving query cursor for next request
            var next_cursor = response.new_cursor

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

function initializeAPI(){
    // Load GHI Donations API
    var ROOT = '/_ah/api';
    gapi.client.load('ghidonations', 'v1', function() {
        ghiapi = gapi.client.ghidonations

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
    }, ROOT); 
}