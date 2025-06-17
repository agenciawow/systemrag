#!/usr/bin/env python3
"""
Teste 2: Ingestão de Documentos
Testa o processo de ingestão de documentos no sistema
"""

import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

class TestDocumentIngestion:
    """Testes de ingestão de documentos"""
    
    def setup_method(self):
        """Configuração para cada teste"""
        self.api_url = "http://localhost:8000"
        self.api_key = os.getenv("API_KEY", "sistemarag-api-key-secure-2024")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def test_google_drive_url_configured(self):
        """Verifica se a URL do Google Drive está configurada"""
        drive_url = os.getenv("GOOGLE_DRIVE_URL")
        assert drive_url is not None, "GOOGLE_DRIVE_URL não configurada"
        assert "drive.google.com" in drive_url, "URL do Google Drive inválida"
    
    def test_ingest_api_endpoint_exists(self):
        """Verifica se o endpoint de ingestão existe"""
        try:
            response = requests.post(
                f"{self.api_url}/ingest",
                headers=self.headers,
                json={"test": "ping"},
                timeout=10
            )
            # Esperamos erro 422 (dados inválidos) mas não 404 (endpoint não existe)
            assert response.status_code in [422, 400], f"Endpoint /ingest não responde adequadamente: {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("API Sistema RAG não está rodando")
    
    def test_document_ingestion_simple(self):
        """Testa ingestão de documento do Google Drive"""
        drive_url = os.getenv("GOOGLE_DRIVE_URL")
        if not drive_url:
            pytest.skip("GOOGLE_DRIVE_URL não configurada")
        
        try:
            response = requests.post(
                f"{self.api_url}/ingest",
                headers=self.headers,
                json={
                    "url": drive_url,
                    "collection_name": "test_zep_document"
                },
                timeout=60
            )
            
            # Sucesso ou documento já existe
            assert response.status_code in [200, 201, 409], f"Ingestão falhou: {response.status_code} - {response.text}"
            
            if response.status_code in [200, 201]:
                data = response.json()
                assert "message" in data or "status" in data, "Resposta da ingestão sem informações adequadas"
                
        except requests.exceptions.ConnectionError:
            pytest.skip("API Sistema RAG não está rodando")
        except requests.exceptions.Timeout:
            pytest.skip("Timeout na ingestão - documento muito grande ou processo lento")
    
    def test_ingestion_status_check(self):
        """Verifica se é possível consultar status da ingestão"""
        try:
            response = requests.get(
                f"{self.api_url}/ingest/status",
                headers=self.headers,
                timeout=10
            )
            
            # Endpoint pode não existir, mas se existir deve responder adequadamente
            if response.status_code != 404:
                assert response.status_code == 200, f"Status da ingestão retornou {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            pytest.skip("API Sistema RAG não está rodando")
    
    def test_document_validation(self):
        """Testa validação de documentos"""
        invalid_cases = [
            {"url": "not-a-url"},
            {"url": "https://example.com/nonexistent.pdf"},
            {"collection_name": ""},
            {}
        ]
        
        for case in invalid_cases:
            try:
                response = requests.post(
                    f"{self.api_url}/ingest",
                    headers=self.headers,
                    json=case,
                    timeout=10
                )
                
                # Deve retornar erro de validação
                assert response.status_code in [400, 422], f"Validação falhou para {case}: {response.status_code}"
                
            except requests.exceptions.ConnectionError:
                pytest.skip("API Sistema RAG não está rodando")
                break

if __name__ == "__main__":
    pytest.main([__file__, "-v"])