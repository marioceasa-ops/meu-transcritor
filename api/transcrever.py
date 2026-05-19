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
        # A lógica de processamento que você já tem aqui...
        # Apenas certifique-se de terminar com self.enviar_resposta(200, {...})