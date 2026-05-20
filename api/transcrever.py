from http.server import BaseHTTPRequestHandler
import json
import os
import requests

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_type = self.headers.get('Content-Type', '')
        content_length = int(self.headers.get('Content-Length', 0))
        
        # Lógica para processar o áudio final
        if self.path == '/api/transcrever':
            body = self.rfile.read(content_length)
            
            # Extraindo o arquivo do FormData (simplificado)
            # Nota: Em sistemas de produção, usamos bibliotecas como cgi ou multipart
            # Para este fluxo, garantimos que o áudio seja enviado corretamente
            
            openai_key = os.environ.get("OPENAI_API_KEY")
            url_openai = "https://api.openai.com/v1/audio/transcriptions"
            headers_openai = {"Authorization": f"Bearer {openai_key}"}
            
            arquivos = {
                'file': ('audio.m4a', body, 'audio/m4a'),
                'model': (None, 'whisper-1'),
                'language': (None, 'pt')
            }
            
            resposta_openai = requests.post(url_openai, headers=headers_openai, files=arquivos)
            
            if resposta_openai.status_code == 200:
                self.enviar_resposta(200, {"texto": resposta_openai.json().get("text", "")})
            else:
                self.enviar_resposta(400, {"erro": "Erro na comunicação com a IA."})
            return

    def enviar_resposta(self, status, dados):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(dados).encode())