from abc import ABC, abstractmethod

class Load(ABC):
    
    @abstractmethod
    def load_data(self):
        pass
    
    @abstractmethod
    def transform_data(self):
        pass
    
    @abstractmethod
    def validate_data(self):
        pass
    
    @abstractmethod
    def save_data(self):
        pass
