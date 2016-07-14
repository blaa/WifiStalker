# Author: Tomasz bla Fortuna
# License: GPLv2
import re

from flask import Blueprint

from flask import Flask, request, g
from flask import jsonify

from IPython import embed

api = Blueprint('api_knowledge', __name__)

def _parse_tags(tags):
    "Parse tags from a space-separated string"
    tags = re.findall('([-+!@#$%^&*()0-9a-zA-Z_]+ ?)', tags, flags=re.UNICODE)
    tags = [tag.strip() for tag in tags]
    return tags

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
    ssid_filter = request.args.getlist('ssid', None)
    tag_filter = request.args.getlist('tag', None)

    if time_window:
        time_window = float(time_window)

    knowledge = g.db.knowledge.sender_query(mac=mac, sort=sort, time_window=time_window,
                                            ssid_filter=ssid_filter, tag_filter=tag_filter)

    for_web = []
    for sender in knowledge:
        sender = sender.get_dict()
        if 'tags' in sender['user']:
            sender['user']['tags'] = " ".join(sender['user']['tags'])
        if mac is None:
            # Limit assocs / dsts in response for the table, keep in directed questions
            sender['aggregate']['tags_dst'] = len(sender['aggregate']['tags_dst'])
        else:
            # List instead of dict + sort it in Python
            dsts = [(mac, tags)
                    for mac, tags in sender['aggregate']['tags_dst'].iteritems()]
            dsts.sort(key=lambda x: x[1]['_sum'], reverse=True)
            sender['aggregate']['tags_dst'] = dsts

        for_web.append(sender)

    if mac is not None:
        # Add additional related data
        sender = for_web[0]
        related_macs = [m for m, t in sender['aggregate']['tags_dst']]
        mapping = g.db.knowledge.alias_query(related_macs)
    else:
        mapping = None

    return jsonify({
        'knowledge': for_web,
        'related': mapping,
    })

@api.route('/userdata', methods=['POST'])
def set_alias():
    u"Handle a alias update"
    data = request.get_json()
    mac = data.get('mac', None)
    alias = data.get('alias', None)
    notes = data.get('notes', None)
    owner = data.get('owner', None)
    # Parse tags
    tags = data.get('tags', '')
    tags = _parse_tags(tags)

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
        sender.set_userdata(alias, owner, notes, tags)
        ret = g.db.knowledge.sender_store(sender)
        if ret is False:
            print "OPTIMISTIC LOCKING FAILED - retry", i
            continue
        return jsonify({'OK': True})
    return jsonify({'OK': False})


@api.route('/tag/range', methods=['POST'])
def tag_range():
    "Add tag to a range of senders"
    from datetime import datetime
    from dateutil import tz
    UTC = tz.gettz('UTC')
    LOCAL = tz.tzlocal()

    ##
    # Parse parameters
    data = request.get_json()

    range_from = data.get('from', None)
    range_to = data.get('to', None)
    min_strength = data.get('min_str', '-100')
    min_strength = int(min_strength)

    tags = data.get('tags', None)
    tags = _parse_tags(tags)
    tag_types = data.get('types', None)
    untag = data.get('untag', False)

    assert tag_types in ['all', 'clients', 'aps']

    if not tags:
        return jsonify({'OK': False, 'cnt': 0})

    print "ORIG from", range_from, "to", range_to

    range_from = range_from.split('.')[0]
    range_to = range_to.split('.')[0]

    time_format =  '%Y-%m-%dT%H:%M:%S' # FIXME: Ending is weird. This should be UTC time.
    range_from = datetime.strptime(range_from, time_format)
    range_to = datetime.strptime(range_to, time_format)
    print "PARSED from", range_from, "to", range_to

    range_from = range_from.replace(tzinfo=UTC)
    range_to = range_to.replace(tzinfo=UTC)
    range_from = range_from.astimezone(LOCAL)
    range_to = range_to.astimezone(LOCAL)

    print "LOCAL from", range_from, "to", range_to

    range_from_local_stamp = float(range_from.strftime('%s'))
    range_to_local_stamp = float(range_to.strftime('%s'))

    ##
    # Aggregate MACs to tag.
    # Multiple sources possible - all_frames, current_frames, events.
    # TODO: all_frames would be nice to be purgeable and events used eventually
    srcs = g.db.frames.all_in_range(range_from_local_stamp, range_to_local_stamp, min_strength, current=False)

    altered_cnt = g.db.knowledge.sender_tag(srcs, tags, types=tag_types, untag=untag)
    print "Tagged entries:", altered_cnt

    return jsonify({'OK': True, 'cnt': altered_cnt})
