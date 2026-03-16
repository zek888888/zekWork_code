"""Transformer预测模型"""
import numpy as np
import warnings
warnings.filterwarnings('ignore')

try:
    import tensorflow as tf
    from tensorflow.keras.models import Model
    from tensorflow.keras.layers import (
        Input, Dense, Dropout, LayerNormalization,
        MultiHeadAttention, GlobalAveragePooling1D
    )
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


if TF_AVAILABLE:
    class TransformerBlock(tf.keras.layers.Layer):
        """Transformer编码器块"""
        
        def __init__(self, embed_dim, num_heads, ff_dim, rate=0.1):
            super().__init__()
            self.att = MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
            self.ffn = tf.keras.Sequential([
                Dense(ff_dim, activation="relu"),
                Dense(embed_dim)
            ])
            self.layernorm1 = LayerNormalization(epsilon=1e-6)
            self.layernorm2 = LayerNormalization(epsilon=1e-6)
            self.dropout1 = Dropout(rate)
            self.dropout2 = Dropout(rate)
        
        def call(self, inputs, training=False):
            attn_output = self.att(inputs, inputs)
            attn_output = self.dropout1(attn_output, training=training)
            out1 = self.layernorm1(inputs + attn_output)
            
            ffn_output = self.ffn(out1)
            ffn_output = self.dropout2(ffn_output, training=training)
            return self.layernorm2(out1 + ffn_output)
else:
    class TransformerBlock:
        """占位Transformer块"""
        def __init__(self, *args, **kwargs):
            pass


class TransformerModel:
    """Transformer股票价格预测模型"""
    
    def __init__(
        self,
        sequence_length: int = 60,
        n_features: int = 10,
        embed_dim: int = 64,
        num_heads: int = 4,
        ff_dim: int = 128,
        num_transformer_blocks: int = 2,
        dropout: float = 0.1,
        learning_rate: float = 0.001
    ):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.num_transformer_blocks = num_transformer_blocks
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.model = None
        self.history = None
    
    def build_model(self):
        """构建Transformer模型"""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required. Install with: pip install tensorflow")
        
        inputs = Input(shape=(self.sequence_length, self.n_features))
        
        # 嵌入层
        x = Dense(self.embed_dim)(inputs)
        
        # Transformer块
        for _ in range(self.num_transformer_blocks):
            x = TransformerBlock(
                self.embed_dim,
                self.num_heads,
                self.ff_dim,
                self.dropout
            )(x)
        
        # 池化和输出
        x = GlobalAveragePooling1D()(x)
        x = Dropout(self.dropout)(x)
        x = Dense(32, activation="relu")(x)
        x = Dropout(self.dropout)(x)
        outputs = Dense(1)(x)
        
        self.model = Model(inputs=inputs, outputs=outputs)
        
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        return self.model
    
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
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=10,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=5
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
        
        pred_direction = np.diff(predictions.flatten()) > 0
        true_direction = np.diff(y_test) > 0
        direction_accuracy = np.mean(pred_direction == true_direction) if len(pred_direction) > 0 else 0
        
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
        self.model = tf.keras.models.load_model(filepath)
