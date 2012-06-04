/* 
 * This javascript file is necessary for the functioning of the theme
 */

$(document).ready(function(){ 
        $("ul.sf-menu").superfish(); // Superfish Menus!

        // $(".sortable").sortable({ // Makes a list sortable
        //     revert: true
        // });

        $("#myaccount").click(function() {
            $("#logindrop").toggle("slow");
            return false;
        });

        $("#logindrop a").click(function(){
            $("#logindrop").toggle("slow");
        })

        $("#search").click(function() {
            $("#searchdrop").toggle("slow");
            return false;
        });
        
        $(".notification").click(function() {
            $(this).fadeOut("slow");
        });
        
});