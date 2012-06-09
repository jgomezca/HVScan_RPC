hs.graphicsDir = 'lib/highslide/graphics/';
hs.align = 'center';
hs.transitions = ['expand', 'crossfade'];
hs.wrapperClassName = 'dark borderless floating-caption';
hs.fadeInOut = true;
hs.dimmingOpacity = .75;
if (hs.addSlideshow) hs.addSlideshow({
    //slideshowGroup: 'group1',
    interval: 5000,
    repeat: false,
    useControls: true,
    fixedControls: 'fit',
    overlayOptions: {
        opacity: .6,
        position: 'bottom center',
        hideOnMouseOut: true
    }
});
$(document).ready(function() {
    getUrParams ();
    var returned_data;
    $.ajax({
        type: 'POST',
        url: 'get_plot_list',
        data : { dbName : dbName, acc : acc, tag : tag, since : since.replace(/%3B/g, ";") },
        async: false,
        success: function (data) {     
                                       returned_data = data;
                                 },
        error: function() { alert("Error in data send while getting plot img "); }
    });
    var sinceValues = new Array();
    var arg3 = since.replace(/;/g, "%3B");
    while( arg3.indexOf('%3B') != -1 ){
        sinceValues.push(arg3.substr(0, arg3.indexOf('%3B')));
        arg3 = arg3.substr((arg3.indexOf('%3B') + 3), (arg3.length -1));
    }
    var arg4 = "&fileType=png&png=";
    if( returned_data.length < 1 ) {
        alert ("Error in retriving images");
    }
    returned_data = returned_data.replace(/%3B/g, ";");
    while(true){
        var pos = returned_data.indexOf(';');
        if(pos != -1){
            var arg5 = returned_data.substr(0, pos);
            var sinceValue = returned_data.substr(0, returned_data.indexOf(':'));
            arg5 = arg5.substr(returned_data.indexOf(':') +1, returned_data.length-1);
            $('#first').append( "<p><a href='get_plot?dbName=" + dbName + "&acc=" + acc + "&tag=" + tag + "&since=" + sinceValue + "&fileType=png&png=" + arg5 + "' class='highslide' onclick='return hs.expand(this)'><img height='75px' src='get_plot?dbName=" + dbName + "&acc=" + acc + "&tag=" + tag + "&since=" + sinceValue + "&fileType=png&png=" + arg5 + "'  alt=''title='" + arg5 + "' /> " + arg5 + "</a><div class='highslide-caption'>" + arg5 + "</div></p>");
            if(returned_data.length > (pos + 2) ) {
                returned_data = returned_data.substr((pos + 1), returned_data.length-1);
            }
            else {
                break;
            }
        }
        else{
            if (returned_data.length > 0){
                 arg5 = returned_data;
                 sinceValue = returned_data.substr(0, returned_data.indexOf(':'));
                 arg5 = returned_data.substr(returned_data.indexOf(':')+1, returned_data.length - 1);
                 $('#first').append( "<p><a href='get_plot?dbName=" + dbName + "&acc=" + acc + "&tag=" + tag + "&since=" + sinceValue + "&fileType=png&png=" + arg5 + "' class='highslide' onclick='return hs.expand(this)'><img height='75px' src='get_plot?dbName=" + dbName + "&acc=" + acc + "&tag=" + tag + "&since=" + sinceValue + "&fileType=png&png=" + arg5 + "'  alt=''title='" + arg5 + "' /> " + arg5 + "</a><div class='highslide-caption'>" + arg5 + "</div></p>");
            }
            break;
        }
    }
    $(function(){
        $("#blocker").hide();
    });
});
