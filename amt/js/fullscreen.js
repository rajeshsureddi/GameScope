{% if fullscreen %}
var elem = document.documentElement;
function openFullscreen() {
	if (elem.requestFullscreen) {
		elem.requestFullscreen();
	} else if (elem.mozRequestFullScreen) { /* Firefox */
		elem.mozRequestFullScreen();
	} else if (elem.webkitRequestFullscreen) { /* Chrome, Safari & Opera */
		elem.webkitRequestFullscreen();
	} else if (elem.msRequestFullscreen) { /* IE/Edge */
		elem.msRequestFullscreen();
	}
}

document.onfullscreenchange = function () {
	if( window.innerHeight != screen.height) {
		alert('Browser is not in fullscreen. Please revert back.');
		openFullscreen();
    // browser is fullscreen
	}
}
{% endif %}
