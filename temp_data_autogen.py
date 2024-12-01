import json
import subprocess
import time
from faker import Faker
import random

# Instância do Faker para gerar dados
fake = Faker()

# Função para gerar dados de temperatura e posição
def gerar_dados_temperatura_posicao():
    return {
        "data": {
            "temperature": [
                {
                    "value": random.randint(-10, 40),  # Gera uma temperatura aleatória entre -10 e 40
                    "timestamp": fake.iso8601()  # Gera timestamp ISO 8601 aleatório
                },
                {
                    "value": random.randint(-10, 40),  # Gera outra temperatura aleatória
                    "timestamp": fake.iso8601()  # Outro timestamp
                }
            ],
            "position": [
                {
                    "value": {
                        "lat": float(fake.latitude()),  # Converte latitude para float
                        "lon": float(fake.longitude())  # Converte longitude para float
                    },
                    "timestamp": fake.iso8601()  # Gera timestamp ISO 8601 aleatório
                }
            ]
        }
    }

# Lista de dados gerados
dados_varios = [gerar_dados_temperatura_posicao() for _ in range(10)]  # Gerar 10 conjuntos de dados

# Endpoint
url = "http://10.10.10.104:8000/adaptor/resources/01c0c304-5068-43b6-9c40-172526a83f31/data"

# Iniciar a medição do tempo total
tempo_inicial_total = time.time()

# Enviar cada registro individualmente
for i, dado in enumerate(dados_varios):
    tempo_inicial = time.time()

    # Convertendo o dado para JSON
    dado_json = json.dumps(dado)
    
    # Executando o comando curl com o subprocess para enviar o dado
    result = subprocess.run([
        'curl', '-X', 'POST',
        '-H', 'Content-Type: application/json',
        '-d', dado_json,
        url
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    # Medir o tempo de execução do envio
    tempo_execucao = time.time() - tempo_inicial

    # Verificar o resultado
    if result.returncode == 0:
        print("Dado {} enviado com sucesso em {:.2f} segundos".format(i + 1, tempo_execucao))
    else:
        print("Erro ao enviar dado {}: {}".format(i + 1, result.stderr))

# Medir o tempo total de execução
tempo_total_execucao = time.time() - tempo_inicial_total
print("Tempo total de execução: {:.2f} segundos".format(tempo_total_execucao))

