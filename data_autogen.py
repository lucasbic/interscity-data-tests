from faker import Faker
import json
import random

fake = Faker('pt_BR')

dados_var = []
for _ in range(50):  # Gera 50 variações
    nova_entrada = {
        "municipio": "São Paulo",
        "data": fake.date_this_year().isoformat(),
        "horario": str(random.randint(6, 22)) + ":" + random.choice(['00', '15', '30', '45']),
        "linhas": [
            {
                "linha": fake.random_element(elements=('8000-10', '9500-10', '875A-10', '6450-10')),
                "nome": fake.street_name() + " - " + fake.neighborhood(),
                "veiculos_em_operacao": random.randint(5, 15),
                "tempo_medio_espera_minutos": random.randint(5, 20),
                "incidentes": [
                    {
                        "tipo": fake.random_element(elements=('atraso', 'acidente', 'obras')),
                        "descricao": fake.sentence(nb_words=6),
                        "tempo_atraso_minutos": random.randint(5, 30)
                    }
                ] if random.random() > 0.3 else []  # 70% de chance de ter incidentes
            } for _ in range(random.randint(1, 5))  # Gera de 1 a 5 linhas por entrada
        ],
        "total_veiculos_em_operacao": random.randint(30, 50),
        "media_tempo_espera_minutos": random.uniform(7.5, 15.0),
        "capability_type": "sensor"
    }
    dados_var.append(nova_entrada)

# Salvar os dados gerados em um novo arquivo
with open('/home/lucas/interscity/dados_var_trafego_onibus_sp.json', 'w') as f:
    json.dump({"capabilities": dados_var}, f, indent=4)

