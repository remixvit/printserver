import logging
from flask import Flask, request, jsonify
from epl import print_label

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
app = Flask(__name__)


@app.route('/print', methods=['POST'])
def handle_print():
    data = request.get_json(force=True)
    logging.info("PRINT job: %s", data)
    print_label(data)
    return jsonify({"ok": True})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"ok": True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050)
