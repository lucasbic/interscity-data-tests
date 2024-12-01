import json
import copy

# Carregar dados originais
with open('/home/lucas/interscity/trafego_onibus_sp.json') as f:
    dados = json.load(f)

novos_dados = []
for entrada in dados['capabilities']:
    for i in range(5):  # Duplica 5 vezes com pequenas variações
        nova_entrada = copy.deepcopy(entrada)
        nova_entrada['data'] = "2024-06-" + str(20 + i)  # Altera data
        nova_entrada['horario'] = str(8 + i) + ":00"  # Altera horário
        # Modificar valores das linhas
        for linha in nova_entrada['linhas']:
            linha['veiculos_em_operacao'] += i  # Aumenta o número de veículos em operação
            if linha['incidentes']:
                for incidente in linha['incidentes']:
                    incidente['tempo_atraso_minutos'] += i * 5  # Modifica o tempo de atraso
        novos_dados.append(nova_entrada)

# Salvar novos dados em arquivo
with open('/home/lucas/interscity/novos_dados_trafego_onibus_sp.json', 'w') as f:
    json.dump({"capabilities": novos_dados}, f, indent=4)

