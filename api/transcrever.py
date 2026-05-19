from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import uuid

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. ROTA PARA CRIAR O PIX DE R$ 15,00
        if self.path == '/api/criar-pix':
            content_length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            email_cliente = body.get('email', 'cliente@email.com')
            
            mp_token = os.environ.get("MERCADO_PAGO_TOKEN")
            if not mp_token:
                self.enviar_resposta(500, {"erro": "Token do Mercado Pago não configurado na Vercel."})
                return

            url_mp = "https://api.mercadopago.com/v1/payments"
            headers_mp = {
                "Authorization": f"Bearer {mp_token}",
                "X-Idempotency-Key": str(uuid.uuid4()),
                "Content-Type": "application/json"
            }
            
            payload_mp = {
                "transaction_amount": 15.00,
                "description": "Transcrição de Áudio Automatizada",
                "payment_method_id": "pix",
                "payer": {
                    "email": email_cliente
                }
            }

            try:
                response = requests.post(url_mp, json=payload_mp, headers=headers_mp)
                dados_pagamento = response.json()

                if response.status_code == 201:
                    resposta = {
                        "id_pagamento": dados_pagamento["id"],
                        "status": dados_pagamento["status"],
                        "qr_code": dados_pagamento["point_of_interaction"]["transaction_data"]["qr_code"],
                        "qr_code_base64": dados_pagamento["point_of_interaction"]["transaction_data"]["qr_code_base64"]
                    }
                    self.enviar_resposta(200, resposta)
                else:
                    self.enviar_resposta(400, {"erro": "Falha ao gerar o Pix no Mercado Pago."})
            except Exception as e:
                self.enviar_resposta(500, {"erro": str(e)})

        # 2. ROTA PARA VERIFICAR SE O PIX FOI PAGO
        elif self.path == '/api/checar-pix':
            content_length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            id_pagamento = body.get('id_pagamento')

            mp_token = os.environ.get("MERCADO_PAGO_TOKEN")
            url_mp = f"https://api.mercadopago.com/v1/payments/{id_pagamento}"
            headers_mp = {"Authorization": f"Bearer {mp_token}"}

            try:
                response = requests.get(url_mp, headers=headers_mp)
                dados_pagamento = response.json()

                if response.status_code == 200:
                    self.enviar_resposta(200, {"status": dados_pagamento["status"]})
                else:
                    self.enviar_resposta(400, {"erro": "Erro ao checar status do pagamento."})
            except Exception as e:
                self.enviar_resposta(500, {"erro": str(e)})

        # 3. ROTA FINAL DA TRANSCRIÇÃO (PROCESSA O AUDIO/VÍDEO REAL)
        elif self.path == '/api/transcrever-final':
            openai_key = os.environ.get("OPENAI_API_KEY")
            if not openai_key:
                self.enviar_resposta(500, {"erro": "Chave OpenAI ausente nas variáveis de ambiente."})
                return

            try:
                # Lendo o corpo do multipart (arquivo enviado)
                content_length = int(self.headers['Content-Length'])
                body_bytes = self.rfile.read(content_length)

                # Para enviar para a OpenAI mantendo a estrutura simples do handler nativo, 
                # repassamos o conteúdo diretamente via requisição multipart para a API do Whisper
                url_openai = "https://api.openai.com/v1/audio/transcriptions"
                headers_openai = {"Authorization": f"Bearer {openai_key}"}
                
                # Enviando via requests simulando o form-data de arquivos
                files = {
                    'file': ('audio.m4a', body_bytes, 'application/octet-stream')
                }
                data = {
                    'model': 'whisper-1',
                    'language': 'pt'
                }

                resposta_openai = requests.post(url_openai, headers=headers_openai, files=files, data=data)
                
                if respuesta_openai.status_code == 200:
                    resultado_txt = respuesta_openai.json().get("text", "")
                    self.enviar_resposta(200, {"texto": resultado_txt})
                else:
                    erro_detalhe = respuesta_openai.json().get("error", {}).get("message", "Erro na OpenAI.")
                    self.enviar_resposta(400, {"erro": f"Falha na OpenAI: {erro_detalhe}"})

            except Exception as e:
                self.enviar_resposta(500, {"erro": f"Erro interno no processamento: {str(e)}"})
        
        else:
            self.enviar_resposta(404, {"erro": "Rota não encontrada."})

    def enviar_resposta(self, status, dados):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(dados).encode('utf-8')))