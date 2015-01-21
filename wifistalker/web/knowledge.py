# Author: Tomasz bla Fortuna
# License: GPLv2

from flask import Blueprint

from flask import Flask, request, g
from flask import jsonify

from IPython import embed

api = Blueprint('api_knowledge', __name__)

@api.route('/logs')
def get_logs():
    u"Read logs"
    logs = g.db.log_get(count=20)
    return jsonify({'logs': logs})

@api.route('/knowledge')
def get_knowledge():
    u"Read knowledge limited to recent appearances"
    time_window = request.args.get('time_window', None)
    sort = request.args.get('sort', 'last_seen')
    mac = request.args.get('mac', None)

    if time_window:
        time_window = float(time_window)

    knowledge = g.db.knowledge.sender_query(mac=mac, sort=sort, time_window=time_window)

    for_web = []
    for sender in knowledge:
        sender = sender.get_dict()
        # These can be huge and aren't displayed
        sender['aggregate']['assocs'] = len(sender['aggregate']['assocs'])
        sender['aggregate']['dsts'] = len(sender['aggregate']['dsts'])
        for_web.append(sender)

    return jsonify({'knowledge': for_web})

@api.route('/snapshot', methods=['POST'])
def post_snapshot():
    u"Handle a data dump"
    data = request.get_json()
    time_window = data.get('timeWindow', None)
    name = data.get('name', 'noname')
    if not name:
        name = 'noname'
    try:
        time_window = int(time_window)
    except (ValueError, TypeError):
        return

    model.presence_snapshot(name, time_window)
    return jsonify({'OK': True})

@api.route('/userdata', methods=['POST'])
def set_alias():
    u"Handle a alias update"
    data = request.get_json()
    mac = data.get('mac', None)
    alias = data.get('alias', None)
    notes = data.get('notes', None)
    owner = data.get('owner', None)
    if mac is None:
        return
    if not alias:  # '' -> None
        alias = None
    if not owner:
        owner = None
    if not notes:
        notes = None

    for i in range(10):
        sender = g.db.knowledge.sender_query(mac=mac)
        if not sender:
            print "UNABLE TO FIND SENDER TO UPDATE"
            return jsonify({'OK': False})

        sender = sender[0]
        sender.set_userdata(alias, owner, notes)
        ret = g.db.knowledge.sender_store(sender)
        if ret is False:
            print "OPTIMISTIC LOCKING FAILED - retry", i
            continue
        return jsonify({'OK': True})
    return jsonify({'OK': False})
