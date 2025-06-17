"""
Módulo principal para executar a API de Agentes via python -m
"""

if __name__ == "__main__":
    import uvicorn
    from .main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8001)