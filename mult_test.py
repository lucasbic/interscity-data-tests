import threading
import pika
import time

# Contadores de métricas
sent_messages = 0
received_messages = 0

def publish_message(queue_name, message, interval):
    global sent_messages
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)

    while True:
        channel.basic_publish(exchange='', routing_key=queue_name, body=message)
        sent_messages += 1
        time.sleep(interval)

def consume_message(queue_name):
    global received_messages
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)

    def callback(ch, method, properties, body):
        global received_messages
        received_messages += 1

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

def monitor_metrics(start_time):
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > 0:
            print(f"\nMétricas:")
            print(f"Mensagens enviadas: {sent_messages}")
            print(f"Mensagens recebidas: {received_messages}")
            print(f"Taxa de envio: {sent_messages / elapsed_time:.2f} mensagens/segundo")
            print(f"Taxa de consumo: {received_messages / elapsed_time:.2f} mensagens/segundo")
        time.sleep(5)

if __name__ == '__main__':
    queue_name = 'test_queue'
    message = "Mensagem de teste"
    interval = 1  # Configuração inicial: envia uma mensagem por segundo

    start_time = time.time()

    # Thread para monitorar métricas
    monitor_thread = threading.Thread(target=monitor_metrics, args=(start_time,))
    monitor_thread.start()

    # Threads de produtor e consumidor
    producer_thread = threading.Thread(target=publish_message, args=(queue_name, message, interval))
    consumer_thread = threading.Thread(target=consume_message, args=(queue_name,))

    producer_thread.start()
    consumer_thread.start()

    producer_thread.join()
    consumer_thread.join()
