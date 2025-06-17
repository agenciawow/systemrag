#!/usr/bin/env python3
"""
Script de limpeza de logs e arquivos temporários

Este script remove logs antigos e arquivos temporários para manter o sistema limpo.
Pode ser executado manualmente ou agendado para execução automática.
"""

import os
import time
import glob
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configuração do logging para este script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LogCleaner:
    """Limpador de logs e arquivos temporários"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        
        # Configurações de limpeza (podem ser modificadas via env)
        self.max_log_age_days = int(os.getenv("LOG_RETENTION_DAYS", "7"))
        self.max_log_size_mb = int(os.getenv("MAX_LOG_SIZE_MB", "100"))
        
        # Padrões de arquivos para limpeza
        self.log_patterns = [
            "*.log",
            "*_log.txt", 
            "*.debug",
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            "*.tmp"
        ]
        
        # Diretórios onde procurar
        self.search_dirs = [
            self.project_root,
            self.project_root / "logs",
            self.project_root / "temp", 
            self.project_root / "tmp"
        ]
    
    def clean_old_logs(self) -> int:
        """Remove logs mais antigos que o limite configurado"""
        cleaned_count = 0
        cutoff_time = time.time() - (self.max_log_age_days * 24 * 60 * 60)
        
        logger.info(f"Limpando logs mais antigos que {self.max_log_age_days} dias...")
        
        for search_dir in self.search_dirs:
            if not search_dir.exists():
                continue
                
            for pattern in self.log_patterns:
                for file_path in glob.glob(str(search_dir / "**" / pattern), recursive=True):
                    try:
                        file_stat = os.stat(file_path)
                        
                        # Verificar idade do arquivo
                        if file_stat.st_mtime < cutoff_time:
                            os.remove(file_path)
                            cleaned_count += 1
                            logger.info(f"Removido: {file_path}")
                            
                    except Exception as e:
                        logger.warning(f"Erro ao remover {file_path}: {e}")
        
        return cleaned_count
    
    def clean_large_logs(self) -> int:
        """Remove ou trunca logs muito grandes"""
        cleaned_count = 0
        max_size_bytes = self.max_log_size_mb * 1024 * 1024
        
        logger.info(f"Verificando logs maiores que {self.max_log_size_mb}MB...")
        
        for search_dir in self.search_dirs:
            if not search_dir.exists():
                continue
                
            for log_file in search_dir.glob("**/*.log"):
                try:
                    file_size = os.path.getsize(log_file)
                    
                    if file_size > max_size_bytes:
                        # Para logs ativos, truncar mantendo últimas linhas
                        if self._is_active_log(log_file):
                            self._truncate_log(log_file, max_size_bytes)
                            logger.info(f"Truncado: {log_file} ({file_size/1024/1024:.1f}MB)")
                        else:
                            # Para logs inativos, remover
                            os.remove(log_file)
                            logger.info(f"Removido log grande: {log_file} ({file_size/1024/1024:.1f}MB)")
                            
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.warning(f"Erro ao processar {log_file}: {e}")
        
        return cleaned_count
    
    def clean_cache_files(self) -> int:
        """Remove arquivos de cache do Python"""
        cleaned_count = 0
        
        logger.info("Limpando arquivos de cache...")
        
        # Cache do Python
        for cache_dir in self.project_root.glob("**/__pycache__"):
            try:
                import shutil
                shutil.rmtree(cache_dir)
                cleaned_count += 1
                logger.info(f"Removido cache: {cache_dir}")
            except Exception as e:
                logger.warning(f"Erro ao remover cache {cache_dir}: {e}")
        
        # Arquivos .pyc
        for pyc_file in self.project_root.glob("**/*.pyc"):
            try:
                os.remove(pyc_file)
                cleaned_count += 1
            except Exception as e:
                logger.warning(f"Erro ao remover {pyc_file}: {e}")
        
        # Cache do pytest
        for pytest_cache in self.project_root.glob("**/.pytest_cache"):
            try:
                import shutil
                shutil.rmtree(pytest_cache)
                cleaned_count += 1
                logger.info(f"Removido pytest cache: {pytest_cache}")
            except Exception as e:
                logger.warning(f"Erro ao remover pytest cache {pytest_cache}: {e}")
        
        return cleaned_count
    
    def clean_temp_files(self) -> int:
        """Remove arquivos temporários"""
        cleaned_count = 0
        
        logger.info("Limpando arquivos temporários...")
        
        temp_patterns = ["*.tmp", "*.temp", "*~", ".DS_Store"]
        
        for search_dir in self.search_dirs:
            if not search_dir.exists():
                continue
                
            for pattern in temp_patterns:
                for temp_file in search_dir.glob(f"**/{pattern}"):
                    try:
                        os.remove(temp_file)
                        cleaned_count += 1
                        logger.info(f"Removido temp: {temp_file}")
                    except Exception as e:
                        logger.warning(f"Erro ao remover {temp_file}: {e}")
        
        return cleaned_count
    
    def _is_active_log(self, log_file: Path) -> bool:
        """Verifica se um log está sendo usado ativamente"""
        # Considera ativo se foi modificado nas últimas 24 horas
        try:
            file_stat = os.stat(log_file)
            last_modified = datetime.fromtimestamp(file_stat.st_mtime)
            return datetime.now() - last_modified < timedelta(hours=24)
        except:
            return False
    
    def _truncate_log(self, log_file: Path, max_size: int):
        """Trunca um log mantendo as últimas linhas"""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Manter aproximadamente metade do tamanho máximo
            target_size = max_size // 2
            total_size = 0
            keep_lines = []
            
            # Começar do final e adicionar linhas até atingir o tamanho alvo
            for line in reversed(lines):
                total_size += len(line.encode('utf-8'))
                if total_size > target_size:
                    break
                keep_lines.insert(0, line)
            
            # Escrever de volta as linhas mantidas
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"[LOG TRUNCADO EM {datetime.now()}]\n")
                f.writelines(keep_lines)
                
        except Exception as e:
            logger.warning(f"Erro ao truncar {log_file}: {e}")
    
    def get_current_usage(self) -> dict:
        """Retorna estatísticas do uso atual de logs"""
        stats = {
            "total_log_files": 0,
            "total_log_size_mb": 0,
            "old_files_count": 0,
            "large_files_count": 0
        }
        
        cutoff_time = time.time() - (self.max_log_age_days * 24 * 60 * 60)
        max_size_bytes = self.max_log_size_mb * 1024 * 1024
        
        for search_dir in self.search_dirs:
            if not search_dir.exists():
                continue
                
            for log_file in search_dir.glob("**/*.log"):
                try:
                    file_stat = os.stat(log_file)
                    file_size = file_stat.st_size
                    
                    stats["total_log_files"] += 1
                    stats["total_log_size_mb"] += file_size / 1024 / 1024
                    
                    if file_stat.st_mtime < cutoff_time:
                        stats["old_files_count"] += 1
                    
                    if file_size > max_size_bytes:
                        stats["large_files_count"] += 1
                        
                except Exception:
                    continue
        
        return stats
    
    def run_full_cleanup(self) -> dict:
        """Executa limpeza completa e retorna estatísticas"""
        logger.info("Iniciando limpeza completa de logs e arquivos temporários...")
        
        start_time = time.time()
        
        # Estatísticas antes
        before_stats = self.get_current_usage()
        
        # Executar limpezas
        results = {
            "old_logs_cleaned": self.clean_old_logs(),
            "large_logs_cleaned": self.clean_large_logs(),
            "cache_files_cleaned": self.clean_cache_files(),
            "temp_files_cleaned": self.clean_temp_files()
        }
        
        # Estatísticas depois
        after_stats = self.get_current_usage()
        
        # Calcular economia
        space_saved_mb = before_stats["total_log_size_mb"] - after_stats["total_log_size_mb"]
        execution_time = time.time() - start_time
        
        results.update({
            "space_saved_mb": round(space_saved_mb, 2),
            "execution_time_seconds": round(execution_time, 2),
            "before_stats": before_stats,
            "after_stats": after_stats
        })
        
        logger.info(f"Limpeza concluída em {execution_time:.1f}s")
        logger.info(f"Espaço liberado: {space_saved_mb:.1f}MB")
        logger.info(f"Total de arquivos limpos: {sum(results[k] for k in results if k.endswith('_cleaned'))}")
        
        return results

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Limpeza de logs e arquivos temporários")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar o que seria removido sem remover")
    parser.add_argument("--max-age", type=int, help="Idade máxima dos logs em dias (padrão: 7)")
    parser.add_argument("--max-size", type=int, help="Tamanho máximo dos logs em MB (padrão: 100)")
    parser.add_argument("--stats-only", action="store_true", help="Apenas mostrar estatísticas")
    
    args = parser.parse_args()
    
    # Configurar variáveis de ambiente se fornecidas
    if args.max_age:
        os.environ["LOG_RETENTION_DAYS"] = str(args.max_age)
    if args.max_size:
        os.environ["MAX_LOG_SIZE_MB"] = str(args.max_size)
    
    cleaner = LogCleaner()
    
    if args.stats_only:
        stats = cleaner.get_current_usage()
        print("\n📊 Estatísticas atuais de logs:")
        print(f"   Total de arquivos: {stats['total_log_files']}")
        print(f"   Tamanho total: {stats['total_log_size_mb']:.1f}MB")
        print(f"   Arquivos antigos: {stats['old_files_count']}")
        print(f"   Arquivos grandes: {stats['large_files_count']}")
        return
    
    if args.dry_run:
        print("🔍 Modo dry-run: mostrando o que seria removido...")
        # Implementar preview se necessário
        return
    
    # Executar limpeza
    results = cleaner.run_full_cleanup()
    
    print("\n✅ Resultados da limpeza:")
    print(f"   Logs antigos removidos: {results['old_logs_cleaned']}")
    print(f"   Logs grandes processados: {results['large_logs_cleaned']}")
    print(f"   Arquivos de cache removidos: {results['cache_files_cleaned']}")
    print(f"   Arquivos temporários removidos: {results['temp_files_cleaned']}")
    print(f"   Espaço liberado: {results['space_saved_mb']}MB")
    print(f"   Tempo de execução: {results['execution_time_seconds']}s")

if __name__ == "__main__":
    main()