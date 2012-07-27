$(document).ready(function(){
    var contact_key = $("#contact_key").val()

    var initial_cursor = $("#initial_cursor").val()

    var rpc_params = [contact_key]
    var data_table = initializeTable(4, initial_cursor, "getContactDonations", rpc_params, function(data_table, i){
        data_table.fnAddData([
            d.key,
            d.formatted_donation_date,
            d.email,
            d.amount_donated,
            d.payment_type
        ])
    })

    //Deserialize the address
    var address = $("#address").val()
    if (address != "None"){
        address = JSON.parse(address)
        $("input[name=street]").val(address[0]) 
        $("input[name=city]").val(address[1])
        $("input[name=state]").val(address[2])
        $("input[name=zip]").val(address[3])
    }

    var phone = $("#phone").val()
    if (phone != "None"){
        $("input[name=phone_1]").val(phone.substr(0,3))
        $("input[name=phone_2]").val(phone.substr(3,3))
        $("input[name=phone_3]").val(phone.substr(6,4))
    }

    $("form").validationEngine()

    $("#donations").delegate("tr", "click", function(){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        var url = "/ajax/reviewdetails?id=" + clicked_id
        loadColorbox(url, "contact_container")
    });

    $("#edit_contact").click(function(){
        //Change the page to edit mode
        $("#edit_contact").hide()
        $("#add_impression").hide()

        $("#save_contact_changes").fadeIn()

        $(".unlockable").removeAttr("disabled")
    })

    $("#add_impression").click(function(){
        $("#impressions_list").hide()
        $("#impression_fields").fadeIn()

        $("#add_impression").hide()
        $("#edit_contact").hide()
    })

    $("input[name=discard_impression]").click(function(){
        $("#impressions_list").fadeIn()
        $("#impression_fields").hide()

        $("#add_impression").show()
        $("#edit_contact").show()

        $("#impressions_edit textarea").val("")
    })

    $("input[name=delete_contact]").click(function(){
        var contact_key = $("#contact_key").val()
        var params = ["deleteContact", contact_key]

        rpcPost(params, function(data){
            window.location.hash = "allcontacts"
        })
    })

    $("#impressions_edit select").change(function(){
        
    })

    $("input[name=save_contact]").click(function(){
        var name = $("input[name=name]").val()
        var email = $("input[name=email]").val()
        var notes = $("textarea[name=notes]").val()

        var phone_1 = $("input[name=phone_1]").val()
        var phone_2 = $("input[name=phone_2]").val()
        var phone_3 = $("input[name=phone_3]").val()
        var phone = phone_1 + phone_2 + phone_3
        
        var street = $("input[name=street]").val()
        var city = $("input[name=city]").val()
        var state = $("input[name=state]").val()
        var zip = $("input[name=zip]").val()

        address = $.toJSON([street, city, state, zip])

        var params = ["updateContact", contact_key, name, email, phone, notes, address]

        rpcPost(params, function(data){
            refreshPage()
        })
    })

    $("input[name=save_impression]").click(function(){
        var impression = $("#impressions_edit select").val()
        var notes = $("#impressions_edit textarea").val()

        var params = ["newImpression", contact_key, impression, notes]

        rpcPost(params, function(data){
            refreshPage()
        })
    })
})