/** An rmStats object is an interface to the stats xml data
    There are various methods for getting data from the xml 
    in an easy to display format.

    interface details:

    find(path) - gets the xmlNode with the path under the current frame
    getText(path) - gets the text of the xml node at path (no formating)
    get(path) - returns the string representation of the node at path
        for example, passing in a Memory type node will return a "50.0mb" string
    count(path) - returns the count of the path specified
    getAttr(attrName) - returns the attr at the current node
    getArray(path) - gets an array of the children of path 
    getTag(path) - gets the tag of the current node

    --- Immediate methods (if you want to use this in a view file, 
            simply wrap in a function() { return rmStats.foo();}   )
    renderTable(
                rows - a list of xmlNodes to render as rows
                headers - column headers (strings)
                row columns - where to find the data for each column of a row
                )

        *** Should probably NOT be used in view files!!! ***
        getFrameNames() - get the array of frames in the stats xml
        setCurrentFrame(frameName) - set the current frame to the one specified
        pushd(xmlNode) - adds the xmlnode to the cursor stack
        popd() - pops the cursor stack


*/
var buttonOff = "<strong>+</strong>";
var buttonOn = "<strong>-</strong>";


function RMStats(xmlData) {
    this.xml = $(xmlData);
    this.currentFrame = this.xml.children().first();
    this.cursorStack = new Array(this.currentFrame);
}

//get the list of name of frames in the xml
RMStats.prototype.getFrameNames = function() {
    var frameNames = [];
    this.xml.find("stats[kind='frame']").each(function() {
        frameNames.push($(this).attr('name'));
    });
    return frameNames;
};

RMStats.prototype.getTabs = function() {
    var tabNames = [];
    this.xml.find("stats[kind='frame']").first().children().each(function() {
        tabNames.push($(this).attr('name'));
    });
    return tabNames;
};

//sets the current frame to the name specified
RMStats.prototype.setCurrentFrame = function(frameName) {
    this.currentFrame = this.xml.children("[name='" + frameName + "']");
    this.cursorStack = [this.currentFrame];
};

//append the xmlNode at path to the cursor stack
RMStats.prototype.pushd = function(path) {
    //console.debug("pushing " + path + " to cursor stack");
    if(typeof path == 'string') {
        var node = rmStats.find(path);
        if(node)
            this.cursorStack.push(node);
        else
            this.lastNotFound = true;
    }
    else  //else if this in an xml node
        this.cursorStack.push($(path));
};

//append the xmlNode at path to the cursor stack
RMStats.prototype.current = function() {
    return this.cursorStack[this.cursorStack.length - 1];
};

//pops the last xmlNode off the cursor stack
RMStats.prototype.popd = function() {
    //console.debug("popping cursor stack");
    if(this.lastNotFound == true) {
        this.lastNotFound = false;
    }
    else
        this.cursorStack.pop();
    
    
};

/*finds an xmlNode lazily based on a path.  Note that a path starting with '/'
 begins at the current frame.  Use [1] to select the first child... 
 * for list.  Generally we use the "name" attribute to specify structure.  
 So /memory/raytrace is the same as /stats[name=memory]/stats[name=raytrace] */
RMStats.prototype.find = function(path, skipErrors) {
    //console.debug("path requested " + path);
    var paths = path.split("/");
    var current = this.current();
    if(path.charAt(0) == '/') {
        current = this.currentFrame;
    }
  
    for(i in paths) {
        var pathElm = paths[i];
        if(pathElm == '.' || pathElm == '') {
            continue;
        }
          
        if(pathElm == '..') {
            current = current.parent();
            continue;
        }

        //if this elm is an array index...
        if(pathElm.charAt(0) == '[') {
          var index = parseInt(pathElm.slice(1,-1));
          //for some reason jquery array indexes at 1.
          current = current.children(':nth-child(' + (index + 1) + ')');
          //console.debug("found " + current.attr('name'));
        }
        else {
            if(pathElm == '*') {
                // this is asking for a list
                //console.debug("returning list");
                return current.children();
            }
            else {
                //actually select something
                if(current.children("[name='" + pathElm + "']").length > 0){
                    current = current.children("[name='" + pathElm +
                                               "']");
                    //console.debug("found " + pathElm);
                }
                else {
                    if(current.children(pathElm).length > 0)
                        current = current.children(pathElm);
                    else {
                        if (!skipErrors)
                            console.warn("Couldn't find " + pathElm + 
                                     " in path " + path + " currently at " +
                                     current.attr('name'));
                        return null;
                    }
                }
            }
        }
    }
    return current;
};

//returns true if stats is in ris mode
RMStats.prototype.isRISmode = function() {
    return this.xml.find('stats[name="integrator"]').length > 0;
};

//returns build id
RMStats.prototype.getBuildID = function() {
    var buildStr = rmStats.getValue('/options/linkTime');
    var tokens = buildStr.split(" ");
    return tokens[tokens.length-1];
};

//returns the render date
RMStats.prototype.getRenderDate = function() {
    var buildStr = rmStats.getValue('/options/timestamp');
    var d = new Date(buildStr);
    return d.toLocaleDateString();
};

//returns the render date
RMStats.prototype.getRenderTime = function() {
    var buildStr = rmStats.getValue('/options/timestamp');
    var d = new Date(buildStr);
    return d.toLocaleTimeString();
};


//get the text of the path specified
RMStats.prototype.getText = function(path) {
    var node = this.find(path);
    if (node) {
        //console.log(node.html());
        return node.text();
    }
    return "";
};

//get the text of the path specified
RMStats.prototype.getFloat = function(path) {
    var node = this.find(path);
    if (node) 
        return parseFloat(node.text());
    return 0.0;
};
//get the text of the path specified
RMStats.prototype.getInt = function(path) {
    var node = this.find(path);
    if (node) 
        return parseInt(node.text());
    return 0;
};

//get the value of the path specified - native type converted to text
RMStats.prototype.getValue = function(path, type) {
    rmStats.pushd(path);
    var val = null;
    if (typeof type === 'undefined') { type = rmStats.getTag(); }
    switch(type) {
        case "string":
            val = this.current().text().trim();
            break;
        case "memory":
            val = this.getInt("peak");
            break;
        case "timer":
            val = this.getFloat("elapsed");
            break;
        case "int":
            val = this.getInt(".");
            break;
        case "float":
            val = this.getFloat(".");
            break;
        case "bin":
            val = this.getFloat(".");
            break;
    }
    rmStats.popd();
    return val;
};

//get the value of the path specified - native type converted to text
RMStats.prototype.toString = function(xmlNode) {
    rmStats.pushd(xmlNode);
    var str = ''
    var type = rmStats.getTag();
    switch(type) {
        case "string":
            str = rmStats.getText(".");
            break;

        case "memory":
            str = rmStats.format( {
                    value: rmStats.getInt("peak"),
                    style: 'bytes' });
            break;
        case "peak":
            str = rmStats.format( {
                    value: rmStats.getInt("."),
                    style: 'bytes' });
            break;
        case "current":
            str = rmStats.format( {
                    value: rmStats.getInt("."),
                    style: 'bytes' });
            break;
        case "timer":
            str = rmStats.format( {
                value: rmStats.getFloat("elapsed"),
                style: "seconds"
            });
            break;
        case "elapsed":
            str = rmStats.format( {
                value: rmStats.getFloat("."),
                style: "seconds"
            });
            break;
        case "user":
            str = rmStats.format( {
                value: rmStats.getFloat("."),
                style: "seconds"
            });
            break;
        case "system":
            str = rmStats.format( {
                value: rmStats.getFloat("."),
                style: "seconds"
            });
            break;
        case "int":
            str = rmStats.format( {
                value: rmStats.getInt("."),
                style: "int", 
                shorten: true
            });
            break;
        case "float":
            str = rmStats.format( {
                value: rmStats.getFloat("."),
                style: "float", 
                shorten: true
            });
            break;

        case "stats":
            str += "<H5>" + rmStats.getName('.') + "</H5>";
            rows = [];
            rmStats.current().children().each(
                function() {
                    rmStats.pushd(this);
                    var desc = rmStats.getDesc('.');
                    if(desc)
                        rows.push([rmStats.getDesc('.'), rmStats.toString('.')]);
                    else
                        rows.push([rmStats.getName('.'), rmStats.toString('.')]);
                    rmStats.popd();
                }
            )
            str += rmStats.renderSimpleTable(rows);
            break;
        
    }
    rmStats.popd();
    return str;
};

RMStats.prototype.getDesc = function(path) {
    if (!path) path = ".";
    rmStats.pushd(path)
    var desc =rmStats.getAttr("description");
    rmStats.popd();
    return desc;
}

RMStats.prototype.getWallTime = function() {
    return rmStats.getFloat("/time/timers/totaltime/elapsed");
}

RMStats.prototype.getThreads = function() {
    return rmStats.getInt("/options/threads");
}

RMStats.prototype.getCPUTime = function() {
    return ( rmStats.getFloat('/time/timers/totaltime/system') +
            rmStats.getFloat('/time/timers/totaltime/user'));
}

//get the value of the path specified - native type converted to text
RMStats.prototype.format = function(data) {
    var style = data.style;
    var value = data.value
    var str = value;
    switch(style) {
        case "percent":
            if(isNaN(value))
                value = 0;
            str =  "" + (value*100.0).toFixed(2) + "%"; 
            break;
        case "bytes":
            str = this.formatBytes(value);
            break;
        case "seconds":
            str =  "" + value.toFixed(2) + " s";
            break;
        case "milliseconds":
            str =  "" + (value*1000.0).toFixed(4) + " ms";
            break;
        case "time":
            var hrs = ~~(value / 3600);
            var mins = ~~((value % 3600) / 60);
            var secs = (value % 60).toFixed(2);
            if(hrs == 0 && mins == 0)
                str = "" + secs + " s";
            else {
                str =  mins + ":";
                if(secs < 10)
                    str += "0" + secs;
                else
                    str += secs;
                if(hrs > 0)
                    str = "" + hrs + ":" + str;
            }
            break;
        case "float":
            str = "" + value.toFixed(2);
            break;
        case "int":
            if (data.size) {
                var smallVal = value;
                switch(data.size) {
                    case "k":
                        smallValue = (value / 1000.0).toFixed(1);
                        str = smallValue + " k";
                        break;
                    case "m":
                        smallValue = (value / 1000000.0).toFixed(1);
                        str = smallValue + " m";
                        break;
                    case "b":
                        smallValue = (value / 1000000000.0).toFixed(1);
                        str = smallValue + " b";
                        break;          
                    case "t":
                        smallValue = (value / 1000000000000.0).toFixed(1);
                        str = smallValue + " t";                    
                }
                str = "<span title='" + value + "'>" + str + "</span>";
            } 
            else {
                str = "" + value.toLocaleString();
            }
            break;
        case "note":
            str = "<div class='alert alert-info'>" + value + "</div>";
            break;
        case "string":
            str = "<text>" + value + "</text>";
            break;
        case "string-line":
            str = "<text>" + value + "</text><br>";
            break;
    }
    if(data.textStyle) {
        switch(data.textStyle) {
            case "bold":
                str = "<strong>" + str + "</strong>";
                break;
        }
        
    }

    return str;

};

//convert a system time to wall time
RMStats.prototype.systemToWallTime = function(t) {
    return t * rmStats.getFloat('/time/timers/totaltime/elapsed') /
                ( rmStats.getFloat('/time/timers/totaltime/system') +
                    rmStats.getFloat('/time/timers/totaltime/user'));
};

//format bytes
RMStats.prototype.formatBytes = function(bytes) {
    /*if      (bytes>=1073741824) {bytes=(bytes/1073741824).toFixed(2)+' GB';}
    else if (bytes>=1048576)    {bytes=(bytes/1048576).toFixed(2)+' MB';}
    else if (bytes>=1024)       {bytes=(bytes/1024).toFixed(2)+' KB';}
    else if (bytes>1)           {bytes=bytes+' bytes';}
    else if (bytes==1)          {bytes=bytes+' byte';}
    else                        {bytes='0 bytes';}*/
    return (bytes/1048576).toFixed(2)+' MB';;
}

//get the count of children at path
RMStats.prototype.count = function(path) {
    return this.find(path).length;
};

RMStats.prototype.sum = function(array, sumFunc) {
    var sum = 0;
    if (sumFunc == null)
        sumFunc = function() {return rmStats.getValue('.');};

    $(array).each(function() {
        rmStats.pushd($(this));
        sum += sumFunc();
        rmStats.popd();
    });

    return sum;
};

RMStats.prototype.sort = function(array, sortFunc) {
    
    if (sortFunc == null)
        sortFunc = function() { return rmStats.getValue(".")};
    return $(array).sort(function(a,b) {
            rmStats.pushd(a);
            var dataA = sortFunc();
            rmStats.popd();

            rmStats.pushd(b);
            var dataB = sortFunc();
            rmStats.popd();
            return dataB - dataA;
        });

};

RMStats.prototype.filter = function(array, filterfunc) {
    return $(array).filter(function() {
        rmStats.pushd(this);
        var tf = filterfunc();
        rmStats.popd();
        return tf;
    });s
};

//get the attr with name at the current cursor
RMStats.prototype.getAttr = function(name) {
    return rmStats.current().attr(name);
};

//get the attr with name at the current cursor
RMStats.prototype.getName = function(path) {
    if(!path)
        path = ".";
    return rmStats.find(path).attr('name');
    
};

//get the parent of the current node.
RMStats.prototype.getParent = function() {
    return rmStats.current().parent();
};


//get the tag with name at the current cursor
RMStats.prototype.getTag = function() {
    return rmStats.current().prop("tagName").toLowerCase();
};

//get the children list of path
RMStats.prototype.getArray = function(path) {
    //console.debug("getting array at path " + path);
    if (path instanceof Array) {
        var l = []
        for(i in path) {
            l.push(this.find(path[i]));
        }
        return $(l);
    }
    else
        return this.find(path).children();
};  

//renders a line from a string 
RMStats.prototype.renderLine = function(str) {
    return str + "<br/>";
}

//renders a set of lines from an array of strings
RMStats.prototype.renderLines = function(arr) {
    var str = "";
    for (var i = 0; i < arr.length - 1; ++i) 
        str += arr[i] + "<br/>";
    return str + arr[arr.length - 1];
}

//renders a line from a string 
RMStats.prototype.renderText = function(rows) {

    var text = "";
    $.each(rows, function() {
        text += rmStats.format({value:this, style:"string-line"});
    });
    return text;
}

//need these functions for sortable column types
jQuery.fn.dataTableExt.aTypes.unshift(
    function ( sData )
    {
        /* Check for size unit KB, MB or GB */
        if ( typeof sData == "string" && (sData.substring(sData.length - 2, sData.length) == "KB"
            || sData.substring(sData.length - 2, sData.length) == "MB"
            || sData.substring(sData.length - 2, sData.length) == "GB" ))
        {   
            return 'file-size';
        }
        if ( typeof sData == "string" && sData.substring(sData.length - 2, sData.length) == " s")
        {   
            return 'seconds';
        }

        return null;
    }
);

jQuery.fn.dataTableExt.oSort["percent-pre"] = function ( a ) {
        var x = (a == "-") ? 0 : a.replace( /%/, "" );
        return parseFloat( x );
};
 
jQuery.fn.dataTableExt.oSort["percent-asc"] = function ( a, b ) {
        return ((a < b) ? -1 : ((a > b) ? 1 : 0));
};

jQuery.fn.dataTableExt.oSort["percent-desc"] = function ( a, b ) {
        return ((a < b) ? 1 : ((a > b) ? -1 : 0));
};

jQuery.fn.dataTableExt.oSort["seconds-pre"] = function ( a ) {
        var x = (a == "-") ? 0 : a.replace( " s", "" );
        return parseFloat( x );
};
 
jQuery.fn.dataTableExt.oSort["seconds-asc"] = function ( a, b ) {
        return ((a < b) ? -1 : ((a > b) ? 1 : 0));
};

jQuery.fn.dataTableExt.oSort["seconds-desc"] = function ( a, b ) {
        return ((a < b) ? 1 : ((a > b) ? -1 : 0));
};


jQuery.fn.dataTableExt.oSort["file-size-pre"] = function ( a ) {
        var x = a.substring(0,a.length - 2);
        var x_unit = (a.substring(a.length - 2, a.length) == "MB" ?
            1000 : (a.substring(a.length - 2, a.length) == "GB" ? 1000000 : 1));
          
        return parseInt( x * x_unit, 10 );
};
 
jQuery.fn.dataTableExt.oSort["file-size-asc"] = function ( a, b ) {
        return ((a < b) ? -1 : ((a > b) ? 1 : 0));
};
 
jQuery.fn.dataTableExt.oSort["file-size-desc"] = function ( a, b ) {
        return ((a < b) ? 1 : ((a > b) ? -1 : 0));
};

//renders a table to html
RMStats.prototype.renderTable = function(tableData) {
    
    var thead = "<tr>";
    //var columnTotals = [];
    var columns = tableData.columns;
    var headers = tableData.headers;
    
    if(tableData.hasOwnProperty('style')) {
        switch(tableData.style) {
            case "timer":
                headers = ["Timer", "Time spent", "% Total"];
                var totaltime = ( rmStats.getFloat('/time/timers/totaltime/system') +
                    rmStats.getFloat('/time/timers/totaltime/user'));
                columns = [
                          function() {return rmStats.getAttr('description');},
                          function() {return rmStats.toString(".");},
                          function() {return rmStats.format(
                            {
                              value:rmStats.getFloat('elapsed') / totaltime,
                              style:'percent'
                            });}
                        ];
                break;
            case "timer_nototal":
                headers = ["Timer", "Time spent"];
                columns = [
                          function() {return rmStats.getAttr('description');},
                          function() {return rmStats.toString(".");},
                        ];
                break;
            case "timer_wallClock":
                headers = ["Timer", "Time spent", "% Total"];
                var totaltime = ( rmStats.getFloat('/time/timers/totaltime/system') +
                    rmStats.getFloat('/time/timers/totaltime/user'));
                columns = [
                          function() {return rmStats.getAttr('description');},
                          function() {return rmStats.format({
                            value:rmStats.systemToWallTime(rmStats.getFloat('elapsed')),
                            style:'seconds'
                          });},
                          function() {return rmStats.format(
                            {
                              value:rmStats.getFloat('elapsed') / totaltime,
                              style:'percent'
                            });}
                        ];
                break;
            case "memory":
                headers = ["Memory", "Peak Allocation", "% Total"];
                var totalmem = rmStats.getInt(
                                    '/memory/systemMem/peakResidentSize/peak');
                columns = [
                          function() {return rmStats.getAttr('description');},
                          function() {return rmStats.toString(".");},
                          function() {return rmStats.format(
                            {
                              value:rmStats.getInt('peak') / totalmem,
                              style:'percent'
                            });}
                        ];
                break;
        }

    }

    var aoColumns = []
    for(var i in headers) {
        aoColumns.push({mData:headers[i]});
        thead += ("<th>" + headers[i] + "</th>");
    }
    thead = "<thead>" + thead + "</thead>";
    var tbody = "<tbody>";
    
    var level = 0;
    var rowData = [];

    $.each(tableData.rows, function() {
        var rowArr = rmStats.getRowData(this, columns, headers, tableData.removeZeros);
        if(rowArr)
            rowData.push(rowArr);
    });
    /*$.each(rowData, function() {
        tbody += rmStats.renderTableRow(this);
    });*/
    
    tfoot = ""
    if (tableData.hasOwnProperty('totalRow')) {
        tfoot = "<tfoot>" + rmStats.renderTableRow({row: rmStats.getRowData(
                                                tableData.totalRow, columns, headers),
                                            doButton: false,
                                            isTotalRow: true,
                                            level: 0
                                        }) + "</tfoot>";

    }
    var table = "<table class='table table-striped table-condensed table-hover' width='100%' cellspacing='0'>";
    table += thead + "<tbody></tbody>" + tfoot + "</table>";

    function innerTable(oTable, nTr) {
                var aData = oTable.fnGetData(nTr);
                var sOut ="<table class='table inner table-striped table-condensed table-hover'><tbody></tbody></table";
                return $(sOut).dataTable({
                    "bAutoWidth": true ,
                    "bPaginate": false,
                    "bSort": false,
                    "fnDrawCallback": function ( oSettings ) {
                        $(oSettings.nTHead).hide();
                    },
                    "aaData": aData.children,
                    "aoColumns": aoColumns,
                 });
        };

    table = $(table).dataTable({
        "bPaginate": false,
        "aaSorting": [[1, "desc"]],
        "aaData": rowData,
        "aoColumns": aoColumns,
     });

    tableActions = function() {
        var nTr = $(this).parents('tr')[0];
        if(table.fnIsOpen(nTr)) {
            $(this).html(buttonOff);
            table.fnClose(nTr);
        }
        else {
            $(this).html(buttonOn); 
            table.fnOpen(nTr, innerTable(table, nTr), "inner");
        }

    };
    return table.on("click", ".table-button", tableActions);
};

RMStats.prototype.renderSimpleTable = function(rows,textscale) {
    // define textscale if it was omitted.
    if (textscale === undefined)
        textscale = 1.0
    tableStr = "<table style=\"font-size:"+textscale+"em\">";
    for(var y in rows) {
        tableStr += "<tr>";
        for(var x in rows[y]) {
            tableStr += "<td>" + rows[y][x] + "</td>";
        }
        tableStr += "</tr>";
    }
    return tableStr += "</table>";

} 

RMStats.prototype.renderTableRow = function(rowData) {
    var tr = "<tr ";
    if(rowData.isTotalRow) {
        tr += "class='totalRow'";
    }
    //tr += 'data-level="' + rowData.level + '"'
    //if(rowData.level > 0)
    //  tr += "style='display: none;'";
    tr += '>';

    for(var i in rowData.row) {
        var button = "";
        //if(rowData.doButton && i == 0)
        //  button = '<button type="button" class="table-button btn btn-default btn-xs">' + buttonOff + '</button> ';
        tr += "<td>" + button + rowData.row[i] + "</td>";
    }
        
    return tr + "</tr>";

}

RMStats.prototype.getRowData = function(row, columns, headers, removeZeros) {
    var rowData = row;
    var doButton = false;
    if(row instanceof Array) {
        var arr = {};
        for(var i in headers) {
            arr[headers[i]] = row[i];
        }
        return arr;
    }
    else if(rmStats.isLayout(row) && row.data('tableChildren'))
    {   
        doButton = true;
    }
    else {
        rowData = $(row);
        /*if(rowData.prop('tagName').toLowerCase() == "stats") {
            doButton = true;
        }*/
    }
    var arr = {};
    rmStats.pushd(rowData);
    for (var i in columns) {
        if(i == 0 && doButton) {
            arr[headers[i]] = rmStats.buttonHtml() + columns[i]();
            var children = rowData.data('tableChildren');
            arr['children'] = [];
            for(c in children) {
                var childRow = rmStats.getRowData(children[c], columns, headers, removeZeros);
                if(childRow)
                    arr.children.push(childRow);
            }
        }
        else 
            arr[headers[i]] = columns[i]();
    }
    if(removeZeros && rmStats.getValue('.') == 0)
        arr = null; 
    rmStats.popd();
    

    return arr;
    

}

RMStats.prototype.buildNodesFromSchema = function(nodeLayout, type, skipUnaccounted) {
    var builtNodes = [];
    for(var i in nodeLayout) {
        var newNode = rmStats.buildNode(nodeLayout[i], type);
        if(newNode)
            builtNodes.push(newNode)
    }
    
    if(!skipUnaccounted) {
        var otherNode = rmStats.otherNode(builtNodes, type);
        otherNode.attr('name', "Other" + type);
        otherNode.attr('description', "Unaccounted");
        builtNodes.push(otherNode);
    }
    
    return builtNodes;
}

RMStats.prototype.sumNodes = function(children, type) {
    var newNode = $("<" + type + "></" + type + ">");
    newNode.prop('tagName', type);
    var sum = rmStats.sum(children, function() {return rmStats.getValue('.');});
    switch(type) {
        case 'timer':
            var elapsed = $('<elapsed></elapsed>');
            elapsed.text(sum);
            newNode.append(elapsed);
            break;
        case 'memory':
            var peak = $('<peak></peak>');
            peak.text(sum);
            newNode.append(peak);
            break;
        case 'int':
            newNode.text(sum);
            break;
        
    }
    return newNode;
}

RMStats.prototype.buildNode = function(node, type) {
    var newNode = null;
    if (node.hasOwnProperty("children"))
    {
        var children = node.children;
        if(node.hasOwnProperty('path'))
            rmStats.pushd(node.path);
        var tableChildren = []
        for(i in children) {
            var child = rmStats.buildNode(children[i], type);
            if(child)   
                tableChildren.push(child);
        }
        
        newNode = rmStats.sumNodes(tableChildren, type);
        newNode.data('tableChildren', tableChildren);
        
        if(node.hasOwnProperty('path'))
            rmStats.popd();
        //copy and sum children to rowData
        
    }
    else {
        newNode = rmStats.find(node.path, true);
        if(!newNode)
            return null;
        else
            newNode = newNode.clone();
        //copy path, no attributes to rowData
    }
    if(node.hasOwnProperty("name")) {
        //set row and desc to name
        newNode.attr('name', node.name);
        newNode.attr('description', node.name);
    }
    return newNode;

}

RMStats.prototype.getTotalTime = function() {
    if(typeof rmStats.totalTime == "undefined")
        rmStats.totalTime = rmStats.getCPUTime();
    return rmStats.totalTime;
}

RMStats.prototype.getTotalMemory = function() {
    if(typeof rmStats.totalMemory == "undefined")
        rmStats.totalMemory = rmStats.getValue("/memory/systemMem/peakResidentSize");
    return rmStats.totalMemory;
}

RMStats.prototype.buttonHtml = function() {
    return '<button type="button" class="table-button btn btn-default btn-xs">' + buttonOff + '</button> ';
}

RMStats.prototype.isLayout = function(obj) {
    if (obj instanceof jQuery && (obj.data('tableChildren')))
        return true;
    return false;
}

RMStats.prototype.otherNode = function(others, type) {
    var newNode = $("<" + type + "></" + type + ">");
    newNode.prop('tagName', type);
    var sum = rmStats.sum(others, function() {return rmStats.getValue('.');});
    switch(type) {
        case 'timer':
            sum = rmStats.getTotalTime() - sum;
            var elapsed = $('<elapsed></elapsed>');
            elapsed.text(sum);
            newNode.append(elapsed);
            break;
        case 'memory':
            sum = rmStats.getTotalMemory() - sum;
            var peak = $('<peak></peak>');
            peak.text(sum);
            newNode.append(peak);
            break;
    }
    return newNode;
}

jQuery.fn.reverse = [].reverse;


RMStats.prototype.renderChart = function(options) {
     var chartColors = ['#3498db',
        '#e67e22',
        '#2ecc71',
        '#e74c3c',
        '#9b59b6',
        '#f1c40f',
        '#34495e',
        '#2980b9',
        '#d35400',
        '#27ae60',
        '#c0392b',
        '#8e44ad',
        '#f39c12',
        '#2c3e50'
        ];

    var doLegend = true;

    var chartOptions = {
                            colors: chartColors,
                            grid: {
                                hoverable: true,
                                clickable: true
                            },
                            legend: {}
                        };
    var chartData = [];
    
    var label = options.data.label;
    var value = options.data.value;

    var tootltipFunc = function(item) { return item.series.label; }

    /*var clickFunc = function(item) { console.log(item);
                                        console.log(item.series.label);
                                        return item.series.label;};*/
    if(options.data.hasOwnProperty('style')) {
        var style = options.data.style;
        switch(style) {
            case 'timer':
                label = function() {return rmStats.getDesc();};
                value = function() {return rmStats.getValue('.');};
                break;
            case 'memory':
                label = function() {return rmStats.getDesc();};
                value = function() {return rmStats.getValue('.');};
                break;
            case 'histogram':
                label = function() {return rmStats.getAttr("label");};
                value = function() {return rmStats.getValue('.');};
                break;
        }

    }

    switch(options.type) {
        case "pie":
            chartOptions.series = { pie: {show: true, innerRadius: 0.5,}};
            chartOptions.legend = { position: 'nw'};
            if (options.combine)
                chartOptions.combine = options.combine;
            $(options.data.rows).each( function() {
                rmStats.pushd(this);
                var seriesRow = {};
                if (this instanceof Array) {
                    seriesRow = this.slice();
                }
                else {
                    seriesRow = { label:label(), data:value()};
                }
                chartData.push(seriesRow);
                rmStats.popd();
            });
            break;  
        case "bar":
            chartOptions.series = { bars: {show: true, align: 'center', barWidth: 0.75}};
            if(options.horizontal)
                chartOptions.series.bars['horizontal'] = true;
            
            var xAxis = [];
            for(var i in options.data.rows) {
                rmStats.pushd(options.data.rows[i]);
                xAxis.push([i, options.data.label()]);
                
                if(options.horizontal) {
                    chartData.push([[options.data.value(),i]]);
                }
                else {
                    chartData.push([[i, options.data.value()]]);  //[[ ]] to give seperated colors
                }
                rmStats.popd();
            }
            if(options.horizontal)
                chartOptions.yaxis = {ticks: xAxis, mode:'categories', tickLength: 0};
            else
                chartOptions.xaxis = {ticks: xAxis, mode:'categories', tickLength: 0};
            break;  
        case "histogram":
            doLegend = false;
            chartOptions.series = { bars: {show: true, align: 'center', barWidth: 0.75}};
            chartOptions.xaxis = {
                mode: "categories",
                tickLength: 0
            };
            chartOptions.yaxis = {
                min: 0
            };
            var series = [];
            options.data.rows.each( function() {
                rmStats.pushd(this);
                series.push([label(), value()]);
                rmStats.popd();
            });
            chartData.push(series);

            tootltipFunc = function(item) {return "" + item.datapoint[0] + " - " + item.datapoint[1];};
            break;
        case "stackedColumn":
            chartOptions.series = { bars: {show: true, align: 'center', barWidth: 0.75}, stack: true, highlightColor: 'rgba(255,255,255,.5)'};
            var series = [];
            chartData = options.data;
            var xAxis = [];
            for(var i in options.xAxisLabels) {
                xAxis.push([i, options.xAxisLabels[i]]);
            }
            chartOptions.xaxis = {ticks: xAxis, tickLength: 0};
            break;  

        case "memoryBar":
            chartOptions.series = { stack: true, bars: {show: true}, highlightColor: 'rgba(255,255,255,.5)' };
            chartOptions.xaxis = {show: false};
            chartOptions.yaxis = {show: false};
            chartOptions.grid.borderWidth = 0;
            chartOptions.bars = {align:'center', horizontal:true, fill:1};
            chartData = [];
            $(options.data.rows).each( function() {
                rmStats.pushd(this);
                var seriesRow = {};
                if (this instanceof Array) {
                    seriesRow = this.slice();
                }
                else {
                    seriesRow = { label:label(), data:[[value(), 0]]};
                }
                chartData.push(seriesRow);
                rmStats.popd();
            });
            break;  

        case "verticalBar":
            chartOptions.series = { stack: true, align: 'center', barWidth: 1.0, bars: {show: true}, highlightColor: 'rgba(255,255,255,.5)' };
            chartOptions.xaxis = {show: false};
            chartOptions.yaxis = {show: false};
            chartOptions.grid.borderWidth = 0;
            chartOptions.bars = {align:'center', fill:1};
            chartData = [];
            $(options.data.rows).each( function() {
                rmStats.pushd(this);
                var seriesRow = {};
                if (this instanceof Array) {
                    seriesRow = this.slice();
                }
                else {
                    seriesRow = { label:label(), data:[[0, -value()]]};
                }
                chartData.push(seriesRow);
                rmStats.popd();
            });
            break;  

        case "spline":
            chartOptions.series = { lines: {show: true}};
            chartOptions.xaxis = {max: options.xmax};
            chartOptions.yaxis = {min: options.ymin};
            var series = [];
            options.data.rows.each( function() {
                rmStats.pushd(this);
                series.push([options.data.label(), options.data.value()]);
                rmStats.popd();
            });
            chartData.push(series);

            tootltipFunc = function(item) {return "" + item.datapoint[0] + " - " + item.datapoint[1];};

            break;  

    }
    //console.log(chartOptions);
    //console.log(chartData);

    /*if($('#chartclick').length == 0) {
        $("<div id='chartClick'></div>").css({
                position: "absolute",
                display: "none",
                border: "1px solid #fdd",
                padding: "2px",
                "background-color": "#fee",
                opacity: 0.80
            }).appendTo("body");
    }*/
    var chart = $("<div class='chartContainer'></div>");
    var legend = $("<div class='legendContainer'></div>");
    chartOptions.legend.container = legend;

    var div = $("<div class='row chart-row'></div>").append([chart, legend]);

    function showTooltip(x, y, color, contents) {
        $('<div id="tooltip">' + contents + '</div>').css({
            position: 'absolute',
            display: 'none',
            top: y + 10,
            left: x + 10,
            border: '2px solid ' + color,
            padding: '3px',
            'font-size': '9px',
            'border-radius': '5px',
            'background-color': '#fff',
            'font-family': 'Verdana, Arial, Helvetica, Tahoma, sans-serif',
            opacity: 0.9
        }).appendTo("body").fadeIn(200);
    }

    div.on("rendered", function(event) {
        //if parent item has height set use that 
        var height = chart.parents('div.item').height();
        if(height > 24)
            chart.height(height);


        if(doLegend) {
            var width = div.parent().width();
            var legendColumns = Math.floor(175/width * 12);
            legendColumns = Math.min(legendColumns, 8);
            var chartColumns = 12 - legendColumns;

            legend.addClass("col-xs-" + legendColumns);
            chart.addClass("col-xs-" + chartColumns);
        }

        //chart.width(div.parent().width() - 225 ); //to make room for the legend
        //chart.height(200);
        chart.plot(chartData, chartOptions);
        window.onresize = function(event) {
            chart.plot(chartData, chartOptions);
        }
        var prevTipLabel = "";
        $(chart).bind("plothover", function (event, pos, item) {
            //console.log(pos);
            if (item) {
                if(item.series.label != prevTipLabel) {
                    prevTipLabel = tootltipFunc(item);    
                    $("#tooltip").remove();

                    showTooltip(pos.pageX, pos.pageY, item.series.color, tootltipFunc(item));
                }
            } else {
                $("#tooltip").remove();
                prevTipLabel = "";
            }
        });
        return false; //to stop propogation up tree
    });
    return div; //.plot(chartData, chartOptions);
}

RMStats.prototype.renderHeatMap = function(options) {
    //color method can be 
    // 0 blue-red
    // 1 red - white
    // 2 black - white

    var transitions = [0.0, .01, .1, 1.0];
    
    var remap = function( val, min, max, overRange, clamp) {
        var outVal = (val - min) / (max - min);
        if(clamp) {
            if (outVal > 1.0)
                outVal = 1.0;
        }
        if(outVal < 0.0)
            outVal = 0.0;
        if(overRange != null) {
            if(outVal > 1.0)
                outVal = 1.0;
            if(outVal < overRange)
                outVal = overRange;
        }

        return outVal;
    }
    var colorMethod = 0;
    if(options.hasOwnProperty('colorMethod'))
        colorMethod = options.colorMethod;

    var timeMap = options.data;
    rmStats.pushd(timeMap);
    var width = rmStats.getInt('width');
    var height = rmStats.getInt('height');
    var arr = rmStats.find('values/*');
    var min = rmStats.getFloat('min');
    var max = rmStats.getFloat('max');
    var avg = rmStats.getFloat('avg');
    rmStats.popd();
    
    var canvasx = width, 
        canvasy = height;
    var tempCanvas = $("<canvas></canvas>").attr('width', canvasx).attr('height', canvasy);
    var ctx = tempCanvas[0].getContext("2d");
    var imgData = ctx.getImageData(0,0,canvasx, canvasy);
    var gamma = .4545;
    
    var scale = 200.0/canvasy;
    var xsize
    if(scale * canvasx > 512.0)
        scale = 512/canvasx;
    
    var image_width = Math.floor(canvasx*scale);
    var image_height = Math.floor(canvasy*scale)
    var histogram = []
    for(var i =0; i < image_width; i++) {
        histogram.push(0);
    }

    var histogram_max = 0;

    function getRGB(value) {
        var histogram_bucket = Math.floor(value*image_width);
        histogram[histogram_bucket] += 1;
        if(histogram[histogram_bucket] > histogram_max) {
            histogram_max = histogram[histogram_bucket];
        }

        var r = 0;
        var g = 0;
        var b = 0;
        
        if(0) {
            b = remap(value, transitions[2], transitions[3], null, false);
            r = remap(value, transitions[0], transitions[1], b, false);
            g = remap(value, transitions[1], transitions[2], b, false);
            
            r = Math.pow(r, gamma);
            g = Math.pow(g, gamma);
            b = Math.pow(b, gamma);
        }

        function hue2rgb(p, q, t){
            if(t < 0) t += 1;
            if(t > 1) t -= 1;
            if(t < 1/6) return p + (q - p) * 6 * t;
            if(t < 1/2) return q;
            if(t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        }

        //remap value from blue (.75) to red (0)
        var h = 0;
        var s = 0;
        var l = 0;
        switch(colorMethod) {
            case 0:
                h = .75 - value*.75;
                s = 1.0;
                l = .5;
                break;
            case 1:
                h = value*(1.0/6.0);
                s = 1.0;
                l = value;
                break
            case 2:
                h = 0;
                s = 0;
                l = value;
                break;
        }

        var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        var p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);

        return [r,g,b];
    }

    arr.each(function(i,elm) {
        var value = parseFloat($(elm).text());
        
        var rgb = getRGB(value);

        imgData.data[i*4] = Math.floor(rgb[0]*255);
        imgData.data[i*4 + 1] = Math.floor(rgb[1]*255);
        imgData.data[i*4 + 2] = Math.floor(rgb[2]*255);
        imgData.data[i*4 + 3] = 255;
    });

    ctx.putImageData(imgData, 0,0);
    
    var canvas = $("<canvas></canvas>").attr('width', image_width).attr('height', image_height);
    ctx = canvas[0].getContext("2d");
    ctx.scale(scale, scale);
    ctx.drawImage(tempCanvas[0], 0,0);
    
    var key = $("<canvas></canvas>").attr('width', image_width).attr('height', 50);
    var key_context = key[0].getContext("2d");
    key_context.scale(1, 50.0/histogram_max); //so I don't have to rescale histogram

    for (var i=0; i<image_width; i++) {
        var rgb = getRGB(i/image_width);
        var rgbStr = "rgb(" + Math.floor(rgb[0]*255) + ',' + Math.floor(rgb[1]*255) + ','
                + Math.floor(rgb[2]*255) + ')';
        key_context.fillStyle = rgbStr;
        if(histogram[i] > 0) {
            key_context.fillRect(i,histogram_max,1,-histogram[i]);
        }
    }

    key_context.fillStyle="#888";
    key_context.strokeStyle="#888";
    key_context.scale(1, histogram_max/50.0);
    var image_avg = (avg - min)/(max-min) * image_width;
    key_context.beginPath();
    key_context.moveTo(0.5,histogram_max);
    key_context.lineTo(0.5,10);
    key_context.moveTo(image_avg,histogram_max);
    key_context.lineTo(image_avg,21);
    key_context.moveTo(image_width - 0.5,histogram_max);
    key_context.lineTo(image_width - 0.5,10);
    key_context.stroke();

    
    key_context.font="12px Helvetica Neue";
    key_context.fillText("min - " + min.toFixed(2),1,12);
    if(image_avg > image_width * .5) {
        key_context.textAlign="right"; 
    }
    key_context.fillText("avg - " + avg.toFixed(2),image_avg + 1,25);
    key_context.textAlign="right"; 
    key_context.fillText("max - " + max.toFixed(2),image_width - 1,12);

    return $("<div class='canvasContainer'></div>").append([canvas,key]);
}
RMStats.prototype.concat = function(arrayA, arrayB) {
    return $.merge(arrayA, arrayB);
}

RMStats.prototype.getMemoryStats = function(options) {
    if(!options)
        options = {}; 
    if(typeof rmStats.memoryNodes == "undefined") {
        var memorySchema = [{
                        name:"Geometry",
                        path:"/geometry",
                        children:[{path:"gprimWrapperMem"},
                                  {path:"gprimInstanceWrapperMem"},
                                  {path:"gsmMem"},
                                  {path:"matrixMem"},
                                  {path:"gprimMem"},
                                  {path:"gopStaticMem"},
                                  {path:"gopDynamicMem"},
                                  {path:"stitchMem"},
                                  {path:"vvMem"},
                                  {path:"vvOverheadMem"},
                                  {path:"catmarkMem"},
                                  {path:"loopMem"},
                                  {path:"trimCurveMem"},
                                  {path:"trimDataMem"},
                                  {path:"coarseTessCacheMem"},
                                  {path:"nonCoarseTessCacheMem"},
                                  {name:"brickmaps", path:"/brickmaps/brickmapGprimMem"},
                                  {path:"proceduralMemory"}]
                         },

                         {
                          name:"Grids",
                          path:"/grids",
                          children:[{name:"Rectangular", path:"gridMemByType/rectangular"}, 
                                    {name:"Disconnected", path:"gridMemByType/disconnected"},
                                    {name:"Linear", path:"gridMemByType/linear"},
                                    {name:"Combined", path:"gridMemByType/multi"},
                                    {name:"Ray Hit", path:"gridMemByType/rayhit"},
                                    {name:"Triangular", path:"gridMemByType/triangular"},
                                    {name:"Irregular", path:"gridMemByType/irregular"},
                                    {name:"Volumetric", path:"gridMemByType/volumetric"},
                                    {name:"Volume Ray Hit", path:"gridMemByType/volumeRayhit"},
                                    {name:"Grouped Linear", path:"gridMemByType/aggregateLinear"},
                                    {name:"Grouped Rectangular", path:"gridMemByType/aggregateRectangular"},

                                    {name:"Shaded Rectangular", path:"shadedGridMemByType/shadedRectangular"}, 
                                    {name:"Shaded Disconnected", path:"shadedGridMemByType/shadedDisconnected"},
                                    {name:"Shaded Linear", path:"shadedGridMemByType/shadedLinear"},
                                    {name:"Shaded Combined", path:"shadedGridMemByType/shadedMulti"},
                                    {name:"Shaded Ray Hit", path:"shadedGridMemByType/shadedRayhit"},
                                    {name:"Shaded Triangular", path:"shadedGridMemByType/shadedTriangular"},
                                    {name:"Shaded Irregular", path:"shadedGridMemByType/shadedIrregular"},
                                    {name:"Shaded Volumetric", path:"shadedGridMemByType/shadedVolumetric"},
                                    {name:"Shaded Volume Ray Hit", path:"shadedGridMemByType/shadedVolumeRayhit"},
                                    {name:"Shaded Grouped Linear", path:"shadedGridMemByType/shadedAggregateLinear"},
                                    {name:"Shaded Grouped Rectangular", path:"shadedGridMemByType/shadedAggregateRectangular"}]
                         },

                         {
                          name:"Ray Accelerator",
                          path:"/rayAccel",
                          children:[{name:"Accelerator", path:"acceleratorMem"},
                                    {name:"RPRIMS", path:"rprimMem"},
                                    {name:"Trace Variables", path:"gvarMem"},
                                    {name:"Prim Sets", path:"primSetMem"},
                                    {name:"Context", path:"contextMem"},
                                    {name:"Paths", path:"pathMem"},
                                    {name:"Scratch", path:"scratchMem"}]
                         },

                         {
                          name:"Ray Tracing",
                          path:"/rayGprim",
                          children:[{name:"Tessellation (GUT) cache", path:"gutCacheMem"},
                                    {name:"Opacity Cache", path:"radioCacheMem"},
                                    {name:"Opacity Cache Paths", path:"radioCachePathMem"}]
                         },

                         {
                          name:"Integration",
                          path:"/RIS",
                          children:[{name:"Integrator", path:"ictx/integratorMem"}]
                         },

                         {
                          name:"Shading (RIS)",
                          path:"/RIS",
                          children:[
                                    {name:"BXDF", path:"sctx/shadingMem"},
                                    {name:"Pattern", path:"ictx/patternMem"}]
                         },

                         {
                          name:"Lighting",
                          path:"/RIS/Lighting",
                          children:[{name:"Lighting", path:"lightingMem"},
                                    {name:"CDF", path:"lightingCdfMem"},
                                    {name:"PDF", path:"lightingPdfMem"},
                                    {name:"Samples", path:"lightingSampleMem"},
                                    {name:"Light Geometry/Maps", path:"lightingDbMem"},
                                    {name:"Estimator", path:"estimatorLightingMem"},
                                    {name:"Estimator Samples", path:"estimatorSampleMem"},
                                    {name:"Estimator Recievers", path:"estimatorReceiverMem"},
                                    {name:"Estimator Emitters", path:"estimatorEmitterMem"},
                                    {name:"Estimator Trees", path:"estimatorTreeMem"},
                                    {name:"Transient", path:"lightingTransientMem"}]
                         },

                         {
                          name:"RIB",
                          children:[{name:"Token Table", path:"/memory/subsystems/SymbolMem"},
                                    {name:"Inline Archives", path:"/memory/subsystems/InlineArchiveMem"},
                                    {name:"User Attributes", path:"/memory/subsystems/usrAttrMem"},
                                    {name:"Coordinate Systems", path:"/memory/subsystems/coordSysMem"},
                                    {name:"Bxdf Nodes", path:"/RIS/RISinstances/RiBxdf/nodeMem"},
                                    {name:"Pattern Nodes", path:"/RIS/RISinstances/RiPattern/nodeMem"},
                                    {name:"Other Nodes", path:"/RIS/RISinstances/MiscRi/nodeMem"}]
                         },

                         {
                          name:"Texture 2D",
                          children:[{name:"Texture Cache", path:"/texture/textureTileCache/size"},
                                    {name:"PTexture Cache", path:"/texture/ptextureCache/ptxMem"}]
                         },

                         {
                          name:"Texture 3D",
                          children:[{name:"Brick Map", path:"/brickmaps/brickLocationTableMem"},
                                    {name:"Brick Map Octree", path:"/brickmaps/brickmapOctreeMem"},
                                    {name:"Brick Map Cache", path:"/brickmaps/brickCacheActualMem"},
                                    {name:"Point Cloud", path:"/pointclouds/pointCloudMem"},
                                    {name:"Point Cloud Octree", path:"/pointclouds/pointOctreeMem"},
                                    {name:"Point Cloud Cache", path:"/pointclouds/pointCacheActualMem"},
                                    {name:"Point Cloud Octree Cache", path:"/pointclouds/nodeCacheActualMem"}]
                         },

                         {
                          name:"Display",
                          children:[{name:"Framebuffer", path:"/RIS/rayHider/framebufferMem"},
                                    {name:"Display Driver", path:"/memory/subsystems/displayMem"}]
                         },
    
                         {                         
                          name:"Plugins",
                          children:[{name:"Photon Map", path:"/plugins/photonMapMemory"}] 
                         }
                            
                       ];
        rmStats.memoryNodes = rmStats.buildNodesFromSchema(memorySchema, 'memory', true);
    }

    var memoryNodes = rmStats.memoryNodes;

    if (options.removeZeros) {
        memoryNodes = rmStats.filter(memoryNodes, function() { //grep removes if false
            if(rmStats.getValue('.') > 0)
                return true;
            else 
                return false;
        });
    };
    if(options.combineThreshold) {
        var sum = rmStats.sum(memoryNodes, function() {return rmStats.getValue('.')});
        var otherSum = 0;
        memoryNodes = rmStats.filter(memoryNodes, function() { //grep removes if false
            var memoryVal = rmStats.getValue('.');
            if(memoryVal/sum >= options.combineThreshold) {
                return true;
            }
            else {
                otherSum += memoryVal;
                return false;
            } 
        });
        if(otherSum > 0) {
            var otherNode = $("<memory name='other', description='Other Memory'><peak>" + otherSum +
                                "</peak></memory>");
            memoryNodes.push(otherNode);
        }

    }
    if (options.sort) {
        memoryNodes = rmStats.sort(memoryNodes);
    };
    return memoryNodes;
}


RMStats.prototype.getTimeStats = function(options) {
    if(!options)
        options = {}; 
    if(typeof rmStats.timeNodes == "undefined") {
        var timeSchema = [{
                        name:"RIB parsing",
                        children:[{name:"Setup", path:"/time/timers/ribInitTimer"}, 
                                  {name:"Bxdf Nodes", path:"/RIS/RISinstances/RiBxdf/nodeTimer"},
                                  {name:"Pattern Nodes", path:"/RIS/RISinstances/RiPattern/nodeTimer"},
                                  {name:"Other Nodes", path:"/RIS/RISinstances/MiscRi/nodeTimer"}]
                      },
            
                      {
                        name:"Shading (RIS)",
                        path:"/RIS/sctx",
                        children:[{name:"Total", path:"sctxExecTime"}]
                      },

                      {
                        name:"Lighting",
                        path:"/RIS/Lighting",
                        children:[{name:"Light Samples", path:"lightingLightSampleTime"},
                                  {name:"Material Samples", path:"lightingMaterialTime"},
                                  {name:"Light Build", path:"/time/timers/lightdbtime"}
                                 ]
                      },

                      {
                        name:"Raytracing",
                        path:"/rayAccel",
                        children:[{name:"Camera Rays", path:"cameraTime"},
                                  {name:"Direct Lighting Rays", path:"directlightTime"},
                                  {name:"Shadow Rays", path:"transmissionTime"},
                                  {name:"Indirect Rays", path:"indirectTime"},
                                  {name:"Photon Rays", path:"photonTime"},
                                  {name:"Splitting", path:"splitTime"},
                                  {name:"ReSplitting", path:"resplitTime"},
                                  {name:"Building BVH", path:"buildTime"},
                                  {name:"Building sub-BVH", path:"subAccelBuildTime"},
                                  {name:"Displacing sub-BVH", path:"subAccelDispTime"},
                                  {name:"GUT cache fill", path:"/rayGprim/gutOtherTimeToFill"},
                                  {name:"GUT cache first fill", path:"/rayGprim/gutFirstTimeToFill"},
                                  {name:"GUT miss", path:"/rayGprim/gutL1Miss"},
                                  {name:"Opacity cache fill", path:"/rayGprim/radioTimeToFill"}]
                      }

                     ];
        rmStats.timeNodes = rmStats.buildNodesFromSchema(timeSchema, 'timer', true);
    }
    var timerNodes = rmStats.timeNodes;
    if (options.removeZeros) {
        timerNodes = rmStats.filter(timerNodes, function() { //grep removes if false
            if(rmStats.getValue(".") > 0)
                return true;
            else 
                return false;
        });
    };
    if(options.combineThreshold) {
        var sum = rmStats.sum(timerNodes, function() {return rmStats.getValue(".")});
        var otherSum = 0;
        timerNodes = rmStats.filter(timerNodes, function() { //grep removes if false
            var timerVal = rmStats.getValue(".");
            if(timerVal/sum >= options.combineThreshold) {
                return true;
            }
            else {
                otherSum += timerVal;
                return false;
            } 
        });
        if(otherSum > 0) {
            var otherNode = $("<timer name='other', description='Other Timers'><elapsed>" + otherSum +
                                "</elapsed></timer>");
            timerNodes.push(otherNode);
        }

    }
    if (options.sort) {
        timerNodes = rmStats.sort(timerNodes);
    };
    

    return timerNodes;
}

RMStats.prototype.pluginTableAndInfo = function(plugins) {
    var headers = ['Name', '% Memory', '% Time'];
    
    var totalMemory = 0;
    var totalTime = rmStats.sum(plugins, function() {return rmStats.getValue("BeginTime");});
    var chart = $("<div class='col-xs-5'></div>").append(rmStats.renderTable({rows: plugins,
                                headers: headers,
                                totalRow: ['Total', "0 mb", 
                                    rmStats.format({value: totalTime, style: 'seconds'})],
                                columns: [
                                    function() {return rmStats.getName('.');},
                                    function() {return "0 %";},
                                    function() {return rmStats.format({
                                        value: rmStats.getValue("BeginTime")/totalTime,
                                        style: "percent"
                                    });}
                                ]
                            }));
    var info = $("<div class='col-xs-7'></div>");
    
    var renderInfoCharts = function() {
        info.append(rmStats.renderChart({
                    type:"pie",
                    data:{
                      rows: plugins, //combine any < 5% into "other"
                      label: function() {return rmStats.getName('.') + " - " + rmStats.format({
                                                              value:rmStats.getValue('BeginTime'),
                                                              style: 'seconds'});},
                      value: function() {return rmStats.getValue('BeginTime');},
                      //style: "timer",
                    }
                  }));
        
        /*info.append(rmStats.renderChart({
                    type:"memoryBar",
                    data:{
                      rows: plugins, //combine any < 5% into "other"
                      label: function() {return rmStats.getName('.') + " - " + rmStats.format({
                                                              value:rmStats.getValue('memory'),
                                                              style: 'bytes'});},
                      value: function() {return rmStats.getValue('memory');},
                      //style: "timer",
                    }
                  }));*/
    };    

    renderInfoCharts();
    var div = $('<div class="row chart-row"></div>').append(chart).append(info);
    div.bind("rendered", function() {
        info.children().each(function() {$(this).trigger("rendered");});
    });

    chart.find('tbody').on( 'click', 'tr', function () {
        var nm = $(this).children().first().text();
        var clicked = jQuery.grep(plugins, function(elm, i) {
            rmStats.pushd(elm);
            var name = rmStats.getName('.');
            rmStats.popd();
            return nm == name;
        });

        var viewfile = $(clicked).attr('viewfile');
        if(viewfile) {
            console.log(statsviewDir + ris_viewdir + "plugins/" + viewfile);
            
        }
        else {
            info.html(rmStats.toString(clicked));
        }
    });

    chart.find('tbody').on( 'mouseout', 'tr', function () {
        info.html('');
        renderInfoCharts();
        info.children().each(function() {$(this).trigger("rendered");});
    });

    return div;


}

RMStats.prototype.render = function(xmlNode) {
    rmStats.pushd(xmlNode);
    var div = ''
    var type = rmStats.getTag();
    var kind = rmStats.getAttr('kind');
    
    switch(type) {
        case "set":
            div = $("<div class='row'/>");
            div.append("<div class='col-xs-3'>" + rmStats.getDesc(".") + "</div>");
            var rc = $("<div class='col-xs-9'/>");
            $(rmStats.getArray(".")).each(function() {
                rmStats.pushd(this);
                rc.append("<div>"+rmStats.getText(".")+"</div>");
                rmStats.popd();
            });
            div.append(rc);
            break;
        case "floatmap2d":
            div = $("<div class='row'/>");
            div.append("<div class='col-xs-3'>" + rmStats.getDesc(".") + "</div>");
            var rc = $("<div class='col-xs-9'/>");
            rc.append(rmStats.renderHeatMap({data: xmlNode,
                                scale: 0, colorMethod: 0}))
            div.append(rc);
            break;
        case "string":
            var desc = rmStats.getDesc('.');
            if(!desc) {
                desc = rmStats.getName('.');
            }

            if(rmStats.getName('.').indexOf('Note') > -1) {
                div = $("<div class='alert alert-info' role='alert'/>");
                div.append(rmStats.getText("."));
            }
            else {
                div = $("<div class='row'/>");
                div.append("<div class='col-xs-3'>" + desc + "</div>");
                div.append("<div class='col-xs-9'>" + rmStats.getText(".") + "</div>");
            }
            break;

        case "histogram":
            div = $("<div class='row'/>");
            div.append("<div class='col-xs-2'>" + rmStats.getDesc('.') + "</div>");
            var rc = $("<div class='col-xs-10'>");
            if(rmStats.getName('.') == 'adaptActive') {
                rc.append(rmStats.renderChart(
                          {
                            type: "spline",
                            ymin: 0,
                            xmax: rmStats.getInt("/options/maxSamples"),
                            data: {
                                label: function() { return rmStats.getAttr("label");},
                                value: function() { return rmStats.getInt('.');},
                                rows: rmStats.getArray(".")
                            }
                          }
                        ));
            
            }
            else {
                rc.append(rmStats.renderChart(
                          {
                            type: "histogram",
                            data: {
                                style: "histogram",
                                rows: rmStats.getArray("."),
                            }
                          }
                        ));
            }
            rc.height(200);
            div.append(rc);
            break;

        case "stats":
            switch(kind) {
                case "section":
                    div = $('<div class="panel panel-default"/>');
                    if($(rmStats.current()).parent().attr("kind") == "frame")
                        div.addClass("expert");
                    div.append(
                    '<div class="panel-heading"><h3 class="panel-title">' +
                        rmStats.getDesc('.') + '</h3></div>');
                    var ul = $('<ul class="list-group"/>');
                    

                    var children = rmStats.getArray('.');
                    //render timer table
                    
                    var subTypes = ['timer', 'memory', 'range'];

                    children = $(children).filter(function() {
                            if ($(this).prop('tagName').toLowerCase() == "string") {
                                var li = $('<li class="list-group-item"/>');
                                li.append(rmStats.render($(this)));
                                ul.append(li);
                                return false;
                            }
                            return true;
                        });

                    for(var typeIndex in subTypes) {
                        var type = subTypes[typeIndex];

                        var subChildren = [];
                        children = $(children).filter(function() {
                            if ($(this).prop('tagName').toLowerCase() == type) {
                                subChildren.push(this);
                                return false;
                            }
                            return true;
                        });

                        if(subChildren.length > 0) {
                            var li = $('<li class="list-group-item"/>');
                            li.append(rmStats.renderTableExpert(type,
                                    subChildren));
                            ul.append(li);
                        }
                    }

                    var subChildren = [];
                    children = $(children).filter(function() {
                        if ($(this).prop('tagName').toLowerCase() == 'int' ||
                            $(this).prop('tagName').toLowerCase() == 'float') {
                            subChildren.push(this);
                            return false;
                        }
                        return true;
                    });

                    if(subChildren.length > 0) {
                        var li = $('<li class="list-group-item"/>');
                        li.append(rmStats.renderTableExpert("numerical",
                                subChildren));
                        ul.append(li);
                    }

                    var subChildren = [];
                    children = $(children).filter(function() {
                        if ($(this).prop('tagName').toLowerCase() == 'stats' &&
                            $(this).attr('kind') == 'textureFile') {
                            subChildren.push(this);
                            return false;
                        }
                        return true;
                    });

                    if(subChildren.length > 0) {
                        var li = $('<li class="list-group-item"/>');
                        li.append(rmStats.renderTableExpert("textureFile",
                                subChildren));
                        ul.append(li);
                    }

                    children = children.filter(function() {
                            if ($(this).prop('tagName').toLowerCase() == "stats" 
                                && $(this).attr('kind') == 'timers'
                                ) {
                                var li = $('<li class="list-group-item"/>');
                                li.append(rmStats.render($(this)));
                                ul.append(li);
                                return false;
                            }
                            return true;
                        });

                    children = children.filter(function() {
                            if ($(this).prop('tagName').toLowerCase() == "stats" 
                                && $(this).attr('kind') == 'memstats'
                                ) {
                                var li = $('<li class="list-group-item"/>');
                                li.append(rmStats.render($(this)));
                                ul.append(li);
                                return false;
                            }
                            return true;
                        });

                    children.each(function() {
                        var li = $('<li class="list-group-item"/>');
                        li.append(rmStats.render($(this)));
                        ul.append(li);
                    });

                    div.append(ul);
                    break;
                case "timers":
                    div = rmStats.renderTableExpert('timer', 
                            rmStats.getArray('.'));
                    break;

                case "memstats":
                    div = rmStats.renderTableExpert('memory', 
                            rmStats.getArray('.'));
                    break;
                case "geometryprocedurals":
                    div = $('<div class="panel panel-default"/>');
                    div.append('<div class="panel-heading"><h3 class="panel-title">' +
                        rmStats.getDesc('.') + '</h3></div>');
                    var ul = $('<ul class="list-group"/>');
                    var procedurals = rmStats.getArray(".");
                    procedurals = rmStats.sort(procedurals,function() {
                        return rmStats.getValue("timer/elapsed");
                    });
                    procedurals.reverse();
                    
                    $(procedurals).each(function() {
                        rmStats.pushd(this);
                        var li = $("<li class='list-group-item'/>");
                        var innerDiv = $("<div class='row'/>");
                        innerDiv.append("<div class='col-xs-3'>" + 
                            rmStats.getDesc('.') + "</div>");
                        var col2 = $("<div class='col-xs-9 procedural-subtable'/>");
                        col2.append(rmStats.renderTableExpert("", rmStats.getArray('.')));
                        innerDiv.append(col2);
                        li.append(innerDiv);
                        ul.append(li);
                        rmStats.popd();
                    });
                    div.append(ul);

                    break; 

                case "pulldown":
                    div = $('<div class="panel panel-default"/>');
                    div.append('<div class="panel-heading"><h3 class="panel-title">' +
                        rmStats.getDesc('.') + '</h3></div>');
                    var items = rmStats.getArray(".");
                    var divs = [];

                    var row = $("<div class='row'/>");
                    var lc = $("<div class='col-xs-3'>");
                    var select = $("<select class='form-control'>");

                    var i = 0;
                    $(items).each(function() {
                        rmStats.pushd(this);
                        select.append("<option value='" + i + "''>" + 
                            rmStats.getDesc('.') + "</option>");
                        divs.push(rmStats.render(this));
                        rmStats.popd();
                        i = i+1;
                    });
                    lc.append(select);
                    row.append(lc);
                    var rc = $("<div class='col-xs-9'>");
                    rc.append(divs[0]);
                    row.append(rc);
                    var ul = $('<ul class="list-group"/>');
                    var li = $("<li class='list-group-item'/>");
                    li.append(row);
                    ul.append(li);
                    div.append(ul);

                    select.change(function() { 
                        var val = $(this).val();
                        rc.html(divs[val]);
                        rc.find("div.chart-row").each(function() {
                            $(this).trigger("rendered");
                        });
                    });

                    break; 
                case "shaders":
                    div = $("<div/>");
                    div.append($("<h3>" + rmStats.getDesc('.') + "</h3>"));
                    var shaders = rmStats.getArray(".");
                    shaders = rmStats.sort(shaders,function() {
                        return rmStats.getValue("timer/elapsed");
                    });
                    div.append(rmStats.renderTableExpert("shaders", shaders));
                    break;
                default:
                    div = $("<div/>");
                    div.append($("<h3>" + rmStats.getDesc('.') + "</h3>"));
                    if(rmStats.getDesc(".") == "Display list") {
                        div.append(rmStats.renderTableExpert("displayList", 
                                                rmStats.getArray('.')));
                    }
                    else {
                        div.append(rmStats.renderTableExpert("", 
                                                rmStats.getArray('.')));
                    }
                    
                    break;


            }
            
            break;


        
    }
    rmStats.popd();
    div.on("rendered", function () { 
        div.find("div.chart-row").each(function() {
            $(this).trigger("rendered");
        });
    });
    return div;
};

RMStats.prototype.renderTableExpert = function(type, rows) {
    var headers = [];
    // see if this is a homogenous table
    if(type === "") {
        var tag = "";
        for(var i = 0; i < rows.length; i++) {
            if(i == 0)
                tag = $(rows[0]).prop("tagName").toLowerCase();
            else {
                if($(rows[i]).prop("tagName").toLowerCase() == tag) {
                    type = tag;
                    continue;
                }
                else {
                    type = "";
                    break;
                }
            }
        }
    }

    switch(type) {
        case "timer":
            headers = ["Timer", "Elapsed"];
            for(var i in rows) {
                if ($(rows[i]).find('user').length > 0) {
                    headers = headers.concat(["User", "System"]);
                    break;
                }
            }
            break;
        case "memory":
            headers = ["Memory", "Peak"];
            break;
        case "range":
            headers = ["Range", "Current", "Total", "Peak", "Average", "Number"];
            break;
        case "textureFile":
            headers = ["Filename", "Lookups", "Reads", "Bytes Read", 
                        "Read Time", "Decompress Time"];
            break;
        case "displayList":
            headers = ["Display", "driver", "channels", "relative pixel variance"];
            break;
        case "stats":
            if($(rows[0]).attr("name") == "dispBound") {
                headers = ["Object", "Shader", "Bound", "Displacement Amount", "Ratio"];
            }
            break;
    }

    var div = $("<div/>");
    var table = $("<table class='table table-striped table-condensed table-hover'/>");
    var thead = $("<thead/>");
    var tr = $("<tr/>");
    $(headers).each(function() {tr.append("<th>" + this + 
        "</th>");});
    thead.append(tr);
    table.append(thead);
    var tbody = $("<tbody/>");
    $(rows).each(function() {
        if(type == "shaders") {
            tbody.append(rmStats.renderShaderRow(this));
        }
        else {
            tbody.append(rmStats.renderRow(this, 0));
        }
    });
    table.append(tbody);
    div.append(table);
    return div;
};

RMStats.prototype.renderRow = function(xmlNode, numFirstTab) {
    rmStats.pushd(xmlNode);
    var tr = $('<tr/>');
    var rows = [tr];
    var type = rmStats.getTag();
    var kind = rmStats.getAttr('kind');
    var firstTD = "";
    for(var i =0; i < numFirstTab; i++) {
        firstTD += "&emsp;";
    }
    var desc = rmStats.getDesc('.');
    if(!desc) {
        desc = rmStats.getName('.');
    }
    
    switch(type) {
        case "int":
            tr.append("<td>" + firstTD + desc + "</td>" +
                "<td>" + rmStats.getValue(".") + "</td>");
            break;
        case "float":
            tr.append("<td>" + firstTD + desc + "</td>" +
                "<td>" + rmStats.getValue(".") + "</td>");
            break;

        case "memory":
            tr.append("<td>" + firstTD + desc + "</td>" +
                "<td>" + rmStats.toString("./peak") + "</td>"); /*+
                "<td>" + rmStats.toString("./current") + "</td>");*/
            break;
        case "timer":
            tr.addClass("timer-row");
            var desc = rmStats.getDesc('.');
            if(desc == "") {
                desc = "Time Elapsed";
            }
            tr.append("<td>" + firstTD + desc + "</td>" +
                "<td>" + rmStats.toString("./elapsed") + "</td>");
            if(rmStats.find("./user", true) != null) {
                tr.append("<td class='user'>" + rmStats.toString("./user") + "</td>" +
                    "<td class='system'>" + rmStats.toString("./system") + "</td>");
            } 
            else {
                tr.append("<td/><td/>");
            }
            break;
        case "range":
            tr.append("<td>" + firstTD + desc + "</td>" +
                "<td>" + rmStats.getInt("./current") + "</td>" +
                "<td>" + rmStats.getInt("./total") + "</td>" +
                "<td>" + rmStats.getInt("./max") + "</td>" +
                "<td>" + rmStats.getInt("./average") + "</td>" +
                "<td>" + rmStats.getInt("./count") + "</td>");
            
            break;
        case "histogram":
            tr.append("<td>" + firstTD + desc + "</td>");
            var td = $("<td/>")
            if(rmStats.getName('.') == 'adaptActive') {
                td.append(rmStats.renderChart(
                          {
                            type: "spline",
                            ymin: 0,
                            xmax: rmStats.getInt("/options/maxSamples"),
                            data: {
                                label: function() { return rmStats.getAttr("label");},
                                value: function() { return rmStats.getInt('.');},
                                rows: rmStats.getArray(".")
                            }
                          }
                        ));
            
            }
            else {
                td.append(rmStats.renderChart(
                          {
                            type: "histogram",
                            data: {
                                style: "histogram",
                                rows: rmStats.getArray("."),
                            }
                          }
                        ));
            }
            td.height(200);
            tr.append(td);
            break;
        case "stats":
            var kind = rmStats.getAttr('kind');
            if(kind == 'section') {
                tr.append("<td>" + desc + "</td>");
                var td = $("<td/>");
                td.append(rmStats.renderTableExpert("", rmStats.getArray('.')));
                tr.append(td);
            } else if (kind == "textureFile") {
                tr.append("<td>" + rmStats.toString("./fileName") + "</td>" +
                    "<td>" + rmStats.toString("./lookups") + "</td>" +
                    "<td>" + rmStats.toString("./reads") + "</td>" +
                    "<td>" + rmStats.toString("./bytesRead") + "</td>" +
                    "<td>" + rmStats.toString("./readTime") + "</td>" +
                    "<td>" + rmStats.toString("./decompressTime") + "</td>"
                    );
                
            } else if(desc == "Display settings") {
                tr.append(
                    "<td>" + rmStats.toString("./name") + "</td>" +
                    "<td>" + rmStats.toString("./type") + "</td>" +
                    "<td>" + rmStats.toString("./mode") + "</td>" +
                    "<td>" + rmStats.toString("./relativePixelVariance") + "</td>");

            } else if(rmStats.getName() == "dispBound") {
                tr.append(
                    "<td>" + rmStats.toString("./objectName") + "</td>" +
                    "<td>" + rmStats.toString("./displacementShader") + "</td>" +
                    "<td>" + rmStats.toString("./displacementBound") + "</td>" +
                    "<td>" + rmStats.toString("./displacement") + "</td>" +
                    "<td>" + rmStats.toString("./ratio") + "</td>");
            }
            else { 
                rmStats.getArray('.').each(function() {
                        rows.push(rmStats.renderRow(this, numFirstTab + 1));
                    });
            }
            break;
        
    }
    rmStats.popd();
    if(numFirstTab > 0) {
        return tr;
    }
    else {
        return rows;
    }

};

RMStats.prototype.renderShaderRow = function(xmlNode, numFirstTab) {
    rmStats.pushd(xmlNode);
    var tr = $('<tr/>');
    var desc = rmStats.getDesc('.');
    if(!desc) {
        desc = rmStats.getName('.');
    }
    tr.append("<td>" + desc + "</td>");

    var td2 = $("<td/>");
    td2.append(rmStats.renderTableExpert("", rmStats.getArray('.')));
    tr.append(td2);
    rmStats.popd();
    return tr;

};


