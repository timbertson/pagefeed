var ajax_reqs = 0
function pushAjax(elm) { ajax_reqs += 1; if(ajax_reqs == 1) throb(); }
function popAjax(elm)  { ajax_reqs -= 1; if(ajax_reqs == 0) stopThrob(); }

function throb() {     $(".throb").fadeIn(100); }
function stopThrob() { $(".throb").fadeOut(100); }

var info;
var debug;
if(typeof(console) != "undefined") {
	// chrome doesn't like native code (i.e console.log) bound to
	// JS variables - so we curry it manually:
	info = function(s) { console.log(s) };
	debug = info;
} else {
	info = function(s) { alert(s) };
	debug = function(s) {}; // nothing to do
}

var transition_speed = 250; // 1/4 second

var fadeout_opacity = 0.2;
function fadeRepace(elem, replacement) {
	if(replacement) {
		replacement.css('opacity',fadeout_opacity)
		elem.replaceWith(replacement);
		elem = replacement;
	}
	elem.animate({'opacity':1, 'speed':transition_speed/2});
}

function markup(base) {
	// apply all unobtrusive JS to an element tree
	if (!base) { base = document.body; }
	ajaxify(base);
	makeToggles(base);
}

function ajaxify(base) {
	$("form.ajax", base).submit(function() {
		var frm = $(this);
		var ajax_flag = function(){ return $("input[name=ajax]", frm); }
		if(ajax_flag.length > 0) {
			alert("already submitted!");
			return false;
		}
		frm.prepend("<input name=\"ajax\" type=\"hidden\" value=\"true\" />");
		pushAjax(frm);

		var method = $("input[name=meth]", frm).val();
		var target_sel = $("input[name=dest]", frm).val();
		var target;
		if(target_sel[0] == '#'){
			target = $(target_sel);
		} else {
			target = frm.closest(target_sel);
		}
		if(target.length ==0) info("no target!");
		if(method == "replace"){
			target.animate({'opacity':fadeout_opacity, 'speed':transition_speed/2});
		}
		
		$.ajax({
			url: frm.attr("action"),
			type: frm.attr("method"),
			data: frm.serialize(),
			dataType: "html",
			complete: function() { ajax_flag().remove(); popAjax(frm); },
			error: function(xhr, textStatus, err) {
				if(method=='replace') {
					fadeRepace(target);
				}
				dlg = $(xhr.responseText, document);
				dlg.dialog({
					modal:true,
					draggable: false,
					hide: 'slide',
					// show: 'show', //FIXME: why doesn't this work?
					title: 'Error:',
					resizeable: true,
					width:600,
					height:'auto',
					position:['center',50],
					beforeclose: function(ev, ui) { debug("removing dialog..."); dlg.remove(); }, //FIXME: why so awkward?
					dialogClass: 'dialog'
				});
			},
			success: function(data, status) {
				debug("Success!");
				var html = $(data, document);
				markup(html);
				$("input[type=text]", frm).val(''); // reset form values
				if(method == "replace") {
					fadeRepace(target, html);
				} else if(method == "remove") {
					if(data.length > 0) {
						console.error("replacement HTML is nonzero: " + data);
					}
					target.slideUp(transition_speed, function(){target.remove()});
				} else {
					if(data.length > 0) {
						$(".placeholder", target).slideUp(); // remove any placeholder for emty content
						html.slideUp();
						if(method == "before"){
							target.prepend(html);
						} else {
							target.append(html);
						}
						html.hide().slideDown(transition_speed);
					}
				}
			},
		});
		return false; // stop propagation
	});
}

function makeToggles(base) {
	var toggleSelector = ".toggleContent";
	$(toggleSelector, base).each(function(){
		var container = $(this).closest(".toggleContainer");
		if (container.length == 0) {
			info("no container for toggleContent!");
			return;
		}
		if($(".toggleButton", container).length == 0){
			var toggleButton = $("<div class=\"toggleButton\"></div>", document);
			container.prepend(toggleButton);
			toggleButton.click(function() {
				$(toggleSelector, container).slideToggle(transition_speed);
				return false;
			});
		}
	})
}

document.write("<style> .startHidden { display: none; } </style>"); // hide toggleable content by default (but only if JS is enabled)

$(function(){markup()});

