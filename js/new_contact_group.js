$(document).ready(function(){
    $("form").validationEngine()

    $("#newteam").delegate("input[value=Save]", "click", function(){
        var validation_result = $("form").validationEngine('validate')
        if (validation_result == true){
            var name = $("#newteam input[name=name]").val()

            //Flash message
            show_flash("setting", "Creating group...", false)

            var params = {'name':name}
            var request = ghiapi.new.contactgroup(params)

            request.execute(function(response){
                rpcSuccessMessage(response)
                window.location.hash = "allcontactgroups"
            })
        }            
    })
});