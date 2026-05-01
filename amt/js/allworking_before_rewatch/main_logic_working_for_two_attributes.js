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
    var init_val = Math.floor(Math.random() * 100);
    sessionStorage['initialVal'] = init_val;
    $('#attributes').find('input[type=checkbox]:checked').removeAttr('checked');
    document.getElementById('points').value = init_val;
    document.getElementById("textbox_input").value = "";
    $('#textbox').hide();
    $('#short_instructions').show();
    $('#buttonA').hide();
    $('#main-slider').show();
    $('#points').change(function() {
      $('#buttonA').show();
      $('#report_video').show();
      $('#sub_butA').prop('disabled', false);
    });
  }
  
  var last_progress = 0;
  var timeout = null;
  
  function show_vid(vids, index = null) {
    if (index == null) index = vids.idx;
    if (index >= vids.items.length || index < 0) return false;
    prepare_vid(vids, index);
    hide_all();
  
    if (index === 0) last_progress = 0;
    let progress = ((index + 1) / vids.items.length) * 100;
    if (progress - last_progress > 10) {
      $('#submit_info').html(parseInt(progress) + '% Done :)');
      last_progress = progress;
    } else {
      $('#submit_info').html('');
    }
  
    $('#traintest').show();
    $('#main-slider').hide();
    $('#btnDidntSeeVideo').show();
  
    currentVid = vids.elements[index];
    currentVid.controls = debug_mode;
    document.getElementById("divVideo").appendChild(currentVid);
    currentVid.play();
  
    var t00 = performance.now();
    var donewatching = function() {
      if (!currentVid) return;
      show_slider(vids);
  
      var t0 = currentVid.timeStart;
      if (t0 !== undefined) t00 = t0;
      var t1 = performance.now();
      var delay = ((t1 - t00) / 1000) - currentVid.duration;
      sessionStorage['delay'] = delay;
  
      if (isNaN(delay)) {
        let selected = $('#nanDelay');
        let info = currentVid.src +
                   ' :start=' + t00.toFixed(2) +
                   '&end=' + t1.toFixed(2) +
                   '&duration=' + currentVid.duration;
        if (selected.val() === "unset") selected.val(info);
        else selected.val(selected.val() + ' | ' + info);
      }
  
      currentVid.remove();
      currentVid = null;
    };
  
    {% if maxDurationMs > 0 %}
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(donewatching, {{ maxDurationMs }});
    {% endif %}
    currentVid.addEventListener('ended', donewatching);
    return true;
  }
  
  function survey() {
    hide_all();
    $('#survey').show();
    $('#short_instructions').detach();
  }
  
  function done() {
    alert('Well done! Click the submit button');
    $('#done').show();
    $('#divNextButton').hide();
    $("#submitButton").show().prop('disabled', false).css("visibility", "visible");
    $('#debugInfo').val(p.items.join(';'));
    $('<input/>', { type:'hidden', name:'welldone', value:'yes' }).appendTo('#survey');
  }
  
  function next(_phase = phase) {
    phase = _phase;
    console.log('['+ phase +']');
    {% if fullscreen %}
      if (window.innerHeight != screen.height) openFullscreen();
    {% endif %}
  
    switch (phase) {
      case 'instruction':
        instruction();
        phase = 'quiz';
        break;
      case 'quiz':
        quiz();
        prepare_vid(t, 0);
        prepare_vid(p, 0);
        phase = 'pre_train';
        break;
      case 'pre_train':
        pre_train();
        phase = 'train';
        break;
      case 'pre_test':
        pre_test();
        phase = 'test';
        break;
      case 'survey':
        survey();
        phase = 'done';
        break;
      case 'done':
        done();
        break;
      case 'reject':
        break;
      case 'train':
        show_vid(t);
        t.idx++;
        if (t.idx == t.items.length) phase = 'pre_test';
        else prepare_vid(t, t.idx);
        break;
      case 'test':
        show_vid(p);
        p.idx++;
        if (p.idx == p.items.length) phase = 'survey';
        else prepare_vid(p, p.idx);
        break;
      default:
        break;
    }
  }
  
  function submitAnswer() {
    // hide the slider and button
    $('#buttonA').hide();
  
    // gather times and slider
    var final_val = document.getElementById("points").value;
    var init_val = sessionStorage['initialVal']  || 'defaultValue';
    var delay    = sessionStorage['delay']       || 'defaultValue';
  
    // collect all attributes in order
    var attributes = [];
  
    // ▶ New radio attributes from the slider panel
    var sharpnessVal = document.querySelector('input[name="sharpness"]:checked')?.value || "";
    if (sharpnessVal) attributes.push(sharpnessVal);
    var artifactsVal = document.querySelector('input[name="artifacts"]:checked')?.value || "";
    if (artifactsVal) attributes.push(artifactsVal);
    var colorVal = document.querySelector('input[name="color"]:checked')?.value || "";
    if (colorVal) attributes.push(colorVal);
    var immersionVal = document.querySelector('input[name="immersion"]:checked')?.value || "";
    if (immersionVal) attributes.push(immersionVal);
  
    // ▶ Existing modal checkboxes
    $('#attributes').find('input[type=checkbox]:checked').each((i, item) => {
      attributes.push(item.value);
    });
  
    // ▶ Existing free‐text “Other” input
    attributes.push(document.getElementById("textbox_input").value);
  
    // ▶ Now append to the appropriate AMT hidden fields
    if (p.idx > 0) {
      var name = p.items[p.idx-1];
      var r = [...labels, ...backup, ...golden].indexOf(name);
      var selected = (r == -1)
        ? $("input[name='"+ name +"']")
        : $("#videos"+ (r+1));
      var entry = init_val + "/" + final_val + "/" + attributes + "/" + delay;
  
      if (selected.val() == "unset") {
        selected.val(entry);
      } else {
        selected.val(selected.val() + " | " + entry);
      }
  
      console.log(selected.attr('name') + ' ' + name + ' ---> ' + selected.val());
      $("#status-test"+p.idx).css("background-color","green");
      $('#sub_butA').prop("disabled", true).trigger('rejection_check');
    } else {
      $("#status-train"+t.idx).css("background-color","green");
    }
  
    next();
  }
  
  $(document).ready(function() {
    $("#submitButton").hide().prop('disabled', true);
    if (is_assigned) {
      $('#nextButton').removeAttr('disabled').html('Start!');
    }
    {% if debug %} dbg(); {% endif %}
    next();
  });
  