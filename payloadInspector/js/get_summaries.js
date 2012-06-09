$(function() {
                $('#container-5').tabs({ fxSlide: true, fxFade: true, fxSpeed: 'normal' });
});

$(document).ready(function() {
    getUrParams();
    $.ajax({
                type: 'POST',
                url: 'get_summary',
                data : { dbName : dbName, acc : acc, tag : tag, since : since.replace(/%3B/g, ";")},
                dataType : 'json',
                async: false,
                success: function (data) {     
                                             $.each(data.summary, function(i,item){
                                                 $.each(item, function(k,itemk){
                                                     $("#container-5").append("<div id='fragment-"+k+"'><textarea class='styled'>"+itemk+"</textarea></div>");  
                                                     $("#tabsList").append("<li><a href='#fragment-"+k+"'><span>"+k+"</span></a></li>");  
                                                  });
                                             });
                                             $('#container-5').tabs({ fxSlide: true, fxFade: true, fxSpeed: 'normal' });
                                         },
                error: function() { alert("Error in data send while getting summary information "); }
           });
    $(function(){
        $("#blocker").hide();
    });               
});
