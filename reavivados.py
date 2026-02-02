import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import re
import os

EMAIL_REMETENTE = os.environ.get('EMAIL_REMETENTE')
EMAIL_SENHA = os.environ.get('EMAIL_SENHA')
EMAIL_DESTINATARIO = os.environ.get('EMAIL_DESTINATARIO')

class ReavivadosPorSuaPalavra:
    def __init__(self):
        self.url_base = "https://reavivadosporsuapalavra.org/"
        self.email_remetente = EMAIL_REMETENTE
        self.email_senha = EMAIL_SENHA
        self.email_destinatario = EMAIL_DESTINATARIO
    
    def buscar_capitulo_do_dia(self):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(self.url_base, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            post_url = None
            for link in soup.find_all('a', href=True):
                href = link['href']
                if re.search(r'/\d{4}/\d{2}/\d{2}/', href):
                    post_url = href
                    break
            
            if not post_url:
                print("Nao encontrou link do post")
                return None
            
            print(f"URL do post: {post_url}")
            
            response2 = requests.get(post_url, headers=headers, timeout=30)
            soup2 = BeautifulSoup(response2.content, 'html.parser')
            
            titulo_texto = "Capitulo do Dia"
            url_parts = post_url.rstrip('/').split('/')
            if url_parts:
                ultimo = url_parts[-1]
                titulo_texto = ultimo.replace('-', ' ').title()
                titulo_texto = re.sub(r'\bIi\b', 'II', titulo_texto)
                titulo_texto = re.sub(r'\bIii\b', 'III', titulo_texto)
            
            titulo_tag = soup2.find('h1', class_='entry-title') or soup2.find('h1')
            if titulo_tag:
                titulo_pagina = titulo_tag.get_text(strip=True)
                if titulo_pagina and titulo_pagina != "Reavivados por Sua Palavra":
                    titulo_texto = titulo_pagina
            
            print(f"Titulo: {titulo_texto}")
            
            conteudo_div = (
                soup2.find('div', class_='entry-content') or
                soup2.find('div', class_='post-content') or
                soup2.find('article')
            )
            
            conteudo_html = ""
            conteudo_texto = ""
            
            if conteudo_div:
                for tag in conteudo_div(['script', 'style', 'nav', 'footer']):
                    tag.decompose()
                
                conteudo_html = str(conteudo_div)
                conteudo_texto = conteudo_div.get_text(separator='\n', strip=True)
                linhas = [l.strip() for l in conteudo_texto.split('\n') if l.strip()]
                conteudo_texto = '\n'.join(linhas)
            
            if not conteudo_texto or len(conteudo_texto) < 100:
                conteudo_texto = f"Leia o capitulo completo no site:\n{post_url}"
                conteudo_html = f'<p><a href="{post_url}">{post_url}</a></p>'
            
            return {
                'titulo': titulo_texto,
                'conteudo_html': conteudo_html,
                'conteudo_texto': conteudo_texto,
                'data': datetime.now().strftime('%d/%m/%Y'),
                'url': post_url
            }
            
        except Exception as e:
            print(f"Erro ao acessar o site: {e}")
            return None
    
    def criar_email_html(self, dados):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Georgia, serif; line-height: 1.8; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
                .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .header h1 {{ margin: 0; font-size: 22px; }}
                .capitulo {{ font-size: 28px; margin-top: 15px; font-weight: bold; }}
                .data {{ margin-top: 10px; opacity: 0.9; font-size: 14px; }}
                .content {{ background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .footer {{ text-align: center; margin-top: 30px; padding: 20px; color: #666; font-size: 12px; }}
                a {{ color: #2a5298; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Reavivados por Sua Palavra</h1>
                <div class="capitulo">{dados['titulo']}</div>
                <div class="data">{dados['data']}</div>
            </div>
            <div class="content">
                {dados['conteudo_html']}
            </div>
            <div class="footer">
                <p><a href="{dados['url']}">Leia no site oficial</a></p>
                <p>Que Deus abencoe sua leitura!</p>
            </div>
        </body>
        </html>
        """
        return html
    
    def enviar_email(self, dados):
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Reavivados - {dados['titulo']} ({dados['data']})"
            msg['From'] = self.email_remetente
            msg['To'] = self.email_destinatario
            
            texto = f"""
REAVIVADOS POR SUA PALAVRA
{dados['data']}

{dados['titulo']}

{dados['conteudo_texto']}

Leia no site: {dados['url']}
            """
            
            html = self.criar_email_html(dados)
            
            msg.attach(MIMEText(texto, 'plain', 'utf-8'))
            msg.attach(MIMEText(html, 'html', 'utf-8'))
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email_remetente, self.email_senha)
                server.send_message(msg)
            
            print("Email enviado com sucesso!")
            return True
            
        except Exception as e:
            print(f"Erro ao enviar email: {e}")
            return False
    
    def executar(self):
        print(f"Iniciando em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        dados = self.buscar_capitulo_do_dia()
        
        if dados:
            print(f"Capitulo: {dados['titulo']}")
            self.enviar_email(dados)
        else:
            print("Nao foi possivel obter o capitulo")


if __name__ == "__main__":
    reavivados = ReavivadosPorSuaPalavra()
    reavivados.executar()
