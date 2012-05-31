$(document).ready(function() {
    iov_list                = new Object();
    iov_list._new_value     = iov_list._new_value   ||  [[7777, 8888], [9999, 99999999]];

    iov_list.get_last_since = function() {
        _iov_list   =   this._new_value; 
        _last_since =   _iov_list[_iov_list.length-1][0];
        return _last_since;
    }

    iov_list.get_old_value  = function() {
        _row            =   this._old_value;
        _row            =   _row+"";
        _iov_list_old   =   _row.match(/<tr>(.*)<\/tr>/)[0];
        return  _iov_list_old+"";
    }

    iov_list.get_new_value  = function() {
        _last_list_iov_html =   "";
        _last_list_iov  =   this._new_value;
        $.each(_last_list_iov,function(key,value){
            value               +=  "";
            _last_list_iov_html +=   value.replace(/(\d+),(\d+)/, "<tr><td>$1</td><td>$2</td></tr>")
        });
        return  _last_list_iov_html;
    }
   
    iov_list.change_old_value = function(){
        old_values = this.get_old_value();
        old_value = old_values.match(/<td>(\d*)<\/td><\/tr>$/)[1];
        new_value = this._new_value[0][0] - 1;
        return old_values.replace(old_value, new_value);
    }

    iov_list.get_new_list   =   function(){
        return this.change_old_value()+this.get_new_value();
    }

});



function format_iovlist(iovList){
	iovList 	= 	iovList.replace(/\), \(/g,"</td></tr><tr><td>")
	iovList 	= 	iovList.replace(/\[\(/g,"<tr><td>")
	iovList 	= 	iovList.replace(/\)\]/g,"</td></tr>")
	iovList 	= 	iovList.replace(/, /g,"</td><td>")
	iovList 	= 	iovList.replace(/L/g,"")
	return iovList;
}
function format_comment(comment){
	comment		= 	comment.replace(/;/g,";<br \>")
	//comment		= 	comment.replace(/\/CMSSW/g,"<br \>/CMSSW")
	return comment;
}

function iov_table_fix_height(){
    var tbl_w=$('div.scrollTableIOV').width();rb_td_w=((219*tbl_w)/455)+'px';$('div.scrollTableIOV tbody td').css('width',rb_td_w);$('div.scrollTableIOV thead th').css('width',rb_td_w);
    var iov_container=$('td.details').height();
    if(iov_container>400)iov_container=390;
    iov_container=iov_container-30;
    $('div.scrollTableIOV').css('height', iov_container);
    $('div.scrollTableIOV tbody').css('height',iov_container);
}

function format_pfn(pfn){
	pfn		= 	pfn.replace(/\)\(/g,")<br>(")
	return pfn;
}
