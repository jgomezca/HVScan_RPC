function bITS(record){
//bITS buildInnerTableStyle
    var rcdId   =   '#'+record+'.myTable01';
    var itemTbl =   $(rcdId);
    numRows =   $(rcdId+' tbody tr').length;
    if(numRows>10)
        itemTbl.fixedHeaderTable({ width: '600', height: '250', footer: true, cloneHeadToFoot: true, altClass: 'odd', themeClass: 'fancyTable', autoShow: false });
    else{
        heightTbl   =   44 + numRows*10;
        itemTbl.fixedHeaderTable({ width: '600', height: heightTbl, footer: false, cloneHeadToFoot: false, altClass: 'odd', themeClass: 'fancyTable', autoShow: false });
    }

    itemTbl.fixedHeaderTable('show', 1000);
    $('a.makeTable').bind('click', function() {
        itemTbl.fixedHeaderTable('destroy');
        //$('.myTable01 th, .myTable01 td')
        //    .css('border', $('#border').val() + 'px solid ' + $('#color').val());
        itemTbl.fixedHeaderTable({ width: $('#width').val(), height: $('#height').val(), footer: true, themeClass: 'fancyTable' });
    });
}

