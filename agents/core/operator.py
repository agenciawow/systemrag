"""
Operador para descoberta automática de agentes

Padrão inspirado no framework Agno para descoberta dinâmica de agentes.
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, List, Type
from dataclasses import dataclass


@dataclass
class AgentInfo:
    """Informações sobre um agente descoberto"""
    name: str
    agent_id: str
    description: str
    agent_class: Type
    module_path: str


class AgentOperator:
    """
    Operador que descobre automaticamente agentes disponíveis
    
    Funcionalidades:
    - Descoberta automática de agentes na pasta
    - Cache de agentes descobertos
    - Criação dinâmica de instâncias
    - Informações sobre agentes disponíveis
    """
    
    def __init__(self, agents_dir: str = "agents"):
        self.agents_dir = agents_dir
        self._discovered_agents: Dict[str, AgentInfo] = {}
        self._agent_instances: Dict[str, Any] = {}
        self._discover_agents()
    
    def _discover_agents(self):
        """Descobre todos os agentes na pasta"""
        agents_path = Path(__file__).parent
        
        for py_file in agents_path.glob("*.py"):
            if py_file.name.startswith("_") or py_file.name == "operator.py":
                continue
            
            try:
                # Importar o módulo
                module_name = f"agents.core.{py_file.stem}"
                module = importlib.import_module(module_name)
                
                # Procurar classes que parecem ser agentes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (name.endswith("Agent") and 
                        hasattr(obj, "agent_id") and 
                        hasattr(obj, "name") and
                        obj.__module__ == module.__name__):
                        
                        # Criar info do agente
                        agent_info = AgentInfo(
                            name=getattr(obj, "name", name),
                            agent_id=getattr(obj, "agent_id", name.lower().replace("agent", "")),
                            description=getattr(obj, "description", obj.__doc__ or ""),
                            agent_class=obj,
                            module_path=module_name
                        )
                        
                        self._discovered_agents[agent_info.agent_id] = agent_info
                        
            except Exception as e:
                print(f"Erro ao importar {py_file}: {e}")
    
    def get_agent(self, agent_id: str) -> Any:
        """
        Obtém instância de um agente por ID
        
        Args:
            agent_id: ID do agente
            
        Returns:
            Instância do agente
        """
        if agent_id not in self._discovered_agents:
            raise ValueError(f"Agente '{agent_id}' não encontrado")
        
        # Cache de instâncias
        if agent_id not in self._agent_instances:
            agent_info = self._discovered_agents[agent_id]
            self._agent_instances[agent_id] = agent_info.agent_class()
        
        return self._agent_instances[agent_id]
    
    def list_agents(self) -> List[Dict[str, str]]:
        """
        Lista todos os agentes disponíveis
        
        Returns:
            Lista de informações dos agentes
        """
        return [
            {
                "agent_id": info.agent_id,
                "name": info.name,
                "description": info.description,
                "module": info.module_path
            }
            for info in self._discovered_agents.values()
        ]
    
    def agent_exists(self, agent_id: str) -> bool:
        """Verifica se um agente existe"""
        return agent_id in self._discovered_agents
    
    def get_agent_info(self, agent_id: str) -> Dict[str, str]:
        """Obtém informações de um agente específico"""
        if agent_id not in self._discovered_agents:
            raise ValueError(f"Agente '{agent_id}' não encontrado")
        
        info = self._discovered_agents[agent_id]
        return {
            "agent_id": info.agent_id,
            "name": info.name,
            "description": info.description,
            "module": info.module_path
        }
    
    def refresh_agents(self):
        """Recarrega a descoberta de agentes"""
        self._discovered_agents.clear()
        self._agent_instances.clear()
        self._discover_agents()


# Instância global do operador
agent_operator = AgentOperator()


# Funções de conveniência
def get_agent(agent_id: str):
    """Obtém um agente por ID"""
    return agent_operator.get_agent(agent_id)


def list_agents():
    """Lista todos os agentes disponíveis"""
    return agent_operator.list_agents()


def agent_exists(agent_id: str) -> bool:
    """Verifica se um agente existe"""
    return agent_operator.agent_exists(agent_id)