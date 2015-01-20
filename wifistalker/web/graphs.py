# Author: Tomasz bla Fortuna
# License: GPLv2

from datetime import datetime

from flask import Blueprint

from flask import Flask, request, g
from flask import jsonify

api = Blueprint('api_graph', __name__)

@api.route('/strength/<mac>')
def get_graph(mac):
    "Get filtered strength graph data"
    labels = []
    data = []
    graph = {
        'labels': labels,
        'datasets': [
            {
                'label': 'dataset1',
                'data': data,
            }
        ]
    }

    # TODO: This could potentially be rewritten to use iterator.
    iterator = g.db.frames.iterframes(src=mac, current=False)
    frames = list(iterator)
    frames_cnt = len(frames)

    pts_max = 100
    group_by = frames_cnt / pts_max

    # Generate data
    point_no = 0
    cur_pts = 0
    cur_value = 0.0
    for frame in frames:
        cur_value += frame['strength']
        cur_pts += 1
        if cur_pts >= group_by:
            val = 1.0 * cur_value / cur_pts
            if point_no % 5 == 0:
                date_str = datetime.fromtimestamp(frame['stamp']).strftime('%Y-%m-%d %H:%M:%S')
                labels.append(date_str)
            else:
                labels.append('')
            data.append(val)
            cur_value = 0.0
            cur_pts = 0
            point_no += 1

    return jsonify({'graph': graph})
