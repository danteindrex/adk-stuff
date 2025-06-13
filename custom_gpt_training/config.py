# Configuration file for GPT training
# GPT-2 Small architecture with custom modifications

# Model Configuration - GPT-2 Small size
GPT_CONFIG = {
    "vocab_size": 50257,        # Will be updated after BPE training
    "context_length": 2000,     # Custom context size as requested
    "emb_dim": 768,            # GPT-2 Small embedding dimension
    "n_heads": 12,             # GPT-2 Small attention heads
    "n_layers": 12,            # GPT-2 Small layers
    "drop_rate": 0.0,          # No dropout as requested
    "qkv_bias": False          # Query-Key-Value bias
}

# Training Configuration
TRAINING_CONFIG = {
    "learning_rate": 5e-4,
    "weight_decay": 0.1,
    "batch_size": 4,           # Adjust based on GPU memory
    "num_epochs": 10,
    "eval_freq": 100,          # Evaluate every N steps
    "eval_iter": 10,           # Number of batches for evaluation
    "warmup_steps": 1000,
    "max_lr": 6e-4,
    "min_lr": 6e-5,
    "gradient_clip": 1.0,
    "save_freq": 1000,         # Save checkpoint every N steps
}

# BPE Tokenizer Configuration
BPE_CONFIG = {
    "vocab_size": 50257,       # Target vocabulary size
    "special_tokens": ["<|endoftext|>", "<|pad|>", "<|unk|>"],
    "end_of_document_token": "<|endoftext|>",
}

# Dataset Configuration
DATASET_CONFIG = {
    "data_dir": "datasets",
    "train_split": 0.9,
    "val_split": 0.1,
    "max_length": 2000,        # Match context length
    "stride": 1000,            # Sliding window stride
}

# Fine-tuning Configuration with Unsloth
FINETUNING_CONFIG = {
    "use_unsloth": True,
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.1,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "learning_rate": 2e-4,
    "num_train_epochs": 3,
    "per_device_train_batch_size": 1,
    "gradient_accumulation_steps": 4,
    "warmup_steps": 10,
    "max_steps": 60,
    "logging_steps": 1,
    "save_steps": 10,
    "eval_steps": 10,
}

# Reinforcement Learning Configuration
RL_CONFIG = {
    # PPO (Proximal Policy Optimization) - Best for conversational models
    "ppo": {
        "learning_rate": 1.41e-5,
        "mini_batch_size": 1,
        "batch_size": 8,
        "ppo_epochs": 4,
        "gamma": 1.0,
        "gae_lambda": 0.95,
        "clip_range": 0.2,
        "clip_range_vf": None,
        "vf_coef": 0.1,
        "ent_coef": 0.0,
        "target_kl": 0.1,
        "max_grad_norm": 0.5,
    },
    
    # ORPO (Odds Ratio Preference Optimization) - Good for alignment
    "orpo": {
        "learning_rate": 8e-6,
        "beta": 0.1,
        "max_length": 1024,
        "max_prompt_length": 512,
        "max_completion_length": 512,
    },
    
    # RGPO (Reward-Guided Policy Optimization) - Custom implementation
    "rgpo": {
        "learning_rate": 1e-5,
        "reward_model_path": None,  # Path to reward model
        "kl_penalty": 0.2,
        "adaptive_kl": True,
        "target_kl": 0.1,
        "reward_clip": 5.0,
    }
}

# Recommended method for conversational model with tool calling
RECOMMENDED_RL_METHOD = "ppo"  # PPO is most stable and effective for conversational AI

# Tool Calling Configuration
TOOL_CALLING_CONFIG = {
    "enable_tool_calling": True,
    "tool_format": "function_calling",  # or "json_schema"
    "max_function_calls": 5,
    "function_timeout": 30,
    "special_tokens": {
        "function_call_start": "<|function_call|>",
        "function_call_end": "<|/function_call|>",
        "function_result_start": "<|function_result|>",
        "function_result_end": "<|/function_result|>",
    }
}

# Hardware Configuration
HARDWARE_CONFIG = {
    "device": "auto",  # auto-detect GPU/CPU
    "mixed_precision": "fp16",  # or "bf16" for newer GPUs
    "gradient_checkpointing": True,
    "dataloader_num_workers": 4,
    "pin_memory": True,
}

# Paths Configuration
PATHS = {
    "model_save_dir": "models",
    "tokenizer_save_dir": "tokenizers",
    "logs_dir": "logs",
    "checkpoints_dir": "checkpoints",
    "datasets_dir": "datasets",
}

# Logging Configuration
LOGGING_CONFIG = {
    "log_level": "INFO",
    "log_to_file": True,
    "log_file": "training.log",
    "wandb_project": "custom_gpt_training",
    "wandb_enabled": False,  # Set to True if you want to use Weights & Biases
}