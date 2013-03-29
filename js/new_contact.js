$(document).ready(function(){

    $("form").validationEngine()
    
    $("#save").click(function(){
        var validation_result = $("form").validationEngine('validate')
        if (validation_result == true){
            var name = $("#newcontact input[name=name]").val()
            var email = $("#newcontact input[name=email]").val()
            var notes = $("#newcontact textarea[name=notes]").val()

            var phone_1 = $("input[name=phone_1]").val()
            var phone_2 = $("input[name=phone_2]").val()
            var phone_3 = $("input[name=phone_3]").val()
            var phone = phone_1 + phone_2 + phone_3

            var street = $("input[name=street]").val()
            var city = $("input[name=city]").val()
            var state = $("input[name=state]").val()
            var zipcode = $("input[name=zip]").val()

            address = {'street':street, 'city':city, 'state':state, 'zipcode':zipcode}

            //Flash message
            show_flash("setting", "Creating donor...", false)
            
            var params = {'name':name, 'email':email, 'phone':phone, 'address':address, 'notes':notes}
            var request = ghiapi.new.contact(params)

            request.execute(function(response){
                rpcSuccessMessage(response)
                refreshPage()
            })            
        }                
    })
});