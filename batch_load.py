import json
import subprocess
import time

# Adicionando a 'dados_var' o conjunto de dados gerado por data_autogen.py
with open('/home/lucas/interscity/dados_var_trafego_onibus_sp.json') as f:
	dados_var = json.load(f)

# Verificar se é uma lista; se não for, transformar em uma lista
if not isinstance(dados_var, list):
    # Tente extrair a lista de dentro do dicionário, se possível
    if isinstance(dados_var, dict) and 'capabilities' in dados_var:
        dados_var = dados_var['capabilities']
    else:
        # Caso não seja lista, transforme o dicionário ou item único em uma lista
        dados_var = [dados_var]

batch_size = 20  # Tamanho do lote
url = "http://10.10.10.104:8000/adaptor/resources/temperature/data"  # URL de destino para o POST

# Iniciar a medição do tempo total
tempo_inicial_total = time.time()

# Loop para dividir os dados em lotes e enviá-los
for i in range(0, len(dados_var), batch_size):
    # Definindo o lote atual
    lote = dados_var[i:i + batch_size]
    
    # Convertendo o lote para JSON
    lote_json = json.dumps(lote)

	# Iniciar a medição do tempo para o envio do lote
    tempo_inicial_lote = time.time()
    
    # Executando o comando curl com o subprocess
    result = subprocess.run([
        'curl', '-X', 'POST',
        '-H', 'Content-Type: application/json',
        '-d', lote_json,
        url
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

	# Medir o tempo de execução do lote
    tempo_execucao_lote = time.time() - tempo_inicial_lote

    # Exibindo o resultado da execução do curl
    print("Lote {} enviado em {:.2f} segundos".format(i // batch_size + 1, tempo_execucao_lote))
    print(result.stdout)
    print(result.stderr)

# Medir o tempo total de execução
tempo_total_execucao = time.time() - tempo_inicial_total

# Exibindo o tempo total de execução
print("Tempo total de execução: {:.2f} segundos".format(tempo_total_execucao))


