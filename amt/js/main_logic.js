function dbg() {
    $('#debug-shortcut').toggle();
    $('span[id^=status]').toggle();
    debug_mode = !debug_mode;
    return debug_mode;
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
    if (!p) return;
    hide_all();
    // Reset learnMoreClicks at the start of training phase
    learnMoreClicks = {
      sharpness: 0,
      artifacts: 0,
      immersion: 0
    };
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
    // ── Reset all previous selections ──────────────────────────────
    // 1. Clear the three new radio groups
    $('input[name="sharpness"], input[name="artifacts"], input[name="immersion"]')
      .prop('checked', false);
    // 2. Clear the modal checkboxes
    $('#attributes').find('input[type=checkbox]').prop('checked', false);
    // 3. Hide any leftover popover from validation
    $('#sub_butA').popover('hide');
    // 4. Disable submit until slider moves
    $('#sub_butA').prop('disabled', true);
  
    // Hide Learn More links during testing phase
    if (phase === 'test') {
      $('.learn-more').hide();
    } else {
      $('.learn-more').show();
    }
  
    // ── Original slider setup logic ────────────────────────────────
    const init_val = Math.floor(Math.random() * 100);
    sessionStorage['initialVal'] = init_val;
    document.getElementById('points').value = init_val;
    document.getElementById('textbox_input').value = "";
    $('#textbox').hide();
    $('#short_instructions').show();
    $('#buttonA').hide();
    $('#main-slider').show();
  
    // ── Re-bind slider change to enable submit ────────────────────
    $('#points').off('change').on('change', function() {
      $('#buttonA, #report_video').show();
      $('#sub_butA').prop('disabled', false);
    });
  }
  
  function show_vid(vids, index = null) {
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
  
  function survey() {
    hide_all();
    $('#survey').show();
    $('#short_instructions').detach();
  }
  
  function done() {
    alert('Well done! IMPORTANT: Please click the SUBMIT button below to complete your task!');
    $('#done').show();
    $('#divNextButton').hide();
    $('#submitButton').show().prop('disabled', false).css('visibility','visible');
    $('#debugInfo').val(p.items.join(';'));
    $('<input/>',{type:'hidden',name:'welldone',value:'yes'}).appendTo('#survey');
  }
  
  function next(_phase = phase) {
    phase = _phase;
    console.log('['+phase+']');
    {% if fullscreen %}
    if( window.innerHeight != screen.height) {
        openFullscreen();
    }
    {% endif %}
  
    // update phase
    switch (phase) {
      case 'instruction': instruction();  phase = 'quiz';        break;
      case 'quiz':        quiz();
          prepare_vid(t, 0);
          prepare_vid(p, 0);
        phase = 'pre_train';   break;
      case 'pre_train':   pre_train();    phase = 'train';       break;
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
          }
          break;
  
      default:
        break;
    }
  }
  
  var learnMoreClicks = {
    sharpness: 0,
    artifacts: 0,
    immersion: 0
  };

  function openAttributePage(attribute) {
    // Only allow Learn More clicks during training phase
    if (phase !== 'train') {
      return;
    }
    learnMoreClicks[attribute]++;
    const pages = {
      'sharpness': 'https://gaming-vqa.s3.us-east-2.amazonaws.com/example-samples/amt_intro/sharpness.htm',
      'artifacts': 'https://gaming-vqa.s3.us-east-2.amazonaws.com/example-samples/amt_intro/artifacts.htm',
      'immersion': 'https://gaming-vqa.s3.us-east-2.amazonaws.com/example-samples/amt_intro/immersion.htm'
    };
    
    if (pages[attribute]) {
      window.open(pages[attribute], '_blank');
    }
  }

  function submitAnswer() {
    // Check if we're in training phase and haven't clicked enough
    if (phase === 'train') {
      const minClicks = 1;
      const missingClicks = [];
      
      if (learnMoreClicks.sharpness < minClicks) missingClicks.push('Clarity');
      if (learnMoreClicks.artifacts < minClicks) missingClicks.push('Pixelation & Blockiness');
      if (learnMoreClicks.immersion < minClicks) missingClicks.push('Immersive Game Experience');
      
      if (missingClicks.length > 0) {
        alert('Please click "Learn More" at least once for each of these attributes:\n' + 
              missingClicks.join('\n') + '\n\nYou can click these links to learn more about each attribute.');
        return;
      }
    }

    // ❗️Require each attribute before proceeding
    var required = [
      {name:'sharpness', label:'Clarity'},
      {name:'artifacts',  label:'Pixelation & Blockiness'},
      {name:'immersion',  label:'Immersive Game Experience'}
    ];
    var missing = required
      .filter(function(a) { return !document.querySelector('input[name="' + a.name + '"]:checked'); })
      .map(function(a) { return a.label; });
    if (missing.length) {
      var msg = 'Please rate: ' + missing.join(', ');
      $('#sub_butA')
        .attr('data-content', msg)
        .popover('show');
      return;
    }
  
    $('#sub_butA').popover('hide');
    $('#buttonA').hide();
  
    // Slider + timing (using var)
    var final_val = document.getElementById('points').value;
    var init_val  = sessionStorage['initialVal'] || 'defaultValue';
    var delay     = sessionStorage['delay']      || 'defaultValue';
  
    // Collect all attributes in desired order:
    var attributes = [];
  
    // 1–4: the new radio groups
    ['sharpness','artifacts','immersion'].forEach(function(name) {
      var v = document.querySelector('input[name="' + name + '"]:checked');
      if (v) attributes.push(v.value);
    });
  
    // 5–n: existing modal checkboxes
    $('#attributes').find('input[type=checkbox]:checked').each(function(_,el) {
      attributes.push(el.value);
    });
  
    // last: free-text "Other"
    attributes.push(document.getElementById('textbox_input').value);
  
    // Push into AMT hidden fields exactly as original:
    if (p.idx > 0) {
      var name = p.items[p.idx-1];
      var r = [].concat(labels, backup, golden).indexOf(name);
      var selected = (r === -1)
        ? $('input[name="' + name + '"]')
        : $('#videos' + (r+1));
      var entry = init_val + '/' + final_val + '/' + attributes + '/' + delay;
  
      if (selected.val() === 'unset') {
        selected.val(entry);
      } else {
        selected.val(selected.val() + ' | ' + entry);
      }
  
      console.log(selected.attr('name') + ' ' + name + ' ---> ' + selected.val());
      $('#status-test' + p.idx).css('background-color','green');
      $('#sub_butA').prop('disabled', true).trigger('rejection_check');
    } else {
      $('#status-train' + t.idx).css('background-color','green');
    }
  
    next();
  }
  
  
  $(document).ready(() => {
    $('#submitButton').hide().prop('disabled',true);
    if (is_assigned) {
      $('#nextButton').removeAttr('disabled').html('Start!');
    }
    {% if debug %} dbg(); {% endif %}
    next();
// Re-watch button: replay the current video, then return to rating
// $('#rewatchButton').on('click', function() {
//     if (phase === 'train') {
//       show_vid(t, t.idx - 1);
//     } else if (phase === 'test') {
//       show_vid(p, p.idx - 1);
//     }
//   });

// updated code to use the new rewatch button
// ── Re-watch button ───────────────────────────────────────────────
// Always replay the same clip, even when it's the last test/train video.
  // ── Re-watch Button ─────────────────────────────────────────────────────
  $('#rewatchButton').on('click', function() {
    let vids, idx;
    if (phase === 'train' || phase === 'pre_test') {
      vids = t;
      idx  = (phase === 'train') ? (t.idx - 1) : (t.items.length - 1);
    } else {
      vids = p;
      idx  = (phase === 'test') ? (p.idx - 1) : (p.items.length - 1);
    }
    show_vid(vids, idx);
  });

  });
  
// ── RE-WATCH SETUP ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  var rewatchBtn = document.getElementById('rewatchButton');
  if (rewatchBtn) {
    rewatchBtn.addEventListener('click', function() {
      // find the <video> inside #divVideo, rewind & play
      var vid = document.querySelector('#divVideo video');
      if (vid) {
        vid.currentTime = 0;
        vid.play();
      }
    });
  }
});

