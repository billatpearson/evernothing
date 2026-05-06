"""
SMS Receive Service — Flask web service for inbound SMS via AWS SNS/Pinpoint.
"""
import datetime
import json
import logging
import os
import sqlite3
import secrets

import boto3
import requests
from flask import Flask, jsonify, request

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
except ImportError:
    pass

AWS_REGION         = os.environ.get('AWS_REGION', 'us-east-1')
PINPOINT_APP_ID    = os.environ.get('PINPOINT_APP_ID', '')
PINPOINT_NUMBER    = os.environ.get('PINPOINT_NUMBER', '')  # E.164 format
SNS_TOPIC_ARN      = os.environ.get('SNS_TOPIC_ARN', '')
DB_FILE            = os.environ.get('DB_FILE', os.path.join(
                         os.path.dirname(os.path.abspath(__file__)), 'sms.db'))
PORT               = int(os.environ.get('PORT', '5050'))

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('sms_service')

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_number TEXT NOT NULL,
    to_number TEXT,
    body TEXT NOT NULL,
    received_at TEXT NOT NULL,
    sns_message_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_from ON messages(from_number);
CREATE INDEX IF NOT EXISTS idx_received ON messages(received_at);
"""

def get_db():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = get_db()
    con.executescript(_SCHEMA)
    con.commit()
    con.close()

# ---------------------------------------------------------------------------
# AWS Pinpoint client
# ---------------------------------------------------------------------------
def _pinpoint_client():
    kwargs = {'region_name': AWS_REGION}
    key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
    if key and secret:
        kwargs['aws_access_key_id'] = key
        kwargs['aws_secret_access_key'] = secret
    return boto3.client('pinpoint', **kwargs)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/sms/inbound', methods=['POST'])
def inbound_sms():
    """Receive SNS notification containing inbound SMS from Pinpoint."""
    # Handle SNS subscription confirmation
    msg_type = request.headers.get('x-amz-sns-message-type', '')

    try:
        payload = json.loads(request.data)
    except (json.JSONDecodeError, TypeError):
        return jsonify({'error': 'Invalid JSON'}), 400

    if msg_type == 'SubscriptionConfirmation':
        # Auto-confirm the subscription
        confirm_url = payload.get('SubscribeURL')
        if confirm_url:
            requests.get(confirm_url, timeout=10)
            log.info(f'SNS subscription confirmed: {SNS_TOPIC_ARN}')
        return jsonify({'ok': True, 'action': 'subscription_confirmed'})

    if msg_type == 'Notification':
        message = json.loads(payload.get('Message', '{}'))
        # Pinpoint SMS event format
        from_number = message.get('originationNumber', '')
        to_number   = message.get('destinationNumber', '')
        body        = message.get('messageBody', '')
        msg_id      = payload.get('MessageId', '')

        if from_number and body:
            con = get_db()
            con.execute(
                'INSERT INTO messages (from_number, to_number, body, received_at, sns_message_id) VALUES (?,?,?,?,?)',
                (from_number, to_number, body,
                 datetime.datetime.utcnow().isoformat() + 'Z', msg_id))
            con.commit()
            con.close()
            log.info(f'SMS received from {from_number}: {body[:50]}')
            return jsonify({'ok': True, 'stored': True})

    return jsonify({'ok': True, 'action': 'ignored'})


@app.route('/sms/messages', methods=['GET'])
def list_messages():
    """List received messages with optional filters."""
    limit       = request.args.get('limit', '50', type=int)
    from_number = request.args.get('from_number', '')
    since       = request.args.get('since', '')

    sql = 'SELECT * FROM messages WHERE 1=1'
    params = []
    if from_number:
        sql += ' AND from_number = ?'
        params.append(from_number)
    if since:
        sql += ' AND received_at >= ?'
        params.append(since)
    sql += ' ORDER BY received_at DESC LIMIT ?'
    params.append(limit)

    con = get_db()
    rows = con.execute(sql, params).fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])


@app.route('/sms/messages/<int:msg_id>', methods=['GET'])
def get_message(msg_id):
    """Get a single message by ID."""
    con = get_db()
    row = con.execute('SELECT * FROM messages WHERE id=?', (msg_id,)).fetchone()
    con.close()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dict(row))


@app.route('/sms/messages/<int:msg_id>', methods=['DELETE'])
def delete_message(msg_id):
    """Delete a message by ID."""
    con = get_db()
    con.execute('DELETE FROM messages WHERE id=?', (msg_id,))
    con.commit()
    con.close()
    return jsonify({'ok': True})


@app.route('/sms/stats', methods=['GET'])
def stats():
    """Message statistics."""
    con = get_db()
    total = con.execute('SELECT COUNT(*) FROM messages').fetchone()[0]
    last = con.execute('SELECT received_at FROM messages ORDER BY received_at DESC LIMIT 1').fetchone()
    senders = con.execute('SELECT COUNT(DISTINCT from_number) FROM messages').fetchone()[0]
    con.close()
    return jsonify({
        'total_messages': total,
        'last_received': last[0] if last else None,
        'unique_senders': senders
    })


@app.route('/sms/send', methods=['POST'])
def send_sms():
    """Send an outbound SMS via AWS Pinpoint."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    to_number = data.get('to', '').strip()
    message   = data.get('message', '').strip()

    if not to_number or not message:
        return jsonify({'error': 'to and message are required'}), 400

    if not PINPOINT_APP_ID or not PINPOINT_NUMBER:
        return jsonify({'error': 'PINPOINT_APP_ID and PINPOINT_NUMBER not configured'}), 500

    try:
        client = _pinpoint_client()
        response = client.send_messages(
            ApplicationId=PINPOINT_APP_ID,
            MessageRequest={
                'Addresses': {
                    to_number: {'ChannelType': 'SMS'}
                },
                'MessageConfiguration': {
                    'SMSMessage': {
                        'Body': message,
                        'MessageType': 'TRANSACTIONAL',
                        'OriginationNumber': PINPOINT_NUMBER
                    }
                }
            }
        )
        result = response['MessageResponse']['Result'].get(to_number, {})
        msg_id = result.get('MessageId', '')
        status = result.get('DeliveryStatus', 'UNKNOWN')

        if status == 'SUCCESSFUL':
            log.info(f'SMS sent to {to_number}: {message[:50]}')
            return jsonify({'ok': True, 'message_id': msg_id})
        else:
            log.warning(f'SMS send failed to {to_number}: {status}')
            return jsonify({'ok': False, 'status': status,
                           'reason': result.get('StatusMessage', '')}), 502

    except Exception as e:
        log.error(f'SMS send error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'service': 'sms-receive', 'port': PORT})


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    init_db()
    log.info(f'SMS Receive Service starting on http://127.0.0.1:{PORT}')
    log.info(f'Pinpoint App: {PINPOINT_APP_ID or "NOT SET"}')
    log.info(f'Pinpoint Number: {PINPOINT_NUMBER or "NOT SET"}')
    log.info(f'SNS Topic: {SNS_TOPIC_ARN or "NOT SET"}')
    app.run(host='127.0.0.1', port=PORT, debug=False)
