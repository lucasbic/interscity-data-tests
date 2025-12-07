import argparse
import threading
import time
import json
import boto3
import pika
import psutil
import sys
import csv
import os
from datetime import datetime

# Métricas globais
metrics = {
    "sent": 0,
    "received": 0,
    "latencies": [],
    "errors": 0
}

prod_duration = 0
cons_duration = 0

metrics_lock = threading.Lock()

# -----------------------------
# Producer for RabbitMQ
# -----------------------------
def rabbitmq_producer(host, queue_name, message_size, max_messages, results):
    credentials = pika.PlainCredentials("testuser", "testpassword")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)

    message = {"payload": "X" * message_size, "timestamp": None}
    sent_messages = 0
    start_time = time.time()

    #while time.time() - start_time < test_duration and sent_messages < max_messages:
    while sent_messages < max_messages:
        message["timestamp"] = time.time()
        channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(message))
        sent_messages += 1
        #time.sleep(1 / producer_rate)

    connection.close()
    results.update({
        "sent": sent_messages
    })

    prod_duration = time.time() - start_time
    print(f"[RabbitMQ Producer] Sent {sent_messages} messages in {prod_duration:.2f} seconds.")
    return sent_messages

# -----------------------------
# Consumer for RabbitMQ
# -----------------------------
def rabbitmq_consumer(host, queue_name, max_messages, results):
    #time.sleep(start_delay)
    credentials = pika.PlainCredentials("testuser", "testpassword")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)

    received_messages = 0
    #total_latency = 0
    #min_latency = float('inf')
    #max_latency = 0
    start_time = time.time()

    def callback(ch, method, properties, body):
        nonlocal received_messages
        if received_messages >= max_messages:
            return

        message = json.loads(body)
        sent_timestamp = message.get("timestamp", None)

        with metrics_lock:
            metrics["received"] += 1
            if sent_timestamp:
                latency = time.time() - sent_timestamp
                metrics["latencies"].append(latency)
                #total_latency += latency
                #min_latency = min(min_latency, latency)
                #max_latency = max(max_latency, latency)
        received_messages += 1
        #time.sleep(consumer_delay)

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    #while time.time() - start_time < test_duration and received_messages < max_messages:
    while received_messages < max_messages:
        connection.process_data_events(time_limit=1)

    connection.close()

    #avg_latency = total_latency / received_messages if received_messages > 0 else 0
    results.update({
        "received": received_messages,
        #"avg_latency": avg_latency,
        #"min_latency": 0 if min_latency == float('inf') else min_latency,
        #"max_latency": max_latency
    })

    cons_duration = time.time() - start_time
    print(f"[RabbitMQ Consumer] Received {received_messages} messages in {cons_duration:.2f} seconds.")

# -----------------------------
# Producer for SQS
# -----------------------------
def sqs_producer(queue_url, message_size, max_messages, batch_size, results):
    sqs = boto3.client('sqs', region_name='sa-east-1')
    message = {"payload": "X" * message_size, "timestamp": None}

    sent_messages = 0
    start_time = time.time()

    # lista vazia
    batch = []
    i = 0

    #while time.time() - start_time < test_duration and sent_messages < max_messages:
    while sent_messages < max_messages:
        message["timestamp"] = time.time()

        batch.append({
            "Id": str(i % batch_size),  # Id único dentro do batch (0 a 9)
            "MessageBody": json.dumps(message)
        })

        # sempre que atingir o batch_size, envia o batch
        if len(batch) == batch_size:
            sqs.send_message_batch(QueueUrl=queue_url, Entries=batch)
            batch = []

        sent_messages += 1
        i += 1
        #time.sleep(1 / producer_rate)

    # se sobrar mensagens < 10, envia também
    if batch:
        sqs.send_message_batch(QueueUrl=queue_url, Entries=batch)
    
    results.update({
        "sent": sent_messages
    })

    prod_duration = time.time() - start_time
    print(f"[SQS Producer] Sent {sent_messages} messages in {prod_duration:.2f} seconds.")
    return sent_messages

# -----------------------------
# Consumer for SQS
# -----------------------------
def sqs_consumer(queue_url, max_messages, batch_size, results):
    #time.sleep(start_delay)
    sqs = boto3.client('sqs', region_name='sa-east-1')

    received_messages = 0
    #total_latency = 0
    #min_latency = float('inf')
    #max_latency = 0
    start_time = time.time()

    #while time.time() - start_time < test_duration and received_messages < max_messages:
    while received_messages < max_messages:
        response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=batch_size, WaitTimeSeconds=20)
        messages = response.get('Messages', [])

        for msg in messages:
            if received_messages >= max_messages:
                break

            with metrics_lock:
                metrics["received"] += 1
                body = json.loads(msg["Body"])
                sent_timestamp = body.get("timestamp", None)
                if sent_timestamp:
                    latency = time.time() - sent_timestamp
                    metrics["latencies"].append(latency)
                    #total_latency += latency
                    #min_latency = min(min_latency, latency)
                    #max_latency = max(max_latency, latency)
                received_messages += 1
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg["ReceiptHandle"])

    cons_duration = time.time() - start_time
    print(f"[SQS Consumer] Received {received_messages} messages in {cons_duration:.2f} seconds.")

# -----------------------------
# Resource Monitoring
# -----------------------------
def monitor_resources(interval=60):
    while True:
        cpu = psutil.cpu_percent(interval=interval)
        mem = psutil.virtual_memory()
        print(f"[Monitor] CPU: {cpu}%, Memory: {mem.percent}%")

# -----------------------------
# Main Test Runner
# -----------------------------
def run_test(args):
    results = {}
    start_time = time.time()

    monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
    monitor_thread.start()

    if args.broker == "rabbitmq":
        producer_thread = threading.Thread(target=rabbitmq_producer, args=(args.host, args.queue_name, args.message_size, args.max_messages, results))
        consumer_thread = threading.Thread(target=rabbitmq_consumer, args=(args.host, args.queue_name, args.max_messages, results))
    elif args.broker == "sqs":
        producer_thread = threading.Thread(target=sqs_producer, args=(args.queue_url, args.message_size, args.max_messages, args.batch_size, results))
        consumer_thread = threading.Thread(target=sqs_consumer, args=(args.queue_url, args.max_messages, args.batch_size, results))
    else:
        print("[Error] Broker not supported.")
        sys.exit(1)

    producer_thread.start()
    producer_thread.join()

    consumer_thread.start()
    consumer_thread.join()

    # Metrics
    
    test_duration = time.time() - start_time
    messages_produced = results.get('sent', 0)
    messages_consumed = metrics["received"]


    with metrics_lock:
        count = metrics["received"]
        lat_list = metrics["latencies"][:]
        
    if count:
        avg_latency = sum(lat_list)/len(lat_list)
        min_latency = min(lat_list)
        max_latency = max(lat_list)
        lat_list.sort()
        def percentile(arr, p):
            if not arr: return 0
            k = int(round((len(arr)-1) * p/100.0))
            return arr[k]
        p50 = percentile(lat_list, 50)
        p95 = percentile(lat_list, 95)
        p99 = percentile(lat_list, 99)
    else:
        avg_latency = min_latency = max_latency =p50 = p95 = p99 = 0

    print("\n===== Test Results =====")
    print(f"Test Duration: {test_duration:.2f} seconds")
    print(f"Messages Produced: {messages_produced}")
    #print(f"Messages Consumed: {results.get('received', 0)}")
    #print(f"Average Latency: {results.get('avg_latency', 0):.6f} s")
    #print(f"Min Latency: {results.get('min_latency', 0):.6f} s")
    #print(f"Max Latency: {results.get('max_latency', 0):.6f} s")
    print(f"Messages Consumed: {messages_consumed}")
    print(f"Average Latency: {avg_latency:.6f} s")
    print(f"Min Latency: {min_latency:.6f} s")
    print(f"Max Latency: {max_latency:.6f} s")
    print(f"p50: {p50:.6f} s")
    print(f"p95: {p95:.6f} s")
    print(f"p99: {p99:.6f} s")
    print("========================")

    # -----------------------------
    # Results Record
    # -----------------------------

    # Parâmetros do teste
    test_metadata = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "queue_type": args.broker,
        "host": args.host,
        "queue_url": args.queue_url,
        "queue_name": args.queue_name,
        "max_messages": args.max_messages,
        "message_size": args.message_size,
        "batch_size": args.batch_size
    }

    # Métricas coletadas
    test_results = {
        "test_duration": test_duration,
        "production_duration": prod_duration,
        "consumption_duration": cons_duration,
        "messages_produced": messages_produced,
        "messages_consumed": messages_consumed,
        "avg_latency": avg_latency,
        "min_latency": min_latency,
        "max_latency": max_latency,
        "p50": p50,
        "p95": p95,
        "p99": p99,
    }

    # Dicionário único
    record = {**test_metadata, **test_results}

    # Nome fixo do arquivo (para acumular resultados)
    csv_filename = "benchmark_results_1.csv"

    # Cabeçalhos (automático)
    fields = list(record.keys())

    # Cria arquivo se não existir e adiciona resultados
    file_exists = os.path.isfile(csv_filename)

    with open(csv_filename, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)

    print(f"\n Resultados adicionados em: {csv_filename}")


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark for RabbitMQ and SQS")
    parser.add_argument("--broker", choices=["rabbitmq", "sqs"], required=True, help="Broker type")
    parser.add_argument("--host", type=str, default="localhost", help="RabbitMQ host")
    parser.add_argument("--queue_url", type=str, help="SQS queue URL")
    parser.add_argument("--queue_name", type=str, default="benchmark_queue")
    #parser.add_argument("--producer_rate", type=int, default=100, help="Messages per second")
    #parser.add_argument("--consumer_delay", type=float, default=0.0, help="Delay per consumed message (s)")
    #parser.add_argument("--start_delay", type=int, default=0, help="Delay before consumer starts (s)")
    #parser.add_argument("--test_duration", type=int, default=60, help="Test duration (s)")
    parser.add_argument("--max_messages", type=int, default=1000, help="Maximum messages to send/consume")
    parser.add_argument("--message_size", type=int, default=1024, help="Message payload size in bytes")
    parser.add_argument("--batch_size", type=int, default=1, help="Batch size (number of messages) for production and consumption")

    args = parser.parse_args()
    run_test(args)
