"""LSTM预测模型"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


class LSTMModel:
    """LSTM股票价格预测模型"""
    
    def __init__(
        self,
        sequence_length: int = 60,
        n_features: int = 10,
        n_units: list = None,
        dropout: float = 0.2,
        learning_rate: float = 0.001
    ):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.n_units = n_units or [64, 32]
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.model = None
        self.history = None
    
    def build_model(self):
        """构建LSTM模型"""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required. Install with: pip install tensorflow")
        
        model = Sequential()
        
        # 第一层LSTM
        model.add(LSTM(
            units=self.n_units[0],
            return_sequences=len(self.n_units) > 1,
            input_shape=(self.sequence_length, self.n_features)
        ))
        model.add(BatchNormalization())
        model.add(Dropout(self.dropout))
        
        # 中间层
        for i, units in enumerate(self.n_units[1:], 1):
            return_sequences = i < len(self.n_units) - 1
            model.add(LSTM(units, return_sequences=return_sequences))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout))
        
        # 输出层
        model.add(Dense(16, activation='relu'))
        model.add(Dense(1))
        
        # 编译
        optimizer = Adam(learning_rate=self.learning_rate)
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
        
        self.model = model
        return model
    
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray = None,
        y_val: np.ndarray = None,
        epochs: int = 50,
        batch_size: int = 32,
        verbose: int = 1
    ):
        """训练模型"""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required. Install with: pip install tensorflow")
        
        if self.model is None:
            self.n_features = X_train.shape[2]
            self.build_model()
        
        callbacks = [
            EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=10,
                restore_best_weights=True
            ),
            ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6
            )
        ]
        
        validation_data = (X_val, y_val) if X_val is not None else None
        
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=verbose
        )
        
        return self.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required. Install with: pip install tensorflow")
        if self.model is None:
            raise ValueError("Model not trained yet!")
        return self.model.predict(X, verbose=0)
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """评估模型"""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required. Install with: pip install tensorflow")
        predictions = self.predict(X_test)
        
        mse = np.mean((predictions.flatten() - y_test) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(predictions.flatten() - y_test))
        
        # 方向准确率
        pred_direction = np.diff(predictions.flatten()) > 0
        true_direction = np.diff(y_test) > 0
        direction_accuracy = np.mean(pred_direction == true_direction)
        
        return {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'direction_accuracy': direction_accuracy
        }
    
    def save(self, filepath: str):
        """保存模型"""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required. Install with: pip install tensorflow")
        if self.model is not None:
            self.model.save(filepath)
    
    def load(self, filepath: str):
        """加载模型"""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required. Install with: pip install tensorflow")
        self.model = load_model(filepath)


class BiLSTMModel(LSTMModel):
    """双向LSTM模型"""
    
    def build_model(self):
        """构建双向LSTM模型"""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required. Install with: pip install tensorflow")
        from tensorflow.keras.layers import Bidirectional
        
        model = Sequential()
        
        model.add(Bidirectional(LSTM(
            units=self.n_units[0],
            return_sequences=len(self.n_units) > 1
        ), input_shape=(self.sequence_length, self.n_features)))
        model.add(BatchNormalization())
        model.add(Dropout(self.dropout))
        
        for i, units in enumerate(self.n_units[1:], 1):
            return_sequences = i < len(self.n_units) - 1
            model.add(Bidirectional(LSTM(units, return_sequences=return_sequences)))
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout))
        
        model.add(Dense(16, activation='relu'))
        model.add(Dense(1))
        
        optimizer = Adam(learning_rate=self.learning_rate)
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
        
        self.model = model
        return model
