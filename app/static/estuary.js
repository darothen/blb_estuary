WIDTH = 700;
HEIGHT = 400;
var DEBUG = true;
var VERBOSE = false;

function toggleVis(elem) {
   current_vis = elem.attr("visibility");

   if (current_vis === "visible" &&
       current_vis !== null) {
      console.log("Toggling visible->hidden");
      elem.attr({
         visibility: 'hidden',
      });
   } else if (current_vis === "hidden" &&
              current_vis !== null) {
      if ( DEBUG ) console.log("Toggling hidden->visible");
      elem.attr({
         visibility: 'visible',
      });
   } else {
      if ( DEBUG ) console.log("Setting default to 'visible'");
      elem.attr({
         visibility: 'visible',
      });
   }
};

if ( DEBUG ) console.log("Loading...");
// var estuary = Snap("#estuary_diagram", WIDTH, HEIGHT);
var estuary = Snap("#estuary_diagram");

// Add water and ground to estuary diagram
ESTUARY_PAD = 50;
var water = estuary.rect(ESTUARY_PAD, 120, 500-ESTUARY_PAD, 204);
water.attr({
   fill: "url(#water_gradient)",
});
var ground = estuary.rect(ESTUARY_PAD, 321, 500-ESTUARY_PAD, 30)
ground.attr({
   fill: "#8C6239",
});

// Add waves to top of estuary
WAVE_WIDTH = 18;
WAVE_HEIGHT = 20;
for (i = 0; i < 13; i++) {
   var wave = estuary.ellipse(i*WAVE_WIDTH*2 + WAVE_WIDTH/2 + ESTUARY_PAD,
                   113, WAVE_WIDTH+4, WAVE_HEIGHT);
   wave.attr({
      fill: "#FFFFFF"
   });
}
if ( DEBUG ) console.log("estuary base done");

// Now we add the source/sink arrows
LINE_LENGTH = 100
ARROW_OFF = 40
ARROW_ATTRS = {
   style: 'marker-end: url(#arrowhead)',
   stroke: "#000",
   strokeWidth: 5,
};
TEXT_ATTRS = {
   style: 'font-weight: bold; font-size: 20px; text-anchor: middle; font-family: sans-serif;',
};

// Ocean Tides
ocean_text = estuary.text(ESTUARY_PAD, 200, "Ocean Tide");
ocean_text.attr(TEXT_ATTRS);
ocean_arrow_in = estuary.line(0, 220, LINE_LENGTH, 220);
ocean_arrow_in.attr(ARROW_ATTRS);
ocean_arrow_out = estuary.line(LINE_LENGTH+ARROW_OFF, 240, 0+ARROW_OFF, 240);
ocean_arrow_out.attr(ARROW_ATTRS);
ocean_group = estuary.g(ocean_text,
                        ocean_arrow_in,
                        ocean_arrow_out);
ocean_group.attr({ id: "ocean_group", });
toggleVis(ocean_group);  // Disabled initially

// River Flow
river_text = estuary.text(500, 200, "River Flow");
river_text.attr(TEXT_ATTRS);
river_arrow_in = estuary.line(460+ESTUARY_PAD+ARROW_OFF, 230, 460+ESTUARY_PAD-LINE_LENGTH+ARROW_OFF, 230);
river_arrow_in.attr(ARROW_ATTRS);
river_group = estuary.g(river_text,
                        river_arrow_in);
river_group.attr({ id: "river_group", });

// Gas Exchange
gas_text = estuary.text(255+200, 115, "Gas Exchange");
gas_text.attr(TEXT_ATTRS);
gas_arrow_in = estuary.line(150+200, 75-ARROW_OFF, 150+200, 75+LINE_LENGTH-ARROW_OFF);
gas_arrow_in.attr(ARROW_ATTRS);
gas_arrow_out = estuary.line(170+200, 75+LINE_LENGTH, 170+200, 75);
gas_arrow_out.attr(ARROW_ATTRS);
gas_group = estuary.g(gas_text,
                      gas_arrow_in,
                      gas_arrow_out);
gas_group.attr({ id: "gas_group", });

// Make the fish!'
if ( DEBUG ) console.log("Pre load");
var animating = false;
var _fish;

function load_fish( state ) {

  animating = true;
  // Sanity check
  // if (typeof _fish === 'undefined' ) {
  //    stop_fish();
  //    stop_fish();
  // }

  if ( state === "healthy" ) {
    if ( DEBUG ) console.log("Loading healthy fish");
    Snap.load("/static/fish_healthy.svg", function (f) {
        var fish = f.select("#fish");
        estuary.append(fish);
        _fish = fish.attr({ visibility: 'visible' });
        swim();
    });
  } else if ( state === "sick" ) {
    if ( DEBUG ) console.log("Loading sick fish");
    Snap.load("/static/fish_healthy.svg", function (f) {
        var fish = f.select("#fish");
        estuary.append(fish);
        _fish = fish.attr({ visibility: 'visible' });
        swim();
    });
  } else {
    if ( DEBUG ) console.log("Loading dead fish");
    Snap.load("/static/fish_healthy.svg", function (f) {
        var fish = f.select("#fish");
        estuary.append(fish);
        _fish = fish.attr({ visibility: 'visible' });
        float();
    });
  }

}

function stop_fish() {
  _fish.attr({ visibility: 'hidden' });
  _fish.stop().remove();
  animating = false;
}

function swim() {

   if ( DEBUG ) console.log("in swim()");
   var fx = _fish.getBBox().cx;
   var fy = _fish.getBBox().cy;

   var duration = 1000;
   x_per = 1000/2;
   x_amp = 80;
   y_per = 1000/6;
   y_amp = 20;
   if ( animating ) {
     Snap.animate(0, duration, function( t ) {
        var dot = {
           x: x_amp - (4*x_amp/x_per)*(Math.abs(t%x_per - x_per/2) - x_per/4),
           y: y_amp*Math.sin((t/y_per)*2.*Math.PI),
        };
        // The logic check in the next line checks if we're
        // in -> or <- period by converting the time value
        // to the "period number", and checking if it's
        // even. Note that we divide the period by 2
        // since two half periods comprise a cycle
        flip = ( (parseInt(t / (x_per/2)) + 2) % 2 ) ? 1 : 0;

        translate = "t" + dot.x + "," + dot.y;
        if ( flip ) {
           translate += "s-1,1";
        }
        _fish.attr({
           transform: translate,
        });
        if ( DEBUG && VERBOSE ) console.log(t, translate, flip);
     }, 10000, mina.linear, swim);
   }
}

function float() {

   if ( DEBUG ) console.log("in float()");

   var duration = 1000;
   y_per = 1000/2;
   y_amp = 20;
   if ( animating ) {
     Snap.animate(0, duration, function( t ) {
        y = y_amp*Math.sin((t/y_per)*2.*Math.PI);
        translate = "t0," + (y - 60);
        _fish.attr({
           transform: translate,
        });
        if ( DEBUG && VERBOSE ) console.log(t, translate);
     }, 10000, mina.linear, float);
   }
}

// load_fish("dead");