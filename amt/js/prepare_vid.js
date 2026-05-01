// load jinja2 python variables here, avoid loading in the context
var golden = {{goldVids | safe}};
var trains = {{trainVids | safe}};
var labels = {{labelVids | safe}};
var backup = {{backupVids | safe}}; // don't shuffle backup videos, if there is one borken video, we will always have backup1 rated instead.
var backupIndex = 0;
var repeat = [];
var arr = [];
while(arr.length < {{n_repeat}}){
  var r = Math.floor(Math.random() * labels.length );
  if(arr.indexOf(r) === -1){
    repeat.push(labels[r]);
    arr.push(r);
  }
} // https://stackoverflow.com/a/2380113

var debug_mode = false; // false initally, will be updated later
var currentVid = null;

var t = {}; // training videos
var p = {}; // testing videos, including repeated, golden, and label videos
t.idx = 0;
p.idx = 0;
var min_distance = 8;

// function shuffle(array) {
//   array.sort(() => Math.random() - 0.5);
// }
// https://javascript.info/task/shuffle
function shuffle(array) {
  for (let i = array.length - 1; i > 0; i--) {
    let j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
}
function wait(timeout) {
    return new Promise(resolve => {
        setTimeout(resolve, timeout);
    });
}
function prepare_backup_vid(vids, index) {
  let new_name = backup[backupIndex];
  console.log('Error when loading video '+ v.src + ' Replaced with ' + new_name);
  backupIndex++;
  backupIndex = backupIndex % backup.length; // avoid array overflow
  vids.items[index] = new_name; // also need to update the name of the repeated video
  // better to update current video element instead of removing it
  // vids.items[vids.items.lastIndexOf(name)] = new_name;
  v.loadFailTimes = 0;
  prepare_vid(vids, index, update=true);
}

// if trigger next, it will bring a lot of data transfer
// no return value, can't know whether is ready or not
function prepare_vid(vids, index, update=false, trigger_next=false) {
  // name = vids.items[index];
  // since name was deprecated, we will use new variable 
  let name = vids.items[index];

  if (vids.elements[index] == 'broken'){return false;}

  // already loaded
  if ((typeof vids.elements[index] !== 'undefined') && (update==false) ){return true;}
  v = update ?  vids.elements[index] : document.createElement('video');

  if (golden.indexOf(name) != -1) {
      v.src = name.includes('http') ? name : '{{baseGoldUrl}}' + name + '.mp4'; // don't support google drive now
  }
  else{
      v.src = name.includes('http') ? name : '{{baseUrl}}' + name + '.mp4'; // don't support google drive now
  }

  // Add 'raw' tag if using github URLs
  if (v.src.includes('github') && !name.includes('http'))
      v.src = v.src + '?raw=true'

  v.preload = 'auto';  // https://www.geeksforgeeks.org/html-video-preload-attribute/
	// type: 'video/mp4'
  v.muted = true;
	v.controls = false; // {% if debug %} true {% else %} false {% endif %};

  load_start = performance.now();

  if(trigger_next) {
    v.addEventListener("canplaythrough", function(){
      if (index+1 < arr.length) {
          prepare_vid(arr[index+1], index+1, arr, elements);
      }
    } );
  }

  if (vids == t) {v.addEventListener("canplaythrough", trainLoadTime);}

	{% if showprogress %}
  // let type = v == t ? 'train':'test';
	// use addEventListener to append listener otherwise it will get overwritten for repeated videos
  v.addEventListener("loadstart", function(){$("#status-"+vids.type+(index+1)).css("background-color", "blue"); console.log("loadstart video "+v.src);});
	v.addEventListener("error", function(){$("#status-"+vids.type+(index+1)).css("background-color", "red"); console.log("loadeddata video "+v.src);});
	v.addEventListener("canplay", function(){$("#status-"+vids.type+(index+1)).css("background-color", "orange"); console.log("canplay video "+v.src);});
	v.addEventListener("canplaythrough", function(){$("#status-"+vids.type+(index+1)).css("background-color", "yellow"); console.log("canplaythrough video "+v.src);});
  v.addEventListener("play", function(){this.timeStart=performance.now();$("#status-"+vids.type+(index+1)).css("background-color", "Violet"); console.log("play video "+v.src);});
	// v.onprogress = function() {console.log("Downloading video {{vid}}");};

  let r = backup.indexOf(name); // item didn't change
  if( r!= -1) {
    // backup videos
    $("#status-"+vids.type+(index+1)).append('->b' +(r+1) );
  }
  {% endif %}

	// https://www.sitepoint.com/create-one-time-events-javascript/

  if(typeof v.loadFailTimes == 'undefined') { v.loadFailTimes = 0; }
	v.addEventListener('error', function() {
      v.loadFailTimes ++;
      if (v.loadFailTimes == 3) {
        {% if useBackupVids %}
        // debug video will also be reloaded
        // assume backup vids are always playable
          prepare_backup_vid(vids, index);
        {% else %}
          // fix the backup video or
          // video83 - backup one
          vids.elements[index] = 'broken';
          // this.remove();
          // load next one!!!
          if (index+1 < arr.length) {
              prepare_vid(vids, index+1);
          }
          if (currentVid == this) {
            show_vid(vids);
            console.log('Error occured when playing. Loadding: '+ v.src);
          }
        {% endif %}
      } else {
        wait(500); // 0.5 s
        this.load(); // simply load it again
      }

      // play the video
      if (currentVid == this) {
        this.play();
        console.log('Error occured when playing. Loadding: '+ v.src);
      }
      // try to load this video again
      // https://dinbror.dk/blog/how-to-preload-entire-html5-video-before-play-solved/
      // solution 4 ajax not working CORS problem
      // prepare_vid(name, index, arr, elements, update=true);
	});
	vids.elements[index] = v; // name --> video

  if( repeat.indexOf(name) != -1) {
      // also set the repeated one but only if it canplay, (it might be broken and replaced)
      // this could be a borken one, old name?
      let idx = vids.items.lastIndexOf(name); // name changed?
      if(index != idx) {
        v.addEventListener('canplay', function() {
          // don't clone or use the element, keep it seperate
          vids.items[idx] = vids.items[index]; // might be changed to backup videos
          prepare_vid(vids, idx);
        } );
      }
  }
  return true;
}

$(document).ready(function(){
  // wait until document ready, since we need to update elements when loading the videos
  t.items = [];
  t.items.push(...trains);

  p.items = [];
  p.items.push(...labels);
  p.items.push(...repeat);
  p.items.push(...golden);


  shuffle(t.items);

  shuffle(p.items);
  shuffle(p.items);
  shuffle(p.items);

  {% if checkdistance %}
  // it will change the arr dyncamically...
  repeat.forEach( function(v, idx) {
    // find occurances:
    var first = p.items.indexOf(v);
    var second = p.items.indexOf(v, first+1);

    if (second - first < min_distance) {
      // console.log('-------Distance change: ' + idx + ':' + first + '-' +  second)
      var i = second
      var j = ( first + min_distance ) % p.items.length;
      [p.items[i], p.items[j]] = [p.items[j], p.items[i]];
    }
  } );
  {% endif %}

  p.elements = []
  p.type = 'test'
  t.elements = []
  t.type = 'train'

  {% if showprogress %}
  p.items.forEach( function(name, index, vids) {
    if (labels.indexOf(name) != -1) {
      // label videos
      $("#status-test"+(index+1)).html(labels.indexOf(name)+1);
      $("#status-test"+(index+1)).css("outline", "");
      if (repeat.indexOf(name) != -1) {
        // repeat videos
        $("#status-test"+(index+1)).css("outline-color", "black");
        $("#status-test"+(index+1)).css("outline-width", repeat.indexOf(name)+1);
        $("#status-test"+(index+1)).css("outline-style", "solid");
      }
    }
    else if (golden.indexOf(name) != -1) {
      // gold videos
      $("#status-test"+(index+1)).html('g'+(golden.indexOf(name)+1) );
      $("#status-test"+(index+1)).css("outline-color", "orange");
      $("#status-test"+(index+1)).css("outline-width", golden.indexOf(name)+1);
      $("#status-test"+(index+1)).css("outline-style", "dotted");
    }
    else {}
  } );
  t.items.forEach( function(name, index, vids) {
    $("#status-train"+(index+1)).html(trains.indexOf(name)+1);
    $("#status-train"+(index+1)).css("outline", "");
  } );
  {% endif %}

  // load one by one or in parallel

});
