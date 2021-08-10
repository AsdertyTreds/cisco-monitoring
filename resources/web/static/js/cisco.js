var hwSwitch = []

function clSwitch (id, name, mac, ip, exclports, stackmaster, stacknum, t, box, fa, gi, description, numinbox) {
		this.id = id;
		this.name = name;
		this.mac = mac;
		this.ip = ip;
		this.exclports = exclports;
		this.stackmaster = stackmaster;
		this.stacknum = stacknum;
		this.t = t;
		this.box = box;
		this.numinbox = numinbox;
		this.fa = fa;
		this.gi = gi;
		this.ports = '';
		this.description = description.trim();
}

clSwitch.prototype.descr = function() {
	return ' Cabinet:' + this.box + '.' + this.numinbox + ' '  + this.name + ' ' + this.ip + ' ' + this.description;
}

clSwitch.prototype.table = function() {
	var sw = '<table class="switch" switchid="'+this.id+'" switchname="'+this.name+'" box="'+this.box+'">' + "\n";
	var sw_th1 = '';
	var sw_td1 = '';
	var sw_th2 = '';
	var sw_td2 = '';
	var st_num = '0/';
	if (this.stacknum > 0) st_num = this.stacknum + '/' + st_num;
	var i = 1;
	var cols = 0;
	while (i <= this.fa) {
		sw_th1 += '<th>Fa' + st_num + i + '</th>';
		sw_td1 += '<td port="Fa' + st_num + i + '"></td>';
		
		sw_th2 += '<th>Fa' + st_num + (i+1) +'</th>';
		sw_td2 += '<td port="Fa' + st_num + (i+1) + '"></td>';
		
		i = i + 2;
		cols ++;
	}
	i = 1
	if (this.fa > 0) {
		while (i <= this.gi) {
			sw_th1 += '<th></th>'
			sw_td1 += '<td></td>'
			
			sw_th2 += '<th>Gi' + st_num + i +'</th>'
			sw_td2 += '<td port="Gi' + st_num + i + '"></td>'
			
			i ++
			cols ++
		}
	}
	else {
		if (this.gi > 8){
			while (i <= this.gi) {
				sw_th1 += '<th>Gi' + st_num + i + '</th>'
				sw_td1 += '<td port="Gi' + st_num + i + '"></td>'
				
				sw_th2 += '<th>Gi' + st_num + (i+1) +'</th>'
				sw_td2 += '<td port="Gi' + st_num + (i+1) + '"></td>'
				
				i = i + 2
				cols ++
			}
		}
		else {
			while (i <= this.gi) {
				sw_th1 += '<th>Gi' + st_num + i + '</th>'
				sw_td1 += '<td port="Gi' + st_num + i + '"></td>'
				i ++
				cols ++
			}
		}
	}
	getswp = '<span cmd="getSwitchPorts" onclick="getSwitchPorts('+ this.id +')" msg="request ports info for this switch">&#128258;</span>';
	showports = '<span cmd="showPorts" onclick="showPorts('+ this.id +')" msg="show ports info">&#128196;</span>';

	sw += "<tr>\n"
	sw += '<th colspan="' + cols + '"><div class="descr">'+ this.descr() + '</div><div class="cmd">' + getswp + '&nbsp;' + showports + '</div>' + "\n"
	sw += "</tr>\n"

	sw += "<tr>\n"
	sw += sw_th1 + "\n"
	sw += "</tr>\n"
	sw += "<tr>\n"
	sw += sw_td1 + "\n"
	sw += "</tr>\n"
	sw += "<tr>\n"
	sw += sw_th2 + "\n"
	sw += "</tr>\n"
	sw += "<tr>\n"
	sw += sw_td2 + "\n"
	sw += "</tr>\n"
	sw += "<tr>\n"
	sw += '<tr><td colspan="' + cols + '" class="list"><table class="ports"><tr><th>port</th><th>connected host mac-address</th><th>connected host ip-address</th><th>connected host name</th><th>last online</th><th>port description</th><th>port speed</th><th></th></tr></table></td>' + "\n"
	sw += "</tr>\n"
	sw += "</table>\n"

	return sw;
}

function get_id_portid(portid) {
	return Number(portid.substr(portid.lastIndexOf("/")+1, portid.length));
}

function sort_ports(ports) {
	let ret = JSON.parse(ports).sort( function(a, b) {
		if (a["portid"].substr(0, 2) < b["portid"].substr(0, 2)) return -1;
		if (a["portid"].substr(0, 2) > b["portid"].substr(0, 2)) return 1;
		if (get_id_portid(a["portid"]) < get_id_portid(b["portid"])) return -1;
		if (get_id_portid(a["portid"]) > get_id_portid(b["portid"])) return 1;
		return 0;
	});
	
	return ret;
}

function showPorts(id) {
	$("table.switch[switchid='" + id + "'] table.ports").toggle()
}

function get_total() {
	var sw_all = $("table.switch td[port]").length;
	var sw_on = $("table.switch td[port]:contains('0')").length;
	var sw_off = sw_all - sw_on;
	var sw_1000 = $("table.switch td[port]:contains('1000')").length;
	var sw_100 = $("table.switch td[port]:contains('100')").length - sw_1000;
	var sw_10 = $("table.switch td[port]:contains('10')").length - sw_100 - sw_1000;
	var total = '<table>'
	total += '<tr>'
	total += '<th>All</th>' +'<th>off</th>' +'<th>on</th>' +'<th>on 10</th>' +'<th>on 100</th>' +'<th>on 1000</th>'
	total += '</tr>'
	total += '<tr>'
	total += '<td>'+sw_all+'</td>' +'<td>'+sw_off+'</td>' +'<td>'+sw_on+'</td>' +'<td class="on10">'+sw_10+'</td>' +'<td class="on100">'+sw_100+'</td>' +'<td class="on1000">'+sw_1000+'</td>';
	total += '</tr>'
	total += '</table>'
	$("#total").html(total);
}

function reloadPorts() {
    $("#reload").hide()

	$.each(hwSwitch, function(j,sw){
		if (sw != undefined)
			getPorts(sw);
	});
	
    $("#reload").show()
}

function getPorts(sw) {
	$("table.switch[switchid='" + sw.id + "'] table.ports tr[port]").remove();
	$.ajax({
		method: "post",
		url: '/ajax',
		dataType: 'text',
		data: {
			cmd: 'loadports',
			id: sw.id,
			rnd: Math.random()
		},
		success: function(ports){
			if(ports) {
				sw.ports = sort_ports(ports)
				loadPorts (sw)
				get_total();
				if ($("#search input").val().length) $("#search input").keyup()
			};
		}
	});
}

function loadPorts(sw) {
	$.each(sw.ports, function(i,port){
		speed = ''
		let onoff = '&#127358;';
		$("table.switch[switchid='" + sw.id + "'] td[port='" + port.portid + "']").removeClass();
		if (port.status == 1) {
			speed = Number(port.speed)
			$("table.switch[switchid='" + sw.id + "'] td[port='" + port.portid + "']").addClass("on" + speed);
			onoff = '&#9989;';
		}
		else {
			$("table.switch[switchid='" + sw.id + "'] td[port='" + port.portid + "']").addClass("off");
		}
		$("table.switch[switchid='" + sw.id + "'] td[port='" + port.portid + "']").text(speed);
		$("table.switch[switchid='" + sw.id + "'] td.list table.ports tr:last").after('<tr swid="' + sw.id + '" port="' + port.portid + '"><td>' + port.portid + '</td><td>' + port.mac + '</td><td>' + port.ip + '</td><td>' + port.name + '</td><td>' + port.date + '</td><td>' + port.descr + '</td><td>' + speed + '</td><td>' + onoff + '</td></tr>');
		$("table.switch[switchid='" + sw.id + "'] td.list table.ports tr:last").mousemove(function (eventObject) {
			$data_tooltip = $("table.switch[switchid='" + sw.id + "'] td[port='" + port.portid + "']");
				$data_tooltip.addClass("sel");
			}).mouseout(function () {
				$data_tooltip.removeClass("sel");
		});
	});
}

function getSwitchs() {
	$.ajax({
		method: "post",
		url: '/ajax',
		dataType: 'json',
		data: {
			cmd: 'loadswitches',
			rnd: Math.random()
		},
		success: function(res){
			if(res && res.total) {
			    var cabinets = [];
                $("div#cabinets").append('<div class="div-table-col selectbox on10" align="center" cabinet="0" onclick="cabSelect(0)">All</div>');
				$.each(res.routers, function(j,router){
					hwSwitch[router.routerid] = new clSwitch(router.routerid, router.name, router.mac, router.ip, router.exclports, router.stackmaster, router.stacknum, router.t, router.box, router.fa, router.gi, router.descr, router.numinbox);
					sw = hwSwitch[router.routerid];
					$("#switchlist").append(sw.table());
					if ($.inArray(router.box, cabinets) === -1) {
					    cabinets.push(router.box)
					    $("div#cabinets").append('<div class="div-table-col selectbox" align="center" cabinet="'
					    + router.box + '" onclick="cabSelect('
					    + router.box + ')">'
					    + router.box + '</div>');
					}
					$("table.switch[switchid='" + sw.id + "']").addClass(sw.description.substr(0, sw.description.indexOf(' ')));
					$("table.switch[switchid='" + sw.id + "'] span[msg]").mousetip(10, 10);
				});
				$.each(hwSwitch, function(j,sw){
					if (sw != undefined){
						getPorts(sw);
					}
				});
                $("div#cabinets .div-table-col").css("width", (($("#container").width() / (cabinets.length + 1)) - 4) + "px");
			}
		}
	});
	$("#reload").show();
}

function getSwitchPorts(id) {
	$("table.switch[switchid='" + id + "'] span[cmd='getSwitchPorts']").html("&#8987;");
	$.ajax({
		method: "post",
		url: '/ajax',
		dataType: 'json',
		data: {
			cmd: 'loadswitchports',
			id: id,
			rnd: Math.random()
		},
		success: function(res){
			if(res) {
				hwSwitch[id].box = res.routers[0].box
				hwSwitch[id].numinbox = res.routers[0].numinbox
				hwSwitch[id].name = res.routers[0].name
				hwSwitch[id].ip = res.routers[0].ip
				hwSwitch[id].description = res.routers[0].descr
				$("table.switch[switchid='" + id + "'] div.descr").html(hwSwitch[id].descr());

				getPorts(hwSwitch[id]);
				$("table.switch[switchid='" + id + "'] span[cmd='getSwitchPorts']").html("&#128258;");
			}
		}
	});

	
	$("#reload").show()
}

function cabSelect (cabinet) {
    $("div[cabinet]").removeClass("on10");
    $("table.switch").hide();
    if (cabinet == 0) {
        $("table.switch").show();
    }
    else {
        $("table.switch[box='" + cabinet + "'] ").show();
    }
    $("div[cabinet=" + cabinet + "]").addClass("on10");
}

$.fn.mousetip = function(x, y) {
	var tip = $('.tip')
	$(this).hover(function() {
		tip.text($(this).attr('msg'))
		tip.show();
	}, function() {
		tip.text('')
		tip.hide().removeAttr('style');
	}).mousemove(function(e) {
		var mouseX = e.pageX + (x || 10);
		var mouseY = e.pageY + (y || 10);
		tip.show().css({
			top:mouseY, left:mouseX
		});
	});
};

$().ready(function(){
	$('[msg]').mousetip(10, 10);
	
    $("#reload").hide();

    getSwitchs();
	$('.selectbox').prop( "checked", true );
	
	$("#search span").text('0')
	$("#search input").val('')
	$("#search input").keyup(function () {
		var value = this.value.toLowerCase().trim();
		$("#search span").text('0')
		if (value.length) {
		    $("div[cabinet]").removeClass("on10");
			$("table.switch").hide();
			$("table.ports").show();
			$("table.ports tr").each(function (index) {
				if (!index) return;
				$(this).find("td").each(function () {
					var id = $(this).text().toLowerCase().trim();
					var not_found = (id.indexOf(value) == -1);
					$(this).closest('tr').toggle(!not_found);
					if (!not_found) {
						$("#search span").text(Number($("#search span").text()) + 1);
						$("table.switch[switchid='" + $(this).parent().attr('swid') + "']").show();
					}

					return not_found;
				});
			});
		}
		else {
		    $("div[cabinet=0]").addClass("on10");
			$("table.switch").show();
			$("table.ports tr").show();
			$("table.ports").hide();
		}
	});
})

