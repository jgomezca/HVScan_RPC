function Helper(){
    this.h1Value    =   $('h1').text();
    this.h1Value    =   "help/"+this.h1Value.replace(/ /g,'-').replace(":-","_")+".html";
}

Helper.prototype.setButton  =   function(){
    $('.ui-bar-a.ui-header').append('<span class="iframe ui-btn-right ui-btn ui-btn-corner-all ui-shadow ui-btn-up-a" data-rel="back" data-icon="arrow-l" data-theme="a"><span class="ui-btn-inner ui-btn-corner-all"><span class="ui-btn-text help">Help</span></span></span>');
}

Helper.prototype.setBehaviour = function(){
    $('span.iframe').attr('href', this.h1Value);
    $('span .ui-btn-text.help').click(function() {
        $("span.iframe").fancybox({
            'hideOnContentClick': true,
            'width'                 : '100%',
            'height'                : '100%',
            'transitionIn'  :   'elastic',
            'transitionOut' :   'elastic',
            'speedIn'       :   600, 
            'speedOut'      :   200, 
            'overlayShow'   :   false
        });
    });
}

Helper.prototype.checkFile = function(){
    var http = new XMLHttpRequest();
    http.open('HEAD', this.h1Value, false);
    http.send();
    if (http.status!=404){
        return 1;
    }
    else return 0;
}
