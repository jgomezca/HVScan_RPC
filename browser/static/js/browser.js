"use strict";

function set_default(argument, default_value) {
    return (typeof argument == 'undefined' ? default_value : argument);
}

var escape_HTML_map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
};

var escape_HTML_regexp_keys = '';
$.each(escape_HTML_map, function(index, value) {
    escape_HTML_regexp_keys += index;
});

var escape_HTML_regexp = new RegExp('[' + escape_HTML_regexp_keys + ']', 'g');

function escape_HTML(string) {
    if (string == null)
        return '';

    return ('' + string).replace(escape_HTML_regexp, function(match) {
        return escape_HTML_map[match];
    });
};

function escape_regexp(string) {
    if (string == null)
        return '';

    return ('' + string).replace(/[\-\[\]{}()*+?.,\\\^$|#\s]/g, '\\$&');
}

function highlight(highlight_regexp, string) {
    if (string == null)
        return '';

    return ('' + string).replace(highlight_regexp, '<span class="highlight">$&</span>');
}

function at_least_two_digits(n) {
    if (n < 10)
        return '0' + n;
    return n;
}

function get_iso_timestamp(){
    var d = new Date();
    return d.getFullYear()
        + '-' + at_least_two_digits(d.getMonth() + 1)
        + '-' + at_least_two_digits(d.getDate())
        + ' ' + at_least_two_digits(d.getHours())
        + ':' + at_least_two_digits(d.getMinutes())
        + ':' + at_least_two_digits(d.getSeconds())
    ;
}

function set_container(what, html) {
    return $(what).html(
          "<div class='container'>"
        + "    <div class='row'>"
        + "        <div class='col-md-12'>"
        + html
        + "        </div>"
        + "    </div>"
        + "</div>"
    );
}

function working() {
    return set_container('#main', "<p class='working'>Fetching results...</p>");
}

function clear_alerts() {
    return $('#alerts').empty();
}

function set_alert(level, msg) {
   return set_container('#alerts',
          "<div class='hidden alert alert-" + level + " alert-in-top'>"
        + "    <span class='alert-timestamp pull-right'><span class='glyphicon glyphicon-time'></span>&nbsp; <em>" + get_iso_timestamp() + "</em></span>"
        + "    " + msg
        + "</div>"
    ).find('.alert').hide().removeClass('hidden').fadeIn('slow');
}

function success(msg) {
    return set_alert('success', "<p>" + escape_HTML(msg) + "</p>");
}

function info(msg) {
    return set_alert('info', "<p>" + escape_HTML(msg) + "</p>");
}

function warning(msg) {
    return set_alert('warning', "<p>" + escape_HTML(msg) + "</p>");
}

function error(msg) {
    return set_alert('danger', "<p>" + escape_HTML(msg) + "</p>");
}

function critical(msg) {
    return set_alert('critical',
          "<p>Critical Error: " + escape_HTML(msg) + "</p>"
        + "<p>If you need assistance or you found a bug, please write an email to <a href='mailto:cms-cond-dev@cern.ch'>cms-cond-dev@cern.ch</a> and <a href='mailto:cms-offlinedb-exp@cern.ch'>cms-offlinedb-exp@cern.ch</a>. If you need immediate/urgent assistance, you can call the Offline DB expert on call (+41 22 76 70817, or 70817 from CERN; check <a href='https://twiki.cern.ch/twiki/bin/viewauth/CMS/DBShifterHelpPage'>https://twiki.cern.ch/twiki/bin/viewauth/CMS/DBShifterHelpPage</a> if it does not work; availability depends on the state of the LHC).</p>"
    );
}

function ajax_error(xhr, textStatus, errorThrown) {
    var genericmsg = 'Please try again later. If the error persists, please reload the entire page (F5).';

    if (xhr.status == 0)
        critical('Lost connection? Please check your network. ' + genericmsg);

    else if (xhr.status >= 500 && xhr.status < 600)
        critical('Server error ' + xhr.status + '. ' + genericmsg + '. However, if you think this is a bug in the server, please report it (see below).');

    else if (errorThrown == 'timeout')
        critical('Request timed out. ' + genericmsg);

    else
        critical('Unknown error. ' + genericmsg);
}

function get(url, data, success) {
    working();
    $.ajax({
        url: url,
        type: 'get',
        data: data,
        success: success,
        error: ajax_error,
    });
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

function get_page(url) {
    get(url, {
    }, function(data) {
        $('#main').html(data);
    });
}

function configure_data_table(data, highlight_string) {
    var aoColumns = [];
    $.each(data['headers'], function(index, value) {
        aoColumns.push({'sTitle': value});
    });

    // Escape HTML and highlight results
    if (highlight_string != null)
        var highlight_regexp = new RegExp(escape_regexp(escape_HTML(highlight_string)), 'ig');

    $.each(data['data'], function(row_index, row) {
        $.each(row, function(column_index, cell) {
            var cell = escape_HTML(cell);

            if (highlight_string != null)
                cell = highlight(highlight_regexp, cell);

            row[column_index] = cell;
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

function build_data_table(type, data, highlight_string) {
    $('#' + type).dataTable(configure_data_table(data, highlight_string));
}

function hash_stringify(data) {
    return '#' + $.map(data, function(value) {
        return encodeURIComponent(value);
    }).join('/');
}

function hash_parse(data) {
    if (data == null)
        return null;

    if (data.length < 2)
        return null;

    if (data[0] != '#')
        return null;

    return $.map(data.split('#')[1].split('/'), function(value) {
        return decodeURIComponent(value);
    });
}

function push_history(state) {
    history.pushState(null, null, hash_stringify(state));
}

$(window).on('hashchange', function() {
    run_from_hash();
});

function run_from_hash() {
    run(hash_parse(location.hash), false);
}

function run(state, push_to_history) {
    clear_alerts();

    state = set_default(state, '');
    push_to_history = set_default(push_to_history, true);

    if (push_to_history == true)
        push_history(state);

    // First time, or back to home via the navbar's brand or run() without args
    if (state == null || state == '')
        return action_news();

    var action = state[0];
    if (action == 'search')
        return action_search(state[1], state[2]);
    else if (action == 'tutorial')
        return action_tutorial();
    else if (action == 'upload')
        return action_upload();
    else if (action == 'list')
        return action_list(state[1], state[2], state[3]);
    else if (action == 'diff')
        return action_diff(state[1], state[2], state[3], state[4]);

    critical('Unrecognized action. This happened because either the link is wrong (e.g. "#bad/a/b/c") or because the loaded version of the application is too old (in this case, try to reload the page completely: <a href="/browser/">Reload</a>).');
}

function action_news() {
    get_page('news');
}

function action_search(database, string) {
    set_database(database);
    $('#search input').val(string);

    post('search', {
        'database': database,
        'string': string,
    }, function(data) {
        $('#main').html(
              "<div class='col-md-12'>"
            + "    <h2>Global Tags <button class='btn btn-danger list' data-type='gts'><span class='glyphicon glyphicon-list'></span> <span>List</span></button> <button class='btn btn-danger diff' data-type='gts'><span class='glyphicon glyphicon-pause'></span> <span>Diff</span></button></h2><table id='gts'></table>"
            + "    <h2>Tags <button class='btn btn-danger list' data-type='tags'><span class='glyphicon glyphicon-list'></span> <span>List</span></button> <button class='btn btn-danger diff' data-type='tags'><span class='glyphicon glyphicon-pause'></span> <span>Diff</span></button></h2><table id='tags'></table>"
            + "    <h2>Payloads</h2><table id='payloads'></table>"
            + "</div>"
        );

        build_data_table('gts', data['gts'], string);
        build_data_table('tags', data['tags'], string);
        build_data_table('payloads', data['payloads'], string);
    });
}

function get_database() {
    return $('#database').html();
}

function set_database(database) {
    return $('#database').html(database);
}

function action_tutorial() {
    get_page('static/html/tutorial.html');
}

function action_upload() {
    get_page('static/html/upload.html');
}

function action_list(database, type, item) {
    set_database(database);
    
    post('list_', {
        'database': database,
        'type_': type,
        'item': item,
    }, function(data) {
        $('#main').html(
              "<div class='col-md-12'>"
            + "    <h2>List</h2><table id='list'></table>"
            + "</div>"
        );

        build_data_table('list', data, null);
    });
}

function action_diff(database, type, first, second) {
    critical('Unimplemented feature.');
    return;

    set_database(database);

    post('diff', {
        'database': database,
        'type_': type,
        'first': first,
        'second': second,
    }, function(data) {
        $('#main').html(
            '<table id="diff"></table>'
        );
    });
}

$('#search').submit(function() {
    run(['search', get_database(), $('#search input').val()]);
    return false;
});

$('.database-selector').click(function() {
    $('#database').html($(this).html());
    return false;
});

$('#main').on('click', '.list', function() {
    var type = $(this).data('type');
    var selected_rows = get_selected_rows(type);

    if (selected_rows.length < 1) {
        error('Please select at least one row in the table.');
        return false;
    }

    if (selected_rows.length > 1) {
        error('Please select at most one row in the table.');
        return false;
    }

    var item = selected_rows.first().text();

    run(['list', get_database(), type, item]);
    return false;
});

$('#main').on('click', '.diff', function() {
    var type = $(this).data('type');
    var selected_rows = get_selected_rows(type);

    if (selected_rows.length < 2) {
        error('Please select at least two rows in the table.');
        return false;
    }

    if (selected_rows.length > 2) {
        error('Please select at most two rows in the table.');
        return false;
    }

    var first = selected_rows.eq(0).first().text();
    var second = selected_rows.eq(1).first().text();

    run(['diff', get_database(), type, first, second]);
    return false;
});

var selected_row_class = 'selectedRow';

function get_selected_rows(type) {
    return $('#' + type + ' .' + selected_row_class + ' > :first-child');
}

$('#main').on('click', 'tbody tr', function() {
    var t = $(this);

    // Do not select if the table is empty
    if (t.children('.dataTables_empty').length > 0)
        return false;

    if (t.hasClass(selected_row_class))
        t.removeClass(selected_row_class);
    else
        t.addClass(selected_row_class);

    return false;
});

$('#search input').focus();

run_from_hash();

