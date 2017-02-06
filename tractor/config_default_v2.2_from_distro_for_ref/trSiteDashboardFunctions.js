//
// Site-specific JavaScript implementations of optional
// Tractor Dashboard functions.
//
//
// ----------------------------------------------------------------
// Copyright (C) 2010-2013 Pixar Animation Studios.
//
// The information in this file is provided for the exclusive use of the
// licensees of Pixar.  Such users have the right to use, modify, and
// incorporate this code into other products for purposes authorized
// by the Pixar license agreement, without fee.
//
// PIXAR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
// ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO EVENT
// SHALL PIXAR BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES
// OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
// WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
// ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
// SOFTWARE.
// ----------------------------------------------------------------
//

//
// Dashboard login password management.  See the Tractor Administration
// documentation for a detailed discussion of the steps required to
// integrate the Tractor login scheme with site security policies.
//
// 

function trSitePasswordHash (passwd, challenge)
{
    // By default, Tractor ignores Dashboard passwords completely,
    // and login names are only used for basic event tracking and to
    // restrict some UI actions.  The return value of this function,
    // below, should be the JavaScript 'null' value when the default
    // ignore-passwords behavior is desired.  This function should also
    // return null if crews.config specifies a Tractor built-in password
    // scheme, such as "internal:PAM".
    //
    // Otherwise, this function should return a string that is the
    // site-customized encoding of the user's typed-in plaintext password,
    // possibly also incorporating the given server-supplied random one-time
    // challenge string.  The matching site-specific server-side handling
    // of this encoded string MUST be implemented in the matching script
    // named in crews.config, such as trSiteLoginValidator.py
    //
    // return null;  // passwords are ignored (default factory setting)
    // or
    // return your_custom_encoding( passwd, challenge );

    return null;
}

//
// ----------------------------------------------------------------
//

// The trSiteOpenPreviewLink function is called when someone
// clicks on the "Preview Task" menu item for tasks that
// specify a -preview or -chaser command.  By default,  we rely
// on the user's browser settings to invoke an appropriate
// external handler for this preview function.  Site's can
// alter the default behavior here.
//
// A typical old-school job script may have a preview or chaser
// specification like this:  Cmd -preview {sho /some/image.img}
// This will arrive here as the "pargs" parameter, in the form
// of a javascript array, like:  ["sho", "/some/image.img"]
// In this example function, we drop the "sho" and attempt to
// load the image argument directly, which assumes that the
// tractor engine (as webserver) has access to that file and
// can serve it back to browser.  Your code here  might instead
// transform the image name string into a URL that is known to
// work (possibly to a different web server at your site), or
// your code might add a custom "URI Scheme" at the beginning
// of the name which can cause the user's browser to invoke a
// locally installed browser plug-in to handle the filename in
// some custom way.
//
// See for example:  http://en.wikipedia.org/wiki/URI_scheme
//

function trSiteOpenPreviewLink (jid, tid, jobowner, pargs)
{
    var url = "";
    
    if ("string" == typeof(pargs))
        url = pargs;
    else
    if ("object" == typeof(pargs))
    {
        if (2==pargs.length && "sho"==pargs[0])  // ["sho", "imgfile"]
        {
            // In this example handler we treat the program named "sho"
            // as a special case, and just attempt to load the image
            // file directly from the server using a simple http fetch.
            // For example, network mounted images that are visible
            // ON THE ENGINE can be served to browsers by specifying
            // the full engine-visible path to the image in the task's
            // -chaser or -preview command, and the mapping the root of
            // the network mount into the root of the tractor-served
            // website area using an entry in the "SiteURLMap" list in
            // tractor.config.
            //
            url = pargs[1];  // url is just the image file name
        }
        else {
            // otherwise, for example, form a URI-scheme-like URL
            // from the arguments ...

            url = pargs.join(':');  // plugin:/some/image.img
        }
    }

    if (url.length > 0)
    {
        // Typically we will want to load the preview image in a
        // separate browser window using the DOM window.open() function.
        // Such as when loading a simple image from a webserver.
        //
        // However, some built-in or plugin-supplied url scheme handlers
        // work better when they are triggered by assigning directly to
        // the semi-magic variable "window.location" since sometimes the
        // handler launches an external program  without actually
        // redirecting the current location or requiring a new browser
        // tab or window.
        //
        // As a working but silly example, consider a chaser definition
        // like this:
        //
        //    -chaser {mailto:rmancusp@pixar.com}
        //
        // The code here in this function might assume that there is a
        // browser or OS handler installed for the "mailto" URI scheme,
        // (as there actually is for all typical browsers, it launches
        // the user's mail program).  Through experimentation we might
        // learn that the "mailto" scheme works best with an assignment
        // to window.location, rather than a call to window.open().
        //
        if (0 == url.search("mailto:"))
            window.location = url;  // launches external mailer
        else
            window.open(url);      // open a new window showing the url
    }
}

//
// ----------------------------------------------------------------
//
