$(document).ready(function(){
    $("form").validationEngine()

    $("#newindividual").delegate("#save", "click", function(){
        var validation_result = $("form").validationEngine('validate')
        if (validation_result == true){
            var name = $("#newindividual input[name=name]").val()
            var team_key = $("#newindividual #team_selector option:selected").val()
            var email = $("#newindividual input[name=email]").val()
            var password = $("#newindividual input[name=password]").val()
            var admin = Boolean($("#newindividual input[name=admin]:checked").val())

            var params = ["newIndividual", name, team_key, email, password, admin]

            //Flash message
            show_flash("setting", "Creating individual...", false)

            rpcPost(params, function(data){
                refreshPage()
            })     
        }  
    })
});