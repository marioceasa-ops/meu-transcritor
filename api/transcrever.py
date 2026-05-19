from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import uuid
import tempfile

# Dicionário simples para rastrear os arquivos fatiados em memória (para planos gratuitos)
# Nota: Em servidores serverless, isso vive enquanto o container estiver ativo.
arquivos_temporarios = {}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # ... (suas rotas de /api/criar-pix e /api/checar-pix permanecem iguais) ...

        # 3. ROTA DE TRANSCRIÇÃO COM UNIÃO DE FATIAS
        elif self.path == '/api/transcrever-final':
            try:
                content_length = int(self.headers['Content-Length'])
                body_bytes = self.rfile.read(content_length)
                
                chunk_index = int(self.headers.get('x-chunk-index', 0))
                total_chunks = int(self.headers.get('x-total-chunks', 1))
                session_id = self.headers.get('x-session-id', 'default')

                if session_id not in arquivos_temporarios:
                    arquivos_temporarios[session_id] = [None] * total_chunks
                
                arquivos_temporarios[session_id][chunk_index] = body_bytes

                # Verifica se todas as partes foram recebidas
                if None not in arquivos_temporarios[session_id]:
                    # Une os bytes
                    full_audio = b"".join(arquivos_temporarios[session_id])
                    
                    # Limpa a memória
                    del arquivos_temporarios[session_id]

                    # Envia para a OpenAI
                    openai_key = os.environ.get("OPENAI_API_KEY")
                    files = {'file': ('audio_completo.m4a', full_audio, 'audio/m4a')}
                    data = {'model': 'whisper-1', 'language': 'pt'}
                    
                    resposta = requests.post("https://api.openai.com/v1/audio/transcriptions", 
                                             headers={"Authorization": f"Bearer {openai_key}"}, 
                                             files=files, data=data)
                    
                    self.enviar_resposta(200, {"texto": resposta.json().get("text", "")})
                else:
                    self.enviar_resposta(200, {"status": "recebido_parte", "parte": chunk_index})

            except Exception as e:
                self.enviar_resposta(500, {"erro": str(e)})

    # ... (método enviar_resposta e OPTIONS devem ser mantidos) ...