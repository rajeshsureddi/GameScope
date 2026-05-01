$(document).ready(function(){
   const ua = navigator.userAgent;
   let browserName = "Unknown Browser";
   let fullVersion = "Unknown Version";
   let OSName = "Unknown OS";

   // Detecting browser name and version
   if (ua.indexOf("Firefox") > -1) {
       browserName = "Firefox";
       fullVersion = ua.match(/Firefox\/(\d+\.\d+)/)[1];
   } else if (ua.indexOf("Edg") > -1) {
       browserName = "Edge";
       fullVersion = ua.match(/Edg\/(\d+\.\d+)/)[1];
   } else if (ua.indexOf("OPR") > -1 || ua.indexOf("Opera") > -1) {
       browserName = "Opera";
       fullVersion = ua.match(/(Opera|OPR)\/(\d+\.\d+)/)[2];
   } else if (ua.indexOf("Chrome") > -1) {
       browserName = "Chrome";
       fullVersion = ua.match(/Chrome\/(\d+\.\d+)/)[1];
   } else if (ua.indexOf("Safari") > -1) {
       browserName = "Safari";
       fullVersion = ua.match(/Version\/(\d+\.\d+)/)[1];
   }

   // Detecting OS
   if (navigator.userAgent.indexOf("Win") != -1) OSName="Windows";
   if (navigator.userAgent.indexOf("Mac") != -1) OSName="MacOS";
   if (navigator.userAgent.indexOf("X11") != -1) OSName="UNIX";
   if (navigator.userAgent.indexOf("Linux") != -1) OSName="Linux";

   // Outputting the results
   const systemInfo = 'Browser name = '+ browserName + '/Full version = ' + fullVersion + '/Your OS: '+ OSName;
   
   const screenH = window.screen.height;
   const screenW = window.screen.width;
   
   console.log(systemInfo);
   console.log('Screen height: ' + screenH + ', Screen width: ' + screenW );
});

