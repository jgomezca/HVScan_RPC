"use strict";

function setDefault(argument, defaultValue) {
    return (typeof argument == 'undefined' ? defaultValue : argument);
}

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

function configureDataTable(data, highlightString) {
    var aoColumns = [];
    $.each(data['headers'], function(index, value) {
        aoColumns.push({'sTitle': value});
    });

    // Escape HTML and highlight results
    if (highlightString != null)
        var highlightRegexp = new RegExp(escapeRegExp(escapeHTML(highlightString)), 'ig');

    $.each(data['data'], function(rowIndex, row) {
        $.each(row, function(columnIndex, cell) {
            var cell = escapeHTML(cell);

            if (highlightString != null)
                cell = highlight(highlightRegexp, cell);

            row[columnIndex] = cell;
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

function buildDataTable(type, title, data, highlightString, list) {
    $('#' + type).dataTable(configureDataTable(data, highlightString));

    var header =
          '<div class="tableHeaderContainer">'
        + '<h2>' + title + '</h2>'
    ;

    if (list == true)
        header +=
              '<button class="list" title="List" data-type="' + type + '"><span>List</span></button>'
            + '<button class="diff" title="Diff" data-type="' + type + '"><span>Diff</span></button>'
        ;

    header +=
        '</div>'
    ;

    $('#' + type + '_wrapper > :first-child').append(header);
}

function hashstringify(data) {
    return '#' + $.map(data, function(value) { return encodeURIComponent(value); }).join('/');
}

function hashparse(data) {
    if (data == null)
        return null;

    if (data.length < 2)
        return null;

    if (data[0] != '#')
        return null;

    return $.map(data.split('#')[1].split('/'), function(value) { return decodeURIComponent(value); });
}

function pushHistory(state) {
    history.pushState(null, null, hashstringify(state));
}

$(window).on('hashchange', function() {
    runFromHash();
});

function runFromHash() {
    var state = hashparse(location.hash);

    if (state == null) {
        resetfirsttime();
        return;
    }

    run(state, false);
}

function run(state, pushToHistory) {
    pushToHistory = setDefault(pushToHistory, true);

    if (pushToHistory == true)
        pushHistory(state);

    firsttime();

    var action = state[0];
    if (action == 'search')
        return action_search(state[1], state[2]);
    else if (action == 'upload')
        return action_upload(state[1]);
    else if (action == 'help')
        return action_help();
    else if (action == 'list')
        return action_list(state[1], state[2], state[3]);
    else if (action == 'diff')
        return action_diff(state[1], state[2], state[3], state[4]);

    error('Unrecognized action. This happened because either the link is wrong (e.g. "#bad/a/b/c") or because the loaded version of the application is too old (in this case, try to reload the page completely: <a href="/browser/">Reload</a>).');
}

function action_search(database, string) {
    setDatabase(database);
    $('#search input').val(string);

    post('search', {
        'database': database,
        'string': string,
    }, function(data) {
        $('#results').html(
            '<table id="tags"></table>'
            + '<table id="payloads"></table>'
            + '<table id="gts"></table>'
        );

        buildDataTable('tags', 'Tags', data['tags'], string, true);
        buildDataTable('payloads', 'Payloads', data['payloads'], string, false);
        buildDataTable('gts', 'Global Tags', data['gts'], string, true);
    });
}

var _database = 'Production';
var _databases = ['Development', 'Integration', 'Archive', 'Production'];

function getDatabase() {
    return _database;
}

function setDatabase(database) {
    _database = database;
    $('#database > span').html(_database);
}

function nextDatabase() {
    setDatabase(_databases[(_databases.indexOf(_database) + 1) % _databases.length]);
}

function action_upload(database) {
    setDatabase(database);
    error('Unimplemented feature.');
}

function action_help() {
    error('Unimplemented feature.');
}

function action_list(database, type, item) {
    setDatabase(database);
    
    post('list_', {
        'database': database,
        'type_': type,
        'item': item,
    }, function(data) {
        $('#results').html(
            '<table id="list"></table>'
        );

        buildDataTable('list', 'List', data, null, false);
    });
}

function action_diff(database, type, first, second) {
    error('Unimplemented feature.');
    return;

    setDatabase(database);

    post('diff', {
        'database': database,
        'type_': type,
        'first': first,
        'second': second,
    }, function(data) {
        $('#results').html(
            '<table id="diff"></table>'
        );
    });
}

$('#search').submit(function() {
    var string = $('#search input').val();

    run(['search', getDatabase(), string]);
    return false;
});

$('#database').click(function() {
    nextDatabase();
    return false;
});

$('#upload').click(function() {
    run(['upload', getDatabase()]);
    return false;
});

$('#help').click(function() {
    run(['help']);
    return false;
});

$('#results').on('click', '.list', function() {
    var type = $(this).data('type');
    var selectedRows = getSelectedRows(type);

    if (selectedRows.length < 1) {
        alert('Please select at least one row in the table.');
        return false;
    }

    if (selectedRows.length > 1) {
        alert('Please select at most one row in the table.');
        return false;
    }

    var item = selectedRows.first().text();

    run(['list', getDatabase(), type, item]);
    return false;
});

$('#results').on('click', '.diff', function() {
    var type = $(this).data('type');
    var selectedRows = getSelectedRows(type);

    if (selectedRows.length < 2) {
        alert('Please select at least two rows in the table.');
        return false;
    }

    if (selectedRows.length > 2) {
        alert('Please select at most two rows in the table.');
        return false;
    }

    var first = selectedRows.eq(0).first().text();
    var second = selectedRows.eq(1).first().text();

    run(['diff', getDatabase(), type, first, second]);
    return false;
});

function getSelectedRows(type) {
    return $('#' + type + ' .selectedRow > :first-child');
}

var selectedRowClass = 'selectedRow';
$('#results').on('click', 'tbody tr', function() {
    var t = $(this);

    // Do not select if the table is empty
    if (t.children('.dataTables_empty').length > 0)
        return false;

    if (t.hasClass(selectedRowClass))
        t.removeClass(selectedRowClass);
    else
        t.addClass(selectedRowClass);

    return false;
});

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

function resetfirsttime()
{
    _firsttime = true;
    $('#results, hr').addClass('firsttime displaynone');
    $('header').addClass('firsttime moveddown');
    $('#search input').val('');
}

$('#search input').focus();

runFromHash();

