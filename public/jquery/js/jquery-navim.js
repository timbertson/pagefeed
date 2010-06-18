/*
 * TODO:
 * - figure out left/right navigation
 * - G, gg navigatoin
 * - next/prev link specification
 * - bottom-of-page when scrolling past last item
 *
 * - make <shift+enter> open links in a new window/tab
 *
 */


var jQuery_navim_plugin = {}

jQuery_navim_plugin.navigationItems = [];
jQuery_navim_plugin.delegate = null;
jQuery_navim_plugin.started = false
jQuery_navim_plugin.activeClassName = "navim_active";

jQuery_navim_plugin.util = {
	get_elem_via_delegate: function(amount) {
		var state = jQuery_navim_plugin.state;
		var method = amount > 0 ? "down" : "up";
		var currentElement = state.currentElement;
		var elem = jQuery_navim_plugin.delegate[method](currentElement);
		if(elem && "length" in elem && elem.length == 0) elem = null;
		return elem;
	},

	get_elem_via_navigation_items: function(amount) {
		var state = jQuery_navim_plugin.state;
		var elems = jQuery_navim_plugin.navigationItems;
		if(state.vertical == null) {
			var details;
			if(amount > 0 || $(window).scrollTop() > 0) {
				// if we're at the top, stay there when pressing "k"
				details = this.getFirstElement();
			} else {
				details = [null, null];
			}
			newIndex = details[0];
			selectedItem = details[1];
		} else {
			newIndex = state.vertical + amount;
			if(newIndex < 0) {
				selectedItem = null;
				newIndex = null;
			} else {
				if(elems.length <= newIndex) {
					newIndex = elems.length - 1;
				}
				selectedItem = elems[newIndex];
			}
		}
		state.vertical = newIndex;
		return selectedItem;
	},

	go: function(amount) {
		// (should be "self", but isn't when acting as
		// an dvent callback)
		var slf = jQuery_navim_plugin.util;

		var selectedItem;
		if(jQuery_navim_plugin.delegate != null) {
			selectedItem = slf.get_elem_via_delegate(amount);
		} else {
			selectedItem = slf.get_elem_via_navigation_items(amount);
		}
		this.selectElement(selectedItem);
	},

	getFirstElement: function() {
		//gets the first [index, element] pair for *after* the current scroll offset
		var win = jQuery(window);
		var collection = jQuery_navim_plugin.navigationItems;
		var selectObject = null;
		var selectIndex = 0;
		for(var i=0; i<collection.length; i++) {
			var item = collection[i];
			selectObject = item;
			selectIndex = i;
			if($(item).offset().top > win.scrollTop()) break;
		}
		return [selectIndex, selectObject];
	},

	tabNext: function() {
		// select the first (non-hidden) input element within the active one
		var slf = jQuery_navim_plugin.util;
		var current = jQuery_navim_plugin.state.currentElement;
		if(slf.hasTabbed || (!current)) return true;
		var inputs = jQuery('input[type!=hidden]', current);
		if(inputs.length > 0) {
			inputs.eq(0).focus();
			slf.hasTabbed = true;
			return false;
		}
		return true;
	},

	selectElement: function(elem) {
		var slf = jQuery_navim_plugin.util;
		var old_elem = jQuery_navim_plugin.state.currentElement;
		slf.hasTabbed = false;
		if(old_elem != null) {
			jQuery("input:focus").blur();
			old_elem.blur();
			old_elem.removeClass(jQuery_navim_plugin.activeClassName);
		}
		if(elem == null) {
			jQuery_navim_plugin.state.currentElement = null;
			$('document,body').scrollTo();
		} else {
			elem = $(elem);
			jQuery_navim_plugin.state.currentElement = elem;
			elem.addClass(jQuery_navim_plugin.activeClassName);
			elem.focus();
			elem.scrollTo();
		}
	},

	action: function(elem, shiftPressed) {
		var links = jQuery("a[href]", elem);
		if(elem.attr("nodeName").match(/^a$/i)) {
			links = $(elem);
		}
		if(links.length > 0) {
			//TODO: why can't i just click() the link?
			var href = links.eq(0).attr('href');
			if(shiftPressed) {
				window.open(href);
			} else {
				document.location.href = href;
			}
		}
	},
};

jQuery_navim_plugin.state = {
	vertical: null,
	currentElement: null,
	shiftPressed: false
}

jQuery_navim_plugin.onKeyUp = function(e) {
	if(e.which == 16) { // shift key
		jQuery_navim_plugin.state.shiftPressed = false;
	}
};

jQuery_navim_plugin.onKeyDown = function(e) {
	if(e.which == 16) { // shift key
		jQuery_navim_plugin.state.shiftPressed = true;
	}
};

jQuery_navim_plugin.keyHandler = function(e) {
	if(jQuery("input:focus").length > 0 && e.which in [13, 0]) return true;
	var u = jQuery_navim_plugin.util;
	if (e.target.nodeName.toLowerCase() == 'input') {
		return;
	}
	var mapping = {
		106: function() {u.go(1);  return false;},
		107: function() {u.go(-1); return false;},
		13:  function() {
			u.action(jQuery_navim_plugin.state.currentElement, jQuery_navim_plugin.state.shiftPressed);
			return false;
		},
		0: function()   {return u.tabNext();},
	};
	if(e.which in mapping) {
		return mapping[e.which]();
	}
}

jQuery_navim_plugin.ensureActive = function() {
	if(jQuery_navim_plugin.started) return;
	jQuery_navim_plugin.started = true;
	jQuery(window).keypress(jQuery_navim_plugin.keyHandler);
	jQuery(window).keydown(jQuery_navim_plugin.onKeyDown);
	jQuery(window).keyup(jQuery_navim_plugin.onKeyUp);
};

jQuery.vimNavigationAction = function(callback) {
	jQuery_navim_plugin.util.action = callback;
};

jQuery.vimNavigation = function(delegate) {
	jQuery_navim_plugin.delegate = delegate;
	jQuery_navim_plugin.ensureActive();
};

jQuery.fn.vimNavigation = function() {
	var collection = Array();
	this.each(function(){ collection.push(this); });
	jQuery_navim_plugin.navigationItems = collection;
	jQuery_navim_plugin.ensureActive();
};

jQuery.fn.scrollTo = function() {
	var offset = this.offset();
	var padding = 20;
	var doc = jQuery('html,body')
	var speed = 50;
	var win = $(window);

	var bounds = {
		height: win.height(),
		width: win.width(),
		top: win.scrollTop(),
		bottom: win.scrollTop() + win.height(),
		left: win.scrollLeft(),
		right: win.scrollLeft() + win.width()
	};

	var content = {
		height: this.outerHeight(),
		width: this.outerWidth(),
		top: offset.top,
		bottom: offset.top + this.outerHeight(),
		left: offset.left,
		right: offset.left + this.outerWidth()
	};

	function scrollH(offset) {
		doc.animate({scrollLeft: offset}, speed);
	};

	function scrollV(offset) {
		doc.animate({scrollTop: offset}, speed);
	};

	// vertical scrolling
	if(bounds.bottom < content.bottom) {
		// content extends below bottom margin
		if(content.height + padding > bounds.height) {
			// just scroll to the top (since we can't get it all in)
			scrollV(content.top - padding);
		} else {
			scrollV(content.bottom - bounds.height + padding);
		}
	} else if(bounds.top > content.top) {
		// content extends above bottom margin
		scrollV(content.top - padding);
	}

	// horizontal scrolling
	if(bounds.right < content.right) {
		// content extends past right margin
		if(content.width + padding > bounds.width) {
			scrollH(content.left - padding);
		} else {
			scrollH(content.right - bounds.width + padding);
		}
	} else if(bounds.left > content.left) {
		// content extends before left margin
		scrollV(content.left - padding);
	}
}

