import json
import subprocess
import time
from faker import Faker
import random

# Instância do Faker para gerar dados
fake = Faker()

# Lista de capabilities e resources
capabilities = ["temperatura", "pressao", "umidade"]
resources_por_capability = 3  # Número de resources por capability (ex.: termômetro1, termômetro2)
dados_por_resource = 5  # Número de dados de sensores por resource


# Função para gerar dados para cada capability e seus resources
def gerar_dados_sensores():
    dados = []
    for capability in capabilities:
        resources = []
        for resource_id in range(1, resources_por_capability + 1):
            resource_name = "{}_resource{}".format(capability, resource_id)
            # Gerar dados de sensores para o resource
            sensor_data = []
            for _ in range(dados_por_resource):
                if capability == "temperatura":
                    value = random.randint(-10, 40)  # Temperatura em graus Celsius
                elif capability == "pressao":
                    value = random.uniform(950, 1050)  # Pressão em hPa
                elif capability == "umidade":
                    value = random.uniform(0, 100)  # Umidade relativa em %
                else:
                    value = None
                
                sensor_data.append({
                    "value": value,
                    "timestamp": fake.iso8601()  # Timestamp em formato ISO 8601
                })

            resources.append({
                "resource_name": resource_name,
                "data": sensor_data
            })

        dados.append({
            "capability": capability,
            "resources": resources
        })
    return dados


# Gerar os dados de sensores
dados_sensores = gerar_dados_sensores()

# URL para envio
url_base = "http://10.10.10.104:8000/adaptor/resources"

# Iniciar a medição do tempo total
tempo_inicial_total = time.time()

# Enviar os dados por capability e resource
for capability_data in dados_sensores:
    capability = capability_data["capability"]
    for resource in capability_data["resources"]:
        resource_name = resource["resource_name"]
        payload = {
            "resource_name": resource_name,
            "data": resource["data"]
        }
        
        # Convertendo o payload para JSON
        payload_json = json.dumps(payload)
        
        # Enviar para o endpoint correspondente
        endpoint = f"{url_base}/{capability}/data"
        tempo_inicial = time.time()
        result = subprocess.run([
            'curl', '-X', 'POST',
            '-H', 'Content-Type: application/json',
            '-d', payload_json,
            endpoint
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        # Medir o tempo de execução do envio
        tempo_execucao = time.time() - tempo_inicial
        
        # Verificar o resultado
        if result.returncode == 0:
            print("Resource {} enviado para capability '{}' em {:.2f} segundos".format(
                resource_name, capability, tempo_execucao))
        else:
            print("Erro ao enviar resource {}: {}".format(resource_name, result.stderr))

# Medir o tempo total de execução
tempo_total_execucao = time.time() - tempo_inicial_total
print("Tempo total de execução: {:.2f} segundos".format(tempo_total_execucao))
