"""
Category-Aware LSTM + Autoencoder AI Predictor
Trains separate models for different API categories (REST API, Website, Database, etc.)
"""

import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import pickle
import os
import json
from bson import ObjectId

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    from sklearn.preprocessing import StandardScaler
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("[WARNING] TensorFlow not installed. Using fallback statistical methods.")

# Define API categories and their characteristics
API_CATEGORIES = {
    "REST API": {
        "expected_latency": 200,  # ms
        "failure_threshold": 0.05,  # 5% failure rate
        "latency_threshold": 2000,  # 2 seconds
        "status_codes": [200, 201, 204, 400, 401, 403, 404, 500, 502, 503]
    },
    "Website": {
        "expected_latency": 500,
        "failure_threshold": 0.02,  # 2% failure rate
        "latency_threshold": 3000,
        "status_codes": [200, 301, 302, 400, 403, 404, 500, 502, 503]
    },
    "Database": {
        "expected_latency": 50,
        "failure_threshold": 0.01,  # 1% failure rate
        "latency_threshold": 1000,
        "status_codes": [200, 408, 500, 503, 504]
    },
    "Microservice": {
        "expected_latency": 100,
        "failure_threshold": 0.03,
        "latency_threshold": 1500,
        "status_codes": [200, 201, 400, 404, 429, 500, 502, 503]
    },
    "Third-Party API": {
        "expected_latency": 1000,
        "failure_threshold": 0.10,  # 10% failure rate (more tolerant)
        "latency_threshold": 5000,
        "status_codes": [200, 400, 401, 403, 429, 500, 502, 503]
    },
    "Internal Service": {
        "expected_latency": 150,
        "failure_threshold": 0.02,
        "latency_threshold": 1000,
        "status_codes": [200, 201, 400, 404, 500, 503]
    }
}

class CategoryAwareAIPredictor:
    def __init__(self, mongo_db):
        self.db = mongo_db
        self.models_dir = "models"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Model parameters
        self.sequence_length = 20
        self.n_features = 10
        
        # Category-specific models
        self.category_models = {}  # {category: {"lstm": model, "autoencoder": model, "scaler": scaler}}
        
        if TENSORFLOW_AVAILABLE:
            self.use_ml = True
            print("[AI] Category-Aware LSTM + Autoencoder initialized")
            # Load existing models on startup
            self._load_all_models()
        else:
            self.use_ml = False
            print("[AI] TensorFlow not available, using statistical methods")
    
    def _load_all_models(self):
        """Load all pre-trained models on startup to avoid retraining"""
        for category in API_CATEGORIES.keys():
            try:
                if self._load_category_model(category):
                    print(f"[AI] Loaded pre-trained model for {category}")
            except Exception as e:
                print(f"[AI] No pre-trained model for {category}: {e}")
    
    def _get_category_path(self, category):
        """Get file paths for category-specific models"""
        safe_category = category.replace(" ", "_").lower()
        return {
            "lstm": os.path.join(self.models_dir, f"lstm_{safe_category}.h5"),
            "autoencoder": os.path.join(self.models_dir, f"autoencoder_{safe_category}.h5"),
            "scaler": os.path.join(self.models_dir, f"scaler_{safe_category}.pkl"),
            "config": os.path.join(self.models_dir, f"config_{safe_category}.json")
        }
    
    def _save_category_model(self, category, lstm_model, autoencoder_model, scaler):
        """Save trained models for a category"""
        if not self.use_ml:
            return False
        
        try:
            paths = self._get_category_path(category)
            
            # Save models
            lstm_model.save(paths["lstm"])
            autoencoder_model.save(paths["autoencoder"])
            
            # Save scaler
            with open(paths["scaler"], 'wb') as f:
                pickle.dump(scaler, f)
            
            # Save config
            config = {
                "category": category,
                "sequence_length": self.sequence_length,
                "n_features": self.n_features,
                "saved_at": datetime.utcnow().isoformat()
            }
            with open(paths["config"], 'w') as f:
                json.dump(config, f)
            
            print(f"[AI] Saved model for {category}")
            return True
        except Exception as e:
            print(f"[AI] Error saving model for {category}: {e}")
            return False
    
    def _load_category_model(self, category):
        """Load pre-trained models for a category"""
        if not self.use_ml:
            return False
        
        try:
            paths = self._get_category_path(category)
            
            # Check if all files exist
            if not all(os.path.exists(p) for p in [paths["lstm"], paths["autoencoder"], paths["scaler"]]):
                return False
            
            # Load models
            lstm_model = keras.models.load_model(paths["lstm"])
            autoencoder_model = keras.models.load_model(paths["autoencoder"])
            
            # Load scaler
            with open(paths["scaler"], 'rb') as f:
                scaler = pickle.load(f)
            
            # Store in memory
            self.category_models[category] = {
                "lstm": lstm_model,
                "autoencoder": autoencoder_model,
                "scaler": scaler
            }
            
            return True
        except Exception as e:
            print(f"[AI] Error loading model for {category}: {e}")
            return False
    
    def _create_lstm_model(self):
        """Create LSTM model for failure prediction"""
        model = keras.Sequential([
            layers.LSTM(64, return_sequences=True, input_shape=(self.sequence_length, self.n_features)),
            layers.Dropout(0.2),
            layers.LSTM(32, return_sequences=False),
            layers.Dropout(0.2),
            layers.Dense(16, activation='relu'),
            layers.Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy', 'AUC'])
        return model
    
    def _create_autoencoder_model(self):
        """Create Autoencoder for anomaly detection"""
        input_layer = layers.Input(shape=(self.sequence_length, self.n_features))
        encoded = layers.LSTM(32, return_sequences=True)(input_layer)
        encoded = layers.LSTM(16, return_sequences=False)(encoded)
        decoded = layers.RepeatVector(self.sequence_length)(encoded)
        decoded = layers.LSTM(16, return_sequences=True)(decoded)
        decoded = layers.LSTM(32, return_sequences=True)(decoded)
        decoded = layers.TimeDistributed(layers.Dense(self.n_features))(decoded)
        autoencoder = keras.Model(input_layer, decoded)
        autoencoder.compile(optimizer='adam', loss='mse')
        return autoencoder
    
    def _load_or_create_category_models(self, category):
        """Load or create models for specific category"""
        if category in self.category_models:
            return self.category_models[category]
        
        paths = self._get_category_path(category)
        models = {}
        
        # Load or create LSTM
        if os.path.exists(paths["lstm"]):
            try:
                models["lstm"] = keras.models.load_model(paths["lstm"])
                print(f"[AI] Loaded LSTM for category: {category}")
            except:
                models["lstm"] = self._create_lstm_model()
        else:
            models["lstm"] = self._create_lstm_model()
        
        # Load or create Autoencoder
        if os.path.exists(paths["autoencoder"]):
            try:
                models["autoencoder"] = keras.models.load_model(paths["autoencoder"])
                print(f"[AI] Loaded Autoencoder for category: {category}")
            except:
                models["autoencoder"] = self._create_autoencoder_model()
        else:
            models["autoencoder"] = self._create_autoencoder_model()
        
        # Load or create Scaler
        if os.path.exists(paths["scaler"]):
            try:
                with open(paths["scaler"], 'rb') as f:
                    models["scaler"] = pickle.load(f)
                print(f"[AI] Loaded scaler for category: {category}")
            except Exception as e:
                print(f"[AI] Error loading scaler for {category}: {e}")
                from sklearn.preprocessing import StandardScaler
                models["scaler"] = StandardScaler()
                print(f"[AI] Created new unfitted scaler for {category}")
        else:
            print(f"[AI] Scaler file not found for {category}: {paths['scaler']}")
            from sklearn.preprocessing import StandardScaler
            models["scaler"] = StandardScaler()
            print(f"[AI] Created new unfitted scaler for {category}")
        
        self.category_models[category] = models
        return models
    
    def _get_api_category(self, api_id):
        """Get category for an API"""
        api = self.db.monitored_apis.find_one({"_id": ObjectId(api_id)})
        if api and api.get("category"):
            return api["category"]
        return "REST API"  # Default category
    
    def _extract_time_series(self, api_id, hours=48):
        """Extract time-series data for LSTM"""
        from bson import ObjectId
        
        time_threshold = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"
        
        logs = list(self.db.monitoring_logs.find({
            "api_id": api_id,
            "timestamp": {"$gte": time_threshold}
        }).sort("timestamp", 1))
        
        if len(logs) < self.sequence_length + 1:
            return None, None, None
        
        # Get API category
        category = self._get_api_category(api_id)
        category_config = API_CATEGORIES.get(category, API_CATEGORIES["REST API"])
        
        features_list = []
        labels_list = []
        
        for log in logs:
            # Normalize latency based on category expectations
            expected_latency = category_config.get("expected_latency", 200)
            if not expected_latency or expected_latency == 0:
                expected_latency = 200  # Default fallback
            
            total_latency = log.get("total_latency_ms")
            normalized_latency = (total_latency / expected_latency) if total_latency is not None else 0.0

            dns_latency = log.get("dns_latency_ms")
            dns_latency_normalized = (dns_latency / 100.0) if dns_latency is not None else 0.0

            tcp_latency = log.get("tcp_latency_ms")
            tcp_latency_normalized = (tcp_latency / 100.0) if tcp_latency is not None else 0.0

            tls_latency = log.get("tls_latency_ms")
            tls_latency_normalized = (tls_latency / 100.0) if tls_latency is not None else 0.0

            server_latency = log.get("server_processing_latency_ms")
            server_latency_normalized = (server_latency / expected_latency) if server_latency is not None else 0.0

            download_latency = log.get("content_download_latency_ms")
            download_latency_normalized = (download_latency / expected_latency) if download_latency is not None else 0.0
            
            features = [
                1.0 if log.get("is_up", True) else 0.0,
                min(normalized_latency, 10.0),  # Cap at 10x expected
                dns_latency_normalized,
                tcp_latency_normalized,
                tls_latency_normalized,
                server_latency_normalized,
                download_latency_normalized,
                (log.get("status_code") or 200) / 500.0,
                1.0 if log.get("error_message") else 0.0,
                0.0  # Placeholder
            ]
            features_list.append(features)
            label = 0.0 if log.get("is_up", True) else 1.0
            labels_list.append(label)
        
        # Create sequences
        sequences = []
        labels = []
        
        for i in range(len(features_list) - self.sequence_length):
            seq = features_list[i:i + self.sequence_length]
            label = labels_list[i + self.sequence_length]
            sequences.append(seq)
            labels.append(label)
        
        return np.array(sequences), np.array(labels), category
    
    def _train_category_model(self, category, api_ids, epochs=50, batch_size=32):
        """Trains models for a specific category"""
        print("\n" + '='*70)
        print(f"Training models for category: {category}")
        print('='*70)
        
        # Collect data for this category
        all_sequences = []
        all_labels = []
        
        for api_id in api_ids:
            sequences, labels, _ = self._extract_time_series(api_id, hours=48)
            if sequences is not None and len(sequences) > 0:
                all_sequences.append(sequences)
                all_labels.append(labels)
        
        if not all_sequences:
            print(f"[AI] No data for category: {category}")
            return None
        
        X = np.vstack(all_sequences)
        y = np.concatenate(all_labels)
        
        print(f"Training on {len(X)} sequences from {len(api_ids)} APIs")
        
        # Load or create models for this category
        models = self._load_or_create_category_models(category)
        
        # Scale data
        n_samples, n_steps, n_features = X.shape
        X_reshaped = X.reshape(-1, n_features)
        X_scaled = models["scaler"].fit_transform(X_reshaped)
        X_scaled = X_scaled.reshape(n_samples, n_steps, n_features)
        
        # Split data
        split_idx = int(len(X_scaled) * 0.8)
        X_train, X_val = X_scaled[:split_idx], X_scaled[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Train LSTM
        print(f"\nTraining LSTM for {category}...")
        history = models["lstm"].fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            verbose=1,
            callbacks=[
                keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
                keras.callbacks.ReduceLROnPlateau(patience=5, factor=0.5)
            ]
        )
        
        # Evaluate
        loss, acc, auc = models["lstm"].evaluate(X_val, y_val, verbose=0)
        print(f"\n[{category}] LSTM Accuracy: {acc*100:.2f}%")
        print(f"[{category}] LSTM AUC: {auc:.3f}")
        
        # Train Autoencoder
        X_normal = X_scaled[y == 0]
        if len(X_normal) > 10:
            print(f"\nTraining Autoencoder for {category}...")
            models["autoencoder"].fit(
                X_normal, X_normal,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=0.2,
                verbose=1,
                callbacks=[keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)]
            )
            
            # Calculate threshold
            reconstructions = models["autoencoder"].predict(X_normal, verbose=0)
            mse = np.mean(np.square(X_normal - reconstructions), axis=(1, 2))
            models["anomaly_threshold"] = np.percentile(mse, 95)
            print(f"[{category}] Anomaly threshold: {models['anomaly_threshold']:.4f}")
        
        # Save models
        paths = self._get_category_path(category)
        models["lstm"].save(paths["lstm"])
        models["autoencoder"].save(paths["autoencoder"])
        with open(paths["scaler"], 'wb') as f:
            pickle.dump(models["scaler"], f)
        
        # Save config
        config = {
            "category": category,
            "sequence_length": self.sequence_length,
            "n_features": self.n_features,
            "accuracy": float(acc),
            "auc": float(auc),
            "trained": True,
            "last_trained": datetime.utcnow().isoformat()
        }
        with open(paths["config"], 'w') as f:
            json.dump(config, f)
        
        return {"accuracy": acc, "auc": auc, "samples": len(X)}

    def train_models_by_category(self, epochs=50, batch_size=32):
        """Train separate models for each category"""
        if not self.use_ml:
            print("[AI] TensorFlow not available")
            return False
        
        print("=" * 70)
        print("Category-Aware Model Training")
        print("=" * 70)
        
        # Group APIs by category
        apis = list(self.db.monitored_apis.find())
        category_apis = defaultdict(list)
        
        for api in apis:
            category = api.get("category", "REST API")
            category_apis[category].append(str(api["_id"]))
        
        print(f"\nFound {len(category_apis)} categories:")
        for cat, api_list in category_apis.items():
            print(f"  - {cat}: {len(api_list)} APIs")
        
        results = {}
        
        # Train models for each category
        for category, api_ids in category_apis.items():
            result = self._train_category_model(category, api_ids, epochs, batch_size)
            if result:
                results[category] = result
        
        # Print summary
        print("\n" + "=" * 70)
        print("Training Summary")
        print("=" * 70)
        for category, metrics in results.items():
            print(f"{category:20s} | Acc: {metrics['accuracy']*100:5.2f}% | AUC: {metrics['auc']:.3f} | Samples: {metrics['samples']}")
        
        return True

    def train_model_for_api_category(self, api_id, epochs=50, batch_size=32):
        """Trains the model for the category associated with a specific API"""
        if not self.use_ml:
            print("[AI] TensorFlow not available")
            return False
        
        category = self._get_api_category(api_id)
        
        # Check if model already exists and is loaded
        if category in self.category_models:
            print(f"[AI] Model for '{category}' already trained and loaded. Skipping training.")
            return True
        
        # Try to load existing model
        if self._load_category_model(category):
            print(f"[AI] Loaded existing model for '{category}'. Skipping training.")
            return True
        
        # Find all APIs in this category
        apis_in_category = list(self.db.monitored_apis.find({"category": category}))
        api_ids_in_category = [str(api["_id"]) for api in apis_in_category]
        
        if not api_ids_in_category:
            print(f"[AI] No APIs found for category: {category}")
            return False
        
        print(f"[AI] Training new model for category '{category}' (triggered by API '{api_id}')")
        result = self._train_category_model(category, api_ids_in_category, epochs, batch_size)
        
        return result is not None
    
    def train_model(self, api_id, epochs=50, batch_size=32):
        """Alias for train_model_for_api_category for backward compatibility"""
        return self.train_model_for_api_category(api_id, epochs, batch_size)

    def predict_failure(self, api_id, hours_ahead=1):
        """Predict failure using category-specific model"""
        try:
            print(f"[AI] predict_failure called for api_id: {api_id}")
            sequences, _, category = self._extract_time_series(api_id, hours=48)
            
            if sequences is None:
                print(f"[AI] No sequences returned - insufficient data")
                return {
                    "will_fail": False,
                    "confidence": 0.0,
                    "reason": "Insufficient data",
                    "risk_score": 0,
                    "method": "none",
                    "category": category
                }
            
            print(f"[AI] Got {len(sequences)} sequences, category: {category}")
            
            if self.use_ml:
                # Load category-specific models
                models = self._load_or_create_category_models(category)
                
                # Use last sequence
                last_seq = sequences[-1:]
                n_samples, n_steps, n_features = last_seq.shape
                
                # Validate sequence shape
                print(f"[AI] Validating shape: got ({n_samples}, {n_steps}, {n_features}), need ({n_samples}, {self.sequence_length}, {self.n_features})")
                
                if n_steps != self.sequence_length or n_features != self.n_features:
                    print(f"[AI] Shape mismatch detected - returning insufficient data message")
                    return {
                        "will_fail": False,
                        "confidence": 0.0,
                        "reason": f"Insufficient data (need {self.sequence_length} time steps, have {n_steps})",
                        "risk_score": 0,
                        "method": "none",
                        "category": category
                    }
                
                seq_reshaped = last_seq.reshape(-1, n_features)
                
                # Check if scaler is fitted
                try:
                    seq_scaled = models["scaler"].transform(seq_reshaped)
                except Exception as scaler_error:
                    print(f"[AI] Scaler not fitted for category {category}: {scaler_error}")
                    return {
                        "will_fail": False,
                        "confidence": 0.0,
                        "reason": f"Model not trained for category: {category}. Run training first.",
                        "risk_score": 0,
                        "method": "none",
                        "category": category
                    }
                
                seq_scaled = seq_scaled.reshape(n_samples, n_steps, n_features)
                
                # Predict
                prediction = models["lstm"].predict(seq_scaled, verbose=0)[0][0]
                
                # Adjust based on category expectations
                category_config = API_CATEGORIES.get(category, API_CATEGORIES["REST API"])
                failure_threshold = category_config.get("failure_threshold", 0.05)
                if not failure_threshold or failure_threshold == 0:
                    failure_threshold = 0.05  # Default 5%
                
                adjusted_confidence = prediction * (1.0 / failure_threshold)
                adjusted_confidence = min(adjusted_confidence, 1.0)
                
                will_fail = bool(prediction > 0.5)
                risk_score = int(adjusted_confidence * 100)
                
                recent_logs = list(self.db.monitoring_logs.find({"api_id": api_id}).sort("timestamp", -1).limit(10))
                reason = self._explain_prediction(recent_logs, prediction, category)
                
                return {
                    "will_fail": will_fail,
                    "confidence": float(adjusted_confidence),
                    "reason": reason,
                    "risk_score": risk_score,
                    "method": "lstm_category",
                    "category": category,
                    "model": f"LSTM ({category})"
                }
            else:
                return self._statistical_prediction(api_id, category)
        
        except Exception as e:
            print(f"[AI] Prediction error: {e}")
            return {
                "will_fail": False,
                "confidence": 0.0,
                "reason": f"Error: {str(e)}",
                "risk_score": 0,
                "method": "error"
            }
    
    def _explain_prediction(self, recent_logs, confidence, category):
        """Generate explanation"""
        if not recent_logs:
            return f"LSTM prediction for {category}"
        
        reasons = []
        failure_count = sum(1 for log in recent_logs if not log.get("is_up", True))
        if failure_count > 0:
            reasons.append(f"{failure_count} recent failures")
        
        latencies = [log.get("total_latency_ms", 0) for log in recent_logs if log.get("total_latency_ms")]
        if latencies:
            avg_latency = np.mean(latencies)
            category_config = API_CATEGORIES.get(category, API_CATEGORIES["REST API"])
            if avg_latency > category_config["latency_threshold"]:
                reasons.append(f"High latency: {avg_latency:.0f}ms")
        
        if not reasons:
            reasons.append(f"LSTM detected pattern ({category})")
        
        return " | ".join(reasons)
    
    def _statistical_prediction(self, api_id, category):
        """Fallback statistical prediction"""
        time_threshold = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"
        recent_logs = list(self.db.monitoring_logs.find({
            "api_id": api_id,
            "timestamp": {"$gte": time_threshold}
        }).sort("timestamp", -1).limit(50))
        
        if len(recent_logs) < 5:
            return {
                "will_fail": False,
                "confidence": 0.0,
                "reason": "Insufficient data",
                "risk_score": 0,
                "method": "statistical",
                "category": category
            }
        
        failure_rate = sum(1 for log in recent_logs if not log.get("is_up", True)) / len(recent_logs)
        category_config = API_CATEGORIES.get(category, API_CATEGORIES["REST API"])
        
        # Adjust risk based on category expectations
        expected_failure_rate = category_config.get("failure_threshold", 0.05)
        if not expected_failure_rate or expected_failure_rate == 0:
            expected_failure_rate = 0.05
        
        risk_score = int(min((failure_rate / expected_failure_rate) * 100, 100))
        
        return {
            "will_fail": risk_score > 70,
            "confidence": risk_score / 100,
            "reason": f"Failure rate: {failure_rate*100:.1f}% ({category})",
            "risk_score": risk_score,
            "method": "statistical",
            "category": category
        }
    
    def detect_anomalies(self, api_id, hours=24):
        """Detect anomalies using category-specific autoencoder"""
        if not self.use_ml:
            return []

        try:
            sequences, _, category = self._extract_time_series(api_id, hours=hours)
            if sequences is None:
                return []

            models = self._load_or_create_category_models(category)
            if "autoencoder" not in models or "scaler" not in models:
                return []

            # Scale the data
            n_samples, n_steps, n_features = sequences.shape
            sequences_reshaped = sequences.reshape(-1, n_features)
            
            try:
                sequences_scaled = models["scaler"].transform(sequences_reshaped)
            except Exception:
                return [] # Scaler not fitted
                
            sequences_scaled = sequences_scaled.reshape(n_samples, n_steps, n_features)

            # Get reconstruction loss
            reconstructions = models["autoencoder"].predict(sequences_scaled, verbose=0)
            mse = np.mean(np.square(sequences_scaled - reconstructions), axis=(1, 2))

            # Use pre-calculated threshold
            threshold = models.get("anomaly_threshold")
            if threshold is None:
                # Fallback: calculate threshold on the fly if not present
                threshold = np.percentile(mse, 95)

            # Find anomalies
            anomalous_indices = np.where(mse > threshold)[0]
            
            if len(anomalous_indices) == 0:
                return []

            # Get original logs for anomalous sequences
            time_threshold = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"
            logs = list(self.db.monitoring_logs.find({
                "api_id": api_id,
                "timestamp": {"$gte": time_threshold}
            }).sort("timestamp", 1))

            anomalies = []
            for i in anomalous_indices:
                # The anomaly is at the end of the sequence
                log_index = i + self.sequence_length
                if log_index < len(logs):
                    anomaly_log = logs[log_index]
                    anomaly_log["_id"] = str(anomaly_log["_id"])
                    anomaly_log["reconstruction_error"] = float(mse[i])
                    anomaly_log["type"] = "Reconstruction Error" # Add type for frontend
                    anomaly_log["description"] = f"High reconstruction error ({anomaly_log['reconstruction_error']:.2f}). "
                    if anomaly_log.get("error_message"):
                        anomaly_log["description"] += f"Original error: {anomaly_log['error_message']}"
                    anomalies.append(anomaly_log)
            
            return anomalies
        except Exception as e:
            print(f"[AI] Anomaly detection error: {e}")
            return []
    
    def generate_insights(self, api_id):
        """Generate insights"""
        try:
            print("[AI] Generating insights...")
            prediction = self.predict_failure(api_id)
            print(f"[AI] Prediction result: {prediction}")
            insights = []
            
            if prediction["will_fail"]:
                insights.append({
                    "type": "warning",
                    "title": f"⚠️ Failure Predicted ({prediction.get('category', 'Unknown')})",
                    "message": f"Category-aware model predicts failure (confidence: {prediction['confidence']*100:.0f}%)",
                    "details": prediction["reason"],
                    "action": "Review recent changes"
                })
            
            if self.use_ml:
                insights.append({
                    "type": "info",
                    "title": "🎯 Category-Aware AI Active",
                    "message": f"Using specialized model for {prediction.get('category', 'Unknown')}",
                    "details": f"Method: {prediction.get('method', 'unknown')}",
                    "action": "Model trained for this API category"
                })
            
            print(f"[AI] Generated insights list: {insights}")
            return insights
        except Exception as e:
            print(f"[AI] Insight generation error: {e}")
            return []
    
    def find_similar_incidents(self, current_issue, limit=5):
        """Find similar incidents using TF-IDF"""
        try:
            incidents = list(self.db.incident_reports.find())
            if not incidents:
                return []

            # Create corpus
            corpus = []
            for inc in incidents:
                text = f"{inc.get('title', '')} {inc.get('summary', '')} {inc.get('root_cause', '')}"
                corpus.append(text)

            # Vectorize
            vectorizer = TfidfVectorizer(stop_words='english', max_df=0.85, min_df=1)
            tfidf_matrix = vectorizer.fit_transform(corpus)
            current_issue_vector = vectorizer.transform([current_issue])

            # Calculate similarity
            cosine_similarities = cosine_similarity(current_issue_vector, tfidf_matrix).flatten()

            # Get top N similar incidents
            similar_indices = cosine_similarities.argsort()[::-1][:limit]

            results = []
            for i in similar_indices:
                if cosine_similarities[i] > 0.1:  # Similarity threshold
                    results.append({
                        "incident": incidents[i],
                        "similarity": float(cosine_similarities[i])
                    })
            
            return results
        except Exception as e:
            print(f"[AI] Similar incidents error: {e}")
            return []
