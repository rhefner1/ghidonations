$(document).ready(function(){
    $("form").validationEngine()

    $("#newteam").delegate("input[value=Save]", "click", function(){
        var validation_result = $("form").validationEngine('validate')
        if (validation_result == true){
            var name = $("#newteam input[name=name]").val()

            //Flash message
            show_flash("setting", "Creating team...", false)

            var params = {'name':name}
            var request = ghiapi.new.team(params)

            request.execute(function(response){
                rpcSuccessMessage(response, function(){
                    window.location.hash = "newindividual"  
                })
                
            })
        }            
    })
});