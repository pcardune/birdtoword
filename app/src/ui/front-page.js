jQuery(
    function(){
        jQuery("#error-dialog").dialog(
            {
                title: "Error",
                zIndex: 9999,
                autoOpen: false,
                modal: true,
                buttons: {
                    "Ok": function(){ window.location.reload(); }
                }
            });
        jQuery.ajaxSetup(
            {
                error: function(){
                    jQuery("#error-dialog").dialog("open");
                }
            });

        var game;
        jQuery("#start-playing-button").click(
            function(){
                jQuery(this).hide();
                game.show();
            });

        function handleChallengeEmailSent(data){
            jQuery("#challenge-friend-sending").hide();
            if (data.error){
                jQuery("#challenge-friend-content").show()
                    .find(".error").show()
                    .find(".message").html(data.errorMessage);
            } else {
                jQuery("#challenge-friend-content").hide();
                jQuery("#challenge-friend-success")
                    .find(".recipient").html(data.to).end()
                    .show();
                window.setTimeout(function(){jQuery("#challenge-friend").dialog("close");},2000);
            }
        }

        jQuery("#challenge-friend-send").click(
            function(){
                jQuery("#challenge-friend-content .error").hide();
                jQuery("#challenge-friend-content").hide();
                jQuery("#challenge-friend-sending").show();
                birdtoword.sendChallengeEmail(
                    {
                        from: jQuery("#challenge-friend-form [name=from]").val(),
                        to: jQuery("#challenge-friend-form [name=to]").val(),
                        message: jQuery("#challenge-friend-form [name=message]").val()
                    }, handleChallengeEmailSent);
            });

        jQuery("#challenge-friend").dialog(
            {
                height: 350,
                title: "Challenge Your Friends!",
                width: 400,
                show: 'slide',
                hide: 'slide',
                autoOpen: false,
                close: function(){
                    jQuery("#challenge-friend-success").hide();
                    jQuery("#challenge-friend-sending").hide();
                    jQuery("#challenge-friend-content").show();
                    jQuery("#challenge-friend-content .error").hide();
                    jQuery("#challenge-friend-form").get(0).reset();
                },
                buttons: {
                    "Challenge!": function(){
                        jQuery("#challenge-friend-content .error").hide();
                        jQuery("#challenge-friend-content").hide();
                        jQuery("#challenge-friend-sending").show();
                        birdtoword.sendChallengeEmail(
                            {
                                from: jQuery("#challenge-friend-form [name=from]").val(),
                                to: jQuery("#challenge-friend-form [name=to]").val(),
                                message: jQuery("#challenge-friend-form [name=message]").val()
                            }, handleChallengeEmailSent);
                    },
                    "Cancel": function(){
                        jQuery(this).dialog("close");
                    }
                }
            });

        jQuery.getJSON(
            '/api/game-words/3',
            function(words){
                game = new birdtoword.Game(
                    {
                        el: 'game',
                        from: words.from,
                        to: words.to
                    });
            });
    });
