$(document).ready(function(){
    $("form").validationEngine()

    $("#newteam").delegate("input[value=Save]", "click", function(){
        var validation_result = $("form").validationEngine('validate')
        if (validation_result == true){
            var name = $("#newteam input[name=name]").val()
            var params = ["newTeam", name]

            //Flash message
            show_flash("setting", "Creating team...", false)

            rpcPost(params, function(data){
                window.location.hash = "newindividual"
            })
        }            
    })
});