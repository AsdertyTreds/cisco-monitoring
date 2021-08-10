from pysnmp.entity.rfc3413.oneliner import cmdgen
from services.db.connector import db_connector, chk_db
import time
from services.net.arp_scan import arp
from flask import render_template, request, Flask
from settings import *
import threading

""" snmp """
cmdGen = cmdgen.CommandGenerator()

""" flask app """
app = Flask(__name__)
app.static_url_path = '/static'
app.static_folder = os.path.join(WEB_DIR, "static")
app.template_folder = WEB_DIR
app.config['SECRET_KEY'] = "1qa2ws3edfkj589ugfpw905eugp90wug"

chk_db(os.path.join(DB_DIR, s_values["dbfile"]))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ajax', methods=('GET', 'POST'))
def get_cmd():
    ret = ''
    if 'cmd' in request.form:
        cmd = request.form['cmd']
        if cmd == 'loadports':
            if 'id' in request.form:
                ret = prepareret_ports(request.form['id'])
        elif cmd == 'getstackmasters':
            ret = getstackmasters()
        elif cmd == 'loadswitchports':
            if 'id' in request.form:
                ret = prepareret_switch_ports(request.form['id'])
        elif cmd == 'loadswitches':
            ret = prepareret_switches()
        elif cmd == 'saveswitch':
            ret = saveswitch(request.form['name'], request.form['ip'], request.form['mac'], request.form['descr'],
                             request.form['box'], request.form['numinbox'], request.form['stackmaster'],
                             request.form['stacknum'], request.form['fa'], request.form['gi'],
                             request.form['exclports'])
    elif 'get_port' in request.args.keys():  # not request.args.get('get_port') is None:
        ret = get_port(request.args.get('get_port'))
    return ret


def get_snmp_data(ip: str, oid: str):
    errorindication, errorstatus, errorindex, varbinds = cmdGen.nextCmd(
        cmdgen.CommunityData(s_values['community']),
        cmdgen.UdpTransportTarget((ip, 161)),
        oid
    )
    return varbinds


@db_connector
def get_port(db, mac: str):
    cursor = db.cursor()
    ret = ""
    ports = cursor.execute(f"SELECT port, \
                            (select name from routers where id = ports.id_r) as router, \
                            (select exclports from routers where id = ports.id_r) as exclports, \
                            t FROM ports \
                            WHERE mac='{mac}'").fetchall()
    if ports:
        for port in ports:
            if port[0] not in port[2]:
                ret = f"{ret}<br />{port[1]}.{port[0]}<br />{port[3]}<br />"

    return ret


def get_mac(name: str):
    macl = str(name[11:]).split('.')
    mac = ''
    for m in macl:
        m = hex(int(m))[2:]
        mac += ':' + (m if len(m) == 2 else '0' + m)
    return mac.lstrip(':')


@db_connector
def get_sw_id(db, router_id, p_sw_num):
    cursor = db.cursor()
    sql = "SELECT id FROM routers WHERE ((stackmaster=0 and id=?) or stackmaster=?) and stacknum=?"
    val = (router_id, router_id, p_sw_num)
    cid = cursor.execute(sql, val).fetchone()
    if cid:
        ret = cid[0]
    else:
        ret = -1
    return ret


@db_connector
def getstackmasters(db):
    cursor = db.cursor()
    sql = "SELECT id, name FROM routers WHERE stackmaster=0 and ip!=''"
    swm = []
    rts = cursor.execute(sql).fetchall()
    if rts:
        for rt in rts:
            swm.append([rt[0], rt[1]])
    return {"total": len(rts), "stackmasters": swm}


@db_connector
def saveswitch(db, name, ip, mac, descr, box, numinbox, stackmaster, stacknum, fa, gi, exclports):
    cursor = db.cursor()
    dt = time.strftime(format_dt, time.localtime(time.time()))
    sql = "SELECT id FROM routers WHERE name=?"
    exist = cursor.execute(sql, (name,)).fetchone()
    if exist:
        return {"total": 0, "routers": [], "err": "name exists"}

    sql = "SELECT id FROM routers WHERE mac=?"
    exist = cursor.execute(sql, (mac,)).fetchone()
    if exist:
        return {"total": 0, "routers": [], "err": "mac exists"}

    sql = "SELECT id FROM routers WHERE ip=? and ip!=''"
    exist = cursor.execute(sql, (ip,)).fetchone()
    if exist:
        return {"total": 0, "routers": [], "err": "ip exists"}

    sql = 'INSERT INTO routers (ip, name, mac, t, exclports, descr, box, numinbox, stackmaster, stacknum, fa, gi, ' \
          'exclports) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) '
    val = (ip, name, mac, dt, '', descr, box, numinbox, stackmaster, stacknum, fa, gi, exclports)
    cursor.execute(sql, val)
    db.commit()
    sql = "SELECT id FROM routers WHERE ip=?"
    cid = cursor.execute(sql, (ip,)).fetchone()
    if cid:
        return prepareret_switch_ports(cid[0])
    return {"total": 0, "routers": [], "err": "error"}


def get_varbinds(router_id, ip, arplist, excl):
    # print (ip)
    """ Get real interfaces ports nums and interfaces ids ["12101":"217"] """
    # ports nums 217
    # interfaces ids 12101
    varbinds1 = get_snmp_data(ip, ".1.3.6.1.2.1.17.1.4.1.1")
    varbinds2 = get_snmp_data(ip, ".1.3.6.1.2.1.17.1.4.1.2")
    d_pid = {}
    cid = 0
    for ids in varbinds1:
        for oid_id, val in ids:
            for name_id, name in varbinds2[cid]:
                d_pid[str(name)] = str(val)
        cid = cid + 1

    """ Get all interfaces ids and short interfaces names ["12101":"Gi5/0/1"] -> ["217":"Gi5/0/1"]"""
    # interfaces ids 12101
    varbinds1 = get_snmp_data(ip, ".1.3.6.1.2.1.2.2.1.1")
    # short interfaces names Gi5/0/1
    varbinds2 = get_snmp_data(ip, ".1.3.6.1.2.1.31.1.1.1.1")
    # interfaces oper status 1(2)
    varbinds3 = get_snmp_data(ip, ".1.3.6.1.2.1.2.2.1.8")
    #    varbinds4 = get_snmp_data(ip, ".1.3.6.1.2.1.2.2.1.2") # interfaces descr (12101 - description text)
    # interfaces alias (12101 - alias text like SW01316111.gi1)
    varbinds4 = get_snmp_data(ip, ".1.3.6.1.2.1.31.1.1.1.18")
    # interfaces speed
    varbinds5 = get_snmp_data(ip, ".1.3.6.1.2.1.2.2.1.5")

    d_idn = {}
    cid = 0
    for ids in varbinds1:
        for name_id, val in ids:
            port = ''
            for val_id, name in varbinds2[cid]:
                if str(val) in d_pid:
                    d_idn[d_pid[str(val)]] = str(name)
                port = str(name)
            sw_id = router_id
            status = 2
            alias = ''
            speed = 0
            if len(port) > 5 and port[3] + port[5] == '//':
                sw_id = get_sw_id(router_id, port[2])

            for status_id, status_ in varbinds3[cid]:
                status = int(str(status_))

            for alias_id, alias_ in varbinds4[cid]:
                alias = str(alias_)

            for speed_id, speed_ in varbinds5[cid]:
                speed = int(str(speed_))

            write_db_ports(sw_id, port, status, alias, speed)
        cid = cid + 1

    """ Get macaddress and and intefaces ids. Replace ids to short names """
    # mac & port num
    varbinds2 = get_snmp_data(ip, ".1.3.6.1.2.1.17.4.3.1.2")

    for ids in varbinds2:
        for name_id, port_id in ids:
            mac = get_mac(name_id)
            if str(port_id) in d_idn:
                name, alias, ip = arplist.get(mac, ['', [], ['']])
                port = d_idn[str(port_id)]
                if port not in excl:
                    sw_id = router_id
                    if len(port) > 5 and port[3] + port[5] == '//':
                        sw_id = get_sw_id(router_id, port[2])
                    write_db(sw_id, port, mac, ip[0], name)

    return len(varbinds2) if varbinds2 else 0


@db_connector
def write_db_ports(db, router_id, port, status, descr, speed):
    if router_id >= 0:
        dt = time.strftime(format_dt, time.localtime(time.time()))
        cursor = db.cursor()
        sql = 'SELECT ip FROM ports WHERE port=? and id_r=?'
        val = (port, router_id)
        rows = cursor.execute(sql, val).fetchall()

        if rows:
            if status == 1:
                sql = 'UPDATE ports SET t=?, onoff=?, descr=?, speed=? WHERE port=? and id_r=?'
                val = (dt, status, descr, speed, port, router_id)
            else:
                sql = 'UPDATE ports SET descr=?, onoff=? WHERE port=? and id_r=?'
                val = (descr, status, port, router_id)
        else:
            sql = 'INSERT INTO ports (id_r, port, onoff, t, descr, speed) VALUES (?,?,?,?,?,?)'
            val = (router_id, port, status, dt, descr, speed)
        cursor.execute(sql, val)


@db_connector
def write_db(db, router_id, port, mac, ip, name):
    if router_id >= 0:
        dt = time.strftime(format_dt, time.localtime(time.time()))
        cursor = db.cursor()

        sql = 'SELECT ip FROM ports WHERE mac=? and port=? and id_r=? and ip=?'
        val = (mac, port, router_id, '')
        rows_nol = cursor.execute(sql, val).fetchall()

        sql = 'SELECT ip FROM ports WHERE mac=? and port=? and id_r=? and ip!=?'
        val = (mac, port, router_id, '')
        rows = cursor.execute(sql, val).fetchall()

        if rows and rows_nol:
            sql = 'DELETE FROM ports WHERE mac=? and port=? and id_r=? and ip=?'
            val = (mac, port, router_id, '')
            cursor.execute(sql, val)

        if ip == '':
            sql = 'UPDATE ports SET t=?, mac=? WHERE port=? and id_r=?'
            val = (dt, mac, port, router_id)
        else:
            sql = 'UPDATE ports SET t=?, mac=?, ip=?, name=? WHERE port=? and id_r=?'
            val = (dt, mac, ip, name, port, router_id)

        cursor.execute(sql, val)


@db_connector
def prepareret(db):
    cursor = db.cursor()
    arplist = arp(s_values['ipaddr'], s_values['interface'])
    routers = cursor.execute("SELECT * FROM routers WHERE ip!='' ORDER BY box, numinbox ").fetchall()

    for router in routers:
        descr = ''
        dt = time.strftime(format_dt, time.localtime(time.time()))
        mib = ".1.3.6.1.2.1.1.1"
        sysdesc = get_snmp_data(router[3], mib)
        for snmp_mib, val in sysdesc[0]:
            descr_a = str(val).split(',')
            descr = descr_a[1] + descr_a[2]

        sql = 'UPDATE routers SET t=?, descr=? WHERE id=?'
        val = (dt, descr, router[0])
        cursor.execute(sql, val)
        db.commit()

        get_varbinds(router[0], router[3], arplist, router[4])

    return {"total": len(routers)}


@db_connector
def prepareret_switch_ports(db, cid):
    cursor = db.cursor()
    arplist = {}
    # arplist = arp(s_values['ipaddr'], s_values['interface'])
    routers = cursor.execute(f"SELECT * FROM routers WHERE id={cid}").fetchall()
    rts = []
    for router in routers:
        r = router
        if router[3] == '':
            routers = cursor.execute(f"SELECT * FROM routers WHERE id={router[5]}").fetchall()
            if routers:
                router = routers[0]
            else:
                return {"total": 0, "routers": rts}
        descr = ''
        dt = time.strftime(format_dt, time.localtime(time.time()))
        mib = ".1.3.6.1.2.1.1.1"
        sysdesc = get_snmp_data(router[3], mib)
        for snmp_mib, val in sysdesc[0]:
            descr_a = str(val).split(',')
            descr = descr_a[1] + descr_a[2]

        sql = 'UPDATE routers SET t=?, descr=? WHERE id=?'
        val = (dt, descr, router[0])
        cursor.execute(sql, val)
        db.commit()

        get_varbinds(router[0], router[3], arplist, router[4])

        rts.append({"routerid": r[0], "name": r[1], "mac": r[2], "ip": r[3], "exclports": r[4], "date": r[7],
                    "stackmaster": r[5], "stacknum": r[6], "fa": r[9], "gi": r[10], "box": r[8], "descr": r[11],
                    "numinbox": r[12]})
    return {"total": len(routers), "routers": rts}


@db_connector
def prepareret_ports(db, cid):
    cursor = db.cursor()
    ports = cursor.execute(f"SELECT * FROM ports WHERE id_r={cid}").fetchall()
    pts = ''
    for port in ports:
        pts += '{"portid": "' + str(port[1]) + '", "ip": "' + str(port[3]) + '", "mac": "' + str(
            port[2]) + '", "name": "' + str(port[4]) + '", "date": "' + str(port[5]) + '", "status": "' + str(
            port[6]) + '", "descr": "' + str(port[7]) + '", "speed": "' + str(port[8] / 1000000) + '"},'
    pts = pts[:-1]
    return f"[{pts}]"


@db_connector
def prepareret_switches(db):
    cursor = db.cursor()
    routers = cursor.execute("SELECT * FROM routers ORDER BY box, numinbox").fetchall()
    rts = []
    for router in routers:
        """router[0] - id router, router[3] - ip router, router[4] - ports"""
        rts.append({"routerid": router[0], "name": router[1], "mac": router[2], "ip": router[3], "exclports": router[4],
                    "date": router[7], "stackmaster": router[5], "stacknum": router[6], "fa": router[9],
                    "gi": router[10], "box": router[8], "descr": router[11], "numinbox": router[12]})
    return {"total": len(routers), "routers": rts}


def do_discovery():
    while True:
        try:
            prepareret()
        except Exception as e:
            print("ERROR DISCOVERY! " + str(e))
        time.sleep(DISCOVERY_PERIOD_SEC)

threading.Thread(target=do_discovery, args=(), daemon=True).start()


if __name__ == "__main__":
    app.run(host=s_values['serverip'], port=s_values['port'])
