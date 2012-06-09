function format_iovlist(iovList){
	iovList 	= 	iovList.replace(/\), \(/g,"</td></tr><tr><td>")
	iovList 	= 	iovList.replace(/\[\(/g,"<tr><td>")
	iovList 	= 	iovList.replace(/\)\]/g,"</td></tr>")
	iovList 	= 	iovList.replace(/, /g,"</td><td>")
	iovList 	= 	iovList.replace(/L/g,"")
	return iovList;
}
function format_comment(comment){
	comment		= 	comment.replace(/;/g,";<br><br>")
	comment		= 	comment.replace(/\/CMSSW/g,"<br>/CMSSW")
	return comment;
}

var CHECKED_BG_COLOR = 'red';
var UNCHECKED_BG_COLOR = '#3ef';
//dirty hack: when a checkbox is checked it first of all unchecks all checkboxes that belongs to table and then checks selected one
            function checkEvent(src) {
                    $('#test :checked').parent().parent().css('background-color', UNCHECKED_BG_COLOR);
                    $('#test :checked').attr('checked', false);
                    $(src).attr('checked', src);
                    $(src).parent().parent().css('background-color', CHECKED_BG_COLOR);
            }
            function getCheckedCell(src, columnNum) {
                //column numeration starts with 0!
                return $(src).parent().parent().children(columnNum).html();
            }
