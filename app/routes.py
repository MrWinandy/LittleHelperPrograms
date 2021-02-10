import uuid

from flask import render_template, request, session

from FunctionInterpolationApproximator import FunctionInterpolationApproximator
from app import app

import io
from flask import Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

import numpy as np
from threading import Thread
import time
session_instances = {}
session_alive = {}


def setDefaultValues():
    sp = (-12, 5)
    ep = (12, 5)
    racines = [-10, -4, -1, 2, 5, 9]
    extrema = [(-8, -3), (-6, -1), (-5, -2), (-2.5, 3), (1, -2), (3.5, 2.5), (7, -3)]
    f: FunctionInterpolationApproximator = None
    return sp, ep, racines, extrema, f


def launch_approximate(racines, extrema, sp, ep):
    racines = list(map(lambda x: float(x), racines))
    sp = [float(p) for p in str(sp).strip("()").split(",")]
    ep = [float(p) for p in str(ep).strip("()").split(",")]
    domaine = [sp[0], ep[0]]
    extrema = [sp] + [[float(p) for p in str(e).strip("()").split(",")] for e in extrema] + [ep]
    f = FunctionInterpolationApproximator(racines, extrema, domaine)
    f.approximate()
    return f


def close_session(uid):
    global session_alive
    while True:
        time.sleep(15)
        if session_alive[uid] == 0:
            session_instances[uid].stop()
            break
        session_alive[uid] = 0


@app.before_request
def before_request():
    global session_alive
    if session.get('uid'):
        session_alive[session['uid']] = 1


@app.route('/')
def home():
    sp, ep, racines, extrema, f = setDefaultValues()
    if not session.get('uid'):
        session['uid'] = uuid.uuid4()
        session_alive.update({session['uid']: 0})
        t = Thread(target=close_session, args=(session['uid'],))
        t.start()
    f = launch_approximate(racines, extrema, sp, ep)
    session_instances.update({session['uid']: f})
    latex = f.axisText()
    geogebra = f.geogebraText()
    return render_template('FunctionApproximator.html', racines=racines, extrema=extrema, sp=sp, ep=ep, latex=latex,
                           geogebra=geogebra)


@app.route('/approx', methods=['GET', 'POST'])
def approximate():
    latex = None
    geogebra = None
    f = session_instances[session['uid']]
    if request.method == "POST":
        result = request.form
        racines = []
        extrema = []
        sp = 0
        ep = 0
        for key, value in result.items():
            if key.startswith("racine"):
                racines.append(value)
            if key.startswith("extremum"):
                extrema.append(value)
            if key == "sp":
                sp = value
            if key == "ep":
                ep = value
        for i in range(len(racines)):
            if f"remove racine {i}" in result:
                del racines[i]
                f = launch_approximate(racines, extrema, sp, ep)
                latex = f.axisText()
                geogebra = f.geogebraText()
        for i in range(len(extrema)):
            if f"remove extremum {i}" in result:
                del extrema[i]
                f = launch_approximate(racines, extrema, sp, ep)
                latex = f.axisText()
                geogebra = f.geogebraText()
        if "add racine" in result:
            racines.append(0)
            latex = None
            geogebra = None
        if "add extremum" in result:
            extrema.append((0, 0))
            latex = None
            geogebra = None
        if "clear racines" in result:
            racines = []
        if "clear extrema" in result:
            extrema = []
        if "approximate" in result:
            f = launch_approximate(racines, extrema, sp, ep)
            latex = f.axisText()
            geogebra = f.geogebraText()

        if not session.get('uid'):
            session['uid'] = uuid.uuid4()
            session_alive.update({session['uid']: 0})
            t = Thread(target=close_session, args=(session['uid'],))
            t.start()
        f = launch_approximate(racines, extrema, sp, ep)
        session_instances.update({session['uid']: f})

    return render_template('FunctionApproximator.html', racines=racines, extrema=extrema, sp=sp, ep=ep, latex=latex,
                           geogebra=geogebra)


@app.route('/plot.png')
def plot_png():
    f = session_instances[session['uid']]
    fig = create_figure(f)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')


def create_figure(f):
    if f is None:
        return None

    fig = Figure(figsize=(f.max_x - f.min_x, f.max_y - f.min_y))
    axis = fig.add_subplot(1, 1, 1)
    # set up a plot
    ax1 = axis

    # spine placement data centered
    ax1.spines['left'].set_position(('data', 0.0))
    ax1.spines['bottom'].set_position(('data', 0.0))
    ax1.spines['right'].set_color('none')
    ax1.spines['top'].set_color('none')

    ax1.set_aspect("equal")

    ax1.grid(True)
    ax1.set_ylim(1.2 * f.min_y, 1.2 * f.max_y)
    ax1.set_xlim(f.min_x, f.max_x)
    ax1.set_xticks(np.arange(np.ceil(0.95 * f.min_x), np.floor(0.95 * f.max_x) + 1, 1))
    ax1.set_yticks(np.arange(np.ceil(1.2 * f.min_y), np.floor(1.2 * f.max_y) + 1, 1))
    xs = f.xs
    ys = f.ys

    axis.plot(xs, ys)
    fig.tight_layout()

    return fig
