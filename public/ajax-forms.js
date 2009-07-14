var ajax_reqs = 0
function pushAjax(elm) { ajax_reqs += 1; if(ajax_reqs == 1) throb(); }
function popAjax(elm)  { ajax_reqs -= 1; if(ajax_reqs == 0) stopThrob(); }

function throb() {   $("throb").show(100); }
function stopThrob() { $("throb").hide(100); }

function fadeRepace(elem, replacement) {
	var replaceIt = function(){
		replacement.css('opacity',0.5)
		elem.replaceWith(replacement);
		$(replacement).animate({'opacity':1, 'speed':500});
	}
	elem.animate({'opacity':0.5, 'speed':500}, "easeOutQuad", replaceIt);
}

function ajaxify(base) {
	if (!base) { base = document.body; }
	$("form.ajax", base).submit(function() {
		frm = $(this);
		if($("input[name=ajax]", frm).length > 0) {
			alert("already submitted!");
			return false;
		}
		alert("submitting!");
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
			},
			success: function(data, status) {
				data = "<h2>TADA!</h2>"
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
				ajaxify(html);
				meth = $("input[name=meth]", frm).val();
				if(meth == "replace") {
					fadeRepace(target, html);
				} else if(meth == "remove") {
					if(data.length > 0) {
						console.error("replacement HTML is nonzero: " + data);
					}
					target.hide(1000, function(){target.remove()});
				} else {
					html.hide();
					if(meth == "before"){
						target.prepend(html);
					} else {
						target.append(html);
					}
					html.show(1000);
				}
			},
		});
		return false; // stop propagation
	});
	return "done"
}

$(function(){ajaxify()});
