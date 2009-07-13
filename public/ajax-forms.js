var ajax_reqs = 0
function pushAjax() { ajax_reqs += 1; if(ajax_reqs == 1) throb(); }
function popAjax()  { ajax_reqs -= 1; if(ajax_reqs == 0) stopThrob(); }

function throb() {   $("throb").show(100); }
function stopThrob() { $("throb").hide(100); }

function ajaxify(base) {
	if (!base) { base = document.body; }
	$("form .ajax", base).submit(function() {
		alert("submitting!");
		frm = $(this);
		if($("input[name=ajax]")) {
			return;
		}
		frm.prepend("<input name=\"ajax\" type=\"hidden\" value=\"true\" />");
		pushAjax();
		$.ajax({
			url: frm.action,
			type: frm.method,
			data: frm.serialize(),
			dataType: "html",
			complete: popAjax,
			error: function(xhr, textStatus, err) {
				alert("fail!");
			},
			success: function(data, status) {
				target_sel = $("input[name=dest]", frm).value;
				if(target_sel[0] == '#'){
					target = $(target_sel);
				} else {
					target = frm.closest(target_sel);
				}
			
				html = $(data, document);
				ajaxify(html);
				meth = $("input[name=dest_type]", frm).value;
				if(meth == "replace") {
					target.replace(html);
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
		return true; // stop propagation
	});
	return "done"
}
