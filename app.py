import logging
from flask import Flask, request, jsonify, render_template, Response
from epl import print_label
from render import render_to_png_bytes, render_to_epl
from config import PRINTER_DEV

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
app = Flask(__name__)


@app.route('/')
def editor():
    return render_template('editor.html')


@app.route('/print', methods=['POST'])
def handle_print():
    data = request.get_json(force=True)
    logging.info("PRINT job: %s", data)
    print_label(data)
    return jsonify({"ok": True})


@app.route('/preview', methods=['POST'])
def preview():
    layout = request.get_json(force=True)
    png = render_to_png_bytes(layout)
    return Response(png, mimetype='image/png')


@app.route('/print-custom', methods=['POST'])
def print_custom():
    layout = request.get_json(force=True)
    logging.info("PRINT custom layout")
    epl = render_to_epl(layout)
    with open(PRINTER_DEV, 'wb') as f:
        f.write(epl)
    return jsonify({"ok": True})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"ok": True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050)
