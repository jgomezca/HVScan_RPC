#################################################
#######   Author: Edvardas Belanas
#################################################

class PopConJsonToHTML:

    def __init__(self):
        self.msg = ''
        self.data_list = []
        self.short_tail = 'short tail'
        self.long_tail = 'long tail'
        self.error_check = 0
        temp = """ 

    def html_template(self, _dict={}):
        self.msg += '<ul class="ui-helper-reset ui-tabs-nav ui-helper-clearfix ui-widget-header ui-corner-all">\n'
        for key in _dict:
            _file_name = key
            self.data_list = _dict[key]
            self.error_check = self.data_list[4]['error']
            self.msg += '''    <li id="_%s">
        <a href="#%s">%s</a>
            <div class="error%s"></div>
    </li>
''' % (_file_name, _file_name, _file_name, self.error_check)
        self.msg += '</ul>\n'
        for key in _dict:
            _file_name = key
            self.data_list = _dict[key]
            self.short_tail = self.data_list[2]
            self.long_tail = self.data_list[3]
            self.msg += '''<div id="%s" class="ui-tabs-panel ui-widget-content ui-corner-bottom">
        <table class="sort_table">
            <tbody>
                <tr>
                    <td style="max-width: 80px;">
                        <div style="height: 400px;">
                            %s
                    </td>
                    <td>
                        <div style="height: 400px;">
                            %s
                    </td>
                </tr>
            </tbody>
        </table>
</div>
''' % (_file_name, self.short_tail, self.long_tail)
 
        return self.msg
 """
    def html_template(self, _dict={}):
        self.msg += '''<table id="data_table">
    <th></th>
    <th>State</th>
    <th>Name</th>
    <th>Crontime(hr)</th>
    <th>Short tail</th>'''
        for key in _dict:
            _file_name = key
            self.data_list = _dict[key]
            self.cronjob_time_ms = self.data_list[0]
            self.cronjob_time_hr = self.data_list[1]
            self.short_tail = self.data_list[2]
            self.long_tail = self.data_list[3]
            self.error_check = self.data_list[4]['error']
            self.msg += '''    <tr>
        <td><div class="icon"></div></td>
        <td><div class="error%s"></div></td>
        <td>%s</td>
        <td>%s</td>
        <td><div class="short_tail">%s</div></td>
    </tr>
    <tr>
        <td colspan="5">
            <div class="the_long_tail">
                <br><b>File name:</b> %s
                <br><b>Crontime (ms):</b> %s
                <br><b>Long tail:</b> %s
            </div>
        </td>
    </tr>
''' % (self.error_check, _file_name, self.cronjob_time_hr, self.short_tail, _file_name, self.cronjob_time_ms, self.long_tail)
        self.msg += '</table>'
        return self.msg

if __name__ == "__main__":
    import sys
    c = PopConJsonToHTML()
    c.html_template({})




