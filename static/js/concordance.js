var d = "";
var colors = {'concordance': 'blue', 'coherence': 'red', 'concordanceTotale': 'green', 'concordanceOrdre3': '#FFCF0B'}

function getContent(opusRef, key, formData) {
    $.ajax({
	    url : '/rest/opus/'+ opusRef +'/concordance',
	    type : 'GET',
	    data : formData,
	    dataType:'json',
	    success : function(data) {
	        d = data;
            toggleChart(key);
	    },
	    error : function(request,error)
	    {
	        alert("Request: " + JSON.stringify(request));
	    }
	});
}

function getData() {
    var parameters = $('.param');
    var data = {}
    parameters.each(function() {
        data[$(this).attr('name')] = $(this).val();
    });
    return data;
}

function process(opusRef, key) {
    if(!d || !('results' in d)) {
        getContent(opusRef, key, getData());
    }
    else {
        toggleChart(key);
    }
}

function toggleChart(key) {
    var chart = $("#chart-" + key);
    if(chart.length == 0) {
        drawChart(d, key);
    }
    else {
        if(chart.attr('style') != 'display: none;') {
            hideChart(chart);
        }
        else {
            showChart(chart);
        }
    }
}

function updateLevels() {
    var numberCharts = countCharts();
    heightChart = 2000;
    var svg = $('#definition-scale');
    systems = svg.find('g.system');
    systems.each(function(index) {
        if(index > 0) {
            translateVertically($(this), index * heightChart * numberCharts);
        }
    });
    var charts = $('.chart:not([style*="display: none"]');
    charts.each(function(i) {
        $(this).attr('data-chart-index', i);
    });
    var elements = $('[data-level]');
    var systems = $('g.system');
    elements.each(function() {
        var parent_chart = $(this).parent('.chart');
        var chart_index = parseInt(parent_chart.attr('data-chart-index'));
        var level = parseInt($(this).attr('data-level'));
        var parent_system = systems[level];
        var system_bbox = parent_system.getBBox();
        var bottom = system_bbox.y + system_bbox.height;
        translateVertically($(this), bottom + level * heightChart * numberCharts + (chart_index + 1) * heightChart);
    });
}

function translateVertically(element, translation) {
    element.attr({'transform': 'translate(0, ' + translation + ')'});
}

function insertChart(key) {
    var chart = getSvgElement('svg');
    chart.setAttribute('class', 'chart');
    chart.setAttribute('id', 'chart-' + key);
    $("#definition-scale").first().append(chart);
    updateLevels();
    return chart;
}

function showChart(chart) {
    chart.show();
    updateLevels();
}

function hideChart(chart) {
    chart.hide();
    updateLevels();
}

function drawChart(content, key) {
    var index = countCharts() - 1;
    insertChart(key);
    var main_svg = $('#verovio svg').first();
    var definition_scale = $('#definition-scale');
    var ratio = 21000/main_svg.width();
    var chart = $('#chart-' + key);
    results = content["results"];

    var maxNote = 0;
    for(var i = 0; i < results.length; i++) {
        if(results[i]['nombreDeNotes'] > maxNote) {
            maxNote = results[i]['nombreDeNotes'];
        }
    }

    var last_system_top = 0;
    var y = 0;
    var margin = 150;
    var system_height = 120;
    var level = -1;
    for(i = 0; i < results.length - 1; i++) {
        var note = $('#' + results[i]['identifiant']);
        var next_note = $('#' + results[i + 1]['identifiant']);
        var x = note.position().left - chart.position().left;
        var x_next = next_note.position().left - chart.position().left;
        var system = note.closest('g.system');
        var system_top = system.position().top;
        if(system_top != last_system_top) {
            last_system_top = system_top;
            level += 1;
            drawLine(chart, level, 0, "100%", 0, 0, 'black');
            drawText(chart, key, level, 0, 400, 300);
        }
        var k = 70;
        y_rect = 0;
        value = results[i][key] * k;
        height = 0;
        width = 0;
        if(x_next < x) {
            width = 50;
        }
        else {
            width = x_next - x;
        }
        if(value > 0) {
            y_rect = y - value;
            height = value;
        }
        else {
            y_rect = y;
            height = -value;
        }
        var color = colors[key];
        opacity = getOpacity(results[i]['nombreDeNotes'], maxNote, key);
        if(key == 'couleurHarmonique') {
            height = 20;
            color = getColorCode([results[i]['concordance'], results[i]['coherence'], results[i]['concordanceTotale']]);
            opacity = 1;
            y_rect = y - height;
        }
        drawRect(chart, level, x*ratio, y_rect*ratio, height*ratio, width*ratio, color, opacity);
    }
    updateLevels();
}

function countCharts() {
    var charts = $('svg.chart:not([style*="display: none"])');
    return charts.length;
}

function drawLine(parent, level, x1, x2, y1, y2, color) {
    var newLine = getSvgElement('line');
    newLine.setAttribute('x1', x1);
    newLine.setAttribute('y1', y1);
    newLine.setAttribute('x2', x2);
    newLine.setAttribute('y2', y2);
    newLine.setAttribute("stroke", color);
    newLine.setAttribute("stroke-width", 40);
    newLine.setAttribute("data-level", level);
    parent.append(newLine);
}

function drawRect(parent, level, x, y, height, width, color, opacity) {
    var rect = getSvgElement('rect');
    rect.setAttributeNS(null, 'x', x);
    rect.setAttributeNS(null, 'y', y);
    rect.setAttributeNS(null, 'height', height);
    rect.setAttributeNS(null, 'width', width);
    rect.setAttributeNS(null, 'fill', color);
    rect.setAttributeNS(null, 'fill-opacity', opacity);
    rect.setAttributeNS(null, 'stroke-width', 40);
    rect.setAttributeNS(null, 'stroke', "black");
    rect.setAttribute("data-level", level);
    parent.append(rect);
}

function drawText(parent, textContent, level, x, y, fontSize) {
    var text = getSvgElement('text');
    text.setAttribute('x', x);
    text.setAttribute('y', y);
    text.setAttribute('font-size', fontSize);
    text.setAttribute("data-level", level);
    text.textContent = textContent;
    parent.append(text);
}

function getSvgElement(name) {
    return document.createElementNS('http://www.w3.org/2000/svg', name);
}

function getOpacity(nombreNotes, maxNote) {
    if(key = "concordance") {
        if(nombreNotes <= 1) {
            return(0);
        }
        else {
            return((nombreNotes - 1)/(maxNote - 1));
        }
    }
    else if(key = "concordanceTotale") {
        return(nombreNotes/maxNote);
    }
    else if(key = "concordanceOrdre3") {
        if(nombreNotes <= 2) {
            return(0);
        }
        else {
            return((nombreNotes - 2)/(maxNote - 2));
        }
    }
    else if(key = "coherence") {
        return(1);
    }
    else {
        return(1);
    }
}

function getColorCode(values) {
    var sum = values[0] + values[1] + values[2];
    return "rgb(" + Math.round(values[1]*255/sum) + "," + Math.round(255*values[2]/sum) +"," + Math.round(255*values[0]/sum) + ")";
}