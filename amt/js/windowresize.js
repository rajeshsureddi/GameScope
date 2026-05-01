function setBodyHeight() {
  var wh = $(window).height();
  $('body').height(wh); // body height = window height
}

$(document).ready(function(){
  $(window).bind('resize', function() {
      setBodyHeight();
  });
});
