function dataTableWriter(data_table, d){
    data_table.fnAddData([
            d.key,
            d.formatted_donation_date,
            d.email,
            d.amount_donated,
            d.payment_type
        ])

    data_table.fnAdjustColumnSizing()
}

$(document).ready(function(){
    var contact_key = $("#contact_key").val()

    var rpc_request = ghiapi.get.contact_donations
    var rpc_params = {'contact_key':contact_key}

    var data_table = initializeTable(4, rpc_request, rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
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

    //Deserialize the phone number
    var phone = $("#phone").val()
    if (phone != "None"){
        $("input[name=phone_1]").val(phone.substr(0,3))
        $("input[name=phone_2]").val(phone.substr(3,3))
        $("input[name=phone_3]").val(phone.substr(6,4))
    }

    //Initialize the validation engine
    $("form").validationEngine()

    //When donation is clicked, pop open the rq_details lightbox
    $("#donations").delegate("tr", "click", function(){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        var url = "/ajax/reviewdetails?id=" + clicked_id
        loadColorbox(url, "contact_container")
    });

    //Change to edit mode
    $("#edit_contact").click(function(){
        //Change the page to edit mode
        $("#edit_contact").hide()
        $("#add_impression").hide()

        $("#save_contact_changes").fadeIn()

        $(".remove_email").css("display", "block")
        $("#add_email_container").fadeIn()

        $(".unlockable").removeAttr("disabled")
    })

    add_email_handler()

    //Change to impression adding mode
    $("#add_impression").click(function(){
        $("#impressions_list").hide()
        $("#impression_fields").fadeIn()

        $("#add_impression").hide()
        $("#edit_contact").hide()
    })

    //Revert to normal view after impression was discarded
    $("input[name=discard_impression]").click(function(){
        $("#impressions_list").fadeIn()
        $("#impression_fields").hide()

        $("#add_impression").show()
        $("#edit_contact").show()

        $("#impressions_edit textarea").val("")
    })

    //Send RPC request to delete contact
    $("input[name=delete_contact]").click(function(){
        var r=confirm("Do you want to delete this contact?")
        if (r==true){
            var contact_key = $("#contact_key").val()
            var params = {'contact_key':contact_key}
            var request = ghiapi.contact.delete(params)

            request.execute(function(response){
                rpcSuccessMessage(response, function(){
                    window.location.hash = "allcontacts"
                })
                
            })
        }
        else{
            return
        }  
    })

    //Save contact and post it to RPC
    $("input[name=save_contact]").click(function(){
        var name = $("input[name=name]").val()
        var email = $(".email_address").map(function(){return $(this).val();}).get()
        var notes = $("textarea[name=notes]").val()

        var phone_1 = $("input[name=phone_1]").val()
        var phone_2 = $("input[name=phone_2]").val()
        var phone_3 = $("input[name=phone_3]").val()
        var phone = phone_1 + phone_2 + phone_3
        
        var street = $("input[name=street]").val()
        var city = $("input[name=city]").val()
        var state = $("input[name=state]").val()
        var zipcode = $("input[name=zip]").val()

        address = {'street':street, 'city':city, 'state':state, 'zipcode':zipcode}

        var params = {'contact_key':contact_key, 'name':name, 'email':email,
                    'phone':phone, 'notes':notes, 'address':address}

        var request = ghiapi.update.contact(params)

        request.execute(function(response){
            rpcSuccessMessage(response, function(){
                refreshPage()  
            })
        })
    })

    //Save impression and post it to RPC
    $("input[name=save_impression]").click(function(){
        var impression = $("#impressions_edit select").val()
        var notes = $("#impressions_edit textarea").val()

        var params = {'contact_key':contact_key, 'impression':impression, 'notes':notes}
        var request = ghiapi.new.impression(params)

        request.execute(function(response){
            rpcSuccessMessage(response, function(){
                refreshPage()  
            })
        })
    })
})