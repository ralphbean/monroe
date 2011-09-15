/**
 * JavaScript to support Ajax lookups
 **/
var twd_popup_data  = null;
var twd_popup_node  = null;
var twd_popup_elem  = null;
var twd_proc_req    = null;
var twd_proc_node   = null;
var twd_onfocus_val = {};
var twd_onfocus_id  = {};

function twd_find_node(node, suffix)
{
    var prefix = node.id.substr(0, node.id.lastIndexOf("_") + (suffix ? 1 : 0));
    return document.getElementById(prefix + suffix);
}

function twd_set_id(node, newid)
{
    var idnode = twd_find_node(node, '');
    var oldid = idnode.value;
    idnode.value = newid;
    if(newid != oldid && idnode.onchange)
        idnode.onchange();
    return oldid;
}

function twd_ajax_onfocus(self)
{        
    twd_onfocus_val[self.id] = self.value;
    twd_onfocus_id[self.id] = twd_set_id(self, '');
    twd_set_style(self, 0);
}

function twd_ajax_onblur(self, evt, ajaxurl)
{
    if(self.value == twd_onfocus_val[self.id] && twd_onfocus_id[self.id])
    {
        twd_set_id(self, twd_onfocus_id[self.id]);
        twd_set_style(self, 1);
    }
    else
    {
        if(self.value != '')
        {
            if(twd_proc_req)
            {
                set_style(self, 2);
                alert('A search is already in progress; please let it complete before making another.');
                return;
            }
            twd_set_style(self, 3);
            twd_proc_node = self;
            if(window.ActiveXObject)
                twd_proc_req = new ActiveXObject("Microsoft.XMLHTTP");
            else
                twd_proc_req = new XMLHttpRequest();
            twd_proc_req.onreadystatechange = twd_process_response;
            twd_proc_req.open("POST", ajaxurl, true);
            twd_proc_req.setRequestHeader("Content-Type", "application/x-www-form-urlencoded")
            twd_proc_req.send("search=" + escape(twd_find_node(self, 'entry').value));
        }
    }
}

function twd_process_response()
{
    if(twd_proc_req.readyState != 4) return;
    if(twd_proc_req.status != 200)
    {
        twd_set_style(twd_proc_node, 2);
        twd_proc_req = null;
        twd_proc_node = null;
        alert('Server error processing request');
        return;
    }
    var data = eval('x=' + twd_proc_req.responseText);
    if(data['status'] != 'Successful')
    {
        twd_set_style(twd_proc_node, 2);
        alert(data['status']);
    }
    else if(data['data'].length == 0)
        twd_set_style(twd_proc_node, 2);
    else if(data['data'].length == 1)
    {
        var data = data['data'][0];
        twd_find_node(twd_proc_node, 'entry').value = data['value'];
        twd_set_id(twd_proc_node, data['id']);
        twd_set_style(twd_proc_node, 1);
    }
    else if(twd_popup_data)
    {
        twd_set_style(twd_proc_node, 2);
        alert('Please select a contact from the open popup before performing another search.');
    }
    else
    {
        twd_popup_node = twd_proc_node;
        twd_popup_data = data;
        twd_raise_popup();
    }

    twd_proc_req = null;
    twd_proc_node = null;
}

/**
 *  0 - editing
 *  1 - matched
 *  2 - problem
 *  3 - working
 **/
function twd_set_style(node, num)
{
    var entry = twd_find_node(node, 'entry');
    entry.disabled = num == 3;
    entry.style.backgroundColor = num == 2 ? 'red' : 'white';
    entry.style.textDecoration = num == 1 ? 'underline' : '';
}

function twd_raise_popup()
{
    var html = "<table class='popup' onclick='event.cancelBubble = true'>";
    for(var i = 0; i < twd_popup_data['data'].length; i++)
    {
        var d = twd_popup_data['data'][i];
        html += "<tr><td><a href='pick' onclick='twd_pick_contact(" + i + "); return false;'>"
                 + d['id'] + "</a></td><td>" + d['value'] + "</td>" +
                 (d['extra'] ? "<td>"+d['extra']+"</td>" : "") + "</tr>";
    }
    html += "<tr><td><a href='cancel' onclick='twd_cancel_popup(); return false;'>Cancel</a></td></tr></table>";
    twd_popup_elem = document.createElement('TR');
    twd_popup_elem.appendChild(document.createElement('TD'));
    twd_popup_elem.firstChild.colSpan = 10; // This should be wide enough to cover all tables in practice
    twd_popup_elem.firstChild.innerHTML = html;
    var tr_node = twd_popup_node;
    while(tr_node.tagName != 'TR')
        tr_node = tr_node.parentNode;
    tr_node.parentNode.insertBefore(twd_popup_elem, tr_node.nextSibling);
}

function twd_pick_contact(i)
{
    var data = twd_popup_data['data'][i];
    twd_find_node(twd_popup_node, 'entry').value = data['value'];
    twd_set_id(twd_popup_node, data['id']);
    twd_set_style(twd_popup_node, 1);
    twd_hide_popup();
}

function twd_cancel_popup()
{
    twd_set_style(twd_popup_node, 2);
    twd_hide_popup();
}

function twd_hide_popup()
{
    twd_popup_elem.parentNode.removeChild(twd_popup_elem);
    twd_popup_data = null;
    twd_popup_node = null;
    twd_popup_elem = null;
}
