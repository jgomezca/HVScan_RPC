function selectCheckedSinceForXml(objectPassed, anchorId, urlBeginning) { 
            var since        =  urlBeginning;
            //$(objectPassed).parent().parent().find('input:checkbox').each(
            var itemSelected    =   $('.Selected')
            objectPassed.parent().parent().find(itemSelected).find("td:first").each(function(){
                    //since +=$(this).parent().parent().children().html();
                    since += $(this).html().split(";")[0];
                    since += '%3B';
                    }
            );
            since = since.replace(/ /g,"%20");
            return since;
}
function selectCheckedSince(objectPassed, anchorId, urlBeginning) { 
            var since           =   urlBeginning;
            var since_size      =   0;
            var itemSelected    =   $('.Selected')
            //$('.Selected').find("td:first").each(function(){
            objectPassed.parent().parent().find(itemSelected).find("td:first").each(function(){
                //console.log($(this).html());
                since += $(this).html().split(";")[0];
                since += '%3B';
                since_size++;
            });
            if(anchorId=='#trendPlot_link' && since_size!=2){
                alert("Please check only two IOVs.\nIt seems you checked "+since_size+" IOVs.");
                return 0;
            }
            if(anchorId=='#summary_link' && since_size==0){
                alert("Please check at least one IOV.\nIt seems you checked "+since_size+" IOV.");
                return 0;
            }
            since += '&iframe=true&width=99%&height=99%&id=frame';
            since = since.replace(/ /g,"%20");
            var hrf    =   $(anchorId).attr('href',since);
            $(anchorId).click();
            setTimeout("$('iframe').width('100%')", 3000);
        }

function check_iov_for_diff(objectPassed, anchorId, urlBeginning, dbName, accName, record){
    var checkedCount = 0;
    var firstIOV = '';
    var secondIOV = '';
//    alert('check_iov_for_diff');

    $(objectPassed).parent().parent().find('input:checkbox').each(
      function(){ 
          if($(this).is(':checked')){
              checkedCount ++;
              if(checkedCount == 1)
                  firstIOV = $(this).parent().parent().children().html();
              else {
                  if(checkedCount == 2) 
                      secondIOV = $(this).parent().parent().children().html();
              } 
          }
      }
    );
    if(checkedCount!=2)
        alert('Exactly two IOV values must be selected - neither less nor more. Now selected '+checkedCount+'.');
    else{
        var urlParameters        =  urlBeginning;
        urlParameters += 'dbName1='+dbName+'&';
        urlParameters += 'acc1='+accName+'&';                
        urlParameters += 'tag1='+record+'&';
        urlParameters += 'since1='+firstIOV+'&';        
        urlParameters += 'fileType1=png&';
        urlParameters += 'png1='+ ''  +'&';
        urlParameters += 'dbName2='+dbName+'&';        
        urlParameters += 'acc2='+accName+'&';                
        urlParameters += 'tag2='+record+'&';
        urlParameters += 'since2='+secondIOV+'&';        
        urlParameters += 'fileType2=png&';
        urlParameters += 'png2='+ ''  +'&';
        urlParameters += 'type=3&';
        urlParameters += 'istkmap=1&';
        urlParameters += '&iframe=true&width=99%&height=99%&id=frame';
//alert(urlParameters);
        var hrf    =   $(anchorId).attr('href', urlParameters);
        $(anchorId).click();
        setTimeout("$('iframe').width('100%')", 3000);
}

}
