//Flag to see if we're in edit mode or not
var save_mode = false
var date_changed = false

function showSave() {
    //Location of target location (email button)
    var target_top = $("#email").position().top
    var target_left = $("#email").position().left

    //Get coordinates of other buttons and calculate how it should move relative to where it is
    var preview_top = target_top - $("#preview").position().top
    var print_top = target_top - $("#print").position().top
    var archive_top = target_top - $("#archive").position().top
    var contact_top = target_top - $("#edit_contact").position().top

    var preview_left = target_left - $("#preview").position().left
    var print_left = target_left - $("#print").position().left
    var archive_left = target_left - $("#archive").position().left
    var contact_left = target_left - $("#edit_contact").position().left

    $("#preview").animate({top: preview_top, left: preview_left})
    $("#print").animate({top: print_top, left: print_left})
    $("#archive").animate({top: archive_top, left: archive_left})
    $("#edit_contact").animate({top: archive_top, left: archive_left})

    $("#email").val("Save")
    $("#email").attr("name", "save")
    save_mode = true
}

// -- Get team members when editing donation -- //
function getTeamMembers(team_key) {
    var params = {'team_key': team_key}
    var request = ghiapi.semi.get.team_members(params)

    request.execute(function (response) {
        //HTML to be inserted
        individual_key = $("#rq_details #individual_key").val()

        if (individual_key !== "None") {
            option_html = '<option value="none">None</option>'
        }
        else {
            option_html = '<option id="current_individual" value="none">* None</option>'
        }

        $.each(response.objects, function (index, d) {
            var key = d.key
            var name = d.name

            if (individual_key !== key) {
                //Putting them into the individual dropdown
                option_html = option_html +
                    "<option value=" + key + ">" + name + "</option>"
            }
            else {
                //Putting them into the individual dropdown
                option_html = option_html +
                    '<option id="current_individual" value=' + key + '>* ' + name + '</option>'
            }

        });
        //Insert parsed HTML into the page
        $("#rq_details #individual_selector select").html(option_html)

        //Select the current value
        $("#rq_details #individual_selector select").val($("#rq_details #current_individual").val())
    })
}

$(document).ready(function () {
    var team_key = $("#rq_details #team_key").val()
    var team_name = $("#rq_details #team_name").val()

    if (team_key == "None") {
        $("#rq_details #team_selector select option[value=general]").text("* General Fund").attr("id", "current_team")
    }
    else {
        $("#rq_details #team_selector select option[value=" + team_key + "]").text("* " + team_name).attr("id", "current_team")
    }
    //Set the team selector to current team
    $("#rq_details #team_selector select").val($("#current_team").val())

    $("#rq_details #change_this input").click(function () {
        if ($(this).attr("id") == "change") {
            //Entering edit mode
            $("#rq_details #change_this input").val("Delete Donation")
            $("#rq_details #change_this input").attr("id", "delete")
            $("#rq_details #change_this input").removeClass("black")

            $("#rq_details .notes").show()

            $("#rq_details #team").hide()
            $("#rq_details #individual").hide()
            $("#rq_details #dateshow").hide()
            showSave()

            // Donation backdate picker
            var donation_date = JSON.parse($("#donation_date").val())
            $("#datepicker").kendoDatePicker({
                value: new Date(donation_date[2], donation_date[1] - 1, donation_date[0]),
                change: function () {
                    date_changed = true
                }
            })

            $("#rq_details .hidden").fadeIn()

            //In case a team was selected during loading (and didn't trigger change event)
            //manually trigger it here
            $("#rq_details #team_selector select").change()

            $("#rq_details .unlockable").removeAttr("disabled")
        }
        else if ($(this).attr("id") == "delete") {
            var r = confirm("Do you want to delete this donation?")
            if (r == true) {
                //Delete donation
                donation_key = $("#donation_key").val()
                var params = {'donation_key': donation_key}
                var request = ghiapi.donation.delete(params)

                request.execute(function (response) {
                    rpcSuccessMessage(response, function () {
                        closeColorbox()
                    })

                })
            }
            else {
                return
            }
        }
    })

    $("#rq_details").delegate("input[name=email]", "click", function () {
        donation_key = $("#donation_key").val()
        var params = {'donation_key': donation_key}
        var request = ghiapi.confirmation.email(params)

        request.execute(function (response) {
            rpcSuccessMessage(response, function () {
                closeColorbox()
            })
        })

    })

    $("#rq_details").delegate("input[name=preview]", "click", function () {
        url = "/thanks?m=w&id=" + $("#donation_key").val()
        window.open(url)
    })

    $("#rq_details").delegate("input[name=print]", "click", function () {
        donation_key = $("#donation_key").val()

        var params = {'donation_key': donation_key}
        var request = ghiapi.confirmation.print(params)

        request.execute(function (response) {
            rpcSuccessMessage(response, function () {
                window.open(response.print_url, "_blank")
                closeColorbox()
            })

        })

    })

    $("#rq_details").delegate("input[name=archive]", "click", function () {
        donation_key = $("#rq_details #donation_key").val()

        var params = {'donation_key': donation_key}
        var request = ghiapi.donation.archive(params)

        request.execute(function (response) {
            rpcSuccessMessage(response, function () {
                closeColorbox()
            })
        })

    })

    $("#rq_details").delegate("input[name=edit_contact]", "click", function () {
        var contact_url = $("#rq_details #contact_url").val()
        window.location.href = contact_url
        $.colorbox.close()

    })

    $("#rq_details").delegate("input[name=save]", "click", function () {
        var donation_key = $("#donation_key").val()
        var name = $("#rq_details input[name=name]").val()
        var email = $("#rq_details input[name=emailaddress]").val()
        var notes = $("#rq_details textarea[name=special_notes]").val()

        var team_key = $("#rq_details #team_selector option:selected").val()
        var individual_key = $("#rq_details #individual_selector option:selected").val()

        if (team_key == "none") {
            team_key = null
        }
        if (individual_key == "none") {
            individual_key = null
        }

        var add_deposit = Boolean($("input[name=add_deposit]").val())

        var donation_date = null
        if (date_changed == true) {
            var donation_string = kendo.toString($("#datepicker").data("kendoDatePicker").value(), "MM/dd/yyyy")
            donation_date = {
                "month": parseInt(donation_string.substr(0, 2)),
                "day": parseInt(donation_string.substr(3, 2)) + 1,
                "year": parseInt(donation_string.substr(6, 4))
            }
        }

        var params = {
            'donation_key': donation_key, 'notes': notes, 'team_key': team_key,
            'individual_key': individual_key, 'add_deposit': add_deposit,
            'donation_date': donation_date
        }

        var request = ghiapi.update.donation(params)

        request.execute(function (response) {
            rpcSuccessMessage(response, function () {
                refreshPage()
            })
        })

    })

    $('#rq_details #team_selector select').bind('change', function () {
        var selection = $("#rq_details #team_selector select").val()
        if (selection == "general") {
            $("#rq_details #individual_selector").hide("fast")
        }
        else {
            getTeamMembers(selection)
            $("#rq_details #individual_selector").show("fast")
        }
    });
})