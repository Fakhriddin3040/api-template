from src.app.shared_kernel.registries.context_registry import ContextVarRegistry

db_session_registry = ContextVarRegistry(key="asyncsession")
