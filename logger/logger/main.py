import json
import logging
import os
from datetime import datetime

import pika

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
LOG_DIR = "logs"

EXCHANGES = [
    "asr",
    "bc",
    "dialogue",
    "dialogue2",
    "dialogue3",
    "emo_act",
    "vap",
    "video_process",
]

timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    filename=os.path.join(LOG_DIR, f"{timestamp}.log"),
    filemode="a",
)


def on_message(channel, method, properties, body):
    """Callback for handling received messages."""
    exchange = method.exchange
    message = {
        "exchange": exchange,
        "body": json.loads(body.decode("utf-8")),
    }
    logging.info(json.dumps(message, ensure_ascii=False))
    channel.basic_ack(delivery_tag=method.delivery_tag)


def setup_audit_queue(channel):
    """Bind a queue to all user-defined exchanges for auditing."""
    queue_name = "log_queue"
    channel.queue_declare(queue=queue_name, durable=True)

    for exchange in EXCHANGES:
        try:
            # Declare the exchange to ensure it exists (idempotent operation)
            channel.exchange_declare(exchange=exchange, exchange_type="fanout")
            channel.queue_bind(exchange=exchange, queue=queue_name, routing_key="#")
            print(f"Bound to exchange: {exchange}")
        except Exception as e:
            print(f"Failed to bind to exchange {exchange}: {e}")

    # Start consuming messages
    channel.basic_consume(queue=queue_name, on_message_callback=on_message)


def main():
    """Main function to set up the RabbitMQ connection and listen for messages."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    try:
        setup_audit_queue(channel)
        print("Listening for messages...")
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Stopping the audit sidecar...")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
