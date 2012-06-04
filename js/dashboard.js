$(document).ready(function(){
    // -- If there are unread donations, highlight box with yellow -- //
    var num_donations = $("#review_queue .value").html()
	if (parseInt(num_donations) !== 0)
    {
        $("#review_queue").addClass("attention")
    }

    // -- This function changes tab behavior -- //
    $("#dashboard .report .button").click(function(){
        var hash = $(this).attr("data-location")
        window.location.hash = hash
    });
});