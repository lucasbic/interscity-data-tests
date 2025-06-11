import yaml
import pika
import time
import sys
import threading
import os

# Variáveis globais para métricas
sent_messages = 0
received_messages = 0
test_duration = 5  # Padrão em minutos, será sobrescrito pelo workload

def load_workload(file_path):
    """Load workload configuration from YAML file."""
    with open(file_path, 'r') as file:
        workload = yaml.safe_load(file)
    return workload

def producer(queue_name, message_size, producer_rate, test_duration, host, payload_file=None):
    global sent_messages
    """Send messages to the RabbitMQ queue."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)

    # Load payload from file or generate one
    if payload_file:
        with open(payload_file, 'r') as f:
            message = f.read()
    else:
        message = "x" * message_size

    message_interval = 1 / producer_rate
    start_time = time.time()
    end_time = start_time + test_duration * 60

    while time.time() < end_time:
        channel.basic_publish(exchange='', routing_key=queue_name, body=message)
        sent_messages += 1
        time.sleep(message_interval)

    connection.close()

def consumer(queue_name, test_duration, host):
    """Consume messages from the RabbitMQ queue."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)

    start_time = time.time()
    end_time = start_time + test_duration * 60

    def callback(ch, method, properties, body):
        global received_messages
        received_messages += 1

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    print("Consumer is waiting for messages...")

    while time.time() < end_time:
        channel.connection.process_data_events(time_limit=1)

    connection.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python benchmark.py <workload.yaml>")
        sys.exit(1)

    workload_file = sys.argv[1]
    workload = load_workload(workload_file)

    # Extract workload configuration
    queue_name = workload.get("name", "benchmark_queue").replace(" ", "_").lower()
    message_size = workload.get("messageSize", 1024)
    payload_file = workload.get("payloadFile", None)
    if payload_file:
        payload_file = os.path.join("/home/lucas/interscity/benchmark/", payload_file)
    producer_rate = workload.get("producerRate", 10000)
    test_duration = workload.get("testDurationMinutes", 5)
    host = "localhost"  # Assuming RabbitMQ is running locally

    # Determine number of producers and consumers
    producers_count = workload.get("producersPerTopic", 1)
    consumers_count = workload.get("consumerPerSubscription", 1)

    # Start producers and consumers
    threads = []

    for _ in range(producers_count):
        t = threading.Thread(target=producer, args=(queue_name, message_size, producer_rate, test_duration, host, payload_file))
        threads.append(t)
        t.start()

    for _ in range(consumers_count):
        t = threading.Thread(target=consumer, args=(queue_name, test_duration, host))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Cálculo da taxa de envio e consumo
    producer_rate = sent_messages / (test_duration * 60)  # Mensagens por segundo
    consumer_rate = received_messages / (test_duration * 60)  # Mensagens por segundo

    # Exibição das métricas
    print(f"Producer finished: Sent {sent_messages} messages in {test_duration} minutes.")
    print(f"Producer rate: {producer_rate:.2f} messages/second.")
    print(f"Consumer finished: Received {received_messages} messages in {test_duration} minutes.")
    print(f"Consumer rate: {consumer_rate:.2f} messages/second.")


    print("Benchmark completed.")
