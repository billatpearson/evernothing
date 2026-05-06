# SMS Receive Service

A standalone Flask web service that receives inbound SMS messages via AWS SNS/Pinpoint and stores them locally in SQLite.

## Architecture

```
[Phone sends SMS] → [AWS Pinpoint Number] → [AWS SNS Topic] → [HTTP POST to this service] → [SQLite DB]
```

## Prerequisites

- Python 3.9+
- AWS Account with Pinpoint SMS enabled
- A Pinpoint phone number (long code or toll-free)
- Public URL or ngrok tunnel for SNS to reach your localhost

## Quick Start

```bash
cd sms_service
pip install -r requirements.txt
python app.py
```

Server starts on `http://127.0.0.1:5050`

## API Endpoints

### POST /sms/inbound
Receives SNS notifications containing inbound SMS messages.
Called automatically by AWS SNS — not for manual use.

**Headers:** `x-amz-sns-message-type: Notification`

**Body:** SNS JSON envelope containing Pinpoint SMS event.

---

### GET /sms/messages
Returns all received messages, newest first.

**Query params:**
- `limit` (int, default 50) — max messages to return
- `from_number` (string) — filter by sender phone number
- `since` (ISO date) — only messages after this timestamp

**Response:**
```json
[
  {
    "id": 1,
    "from_number": "+16027694235",
    "to_number": "+18005551234",
    "body": "Hello world",
    "received_at": "2026-05-05T14:30:00Z",
    "sns_message_id": "abc-123"
  }
]
```

---

### GET /sms/messages/{id}
Returns a single message by ID.

---

### GET /sms/stats
Returns message count and last received timestamp.

```json
{
  "total_messages": 42,
  "last_received": "2026-05-05T14:30:00Z",
  "unique_senders": 3
}
```

---

### POST /sms/send
Sends an outbound SMS via AWS Pinpoint.

**Body:**
```json
{
  "to": "+16027694235",
  "message": "Test from SMS service"
}
```

**Response:**
```json
{
  "ok": true,
  "message_id": "pinpoint-msg-id-123"
}
```

---

### DELETE /sms/messages/{id}
Deletes a message by ID.

---

## Configuration

Set in `.env` or environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for Pinpoint | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | AWS credentials | (IAM role preferred) |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials | (IAM role preferred) |
| `PINPOINT_APP_ID` | Pinpoint application ID | required |
| `PINPOINT_NUMBER` | Your Pinpoint phone number (E.164) | required |
| `SNS_TOPIC_ARN` | SNS topic ARN for inbound SMS | required |
| `DB_FILE` | SQLite database path | `sms.db` |
| `PORT` | Server port | `5050` |
| `SECRET_KEY` | Flask session key | auto-generated |

## AWS Setup Guide

### 1. Enable Pinpoint SMS

```bash
aws pinpoint create-app --create-application-request Name=sms-service
```

### 2. Request a phone number

In AWS Console → Pinpoint → SMS and voice → Phone numbers → Request number.
Choose a long code or toll-free number.

### 3. Create SNS Topic

```bash
aws sns create-topic --name sms-inbound
```

### 4. Configure Pinpoint to forward SMS to SNS

In Pinpoint → SMS → Number settings → Two-way SMS → Enable → Set SNS topic.

### 5. Subscribe this service to the SNS topic

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT:sms-inbound \
  --protocol http \
  --notification-endpoint http://YOUR_PUBLIC_URL/sms/inbound
```

### 6. Confirm subscription

The service auto-confirms SNS subscription requests.

## Cost Estimate (AWS, US)

| Item | Cost |
|------|------|
| Pinpoint long code number | $1.00/month |
| Inbound SMS (receive) | $0.0075/message |
| Outbound SMS (send, US) | $0.00645/message |
| SNS notifications | $0.50/million (effectively free) |
| **Monthly estimate (100 msgs/month)** | **~$2.00/month** |
| **Monthly estimate (1000 msgs/month)** | **~$9.00/month** |

Notes:
- Toll-free numbers cost $2.00/month but have better deliverability
- Short codes cost $1000+/month — not recommended for personal use
- No charge for the Flask service itself (runs on your machine)

## Test

```bash
python test_sms.py
```

Sends a test SMS to the configured number and verifies delivery.
