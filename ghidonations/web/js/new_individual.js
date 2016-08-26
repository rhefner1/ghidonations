$(document).ready(function () {
    $('form').validationEngine();
    $('#newindividual').delegate('#save', 'click', function () {
        var validation_result = $('form').validationEngine('validate');
        if (validation_result == true) {
            var name = $('#newindividual input[name=name]').val();
            var team_key = $('#newindividual #team_selector option:selected').val();
            var email = $('#newindividual input[name=email]').val();
            var password = $('#newindividual input[name=password]').val();
            var admin = Boolean($('#newindividual input[name=admin]:checked').val());
            //Flash message
            show_flash('setting', 'Creating individual...', false);
            var params = {
                'name': name,
                'team_key': team_key,
                'email': email,
                'password': password,
                'admin': admin
            };
            var request = ghiapi.new.individual(params);
            request.execute(function (response) {
                rpcSuccessMessage(response, function () {
                    refreshPage();
                });
            });
        }
    });
});