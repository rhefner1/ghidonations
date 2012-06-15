//Global variables
var selected_team = null
var selected_individual = null
var settings_key = null

function rpcGet(data, callback){
    var url = '/rpc?' + $.param(data)
    $.getJSON(url, function(data){
        callback(data)
    })
}

function loadTeams(){
    $("#designate").css("height", "auto")
    $("#designate_label").html("<strong>Select one:</strong>")
    $("#designate").html("<p>Loading...</p>")

    selected_team = null
    selected_individual = null

    var params = {action: "pub_allTeams", arg0:JSON.stringify(settings_key)}
    rpcGet(params, function(data){    
        $("#designate").html("")      
               
        $.each(data, function(entry_number, data) {
            var name_json = data[0]
            var key_json = data[1]

            var div = '<input type="button" class="button black team" style="margin-right:10px" data-id="key" value="name">'
            $("#designate").append(div.replace("name", name_json).replace("key", key_json))
        });  
    })  
}

function loadIndividuals(team_key){
    $("#designate_label").html("<strong>Select one:</strong>")
    $("#designate").css("height", "300px")
    $("#designate").css("overflow", "auto")
    $("#designate").html("<p>Loading...</p>")

    selected_individual = null
    
    var params = {action: "pub_teamInfo", arg0: JSON.stringify(team_key)}
    rpcGet(params, function(data){  
        
        $("#designate").html("")

        var back_button = '<br><a href="#" class="button black small" id="back_button"><-- Back</a>'
        $("#designate").append(back_button)

        var ul = '<ul class="gallery medium" id="members_list"></ul>'
        $("#designate").append(ul)
              
        var odd = true
        $.each(data, function(entry_number, data) {
            var name_json = data[0]
            var pic_json = data[1]
            var key_json = data[2]

            

            //To fix the weird spacing issues, use a special 'odd' style
            if (odd == true){
                var li = '<li class="donate_normal" style="margin-left:10px; clear:both" data-id="key"></li>'
                odd = false
            }
            else{
                var li = '<li class="donate_normal" style="margin-left:10px" data-id="key"></li>'
                odd = true
            }
            var pic = '<img src="image_url" style="width:50px; height:auto; margin-right:10px; float:left">'
            var name = '<h3 style="margin-bottom:10px;">name</h3>'
            var readmore = '<button class="read_more button small">Designate</button>'              
            
            $("#members_list").append(li.replace("key", key_json))
            $("[data-id=" + key_json + "]").append(pic.replace("image_url", pic_json))
            $("[data-id=" + key_json + "]").append(name.replace("name", name_json))
            $("[data-id=" + key_json + "]").append(readmore)
        });  
    })  
}

function showInfo(team_key, individual_key){
    $("#designate_label").html("<strong>Your donation will be designated to:</strong>")
    var params = {action: "pub_individualInfo", arg0: JSON.stringify(team_key), arg1: JSON.stringify(individual_key)}

    rpcGet(params, function(data){  
        var photo_url = data[0]
        var name = data[1]
        var description = data[2]
        var percentage = data[3]
        var message = data[4]

        $("#info_container img").attr("src", photo_url)
        $("#info_name").text(name)
        $("#info_description").text(description)

        $("#info_progressbar div").css("width", percentage + "%")
        $("#info_message").text(message)

        $("#designate").hide()
        $("#info_container").fadeIn()
    })  
}

function hideInfo(){
    $("#info_container").hide()
    $("#designate").fadeIn()
}

function submitForm(){
    if ($("#custom").is(":checked") == true) {
        //console.log("Custom is checked.")
        var new_val = $("#custom_donation").val()

        //Formatting new value for sending to PayPal
        new_val = new_val.replace("$", "")
        new_val = new_val.replace(",", "")
        new_val = parseFloat(new_val)
        new_val = new_val.toFixed(2)
        new_val = new_val.toString()

        $("#custom").val(new_val)
    }

    //If the donor has chosen to cover the donation costs
    if ($("#cover_trans").attr("checked") == "checked") {
        //console.log("Covering transaction")
        var current_price = $(".radio_amount:checked").val()
        current_price = parseFloat(current_price)
        var new_price = current_price + (.022 * current_price) + .3
        new_price = new_price.toFixed(2)
        new_price = new_price.toString()

        $(".radio_amount:checked").val(new_price)
    }

    //Embed individual designation info as well as 
    //other specials notes as JSON into the purpose field

    var other_notes = $("#other_notes").val()
    if (other_notes == ""){
        other_notes = null
    }

    var cover_trans = $("#cover_trans").is(":checked")
    var email_subscr = $("#email_subscr").is(":checked")

    var to_send = [selected_team, selected_individual, other_notes, cover_trans, email_subscr]
    var encoded = $.toJSON(to_send)
    $("input[name=custom]").val(encoded)

    parent.donate_form.submit();
}

$(document).ready(function() {

    settings_key = $("#settings_key").val()

    //Function to check if an element exists
    jQuery.fn.exists = function() {
        return jQuery(this).length > 0;
    }

    $("#designate #start_designate").click(function(){
        loadTeams()      
    })

    $("#designate").delegate(".team", "click", function(){
        selected_team = $(this).attr("data-id")
        loadIndividuals(selected_team)
    })


    $("#members_list .read_more").live("click", function(event){
        event.preventDefault()

        selected_individual = $(this).parent().attr("data-id")
        showInfo(selected_team, selected_individual)
    })

    $("#custom_donation").click(function() {
        //console.log("Button clicked")
        $('input[name="a3"]').filter("[id='custom']").attr("checked", "checked");
        $('input[name="amount"]').filter("[id='custom']").attr("checked", "checked");
    });

    //When donation duration is switched, change appropriate values
    $("input[name='donation_duration']").change(function() {
        var checked_val = $("input[name='donation_duration']:checked").val()
        if (checked_val == "monthly") {
            //Change to monthly
            $("#duration").val("M")
            $("#donation_type").val("_xclick-subscriptions")
            $(".money_select").attr("name", "a3")
            $("#donation_name").val("Recurring Donation | Global Hope India")
        }
        else if (checked_val == "weekly") {
            //Change to weekly
            $("#duration").val("W")
            $("#donation_type").val("_xclick-subscriptions")
            $(".money_select").attr("name", "a3")
            $("#donation_name").val("Recurring Donation | Global Hope India")
        }
        else if (checked_val == "onetime") {
            //Change to one-time
            $("#donation_type").val("_donations")
            $(".money_select").attr("name", "amount")
            $("#donation_name").val("One-Time Donation | Global Hope India")
        }
    });

    $("#donate_form").submit(function() {
        submitForm()
    })

    $("#back_button").live("click", function(){
        loadTeams()
    })

    $("#backtolist_button").click(function(e){
        $("#designate_label").html("<strong>Select one:</strong>")
        hideInfo()
    })

    //Set up AJAX
    $.ajaxSetup({
        error: function(jqXHR, exception) {
            if (jqXHR.status === 0) {
                alert("I couldn't connect to the Internet. Check your connection.")
            } else if (jqXHR.status == 404) {
                alert("Whoops! I couldn't find that page.")
            } else if (jqXHR.status == 500) {
                alert("Uh oh! The server's not playing nice right now. Try again later.")
            } else if (exception === 'parsererror') {
                alert("Uh oh! The server gave me something I don't understand. Try again later.")
            } else if (exception === 'timeout') {
                alert("undone", "Hmm... the server's not responding. Try your request again.")
            } else {
                alert("Uh oh, something happened but I don't know what it is - " + jqXHR.responseText)
            }
        }
    });
});