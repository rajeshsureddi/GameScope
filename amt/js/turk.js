/*
// from http://stackoverflow.com/questions/15589764/how-to-hide-the-link-to-an-external-web-page-in-a-hit-before-workers-accept-the
Amazon will pass variables in the url query string when opening your external web page. For this use case, you want to look at assignmentId. If assignmentId is ASSIGNMENT_ID_NOT_AVAILABLE the worker is previewing the HIT. (More info in the mturk docs.)

You can grab those variables with the following javascript:


var assignmentId = $.getUrlVar('assignmentId');
var workerId = $.getUrlVar('workerId');
var hitId = $.getUrlVar('hitId');
if (assignmentId == "ASSIGNMENT_ID_NOT_AVAILABLE"){
  // Worker is previewing the HIT
}
else {
  // Worker has accepted the HIT
}
*/

$.extend({
  getUrlVars: function(){
    // From http://code.google.com/p/js-uri/source/browse/trunk/lib/URI.js
    var parser = /^(?:([^:\/?\#]+):)?(?:\/\/([^\/?\#]*))?([^?\#]*)(?:\?([^\#]*))?(?:\#(.*))?/;
    var result = window.location.href.match(parser);
    var scheme    = result[1] || null;
    var authority = result[2] || null;
    var path      = result[3] || null;
    var query     = result[4] || null;
    var fragment  = result[5] || null
    if (query === null || query === undefined) {
      return {};
    }
    var vars = [], hash;
    var hashes = query.split('&');
    for(var i = 0; i < hashes.length; i++)
    {
      hash = hashes[i].split('=');
      vars.push(hash[0]);
      vars[hash[0]] = hash[1];
    }
    return vars;
  },
  getUrlVar: function(name){
    return $.getUrlVars()[name];
  }
});

var is_assigned = ($.getUrlVar('assignmentId') != 'ASSIGNMENT_ID_NOT_AVAILABLE');
