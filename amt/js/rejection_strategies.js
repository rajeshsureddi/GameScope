// Rejection during instruction phase
var score_diff = [];
var sd1 = 10;
var scores = [];
var sd2 = 10;
var train_delay = 0;
// Number of Stalls
var stall_count = 0;
var score_diff = [];
var delay = 0;
var load_start = 0;
var load_end = 0;
var loadTime = 0;
var loadThresh = {{maxLoadingTime | safe}};

var trainc = 0;

var phase = "{{ phase|default('instruction') }}"


function hide_all() {
	$('#instruction').hide();
	$('#quiz').hide();
	$('#survey').hide();
	$('#done').hide();

	$('#traintest').hide();
	$('#divRejected').hide();

	$('#divNextButton').hide();
	$('#imageA').hide();
	$('#buttonA').hide();
	$('#btnDidntSeeVideo').hide();
	// $('#bottomLeftCorner').hide();
}

function rejected(msg, retry=true) {
	console.log('user [' + $.getUrlVar('assignmentId') + '] rejected because of ' + msg);
	 {% if debug %}
		 $("textarea#debugMsg").val(logMessages.join('\n'));
	 {% else %}
		 if(retry==false) {
			 msg = 'You may have violated one of our Ethics policies. Please return the HIT.';
		 }
	 {% endif %}
	 $('#reasonRejected').html(msg);

	 hide_all();
 	$('#submitButton').remove();
 	// record information?
 	$('#divRejected').show();
 	$('#divNextButton').hide();
	phase = 'reject'
}

function standardDeviation(values){
  var avg = average(values);

  var squareDiffs = values.map(function(value){
    var diff = value - avg;
    var sqrDiff = diff * diff;
    return sqrDiff;
  });

  var avgSquareDiff = average(squareDiffs);

  var stdDev = Math.sqrt(avgSquareDiff);
  return stdDev;
}

function average(data){
  var sum = data.reduce(function(sum, value){
    return sum + value;
  }, 0);

  var avg = sum / data.length;
  return avg;
}

// var gold_scores = [20,30,40,50];
// Browser resolution
function rejectBrowserRes() {
  var wh = $(window).height();
  var ww = $(window).width();
  $("#browserWindowSize").val(wh+' / '+ww);
  console.log("Browser Height: " + wh + " / " + "Browser Width: " + ww );
  if(isMobile) {
    // if(wh < 640 && ww < 360) {
    //   rejected('The mobile browser resolution is too small for this study. Please return the HIT.');
    // }
    rejected('Mobile browser detected - this study is only open to desktop/laptop viewers. Please return the HIT.')
  }
  else {
    if(wh < 720 && ww < 1280) {
      rejected('The desktop browser resolution is too small for this study. Please return the HIT.');
    }
  }
}

// Browser Version
function rejectBrowser() {
    var ua = navigator.userAgent;

    // Browser detection
    var isChrome = /Chrome/.test(ua) && !/Edg/.test(ua); // Exclude Edge which also includes "Chrome" in UA
    var isEdge = /Edg/.test(ua);
    var isSafari = /^((?!chrome|android).)*safari/i.test(ua); // Exclude Chrome for Android which also includes "Safari" in UA

    // Version extraction
    var chromeVersion = isChrome ? parseInt((/Chrome\/(\d+)/.exec(ua) || [0,0])[1], 10) : 0;
    var edgeVersion = isEdge ? parseInt((/Edg\/(\d+)/.exec(ua) || [0,0])[1], 10) : 0;
    var safariVersion = isSafari ? parseInt((/Version\/(\d+)/.exec(ua) || [0,0])[1], 10) : 0;

    // Minimum version requirements
    var minChromeVersion = 115; //  minimum Chrome version
    var minEdgeVersion = 120; //  minimum Edge version
    var minSafariVersion = 15; //  minimum Safari version

    // Check if the browser is supported and meets the minimum version requirement
    if (isChrome && chromeVersion < minChromeVersion) {
        rejected('Your version of Chrome is not supported. Please update your browser to latest and try again.');
    } else if (isEdge && edgeVersion < minEdgeVersion) {
        rejected('Your version of Edge is not supported. Please update your browser to latest and try again.');
    } else if (isSafari && safariVersion < minSafariVersion) {
        rejected('Your version of Safari is not supported. Please update your browser to latest and try again.');
    } else if (!isChrome && !isEdge && !isSafari) {
        rejected('Your browser is not compatible with this study. Please use Chrome (we also support Edge and Safari but might have limited support).');
    }
}

// Browser zoom
function rejectBrowserZoom(){
	pr = window.devicePixelRatio;
	pr = parseFloat(pr.toFixed(2));
	pr1 = Math.abs(pr-1);
	pr2 = Math.abs(pr-2);
	console.log("Browser zoom: " + pr);
	if((pr1 > 0) && (pr2 > 0)){
		$('#alert-msg').attr('class', "alert alert-warning");
		$('#alert-msg').html('Please check if the browser zoom is set to 100%. If not, you can set it by pressing Ctrl ++ or Cmd ++.')
	}
}
// Loading Time
function trainLoadTime(){
	// measure load time for each individual video
    load_end = performance.now();
		var loadTimeThis = (load_end - load_start)/1000;
		loadTime += loadTimeThis;
		trainc += 1;
		if(trainc=={{trainVids|length}}){
	    console.log("Loading time: " + loadTime);
	    if (loadTime > loadThresh){
	      rejected('Your internet connection is too slow for this study. You could try again after getting a faster connection.');
	    }
		}
}

// Rejection during training phase

// Stalls and spped up
function checkStalls(){
  var singleDelay = 2;
  var totDelay = 5;
  if (delay > singleDelay || train_delay > totDelay){
    rejected('Your internet connection is too slow for this study. You could try again after getting a faster connection.');
  }
  if ( train_delay < -0.5) {
    rejected('speedup', retry=false);
  }
}

//Rejection during testing phase (halfway)

// Diff of points
// var sd1 = 10;


function checkDiffSD(){
  var diffSD = standardDeviation(score_diff);
  console.log("diffSD: " + diffSD);
  if(diffSD < 10){
    rejected('checkDiffSD', retry=false);
  }
}

// Score Consistency


function checkScoreConsistency(){
  var conSD = standardDeviation(scores);
  console.log("conSD: " + conSD);
  if(conSD < 10){
    rejected('checkScoreConsistency', retry=false);
  }
}

// Check stalls
function checkStallCount(){
  console.log("stall count:" + stall_count);
  if(stall_count > 15){
    rejected('Your internet connection is too slow for this study. You could try again after getting a faster connection.');
  }
}



// //Rejection during survey
//
// //Repeated videos
// fault_repeat = 0;
// // for repeated idx, push to array
// if(diff>sd2){
//   fault_repeat += 1;
// }
// function checkRepeatDiffs(){
//   if(fault_repeat>2){
//     rejected('You did not satisfy the requirements for this study. Please return the HIT.');
//   }
// }
//
// // // Golden videos
// fault_golden = 0;
// if(diff>20){
//   fault_golden += 1;
// }
// function checkGoldenDiffs(){
//   if(fault_repeat>2){
//     rejected('You did not satisfy the requirements for this study. Please return the HIT.');
//   }
// }

// Check lens correction
// Do after the study

$(document).ready(function(){
		$( window ).load(function() {
		  // Run code
		rejectBrowserRes();
		rejectBrowser();
		rejectBrowserZoom();
		
		  $( "#sub_butA" ).on({
		    rejection_check: function() {
		      if (phase == 'test') {
		        var final_val = document.getElementById("points").value
		        var init_val = sessionStorage['initialVal'] || 'defaultValue';
		  			d = Math.abs(parseInt(final_val,10) - parseInt(init_val,10));
		  			score_diff.push(d);
		  			scores.push(parseInt(final_val,10));

		  			if (p.im_num == parseInt(p.items.length/2) ){
							console.log('halfway rejection check!!!')
		  				checkDiffSD();
		  				checkStallCount();
		          checkScoreConsistency();
		  			};
					

		        // check at end of testing phase
		        // if (p.im_num == {{labelVids|length + n_repeat + goldVids|length}}){
		        //   for (var i=0, len=p.items.length; i<len; i++) {
		        //     if (p.items[i].videotype == 'gold') {
		        //
		        //     }
		        //   }
		        //   p.items.forEach( function(v, index) {
		        //     switch (v.videotype) {
		        //       case 'gold':
		        //         break;
		        //       case 'repeat':
		        //         break;
		        //       default:
		        //         break;
		        //     }
		        //   } );
		        // };
		  		// }

		      // checkGoldenDiffs();
		      // checkRepeatDiffs();

		    }
		  }
		  });
		});
});
