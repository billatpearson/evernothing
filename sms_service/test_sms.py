"""
test_sms.py — Test case that sends an SMS to 602-769-4235 via AWS Pinpoint.

Prerequisites:
  - .env configured with PINPOINT_APP_ID, PINPOINT_NUMBER, AWS credentials
  - Pinpoint number must be provisioned and active

Usage:
  python test_sms.py
"""
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
except ImportError:
    pass

from app import app, init_db, DB_FILE

TARGET_NUMBER = '+16027694235'


class TestSMSService(unittest.TestCase):
    """Unit tests — no real AWS calls."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        init_db()

    def tearDown(self):
        try:
            os.unlink(DB_FILE)
        except OSError:
            pass

    def test_health_check(self):
        rv = self.client.get('/health')
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertEqual(data['status'], 'ok')

    def test_inbound_sns_subscription_confirmation(self):
        """Simulates SNS subscription confirmation."""
        payload = {
            'Type': 'SubscriptionConfirmation',
            'SubscribeURL': 'https://example.com/confirm',
            'TopicArn': 'arn:aws:sns:us-east-1:123:test'
        }
        with patch('app.requests.get') as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            rv = self.client.post('/sms/inbound',
                data=json.dumps(payload),
                content_type='application/json',
                headers={'x-amz-sns-message-type': 'SubscriptionConfirmation'})
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(rv.get_json()['ok'])

    def test_inbound_sms_stored(self):
        """Simulates receiving an inbound SMS via SNS notification."""
        sms_event = {
            'originationNumber': TARGET_NUMBER,
            'destinationNumber': '+18005551234',
            'messageBody': 'Hello from test'
        }
        payload = {
            'Type': 'Notification',
            'MessageId': 'test-msg-001',
            'Message': json.dumps(sms_event)
        }
        rv = self.client.post('/sms/inbound',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'x-amz-sns-message-type': 'Notification'})
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(rv.get_json()['stored'])

        # Verify stored
        rv = self.client.get('/sms/messages')
        msgs = rv.get_json()
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['from_number'], TARGET_NUMBER)
        self.assertEqual(msgs[0]['body'], 'Hello from test')

    def test_list_messages_filter_by_number(self):
        """Filter messages by sender number."""
        sms1 = {'originationNumber': '+11111111111', 'destinationNumber': '+18005551234', 'messageBody': 'msg1'}
        sms2 = {'originationNumber': TARGET_NUMBER, 'destinationNumber': '+18005551234', 'messageBody': 'msg2'}
        for sms in [sms1, sms2]:
            self.client.post('/sms/inbound',
                data=json.dumps({'Type': 'Notification', 'MessageId': 'x',
                                 'Message': json.dumps(sms)}),
                content_type='application/json',
                headers={'x-amz-sns-message-type': 'Notification'})

        rv = self.client.get('/sms/messages', query_string={'from_number': TARGET_NUMBER})
        msgs = rv.get_json()
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['body'], 'msg2')

    def test_delete_message(self):
        """Delete a stored message."""
        sms = {'originationNumber': TARGET_NUMBER, 'messageBody': 'delete me'}
        self.client.post('/sms/inbound',
            data=json.dumps({'Type': 'Notification', 'MessageId': 'del1',
                             'Message': json.dumps(sms)}),
            content_type='application/json',
            headers={'x-amz-sns-message-type': 'Notification'})

        rv = self.client.get('/sms/messages')
        msg_id = rv.get_json()[0]['id']

        rv = self.client.delete(f'/sms/messages/{msg_id}')
        self.assertEqual(rv.status_code, 200)

        rv = self.client.get(f'/sms/messages/{msg_id}')
        self.assertEqual(rv.status_code, 404)

    def test_stats(self):
        """Stats endpoint returns correct counts."""
        rv = self.client.get('/sms/stats')
        data = rv.get_json()
        self.assertEqual(data['total_messages'], 0)

    @patch('app._pinpoint_client')
    def test_send_sms(self, mock_client_fn):
        """Test outbound SMS send (mocked)."""
        mock_client = MagicMock()
        mock_client.send_messages.return_value = {
            'MessageResponse': {
                'Result': {
                    TARGET_NUMBER: {
                        'DeliveryStatus': 'SUCCESSFUL',
                        'MessageId': 'mock-msg-123'
                    }
                }
            }
        }
        mock_client_fn.return_value = mock_client

        # Temporarily set required config
        import app as _app
        _app.PINPOINT_APP_ID = 'test-app-id'
        _app.PINPOINT_NUMBER = '+18005551234'

        rv = self.client.post('/sms/send',
            data=json.dumps({'to': TARGET_NUMBER, 'message': 'Test SMS from service'}),
            content_type='application/json')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(rv.get_json()['ok'])
        self.assertEqual(rv.get_json()['message_id'], 'mock-msg-123')

    def test_send_sms_missing_fields(self):
        """Send endpoint rejects missing fields."""
        rv = self.client.post('/sms/send',
            data=json.dumps({'to': '', 'message': ''}),
            content_type='application/json')
        self.assertEqual(rv.status_code, 400)


class TestSMSLive(unittest.TestCase):
    """
    Live integration test — actually sends an SMS to 602-769-4235.
    Only runs when PINPOINT_APP_ID is configured.
    Skip with: python -m pytest test_sms.py -k "not Live"
    """

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @unittest.skipUnless(os.environ.get('PINPOINT_APP_ID'),
                         'PINPOINT_APP_ID not set — skipping live test')
    def test_live_send_sms(self):
        """Send a real SMS to 602-769-4235."""
        rv = self.client.post('/sms/send',
            data=json.dumps({
                'to': TARGET_NUMBER,
                'message': 'EverNothing SMS Service test — if you received this, the service is working.'
            }),
            content_type='application/json')
        data = rv.get_json()
        print(f'\nLive SMS result: {data}')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(data['ok'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
