# save_model.py

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import MinMaxScaler
from sklearn.impute import KNNImputer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from catboost import CatBoostClassifier
import pickle
import warnings

# 關閉警告
warnings.filterwarnings("ignore")

# ==============================================================================
#  工具函數 (僅供訓練階段使用)
# ==============================================================================

def train_preprocess_pipeline(df):
    """
    訓練專用的預處理：
    1. 回傳處理好的 df
    2. 回傳訓練好的 scaler 和 imputer 物件 (以便存檔)
    """
    df = df.copy()
    col_to_scale = ['Age', 'MaxHR', 'Oldpeak']  # 數值欄位
    
    # 1. 建立並訓練 Imputer (這裡簡化，先針對數值做)
    # 若資料有缺失，KNNImputer 需 fit 在所有欄位或特定欄位
    # 這裡假設針對數值欄位做處理
    imputer = KNNImputer()
    # 注意：KNNImputer 會回傳 numpy array，要轉回 DataFrame
    df[col_to_scale] = imputer.fit_transform(df[col_to_scale])
    
    # 2. 處理異常值 (僅在訓練時做，預測時通常不做截斷，除非極端不合理)
    for i in col_to_scale:
        z_scores = stats.zscore(df[i])
        lower = df[i][z_scores > -3].min()
        upper = df[i][z_scores < 3].max()
        df[i] = df[i].clip(lower, upper)

    # 3. 建立並訓練 Scaler
    scaler = MinMaxScaler()
    df[col_to_scale] = scaler.fit_transform(df[col_to_scale])
    
    return df, imputer, scaler

# ==============================================================================
#  通用預測器類別
# ==============================================================================

class HeartDiseasePredictor:
    def __init__(self):
        self.model = None
        self.model_name = None
        self.feature_columns = None
        self.imputer = None
        self.scaler = None
    
    def load_model(self, filepath):
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        self.model = data['model']
        self.model_name = data['model_name']
        self.feature_columns = data['feature_columns']
        # 載入訓練時的處理器
        self.imputer = data.get('imputer') 
        self.scaler = data.get('scaler')
        return self
    
    def _preprocess_new_data(self, df):
        """預測時專用的預處理 (使用已訓練的 scaler/imputer)"""
        df = df.copy()
        
        # 1. One-Hot Encoding
        cat_col = ['Sex', 'ST_Slope', 'ChestPainType', 'ExerciseAngina']
        # 確保現有資料有這些欄位才做 encoding
        existing_cat = [c for c in cat_col if c in df.columns]
        if existing_cat:
            df = pd.get_dummies(data=df, columns=existing_cat, drop_first=True)
            
        # 2. 補齊缺失的 One-Hot 欄位 (關鍵步驟)
        if self.feature_columns:
            for col in self.feature_columns:
                if col not in df.columns:
                    df[col] = 0
            # 確保欄位順序一致
            df = df[self.feature_columns]
            
        # 3. 數值處理 (使用訓練好的 Imputer 和 Scaler)
        num_cols = ['Age', 'MaxHR', 'Oldpeak']
        
        # 注意：這裡使用 transform 而不是 fit_transform
        if self.imputer:
            df[num_cols] = self.imputer.transform(df[num_cols])
            
        if self.scaler:
            df[num_cols] = self.scaler.transform(df[num_cols])
            
        return df
    
    def predict(self, data):
        if self.model is None: raise ValueError("請先載入模型")
        if isinstance(data, dict): df = pd.DataFrame([data])
        else: df = data.copy()
        
        df_processed = self._preprocess_new_data(df)
        return self.model.predict(df_processed)

    def predict_detail(self, data):
        """回傳詳細預測資訊"""
        if self.model is None: raise ValueError("請先載入模型")
        if isinstance(data, dict): df = pd.DataFrame([data])
        else: df = data.copy()
            
        df_processed = self._preprocess_new_data(df)
        pred = self.model.predict(df_processed)[0]
        prob = self.model.predict_proba(df_processed)[0][1] # 取出患病機率
        
        return {
            'model': self.model_name,
            'prediction': int(pred),
            'probability': float(prob),
            'risk_level': '高風險' if pred == 1 else '低風險'
        }
    def predict_detail(self, data):
        """回傳詳細預測資訊"""
        if self.model is None: raise ValueError("請先載入模型")
        if isinstance(data, dict): df = pd.DataFrame([data])
        else: df = data.copy()
            
        df_processed = self._preprocess_new_data(df)
        pred = self.model.predict(df_processed)[0]
        prob = self.model.predict_proba(df_processed)[0][1] 
        
        return {
            'model': self.model_name,
            'prediction': int(pred),
            'probability': float(prob),
            # 補上這行：
            'risk_percentage': f"{prob:.1%}", 
            'risk_level': '高風險' if pred == 1 else '低風險'
        }
    # ... (放在 predict 函式下方) ...

    def predict_proba(self, data):
        """
        新增這個函式：讓外部可以直接取得預測機率 (0~1)
        """
        if self.model is None: raise ValueError("請先載入模型")
        if isinstance(data, dict): df = pd.DataFrame([data])
        else: df = data.copy()
        
        df_processed = self._preprocess_new_data(df)
        
        # 回傳「患病 (Class 1)」的機率
        # [:, 1] 代表取出所有樣本的第 2 個欄位 (即 label=1 的機率)
        return self.model.predict_proba(df_processed)[:, 1]

    # ... (下面接著 predict_detail) ...

# ==============================================================================
#  主程式：訓練並存檔
# ==============================================================================

if __name__ == "__main__":
    try:
        # 1. 讀取與初步整理
        df_train = pd.read_csv("heart_train.csv")
        selected_features = ['Age', 'Sex','ChestPainType', 'MaxHR', 'ExerciseAngina' ,'Oldpeak', 'ST_Slope','HeartDisease']
        df_train = df_train[selected_features].copy()
        
        # One-Hot Encoding (先做，因為這會改變欄位結構)
        cat_col = ['Sex', 'ST_Slope', 'ChestPainType', 'ExerciseAngina']
        df_train_encoded = pd.get_dummies(data=df_train, columns=cat_col, drop_first=True)
        
        # 2. 執行預處理 pipeline 並取得訓練好的 Scaler/Imputer
        df_processed, imputer_trained, scaler_trained = train_preprocess_pipeline(df_train_encoded)

        X = df_processed.drop(['HeartDisease'], axis=1)
        y = df_processed['HeartDisease']
        feature_columns = X.columns.tolist() # 記住最終特徵欄位名稱

        # 3. 定義模型
        models_config = [
            {'name': 'CatBoost', 'model': CatBoostClassifier(verbose=False, random_state=369), 'file': 'catboost_best.pkl'},
            {'name': 'Gradient Boosting', 'model': GradientBoostingClassifier(random_state=369), 'file': 'gradient_boosting_best.pkl'},
            {'name': 'Random Forest', 'model': RandomForestClassifier(random_state=369), 'file': 'random_forest_best.pkl'}
        ]

        print("開始訓練模型...")
        for config in models_config:
            model = config['model']
            model.fit(X, y)
            
            # 4. 存檔：把 模型 + 特徵欄位 + 預處理器 全部包在一起
            save_packet = {
                'model': model,
                'model_name': config['name'],
                'feature_columns': feature_columns,
                'imputer': imputer_trained, # 存入訓練好的補值器
                'scaler': scaler_trained    # 存入訓練好的縮放器
            }
            
            with open(config['file'], 'wb') as f:
                pickle.dump(save_packet, f)
            print(f"已儲存: {config['file']}")

        print("\n所有模型已正確儲存（包含預處理邏輯）。")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"發生錯誤: {e}")