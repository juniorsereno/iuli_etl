import os
from playwright.sync_api import sync_playwright
import psycopg2
from dotenv import load_dotenv, dotenv_values
from datetime import datetime
import re

# Carrega variáveis de ambiente
load_dotenv("login.env")
config = dotenv_values("login.env")

# Configurações do Supabase
DB_CONFIG = {
    'host': 'aws-0-sa-east-1.pooler.supabase.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres.iblnvknimlvbkkjgdmto',
    'password': os.getenv('SUPABASE_PASSWORD')
}

# Configurações do site
LOGIN_URL = "https://app.iuli.com.br/sales-dashboard"
USERNAME = os.getenv('IULI_USER')
PASSWORD = os.getenv('IULI_PASSWORD')

def convert_bruto_para_numero(texto):
    """Converte texto bruto (ex: 'R$ 2.836,68') para float"""
    try:
        # Remove tudo exceto números e vírgula
        numero = re.sub(r'[^\d,]', '', texto.replace('.', ''))
        # Substitui vírgula por ponto e converte para float
        return float(numero.replace(',', '.'))
    except:
        return None

def create_table_if_not_exists():
    """Cria ou altera a tabela para armazenar dados como números"""
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Verifica se a tabela existe
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'UNIFYTB502_IULI'
        )
        """)
        
        if not cursor.fetchone()[0]:
            # Cria nova tabela com campos numéricos
            cursor.execute("""
            CREATE TABLE public."UNIFYTB502_IULI" (
                id SERIAL PRIMARY KEY,
                dia DATE NOT NULL,
                cac NUMERIC(15, 2),
                ltv NUMERIC(15, 2),
                ebitda NUMERIC(15, 2),
                faturamento NUMERIC(15, 2),
                tipo VARCHAR(10) NOT NULL,
                data_importacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()
            print("Tabela criada com campos numéricos.")
        else:
            # Verifica se precisa alterar a estrutura
            cursor.execute("""
            SELECT data_type FROM information_schema.columns 
            WHERE table_name = 'UNIFYTB502_IULI' AND column_name = 'cac'
            """)
            current_type = cursor.fetchone()[0]
            
            if current_type != 'numeric':
                print("Convertendo tabela para armazenar dados numéricos...")
                cursor.execute("""
                ALTER TABLE public."UNIFYTB502_IULI" 
                ALTER COLUMN cac TYPE NUMERIC(15, 2),
                ALTER COLUMN ltv TYPE NUMERIC(15, 2),
                ALTER COLUMN ebitda TYPE NUMERIC(15, 2),
                ALTER COLUMN faturamento TYPE NUMERIC(15, 2)
                """)
                conn.commit()
                print("Tabela alterada com sucesso.")
    except Exception as e:
        print(f"Erro ao configurar tabela: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def extract_raw_data(page, xpath):
    """Extrai o conteúdo bruto do elemento"""
    try:
        element = page.query_selector(f'xpath={xpath}')
        return element.inner_text() if element else "N/A"
    except Exception as e:
        print(f"Erro ao extrair dado bruto: {e}")
        return "Erro"

def scrape_iuli_metrics():
    """Raspa as métricas e converte para números"""
    try:
        with sync_playwright() as p:
            # Configuração do navegador
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            # Navegação para login
            page.goto("https://app.iuli.com.br/")
            page.wait_for_timeout(3000)
            
            # Preenche formulário de login
            USERNAME_XPATH = '//*[@id="root"]/div[2]/div/div/div/div/main/div/div/div[2]/div/form/div[1]/div[1]/input'
            PASSWORD_XPATH = '//*[@id="root"]/div[2]/div/div/div/div/main/div/div/div[2]/div/form/div[2]/div[1]/input'
            LOGIN_BUTTON_XPATH = '//*[@id="root"]/div[2]/div/div/div/div/main/div/div/div[2]/div/form/div[5]/div[2]/button'
            
            page.fill(f'xpath={USERNAME_XPATH}', USERNAME)
            page.fill(f'xpath={PASSWORD_XPATH}', PASSWORD)
            page.click(f'xpath={LOGIN_BUTTON_XPATH}')
            
            # Aguarda login e navega para dashboard
            page.wait_for_timeout(5000)
            page.goto("https://app.iuli.com.br/sales-dashboard")
            page.wait_for_timeout(25000)
            
            # Verifica se dashboard carregou
            DASHBOARD_XPATH = '//*[@id="root"]/div[2]/div[3]/div[3]/div/div[2]/div[2]/div[1]'
            page.wait_for_selector(f'xpath={DASHBOARD_XPATH}', timeout=30000)
            
            # Extrai dados brutos
            data_atual = datetime.now().strftime('%d/%m/%Y')
            
            # Métricas do MÊS (texto bruto)
            cac_mes = extract_raw_data(page, '//*[@id="root"]/div[2]/div[3]/div[3]/div/div[2]/div[2]/div[1]/div/div/div[2]/h6[1]')
            ltv_mes = extract_raw_data(page, '//*[@id="root"]/div[2]/div[3]/div[3]/div/div[2]/div[2]/div[2]/div/div/div[2]/h6[1]')
            ebitda_mes = extract_raw_data(page, '//*[@id="root"]/div[2]/div[3]/div[3]/div/div[2]/div[2]/div[4]/div/div/div[2]/h6[1]')
            faturamento_mes = extract_raw_data(page, '//*[@id="root"]/div[2]/div[3]/div[3]/div/div[2]/div[2]/div[5]/div/div/div[2]/h3[2]')
            
            # Métricas do ANO (texto bruto)
            cac_ano = extract_raw_data(page, '//*[@id="root"]/div[2]/div[3]/div[3]/div/div[2]/div[2]/div[1]/div/div/div[2]/h6[3]')
            ltv_ano = extract_raw_data(page, '//*[@id="root"]/div[2]/div[3]/div[3]/div/div[2]/div[2]/div[2]/div/div/div[2]/h6[3]')
            ebitda_ano = extract_raw_data(page, '//*[@id="root"]/div[2]/div[3]/div[3]/div/div[2]/div[2]/div[4]/div/div/div[2]/h6[2]')
            
            context.close()
            browser.close()
            
            # Converte para números
            faturamento_ano_valor = 11876792.64  # Valor fixo para faturamento anual
            
            return [
                {
                    'dia': data_atual,
                    'cac': convert_bruto_para_numero(cac_mes.split(':')[-1].strip()),
                    'ltv': convert_bruto_para_numero(ltv_mes.split(':')[-1].strip()),
                    'ebitda': convert_bruto_para_numero(ebitda_mes.split(':')[-1].strip()),
                    'faturamento': convert_bruto_para_numero(faturamento_mes),
                    'tipo': 'mês'
                },
                {
                    'dia': data_atual,
                    'cac': convert_bruto_para_numero(cac_ano.split(':')[-1].strip()),
                    'ltv': convert_bruto_para_numero(ltv_ano.split(':')[-1].strip()),
                    'ebitda': convert_bruto_para_numero(ebitda_ano.split(':')[-1].strip()),
                    'faturamento': faturamento_ano_valor,
                    'tipo': 'ano'
                }
            ]
            
    except Exception as e:
        print(f"Erro durante o scraping: {e}")
        return None

def save_to_database(data):
    """Salva os dados convertidos no banco"""
    if not data:
        return False
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        for item in data:
            cursor.execute("""
            INSERT INTO public."UNIFYTB502_IULI"
            (dia, cac, ltv, ebitda, faturamento, tipo)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                datetime.strptime(item['dia'], '%d/%m/%Y').date(),
                item['cac'],
                item['ltv'],
                item['ebitda'],
                item['faturamento'],
                item['tipo']
            ))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao salvar no banco: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    create_table_if_not_exists()
    dados = scrape_iuli_metrics()
    
    if dados and save_to_database(dados):
        print("Dados convertidos e salvos com sucesso!")
        print("Exemplo de dados salvos:", dados[0])  # Mostra um exemplo
    else:
        print("Falha ao coletar ou salvar os dados.")