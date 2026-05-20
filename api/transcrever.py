from http.server import BaseHTTPRequestHandler
import json
import os
import requests

arquivos_temporarios = {}

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, x-chunk-index, x-total-chunks, x-session-id')
        self.end_headers()

    def enviar_resposta(self, status, data):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        if self.path == '/api/transcrever-final':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body_bytes = self.rfile.read(content_length)
                
                chunk_index = int(self.headers.get('x-chunk-index', 0))
                total_chunks = int(self.headers.get('x-total-chunks', 1))
                session_id = self.headers.get('x-session-id', 'default')

                if session_id not in arquivos_temporarios:
                    arquivos_temporarios[session_id] = [None] * total_chunks
                
                arquivos_temporarios[session_id][chunk_index] = body_bytes

                if None not in arquivos_temporarios[session_id]:
                    full_audio = b"".join(arquivos_temporarios[session_id])
                    del arquivos_temporarios[session_id]

                    openai_key = os.environ.get("OPENAI_API_KEY")
                    files = {'file': ('audio.m4a', full_audio, 'audio/m4a')}
                    data = {'model': 'whisper-1', 'language': 'pt'}
                    
                    resposta = requests.post("https://api.openai.com/v1/audio/transcriptions", 
                                             headers={"Authorization": f"Bearer {openai_key}"}, 
                                             files=files, data=data, timeout=60)
                    
                    if resposta.status_code == 200:
                        self.enviar_resposta(200, {"texto": resposta.json().get("text", "")})
                    else:
                        self.enviar_resposta(resposta.status_code, {"erro": resposta.text})
                else:
                    self.enviar_resposta(200, {"status": "recebido_parte", "parte": chunk_index})
            except Exception as e:
                self.enviar_resposta(500, {"erro": str(e)})

if __name__ == '__main__':
    from http.server import HTTPServer
    port = int(os.environ.get('PORT', 10000))
    HTTPServer(('0.0.0.0', port), handler).serve_forever()