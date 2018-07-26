var span_to_group = null;
var fragment_to_spans = null;

function init_maps() {
  // Create span_to_group
  span_to_group = new Array(span_to_fragments.length);
  group_to_spans.forEach((spans, group) => {
    spans.forEach(span => span_to_group[span] = group);
  });

  // Create fragment_to_spans
  fragment_to_spans = {};
  span_to_fragments.forEach(frags => frags.forEach(frag => fragment_to_spans[frag] = []));
  span_to_fragments.forEach((frags, span) => {
    frags.forEach(frag => fragment_to_spans[frag].push(span));
  });
}

document.addEventListener("DOMContentLoaded", function(event) {
  init_maps();
  console.log("group_to_spans", group_to_spans);
  console.log("span_to_fragments", span_to_fragments);
  console.log("span_to_group", span_to_group);
  console.log("fragment_to_spans", fragment_to_spans);
});
