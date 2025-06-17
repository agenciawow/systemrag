"""
Módulo principal para executar a API do Sistema RAG via python -m
"""

if __name__ == "__main__":
    import uvicorn
    from .api import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000)