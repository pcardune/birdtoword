jQuery(".word-cloud span").click(
    function(){
        var word = jQuery(this).text();
        jQuery("#definition-wrapper").show().find(".definition")
            .html("Getting definition for <em>"+word+"</em>...");
        birdtoword.getWordDefinitionHtml(
            word,
            function(html){
                jQuery("#definition-wrapper")
                    .show()
                    .find(".definition")
                    .html("<strong>"+word+"</strong>"+html);
            });
    });
