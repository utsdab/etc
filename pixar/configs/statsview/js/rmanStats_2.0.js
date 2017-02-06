scripts= document.getElementsByTagName('script');
var path = '';
for(i in scripts) {
  var script = scripts[i];
  if(script.src && script.src != '') {
    path = script.src.split('?')[0];
  }
} //the src url of this
statsviewDir= path.split('/').slice(0, -2).join('/')+'/'; //basedir/..
jqueryFile = "js/jquery-1.10.2.min.js";

/* check if user has set a "theme" in localstorage */
statsTheme = 'dark';
if(typeof window.localStorage != 'undefined') {
  if (localStorage.rmanStatsTheme) {
    statsTheme = localStorage.rmanStatsTheme;
  }
}


/** Resource files to load
    we can't put jquery in here because it's used to load them.
    If a new css or js file is needed add here.
*/
resources = [
  {type:'js', file: "js/bootstrap.min.js"},
  {type:'css', file: "css/bootstrap.min.css"},
  {type:'js', file: "js/jquery.dataTables.min.js"},
  {type:'css', file: "css/jquery.dataTables.min.css"},
  {type:'js', file: "js/dataTables.bootstrap.js"},
  {type:'css', file: "css/dataTables.bootstrap.css"},
  {type:'js', file: "js/jquery.flot.min.js"},
  //{type:'js', file: "js/jquery.flot.pie.min.js"},
  {type:'css', file: "css/stats.css" },
  {type:'js', file: 'js/rmStats.js', onLoad: function() {
    //create the rmStats interface
    var xmlString;
    if(typeof xml != 'undefined') {
      xmlString = $(xml)[0].childNodes[3].childNodes[3];
      xml = null;
    }
    else {
      xmlString = $("#xml_data")[0];
    }
    
    rmStats = new RMStats(xmlString);
    initialRender();
  }},
];

if (statsTheme == 'dark') {
  resources.push({type:'css', file: "css/stats.dark.css" });
}

//Used for loading jquery only
function loadScript(baseDir,url, onLoad, onError)
{
    var head = document.getElementsByTagName('head')[0];
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = baseDir + url;


    // Then bind the event to the callback function.
    // There are several events for cross browser compatibility.
    script.onreadystatechange = onLoad;
    script.onload = onLoad;
    script.onerror = onError;

    // Fire the loading
    head.appendChild(script);
}

//Once jquery is loaded, load the other css/js files    
var onLoad = function() {
  console.log("jquery loaded from local file");



  $.ajaxPrefilter( "json script", function( options ) {
    options.crossDomain = true;
  });
  console.log("loading resources");
  loadResources(resources);
};

var onError = function() {
  console.log("jquery not loaded from RMANTREE/etc/statsview");
  alert("Loading jquery failed. \
         \nCheck RMANTREE/etc/statsview in stats file.");
};

//load the resources passed in, using jquery then render the page
function loadResources(resources) {
  if(resources.length == 0)
    return;
  var resource = resources[0];
  switch(resource.type) {
    case "js":
      $.getScript(statsviewDir + resource.file, function() {
        console.log("loaded javascript " + statsviewDir + resource.file);
        if(resource.hasOwnProperty('onLoad'))
          resource.onLoad();
        loadResources(resources.slice(1, resources.length));
      });
      
      break;
    case "css":
      $('head').append( $("<link rel='stylesheet' type='text/css' />").attr(
          'href', statsviewDir + resource.file));
      console.log("loaded css " + statsviewDir + resource.file);
      loadResources(resources.slice(1, resources.length));
      break;
  }
  
}
     
// -- MAIN --
loadScript(statsviewDir, jqueryFile, onLoad, onError);

//html code for the skeleton of the page before loading the appearance data
initialBody = '\
  <nav class="navbar navbar-default navbar-fixed-top" role="navigation">\
    <div class="container">\
      <div class="collapse navbar-collapse">\
        <ul class="nav navbar-nav">\
          <li class="dropdown" id="frame-select">\
              <a href="#" class="dropdown-toggle" data-toggle="dropdown">Frame\
                 <b class="caret"></b>\
              </a>\
              <ul class="dropdown-menu">\
              </ul>\
          </li>\
        </ul>\
      </div>\
    </div>\
  </nav>\
  <div id="content" class="container"></div>\
  <div id="noteModal" class="modal fade" tabindex="-1" role="dialog" aria-hidden="true">\
    <div class="modal-dialog modal-sm note-modal">\
      <div class="modal-content"></div>\
    </div>\
  </div>';

ris_views = {'Overview':'overview.js',
             'Time': 'time.js',
             'Memory': 'memory.js',
             'Raytracing': 'raytracing.js',
             "Integration": 'integration.js',
             'Shading': 'shading.js',
             'Lighting': 'lighting.js',
             'Texture': 'texture.js',
             'Geometry': 'geometry.js', 
             //'Plugins': 'plugins.js'  //to be enabled when more complete stats are made
            };
ris_viewdir = "js/views/RIS/";

reyes_views = { 'Overview':'overview.js',
                'Time': 'time.js',
                'Memory': 'memory.js',
                'Raytracing': 'raytracing.js',
                'Shading': 'shading.js',
                'Texture': 'texture.js',
                'Geometry': 'geometry.js'};
reyes_viewdir = "js/views/reyes/";



//here we add the html to the page and run the postscript function
function initialRender() 
{
  // construct the rmStats object
  $("div#main").html(initialBody);
  addInitialActions();
}

//adds the pages to the table of contents and the actions to handle their clicks 
function addInitialActions() {
  //get the list of views
  var viewdir = '';
  var views = {};
  var activeView = window.location.hash;
  var viewHref = "#view-";

  window.onhashchange = function() {
    var newView = window.location.hash;
    if(newView == "#expert" || newView == '' || newView == '#') {
      initialRender();
    }
  }

  if(activeView.substr(1,6) == 'expert' ) {
    var tabNames = rmStats.getTabs();
    $(tabNames).each(function() {
      var path = "/" + this;
      var key = this.substr(0, 1).toUpperCase() + this.substr(1);
      views[key] = function() {return rmStats.render(path);};
    });
    viewHref = "#expert-view-";
    if(activeView == "#expert")
      activeView = '';
  }
  else {
    if(rmStats.isRISmode()) {
      viewdir = ris_viewdir;
      views = ris_views;
    }
    else {
      viewdir = reyes_viewdir;
      views = reyes_views;
    }
  }

  //add the frames in the xml to the dropdown
  var frameNames = rmStats.getFrameNames();


  var dropdown = $("#frame-select ul.dropdown-menu");
  for (i in frameNames)
  { 
    var frameTitle = frameNames[i];
    var prettyTitle = frameTitle.charAt(0).toUpperCase() + frameTitle.slice(1);
    var stuff = "<li>";
    stuff += "<a href=\"#" + frameTitle + "\">";
    stuff += prettyTitle + "</a>";
    stuff += "</li>";
    dropdown.append(stuff);
  }
  dropdown.children().first().addClass("active");
  if(frameNames.length == 1)
    $("#frame-select").hide();

  //add the view pages defined in the layout
  var viewList = $(".navbar-nav");

  for(var key in views){
    var href = viewHref + key.replace(/\s+/g, '');
    $("#frame-select").before("<li class='view-select'><a href='" + 
                              href+"'>"+key+"</a></li>");
  };
  if(activeView != '') {
    $("a[href="+activeView+"]").parent().addClass("active");
  }
  else 
    viewList.children().first().addClass("active");

  //when view or frame is changed, redraw
  $(".dropdown-menu > li, li.view-select").click(function() {
    var old = $(this).siblings(".active").removeClass("active");
    $(this).addClass("active");
    
    renderPage(views, viewdir);
  });

  //initialDraw
  renderPage(views, viewdir);

  
  
}

function makeFooter(maincontent, mode) {
  var footer = maincontent.append('<div class="row switchMode center-block"></div>');
  footer.append('<div class="col-xs-5"></div>');
  if(mode == 'artist') {
    footer.append('<a class="col-xs-12 offset" href="#">Artist View</a>');
  } else {
    footer.append('<a class="col-xs-12 offset" href="#expert">Expert View</a>');
  }
  
}

//This is called when a page is clicked to replace the main content
function renderPage(views, viewdir) {
  var viewkey = $(".navbar-nav").children("li.active").children("a").text();
  var frameNum = $("#frame-select li.active a").attr('href').slice(1);
  rmStats.setCurrentFrame(frameNum);
  var maincontent = $("#content");
  maincontent.html('');

  if(typeof(views[viewkey]) == "string") {
    var viewFile = viewdir + views[viewkey];
    console.log("Loading view " + viewFile + " for " + frameNum);
    $.getScript( statsviewDir + viewFile, function() {
      var div = $("<div></div>");
      maincontent.append(div);
      renderItem(view, div, 1);
      //enable info modals
      $("[data-toggle='popover']").popover();

      $(".note button").click(function() {
        //$(".modal-content").appendTo($(this).parent().parent());
        $(".modal-content").html($(this).attr("data-content"));
      });
      makeFooter(maincontent, 'expert');
    });
  }
  else {
    var div = $("<div></div>");
    maincontent.append(div);
    renderItem({value:views[viewkey]}, div, 1);
    makeFooter(maincontent, 'artist');
  }
}

//render an item based on the layout
var hrefIndex = 0;
function renderItem(layoutItem, parent, level) {
  var divStr = "<div class='item'></div>";
  var div = $(divStr);
  
  //set the height if specified
  if(layoutItem.hasOwnProperty('height')) 
    div.height(layoutItem.height)

  parent.append(div);
  


  //cd to the point in the structure if cd is present
  if(layoutItem.hasOwnProperty('pushd')) {
    rmStats.pushd(layoutItem.pushd);
  }
  
  //first render the label
  if(layoutItem.hasOwnProperty('label')) {
    var level = 3;
    div.append('<H' + level + '>' + layoutItem.label + '</H' + level + '>');
  }
  
  //then the data
  if(layoutItem.hasOwnProperty('value')) {
    var renderedItem = layoutItem.value();
    div.append(renderedItem);
    $(renderedItem).trigger('rendered');
  }
  else {
    div.removeClass('item');
  }
    
  //then the children
  if (layoutItem.hasOwnProperty('children')) {
    var appendTo = div;
    var columns = -1;
    if (layoutItem.hasOwnProperty('columns'))
      columns = layoutItem.columns;
    for(var index in layoutItem.children) {
      var newParent = appendTo;
      var item = layoutItem.children[index];
      if(columns > 0) {
        if(index % columns == 0) {
          //make a new row
          div.addClass('row mainrow');
          //div.append(row);
          //appendTo = row;
        }
        var columnwidth = 12/columns;
        if(item.hasOwnProperty('width')) {
          columnwidth = item.width;
        }
        newParent = $("<div class='col-xs-" + columnwidth + "'></div>");
        appendTo.append(newParent);
      }
      else if (item.hasOwnProperty('width')) {
          newParent.addClass('col-xs-' + item.width)
      }
      renderItem(item, newParent, level + 1);  
    }  
  }

  if(layoutItem.hasOwnProperty('note')) {
    var button = $("<div class='note'><button type='button' class='btn btn-default' data-toggle='modal'" + 
      " data-target='#noteModal' data-content='" + layoutItem.note + "'" + ">i</button></div>");
 // var button = $("<div class='note'><button type='button' class='btn btn-default' data-toggle='popover'" + 
 //      " data-placement='left' data-content='" + layoutItem.note + "'" + ">i</button></div>");
    div.prepend(button);
  }  

  if(layoutItem.hasOwnProperty('pushd')) {
    rmStats.popd();
  }

}




