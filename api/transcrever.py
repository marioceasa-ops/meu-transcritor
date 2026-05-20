from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import threading
import uuid

# Armazenamento em memória (em produção real, use um banco ou Redis)
jobs = {}
arquivos_temporarios = {}

def processar_transcricao(job_id, full_audio):
    try:
        openai_key = os.environ.get("OPENAI_API_KEY")
        files = {'file': ('audio.m4a', full_audio, 'audio/m4a')}
        data = {'model': 'whisper-1', 'language': 'pt'}
        resposta = requests.post("https://api.openai.com/v1/audio/transcriptions", 
                                 headers={"Authorization": f"Bearer {openai_key}"}, 
                                 files=files, data=data, timeout=300)
        
        if resposta.status_code == 200:
            jobs[job_id] = {"status": "concluido", "texto": resposta.json().get("text", "")}
        else:
            jobs[job_id] = {"status": "erro", "erro": resposta.text}
    except Exception as e:
        jobs[job_id] = {"status": "erro", "erro": str(e)}

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def enviar_resposta(self, status, data):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        if self.path.startswith('/status/'):
            job_id = self.path.split('/')[-1]
            self.enviar_resposta(200, jobs.get(job_id, {"status": "nao_encontrado"}))

    def do_POST(self):
        if self.path == '/api/transcrever-final':
            chunk_index = int(self.headers.get('x-chunk-index', 0))
            total_chunks = int(self.headers.get('x-total-chunks', 1))
            session_id = self.headers.get('x-session-id', str(uuid.uuid4()))

            if session_id not in arquivos_temporarios:
                arquivos_temporarios[session_id] = [None] * total_chunks
            
            arquivos_temporarios[session_id][chunk_index] = self.rfile.read(int(self.headers.get('Content-Length', 0)))

            if None not in arquivos_temporarios[session_id]:
                full_audio = b"".join(arquivos_temporarios[session_id])
                del arquivos_temporarios[session_id]
                jobs[session_id] = {"status": "processando"}
                threading.Thread(target=processar_transcricao, args=(session_id, full_audio)).start()
                self.enviar_resposta(202, {"status": "processando", "job_id": session_id})
            else:
                self.enviar_resposta(200, {"status": "recebido_parte"})

if __name__ == '__main__':
    from http.server import HTTPServer
    port = int(os.environ.get('PORT', 10000))
    HTTPServer(('0.0.0.0', port), handler).serve_forever()