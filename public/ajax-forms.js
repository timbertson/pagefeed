var ajax_reqs = 0
function pushAjax(elm) { ajax_reqs += 1; if(ajax_reqs == 1) throb(); }
function popAjax(elm)  { ajax_reqs -= 1; if(ajax_reqs == 0) stopThrob(); }

function throb() {     $("throb").show(100); }
function stopThrob() { $("throb").hide(100); }

var transition_speed = 1000; // 1 second

function fadeRepace(elem, replacement) {
	var fadeout_opacity = 0.2;
	var replaceIt = function(){
		replacement.css('opacity',fadeout_opacity)
		elem.replaceWith(replacement);
		$(replacement).animate({'opacity':1, 'speed':transition_speed/2});
	}
	elem.animate({'opacity':fadeout_opacity, 'speed':transition_speed/2}, "linear", replaceIt);
}

function markup(base) {
	// apply all unobtrusive JS to an element tree
	if (!base) { base = document.body; }
	ajaxify(base);
	makeToggles(base);
}

function ajaxify(base) {
	if (!base) { base = document.body; }
	$("form.ajax", base).submit(function() {
		frm = $(this);
		if($("input[name=ajax]", frm).length > 0) {
			alert("already submitted!");
			return false;
		}
		ajaxFlag = $("<input name=\"ajax\" type=\"hidden\" value=\"true\" />", document)
		frm.prepend(ajaxFlag);
		pushAjax(frm);
		console.log("submitting:" + frm.attr("action"));
		console.log("via:" + frm.attr("method"));
		console.log("data: " + frm.serialize());
		$.ajax({
			url: frm.attr("action"),
			type: frm.attr("method"),
			data: frm.serialize(),
			dataType: "html",
			complete: function() { ajaxFlag.remove(); popAjax(frm); },
			error: function(xhr, textStatus, err) {
				alert("fail!");
				$(err, document).dialog({
					modal:True,
					draggable: false,
					hide: 'slide',
					show: 'fade',
					title: 'Error:'
					resizeable: false,
					dialogClass: 'dialog'
				});
			},
			success: function(data, status) {
				console.log("Success!");
				console.log(status);
				console.log(data);
				target_sel = $("input[name=dest]", frm).val();
				if(target_sel[0] == '#'){
					target = $(target_sel);
				} else {
					target = frm.closest(target_sel);
				}
				console.log("target: " + target);
				html = $(data, document);
				console.log("html: " + html);
				markup(html);
				meth = $("input[name=meth]", frm).val();
				if(meth == "replace") {
					fadeRepace(target, html);
				} else if(meth == "remove") {
					if($.strip(data).length > 0) {
						console.error("replacement HTML is nonzero: " + data);
					}
					target.hide(transition_speed, function(){target.remove()});
				} else {
					html.hide();
					if(meth == "before"){
						target.prepend(html);
					} else {
						target.append(html);
					}
					html.show(transition_speed);
				}
			},
		});
		return false; // stop propagation
	});
	return "done"
}

function makeToggles(base) {
	var toggleSelector = ".toggleContent";
	$(toggleSelector).each(function(){
		container = $(this).closest(".toggleContainer");
		if(container.length == 0){
			toggleButton = $("<img class=\"toggleButton\" src=\"public/toggle.gif\" />", document)
			container.append(toggleButton);
			toggleButton.click(function() {
				$(toggleSelector, this).toggle(transition_speed);
				return false;
			});
		}
	})
}

document.write("<style> .startHidden { display: none; } </style>"); // hide toggleable content by default (but only if JS is enabled)

$(function(){markup()});

