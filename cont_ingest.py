import json
import time
import requests

# Dados a serem enviados (vários registros)
dados_varios = [
    {"capabilities": {"id": 1, "nome": "Teste 1"}},
    {"capabilities": {"id": 2, "nome": "Teste 2"}},
    {"capabilities": {"id": 3, "nome": "Teste 3"}},
    # ...mais dados...
]

url = "http://10.10.10.104:8000/catalog/capabilities"  # URL de destino

# Medir o tempo total
tempo_inicial_total = time.time()

# Enviar cada registro individualmente
for i, dado in enumerate(dados_varios):
    tempo_inicial = time.time()
    
    # Enviar a requisição POST para cada dado individual
    response = requests.post(url, json=dado, headers={'Content-Type': 'application/json'})
    
    # Medir o tempo de execução da requisição
    tempo_execucao = time.time() - tempo_inicial
    
    # Verificar o resultado
    if response.status_code == 200:
        print(f"Dado {i + 1} enviado com sucesso em {tempo_execucao:.2f} segundos")
    else:
        print(f"Erro ao enviar dado {i + 1}: {response.text}")

# Medir o tempo total de execução
tempo_total_execucao = time.time() - tempo_inicial_total
print(f"Tempo total de execução: {tempo_total_execucao:.2f} segundos")

