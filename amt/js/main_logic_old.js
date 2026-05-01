function dbg() {
		$('#debug-shortcut').toggle();
		$('span[id^=status]').toggle();
		debug_mode = !debug_mode
		// currentVid.controls = !currentVid.controls;
		return debug_mode
}



function instruction() {
	hide_all();
	$('#basic').show();
	$('#instruction').show();
}

function quiz() {
	hide_all();
	$('#quiz').show();
}

function pre_train() {
	if (p == null) return;
	hide_all();
	$('#phase_info').html("You are entering the training session. Click to Continue.");
	$('#nextButton').html('Continue');
	$('#divNextButton').show();
}

function pre_test() {
	hide_all();
	$('#phase_info').html("You are entering the testing session. Click to Continue.");
	$('#divNextButton').show();
}

function show_slider(vids) {
	// video done playing
	var init_val = Math.floor(Math.random() * 100);
	sessionStorage['initialVal'] = init_val;
	$('#attributes').find('input[type=checkbox]:checked').removeAttr('checked');
	document.getElementById('points').value = init_val;
	document.getElementById("textbox_input").value = "";
	$('#textbox').hide();
	$('#short_instructions').show();
	$('#buttonA').hide();
	$('#main-slider').show();
	$('#points').change(function(){$('#buttonA').show();$('#report_video').show(); $('#sub_butA').prop('disabled', false);});
}

// combine train and test function
var last_progress = 0;
var timeout = null;

function show_vid(vids, index=null) {

	if (index == null) {
		index = vids.idx;
	}
	// avoid bad calls
	if (index >= vids.items.length || index < 0) {return false;}
	// check if is ready
	prepare_vid(vids, index);
	// auto skip: this function is not working. disabled, we don't change vids.idx here
	// if (prepare_vid(vids, vids.idx) == false) {
	// 	// wont call if use backup (prepare vid always returns true )
	//  	vids.idx ++; // load next one
	// 	console.log('broken p.idx=' + p.idx);
	// 	return show_vid(vids);
	// }

	// video is ready
	hide_all();
	// show progress every 10% done
	// showing the number of videos will scare people away
	// showing the precentage for every video introduce stress
	if (index == 0) {last_progress = 0;}
	let progress = (index+1)/(vids.items.length)*100;
	if (progress - last_progress > 10) {
		$('#submit_info').html(parseInt(progress) + '% Done :)');
		last_progress = progress;
	} else {
		$('#submit_info').html('');
	}

	// (index+1) + " out of " + (vids.items.length)
	// instead of showing the exact number, it's better to show a percentage
	$('#traintest').show(); // video and slider
	$('#main-slider').hide();
	$('#btnDidntSeeVideo').show();
	// show video

		// // we cannot know if it's borken when preparing it.
		// // it's not ready yet

		// video.readyState == 4
		// wait until it's ready or borken
		currentVid = vids.elements[index];
		currentVid.controls = debug_mode;
		document.getElementById("divVideo").appendChild(currentVid);


		currentVid.play();
		console.log(currentVid.duration); // sometime it's NaN. if the metadata is not ready, then it's nan

		// if error, load it gain
		// start counting video start playing
		var t00 = performance.now();
		var donewatching = function() {
			if (currentVid != null) {
				// is it possible currentVid changed? No
				show_slider(vids);
				var t0 = currentVid.timeStart;
				if (t0 != undefined) {
					 t00 = t0; // wait until time runs out
				}
				var t1 = performance.now();
				// let duration = isNan(currentVid.duration)?
				delay =  ((t1 - t00)/1000) - currentVid.duration; // now the duration is ready
				// the same video? what if it get replaced?
				train_delay += delay;
				if (phase == 'train') {
					checkStalls();
				}
				if (phase == 'test') {
					if(delay > 1){
						stall_count += 1;
					}
				}
				// sessionStorage['delay'] = isNaN(delay)? 'start=' + t00 + ';end=' + t1 + ';duration=' + currentVid.duration : delay;
				sessionStorage['delay'] = delay;
				if (isNaN(delay)) { // only for nan videos
					let selected = $('#nanDelay');
					let info = currentVid.src + ' :start=' + t00.toFixed(2) + '&end=' + t1.toFixed(2) + '&duration=' + currentVid.duration;
					if (selected.val() == "unset") {
						selected.val(info);
					} else { // append the value
						selected.val(selected.val() + ' | ' + info);
					}
				}
				console.log("Time taken: " + (t1 - t0)/1000);
				console.log("Train Delay: " + train_delay);
				console.log("Delay: " + delay);
				currentVid.remove();
				currentVid = null;
			}
		}
		// Set the timeout in case there are something wrong going on
		{% if maxDurationMs > 0 %}
		if(timeout != null) {clearTimeout(timeout);}
		timeout = setTimeout(donewatching, {{ maxDurationMs }});
		{% endif %}
		// normal way
		currentVid.addEventListener('ended', donewatching);
		return true;
}


// golden video broken

function survey() {
	// $('#instruction').hide();
  // $('#report_video').hide();
	hide_all();
	$('#survey').show();
	$('#short_instructions').detach();
	// $('#divNextButton').show();
	// $('#nextButton').addAttr("disabled");
	// $('#nextButton').prop("disabled", true);
}

function done() {
	// configuration and thanks
	alert('Well done! Click the submit button');

	$('#done').show();
	// $('#survey_box').animate({right: '-100%'});
	$('#survey').hide();
	$('#divNextButton').hide();
	$("#submitButton").show();
  $("#submitButton").prop('disabled', false);
	$("#submitButton").css("visibility", "visible");

	$('#debugInfo').val(p.items.join(';'));
	$('<input/>').attr({type:'hidden',name:'welldone',value:'yes'}).appendTo('#survey');
}



function next(_phase=phase) {
	phase = _phase
	console.log('[' + phase + ']');
	{% if fullscreen %}
		if( window.innerHeight != screen.height) {
			openFullscreen();
		}
	{% endif %}

  // update phase
  switch (phase) {
		case 'instruction': instruction();  phase = 'quiz';        break;
		case 'quiz':			  quiz();
			prepare_vid(t, 0);
			prepare_vid(p, 0);
		  phase = 'pre_train';   break;
		case 'pre_train':	  pre_train();    phase = 'train';       break;
		case 'pre_test':    pre_test();     phase = 'test';        break;
		case 'survey':      survey();       phase = 'done';        break;
		case 'done':        done();         break;
		case 'reject':      break;

		case 'train':
			show_vid(t); t.idx++;
			if (t.idx == t.items.length) { phase = 'pre_test'; }
			else {prepare_vid(t, t.idx);}
			break;
    case 'test':
			show_vid(p); p.idx++;
			// prepare next video
			if (p.idx == p.items.length) { phase = 'survey'; }
			else {
				prepare_vid(p, p.idx);
				// if (p.elements[p.idx].src.includes('https://drive.google.com/')) {
				// 	console.log(p.items[p.idx] + p.elements[p.idx].readyState);
				// 	p.elements[p.idx].load(); //
				// }
			}
			break;

    default:
      break;
  }
}

function submitAnswer() {
		// update user interface ----------------------------
		// $('#main-slider').animate({top: '-2000px'});
		$('#buttonA').hide();

		// recording information -----------------------------
		var final_val = document.getElementById("points").value
		var init_val = sessionStorage['initialVal'] || 'defaultValue';
		var delay = sessionStorage['delay'] || 'defaultValue'; // sessionStorage['delay'] is null


		var attributes = [];

		$('#attributes').find('input[type=checkbox]:checked').each( (index, item) => {
				attributes.push(item.value);
		});
		attributes.push(document.getElementById("textbox_input").value)
		// select the correct index
		if (p.idx>0) { // set if phase == test -- will lose the last rating!!!
			var name = p.items[p.idx-1]
			var r = [...labels, ...backup, ...golden].indexOf(name) // videos1 to vides 82 and then backup videos

			// golden video or broken video (backup loaded, we have 80 backup videos)
			if (r == -1) {selected = $("input[name='" + name + "']");}
			else {selected = $("#videos"+(r+1)); } // double-checked, r start with 0 while videos start with 1
			// selected = $("#selection"+(p.idx)) // be carefull +1 -1

			if (selected.val() == "unset") {
				selected.val(init_val+"/"+final_val+"/" + attributes + "/" + delay);
			} else { // append the value
				selected.val(selected.val() + ' | ' + init_val+"/"+final_val+"/" + attributes + "/" + delay);
			}

			console.log( selected.attr('name') + ' ' + name + ' ---> ' + selected.val() );
	    $("#status-test"+p.idx).css("background-color", "green");
			$('#sub_butA').attr("disabled",true);

			// rejection ----------------------------------
	    $('#sub_butA').trigger('rejection_check');
		} else {
			$("#status-train"+t.idx).css("background-color", "green");
		}

    next();
}

$(document).ready(function(){
	// ui --------------------------

  $("#submitButton").hide(); // not working on AMT anymore, why?
  $("#submitButton").prop('disabled', true);
  if (is_assigned) {
      $('#nextButton').removeAttr('disabled');
      $('#nextButton').html('Start!');
  }

	{% if debug %}
	dbg();
	{% endif %}
  next(); // phase = 'instruction'

//   $(document).keyup(function(e) {
//      if (e.key === "Escape") { // escape key maps to keycode `27`
//         // <DO YOUR WORK HERE>
//
//   			alert('Browser is in not in fullscreen');
// 				openFullscreen();
//
//     }
// };);
});