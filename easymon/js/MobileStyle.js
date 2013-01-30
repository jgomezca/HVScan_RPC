function MobileStyle(){
}

MobileStyle.prototype.setCssProperties =    function(){
    $('.cap').css("text-transform", "uppercase"); 
    $('.cap').css("font-weight", "bold")
    $('div li[data-role="list-divider"]').remove();
    $('.ui-body-c').css('color','#000000');
    $('.ui-body-c').css('text-shadow','none');
    $('.chart .bar').css('background','transparent')
    $('.healthy100').css('background-color','#33FF66')
    $('.healthy100').css('background','-webkit-gradient(linear, left top, left bottom, from(#009933), to(#33FF00))');
    $('.healthy90').css('background-color','#33FF66')
    $('.healthy90').css('background','-webkit-gradient(linear, left top, left bottom, from(#009933), to(#33FF00))');
    $('.healthy75').css('background-color','#FFCC33')
    $('.healthy75').css('background','-webkit-gradient(linear, left top, left bottom, from(#FF9900), to(#FFFF00))');
    $('.healthy50').css('background-color','#FFCC33')
    $('.healthy50').css('background','-webkit-gradient(linear, left top, left bottom, from(#FF9900), to(#FFFF00))');
    $('.healthy25').css('background-color','#FF0033')
    $('.healthy25').css('background','-webkit-gradient(linear, left top, left bottom, from(#FF0033), to(#FF0000))');
    $('.healthy0').css('background-color','#FF0033')
    $('.healthy0').css('background','-webkit-gradient(linear, left top, left bottom, from(#680000), to(#FF0000))');
}

MobileStyle.prototype.setButton = function(){
    if( (location.href).indexOf('?fileName=') > -1 ){
        url     =   location.origin+location.pathname;
        url_txt =   "Back";
        $('.ui-bar-a.ui-header').append('<a href="'+url+'" class="ui-btn-left ui-btn ui-btn-icon-left ui-btn-corner-all ui-shadow ui-btn-up-a" data-rel="back" data-icon="arrow-l" data-theme="a"><span class="ui-btn-inner ui-btn-corner-all"><span class="ui-btn-text">'+url_txt+'</span><span class="ui-icon ui-icon-arrow-l ui-icon-shadow"></span></span></a>');
    }
    else{
        url=   "./";
        url_txt =   "Home"   
        //$('.ui-bar-a.ui-header').append('<a href="'+url+'" class="ui-btn-left ui-btn ui-btn-icon-left ui-btn-corner-all ui-shadow ui-btn-up-a" data-rel="back" data-icon="arrow-l" data-theme="a"><span class="ui-btn-inner ui-btn-corner-all"><span class="ui-btn-text">'+url_txt+'</span></span></a>');
    }
}

