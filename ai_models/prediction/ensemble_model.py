"""集成模型"""
import numpy as np
from typing import List, Dict
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor


class EnsembleModel:
    """
    集成模型 - 结合多个模型的预测
    """
    
    def __init__(self, models: List = None, weights: List[float] = None):
        self.models = models or []
        self.weights = weights or []
        self.meta_learner = None
        self.use_meta_learner = False
    
    def add_model(self, model, weight: float = 1.0):
        """添加基础模型"""
        self.models.append(model)
        self.weights.append(weight)
    
    def fit_meta_learner(
        self,
        X: np.ndarray,
        y: np.ndarray,
        meta_learner_type: str = 'ridge'
    ):
        """
        训练元学习器
        
        Args:
            X: 特征数据
            y: 目标数据
            meta_learner_type: 'ridge', 'gb', 'rf'
        """
        # 获取所有基础模型的预测
        predictions = self._get_base_predictions(X)
        
        # 选择元学习器
        if meta_learner_type == 'ridge':
            self.meta_learner = Ridge(alpha=1.0)
        elif meta_learner_type == 'gb':
            self.meta_learner = GradientBoostingRegressor(n_estimators=100)
        elif meta_learner_type == 'rf':
            self.meta_learner = RandomForestRegressor(n_estimators=100)
        
        # 训练元学习器
        self.meta_learner.fit(predictions, y)
        self.use_meta_learner = True
    
    def _get_base_predictions(self, X: np.ndarray) -> np.ndarray:
        """获取基础模型的预测"""
        predictions = []
        for model in self.models:
            try:
                pred = model.predict(X)
                if len(pred.shape) > 1:
                    pred = pred.flatten()
                predictions.append(pred)
            except Exception as e:
                print(f"Prediction error: {e}")
                predictions.append(np.zeros(len(X)))
        
        return np.column_stack(predictions)
    
    def predict(self, X: np.ndarray, method: str = 'weighted') -> np.ndarray:
        """
        集成预测
        
        Args:
            X: 特征数据
            method: 'weighted', 'average', 'meta'
        """
        predictions = self._get_base_predictions(X)
        
        if method == 'weighted' and self.weights:
            # 加权平均
            weights = np.array(self.weights) / sum(self.weights)
            return np.average(predictions, axis=1, weights=weights)
        
        elif method == 'meta' and self.use_meta_learner:
            # 元学习器预测
            return self.meta_learner.predict(predictions)
        
        else:
            # 简单平均
            return np.mean(predictions, axis=1)
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """评估集成模型"""
        predictions = self.predict(X)
        
        mse = np.mean((predictions - y) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(predictions - y))
        
        pred_direction = np.diff(predictions) > 0
        true_direction = np.diff(y) > 0
        direction_accuracy = np.mean(pred_direction == true_direction) if len(pred_direction) > 0 else 0
        
        return {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'direction_accuracy': direction_accuracy
        }
    
    def get_model_weights(self) -> Dict[str, float]:
        """获取模型权重（从元学习器）"""
        if self.use_meta_learner and hasattr(self.meta_learner, 'coef_'):
            weights = self.meta_learner.coef_
            return {f"model_{i}": w for i, w in enumerate(weights)}
        return {f"model_{i}": w for i, w in enumerate(self.weights)}


class StackingEnsemble:
    """
    堆叠集成模型
    """
    
    def __init__(self, base_models: Dict[str, any], meta_model=None):
        self.base_models = base_models
        self.meta_model = meta_model or Ridge(alpha=1.0)
        self.fitted_models = {}
    
    def fit(self, X: np.ndarray, y: np.ndarray, cv: int = 5):
        """
        训练堆叠模型
        
        使用交叉验证方式生成元特征
        """
        from sklearn.model_selection import KFold
        
        n_samples = len(X)
        meta_features = np.zeros((n_samples, len(self.base_models)))
        
        kf = KFold(n_splits=cv, shuffle=True)
        
        # 为每个基础模型生成元特征
        for idx, (name, model) in enumerate(self.base_models.items()):
            fold_predictions = np.zeros(n_samples)
            
            for train_idx, val_idx in kf.split(X):
                X_train, X_val = X[train_idx], X[val_idx]
                y_train = y[train_idx]
                
                # 训练模型
                if hasattr(model, 'fit'):
                    model.fit(X_train, y_train)
                
                # 预测验证集
                pred = model.predict(X_val)
                if len(pred.shape) > 1:
                    pred = pred.flatten()
                fold_predictions[val_idx] = pred
            
            meta_features[:, idx] = fold_predictions
            
            # 保存完整训练的模型
            model_copy = self._clone_model(model)
            if hasattr(model_copy, 'fit'):
                model_copy.fit(X, y)
            self.fitted_models[name] = model_copy
        
        # 训练元学习器
        self.meta_model.fit(meta_features, y)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        # 生成元特征
        meta_features = np.zeros((len(X), len(self.fitted_models)))
        
        for idx, (name, model) in enumerate(self.fitted_models.items()):
            pred = model.predict(X)
            if len(pred.shape) > 1:
                pred = pred.flatten()
            meta_features[:, idx] = pred
        
        # 元学习器预测
        return self.meta_model.predict(meta_features)
    
    def _clone_model(self, model):
        """克隆模型"""
        import copy
        return copy.deepcopy(model)
