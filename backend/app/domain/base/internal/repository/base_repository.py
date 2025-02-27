"""领域基础仓储类"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from typing import TypeVar, Generic, Type
from app.db.internal.base import Base
from app.core.base.internal.repository.core_repository import CoreRepository

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(CoreRepository[ModelType]):
    """领域基础仓储类
    
    继承自核心仓储类，可以在这里添加领域特定的功能
    """
    
    def __init__(self, model: Type[ModelType]):
        """初始化仓储
        
        Args:
            model: 模型类
        """
        super().__init__(model)
