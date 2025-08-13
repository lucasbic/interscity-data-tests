import boto3
import json
import subprocess

# Configurar o cliente SQS
sqs = boto3.client('sqs', region_name='sa-east-1',

aws_access_key_id = 'xxx',

aws_secret_access_key = 'yyy'
)

# Enviar mensagem para a fila
def send_message(queue_url, message_body):
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_body)
    )
    return response

# Receber mensagens da fila
def receive_messages(queue_url):
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=10
    )
    messages = response.get('Messages', [])
    return messages

# Processar e enviar para o endpoint
def process_and_forward(messages, endpoint_url):
    for message in messages:
        body = json.loads(message['Body'])
        mensagem = json.dumps(body)
        print("{}".format(mensagem))
        # Executando o comando curl com o subprocess para enviar o dado
        result = subprocess.run([
            'curl', '-X', 'POST',
            '-H', 'Content-Type: application/json',
            '-d', mensagem,
            endpoint_url
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        print("Enviando mensagem para {}: {}".format(endpoint_url, mensagem))
        
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message['ReceiptHandle']
        )

# Inputs
queue_url = 'queue_url'
message_body = {"data":{"environment_monitoring":[{"temperature":25,"timestamp":"27/01/2025T23:14:07"}]}}

# Functions Calls
send_message(queue_url, message_body)
messages = receive_messages(queue_url)
#print("{}".format(messages))
process_and_forward(messages, 'http://10.10.10.104:8000/adaptor/resources/01c0c304-5068-43b6-9c40-172526a83f31/data')
