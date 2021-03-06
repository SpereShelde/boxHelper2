import configparser
import sqlite3

import time
from flask import Flask, render_template, Response, flash, redirect, url_for, request

from feed import Feed
from torrent_controller import tc

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'
app.debug = True

@app.route('/')
@app.route('/index')
@app.route('/home')
def index():
    return render_template('index.html')


@app.route('/rss', methods=['GET'])
def rss():
    num, pro, show, low, high = 20, 0, 3, 0,109951162777600
    #show: 0 for B, 1 for KB, 2 for MB, 3 for GB, 4 for TB
    if 'num' in request.args.keys():
        par = request.args.get('num')
        if str.isdigit(par):
            num = min(int(par), 100)
    if 'pro' in request.args.keys():
        par = request.args.get('pro')
        if str.isdigit(par):
            pro = int(par)
    if 'show' in request.args.keys():
        par = request.args.get('show')
        if str.isdigit(par):
            show = int(par)
    if 'low' in request.args.keys():
        par = request.args.get('low')
        if str.isdigit(par):
            low = int(par)
    if 'high' in request.args.keys():
        par = request.args.get('high')
        if str.isdigit(par):
            high = min(109951162777600, int(par))
    config = configparser.RawConfigParser()
    config.read("config.ini", encoding="utf-8")
    connection = sqlite3.connect('boxHelper.db')
    cursor = connection.cursor()
    cursor.execute('SELECT title, size, promotions, detail_link, download_link, uploader  FROM torrents_collected where download_link != "" and promotions >= ? and size >= ? and size <= ? ORDER BY get_time DESC limit ?', (pro, low, high, num))
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    feed = Feed('Box Helper', 'http://127.0.0.1:12020')

    for result in results:
        size = result[1]
        size_str = "%dB" % size
        if show == 1:
            size_str = "%fKB" % (size / 1024)
        elif show == 2:
            size_str = "%fMB" % (size / 1024**2)
        elif show == 3:
            size_str = "%fGB" % (size / 1024 ** 3)
        elif show == 4:
            size_str = "%fTB" % (size / 1024 ** 4)
        feed.append_item("%s [%s%s] [%s]" % (result[0], size_str, 'Free' if result[2]>=10 else '', result[5]), result[3], result[4], result[1])
    return Response(feed.get_xml(), mimetype='application/xml')

@app.route('/panel')
def panel():
    return render_template('panel.html')

@app.route('/status', methods=['POST'])
def status():
    if tc.is_alive():
        flash('Box Helper is running.')
    else:
        flash('Box Helper is stopped.')
    return redirect(url_for('panel'))

@app.route('/start', methods=['POST'])
def start():
    if tc.is_alive():
        flash('Box Helper is running.')
    else:
        tc.start()
        time.sleep(2)
        if tc.is_alive():
            flash('Box Helper started.')
        else:
            flash('Box Helper CANNOT start.')
    return redirect(url_for('panel'))

@app.route('/stop', methods=['POST'])
def stop():
    if tc.is_alive():
        tc.stop()
        flash('Box Helper is stopping.')
    else:
        flash('Box Helper already stopped.')
    return redirect(url_for('panel'))

@app.route('/truncate', methods=['POST'])
def truncate():
    if tc.is_alive():
        flash('Box Helper is running. Please stop it first.')
    else:
        config = configparser.RawConfigParser()
        config.read("config.ini", encoding="utf-8")
        connection = sqlite3.connect('boxHelper.db')
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM torrents_collected")
            cursor.execute("DELETE FROM patterns")
            cursor.execute("UPDATE sqlite_sequence SET seq = 0")
            connection.commit()
        except:
            flash('Box Helper CANNOT clear data.')
        cursor.close()
        connection.close()
        flash('Box Helper cleared data.')
    return redirect(url_for('panel'))

if __name__ == '__main__':
    app.run(debug=True)