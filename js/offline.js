$(document).ready(function(){
    $("#individual_selector").hide()

    //Form validation - not yet ready for production
    $("form").validationEngine()

    if (home_page == "dashboard"){
        // Autocomplete for contacts
        params = {"action" : "getContactsJSON"}
        var url = '/rpc?' + $.param(params)
        $.getJSON(url, function(data){
            $("input[name=name]").autocomplete({
                source: data,
                select: function(event, ui){
                    $("input[name=email]").val(ui.item.email)

                    try{
                        var address = JSON.parse(ui.item.address)
                        $("input[name=street]").val(address[0])
                        $("input[name=city]").val(address[1])
                        $("input[name=state]").val(address[2])
                        $("input[name=zip]").val(address[3])
                    }
                    catch(err) {
                        void(0)
                    }
                }
            });
        })
    }
    

    $('#team_selector select').bind('change', function(){ 
        var team_key = $("#team_selector select").val()
        if (team_key == "general") {
            $("#individual_selector").hide("fast")
        }
        else {
            params = {action: "semi_getTeamMembers", arg0: JSON.stringify(team_key)}
            
            rpcGet(params, function(data){
                //HTML to be inserted
                option_html = '<option value="none">None</option>'

                $.each(data, function(name, key) {
                    option_html = option_html + 
                    "<option value=" + key + ">" + name + "</option>"
                });  

                $("#individual_selector select").html(option_html)
            })

            $("#individual_selector").show("fast")
        }   
    });
    
    $("#offline").delegate("#save", "click", function(){
        var validation_result = $("form").validationEngine('validate')
        if (validation_result == true){
            var name = $("#offline input[name=name]").val()
            var email = $("#offline input[name=email]").val()
            var amount_donated = $("#offline input[name=amount_donated]").val()
            var notes = $("#offline textarea[name=special_notes]").val()

            var street = $("input[name=street]").val()
            var city = $("input[name=city]").val()
            var state = $("input[name=state]").val()
            var zip = $("input[name=zip]").val()

            address = $.toJSON([street, city, state, zip])
            
            var team_key = $("#offline select[name=team] option:selected").val()
            var individual_key = $("#offline select[name=individual] option:selected").val()
            var add_deposit = Boolean($("input[name=add_deposit]:checked").val())

            var home_page = $("#home_page").val()
            var submit_action = ""
            var params

            if (home_page == "dashboard"){
                submit_action = "offlineDonation"
                params = [submit_action, name, email, amount_donated,
                        notes, address, team_key, individual_key, add_deposit]
            }
            else{
                submit_action = "semi_createDonation"
                var params = [submit_action, name, email, amount_donated,
                        notes, address, team_key, individual_key]
            }
            
            

            //Flash message
            show_flash("setting", "Saving donation...", false)

            rpcPost(params, function(data){
                refreshPage()
            })
        }
        
    })
});