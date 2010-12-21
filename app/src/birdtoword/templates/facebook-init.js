var fb_session = null;
var fb_api = null;

function handleUserConnected(){
    jQuery.cookies.set("facebook-uid",""+fb_session.uid);

//    console.log("detected that user is now logged in.");

//    console.log("Checking for permissions");
    // Step 1: Check for all the permissions...
//    FB.Facebook.apiClient.users_hasAppPermission(
//        "status_update",
//        function(result){
//            console.log("status_update permission:", result);
//            if (result !== 1){
//                FB.Connect.showPermissionDialog("status_update");
//            }
//        });

    // Step 2: override logout button...
    jQuery("#nav-logout").click(
        function(){
            jQuery.cookies.del("facebook-uid");
//            FB.Connect.logout(function(){console.log("User is now logged out!");});
            FB.Connect.logoutAndRedirect(window.location);
        });
}



function handleFacebookLogin(){
    window.setTimeout(function(){window.location.reload();}, 1000);
}



FB_RequireFeatures(
    ["XFBML","Api"],
    function(){
//        console.log("facebook features loaded, doing more stuff.");
        FB.init("bd02d19336f0dd5399414f1ef8b6cc9c", "/xd_receiver.htm");
        FB.Facebook.get_sessionState().waitUntilReady(
            function(session){
                fb_session = session;
            });
        FB.Connect.ifUserConnected(handleUserConnected);

    });
