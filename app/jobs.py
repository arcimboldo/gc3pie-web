#!/usr/bin/env python
# -*- coding: utf-8 -*-#
#
#
# Copyright (C) 2016, S3IT, University of Zurich. All rights reserved.
#
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

__docformat__ = 'reStructuredText'
__author__ = 'Antonio Messina <antonio.s.messina@gmail.com>'

from flask import Blueprint, render_template, abort, current_app, request, redirect, url_for
from jinja2 import TemplateNotFound
# import gc3libs
import xmlrpclib
import os
import json
import yaml

jobs = Blueprint("jobs", __name__,
                      template_folder='templates')


@jobs.route('/jobs')
def list():
    try:
        wdir = current_app.config.get('GC3APP_DIR', '.')
        portfile = os.path.join(wdir, 'daemon.port')
        with open(portfile, 'r') as fd:
            try:
                ip, port = fd.read().split(':')
                port = int(port)
            except Exception as ex:
                raise Exception("Error parsing file %s: %s" % (portfile, ex))
    except Exception as ex:
        abort(500, "Unable to access to remote GC3Pie daemon: %s" % ex)
    server = xmlrpclib.ServerProxy('http://%s:%d' % (ip, port))
    msg = request.args.get('msg')
    jobs = json.loads(server.json_list())
    return render_template('jobs/list.html', jobs=jobs, msg=msg)

@jobs.route('/job/<jobid>', methods=['GET', 'POST'])
def show(jobid):
    try:
        wdir = current_app.config.get('GC3APP_DIR', '.')
        portfile = os.path.join(wdir, 'daemon.port')
        with open(portfile, 'r') as fd:
            try:
                ip, port = fd.read().split(':')
                port = int(port)
            except Exception as ex:
                raise Exception("Error parsing file %s: %s" % (portfile, ex))
    except Exception as ex:
        abort(500, "Unable to access to remote GC3Pie daemon: %s" % ex)
    server = xmlrpclib.ServerProxy('http://%s:%d' % (ip, port))

    msg = request.args.get('msg')

    if request.method == 'GET':
        job = json.loads(server.json_show(jobid))
        job_s = json.dumps(job, indent=4)
        # Fix a few things...
        if 'arguments' in job:
            job['arguments'] = job['arguments'].split(',')
        if 'tasks' in job:
            job['tasks'] = job['tasks'].split(',')
        return render_template('jobs/show.html', job=job, job_s=job_s, msg=msg)
    else:
        action = request.form.get('action')
        if action == 'kill':
            msg = server.kill(jobid)
            return redirect(url_for('jobs.show', jobid=jobid, msg=msg))
        elif action == 'remove':
            msg = server.remove(jobid)
            return redirect(url_for('jobs.list', msg=msg))
        elif action == 'resubmit':
            msg=server.resubmit(jobid)
            return redirect(url_for('jobs.show', jobid=jobid, msg=msg))
        abort(404)
