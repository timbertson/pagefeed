$(function() {
	var blank = function(obj) {
		return ((!obj) || ('length' in obj && obj.length == 0));
	};

	var next_to = function(method, collection) {
		if(method == "next") return collection.eq(0);
		return collection.eq(collection.length-1);
	}

	// TODO: figure out how to go between navigation & links
	//
	var selector = ".selectable,.pagination";
	var parent_selector = '.pagination_container,ul';
	var try_ = function(elem, method, next_selector, then_upto, then_next, then_selector){
		var selected = elem[method](next_selector);
		if(!blank(selected)) return selected;

		var parent_elems = elem.closest(then_upto)[method+"All"](then_next);
		if(blank(parent_elems)) return null;

		var closest_parent = next_to(method, parent_elems);
		var all_selectable = $(then_selector, closest_parent);
		selected = next_to(method, all_selectable);
		if(!blank(selected)) return selected;
		return null;
	};

	var delegate = {
		up: function(currentElement) {
			if(currentElement == null) return null;
			return try_(currentElement, 'prev', selector, parent_selector, parent_selector, selector);
		},

		down: function(currentElement) {
			if(currentElement == null) return $(selector).eq(0);
			var next_elem = try_(currentElement, 'next', selector, parent_selector, parent_selector, selector);
			if((!next_elem) || next_elem.length == 0) {
				return currentElement;
			} else {
				return next_elem;
			}
		}
	};

	$.vimNavigation(delegate);
});

