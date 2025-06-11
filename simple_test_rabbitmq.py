import pika

def publish_message():
    # Configurações de conexão com RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # Declaração de uma fila (garante que ela exista)
    queue_name = 'test_queue'
    channel.queue_declare(queue=queue_name)

    # Mensagem para enviar
    message = "Hello RabbitMQ!"
    channel.basic_publish(exchange='', routing_key=queue_name, body=message)

    print(f"Mensagem enviada: {message}")

    # Fecha a conexão
    connection.close()

def consume_message():
    # Configurações de conexão com RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # Declaração da fila (garante que ela exista)
    queue_name = 'test_queue'
    channel.queue_declare(queue=queue_name)

    # Callback para processar mensagens
    def callback(ch, method, properties, body):
        print(f"Mensagem recebida: {body.decode()}")

    # Consumidor da fila
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    print("Aguardando mensagens. Pressione CTRL+C para sair.")
    channel.start_consuming()

# Testa publicação e consumo
if __name__ == '__main__':
    print("Enviando mensagem para RabbitMQ...")
    publish_message()

    print("Consumindo mensagens do RabbitMQ...")
    consume_message()
