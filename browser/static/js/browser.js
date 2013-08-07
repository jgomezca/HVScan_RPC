var escapeHTMLMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
};

var escapeHTMLRegexpKeys = '';
$.each(escapeHTMLMap, function(index, value) {
    escapeHTMLRegexpKeys += index;
});

var escapeHTMLRegexp = new RegExp('[' + escapeHTMLRegexpKeys + ']', 'g');

function escapeHTML(string) {
    if (string == null)
        return '';

    return ('' + string).replace(escapeHTMLRegexp, function(match) {
        return escapeHTMLMap[match];
    });
};

function escapeRegExp(string) {
    if (string == null)
        return '';

    return ('' + string).replace(/[\-\[\]{}()*+?.,\\\^$|#\s]/g, '\\$&');
}

function highlight(highlightRegexp, string) {
    if (string == null)
        return '';

    return ('' + string).replace(highlightRegexp, '<span class="highlight">$&</span>');
}

function results(html) {
    $('#results').html(html);
}

function working() {
    results('<p class="working">Fetching results...</p>');
}

function error(msg) {
    var contacthelp = 'If you need assistance or you found a bug, please write an email to <a href="mailto:cms-cond-dev@cern.ch">cms-cond-dev@cern.ch</a> and <a href="mailto:cms-offlinedb-exp@cern.ch">cms-offlinedb-exp@cern.ch</a>. If you need immediate/urgent assistance, you can call the Offline DB expert on call (+41 22 76 70817, or 70817 from CERN; check <a href="https://twiki.cern.ch/twiki/bin/viewauth/CMS/DBShifterHelpPage">https://twiki.cern.ch/twiki/bin/viewauth/CMS/DBShifterHelpPage</a> if it does not work; availability depends on the state of the LHC).';
    
    results(
          '<p class="error">' + msg + '</p>'
        + '<p class="error">' + contacthelp + '</p>'
    );
}

function ajax_error(xhr, textStatus, errorThrown) {
    var genericmsg = 'Please try again later. If the error persists, please reload the entire page (F5).';

    if (xhr.status == 0)
        error('Lost connection? Please check your network. ' + genericmsg);

    else if (xhr.status >= 500 && xhr.status < 600)
        error('Server error ' + xhr.status + '. ' + genericmsg + '. However, if you think this is a bug in the server, please report it (see below).');

    else if (errorThrown == 'timeout')
        error('Request timed out. ' + genericmsg);

    else
        error('Unknown error. ' + genericmsg);
}

function post(url, data, success) {
    working();
    $.ajax({
        url: url,
        type: 'post',
        data: data,
        success: success,
        error: ajax_error,
    });
}

function dataTable(data, searchString) {
    var aoColumns = [];

    $.each(data['headers'], function(index, value) {
        aoColumns.push({'sTitle': value});
    });

    // Escape HTML and highlight results
    var highlightRegexp = new RegExp(escapeRegExp(escapeHTML(searchString)), 'ig');
    $.each(data['data'], function(rowIndex, row) {
        $.each(row, function(columnIndex, cell) {
            row[columnIndex] = highlight(highlightRegexp, escapeHTML(cell));
        });
    });

    return {
        'bJQueryUI': true,
        'sPaginationType': 'full_numbers',
        'iDisplayLength': 10,
        'aaData': data['data'],
        'aoColumns': aoColumns,
    };
}

$('#search').submit(function() {
    firsttime();
    var string = $('#search input').val();
    post('search', { 'string': string }, function(data) {
        $('#results').html(
              '<h2>Tags</h2>'
            + '<table id="tags"></table>'
            + '<h2>Payloads</h2>'
            + '<table id="payloads"></table>'
            + '<h2>Global Tags</h2>'
            + '<table id="gts"></table>'
        );
        $('#tags').dataTable(dataTable(data['tags'], string));
        $('#payloads').dataTable(dataTable(data['payloads'], string));
        $('#gts').dataTable(dataTable(data['gts'], string));
    });
    return false;
});

$('#upload').submit(function() {
    firsttime();
    error('Unimplemented feature.');
    return false;
});

$('#help').submit(function() {
    firsttime();
    error('Unimplemented feature.');
    return false;
});

$('#search input').focus();

var _firsttime = true;
function firsttime()
{
    if (!_firsttime)
        return;

    _firsttime = false;

    $('.firsttime').each(function() {
        $(this).removeClass('displaynone moveddown');
    });
}

