// https://stackoverflow.com/questions/24052775/how-to-get-the-console-log-content-as-string-in-javascript
var logBackup = console.log; // console.log with timestamp
var logMessages = [];

console.log = function() {
  var timestamp = new Date().toJSON(); // The easiest way I found to get milliseconds in the timestamp
  var args = arguments;

  logBackup.apply(console, arguments); // console don't show timestamp
  args[0] = timestamp + ' > ' + arguments[0];
  logMessages.push.apply(logMessages, args);
};
