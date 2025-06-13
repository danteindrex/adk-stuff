# Main training script for GPT model
# Orchestrates the entire training pipeline

import os
import sys
import argparse
import json
import time
from typing import Dict, List, Optional

import torch
import numpy as np
import random

# Local imports
from config import (
    GPT_CONFIG, TRAINING_CONFIG, BPE_CONFIG, DATASET_CONFIG, 
    FINETUNING_CONFIG, RL_CONFIG, RECOMMENDED_RL_METHOD, PATHS
)
from model import create_model
from tokenizer import BPETokenizer, train_tokenizer
from dataset import create_pretraining_dataloader, create_instruction_dataloader
from trainer import GPTTrainer


def set_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def create_directories():
    """Create necessary directories."""
    for path in PATHS.values():
        os.makedirs(path, exist_ok=True)
    
    # Create datasets directory if it doesn't exist
    os.makedirs(DATASET_CONFIG["data_dir"], exist_ok=True)


def check_datasets():
    """Check if datasets exist and create sample data if needed."""
    data_dir = DATASET_CONFIG["data_dir"]
    
    # Check for text files
    text_files = [f for f in os.listdir(data_dir) if f.endswith(('.txt', '.md'))]
    
    if not text_files:
        print(f"No text files found in {data_dir}")
        print("Creating sample dataset...")
        
        # Create sample text data
        sample_text = """
        The quick brown fox jumps over the lazy dog. This is a sample text for training a language model.
        Language models are trained on large amounts of text data to learn patterns and generate coherent text.
        
        Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.
        Deep learning uses neural networks with multiple layers to model complex patterns in data.
        
        Natural language processing involves teaching computers to understand and generate human language.
        Transformers are a type of neural network architecture that has revolutionized NLP tasks.
        
        GPT models use the transformer architecture to generate text by predicting the next token in a sequence.
        Training these models requires large datasets and significant computational resources.
        """ * 100  # Repeat to create more training data
        
        sample_file = os.path.join(data_dir, "sample_training_data.txt")
        with open(sample_file, 'w', encoding='utf-8') as f:
            f.write(sample_text)
        
        print(f"Created sample dataset: {sample_file}")
        return True
    
    print(f"Found {len(text_files)} text files in {data_dir}")
    return True


def train_bpe_tokenizer():
    """Train or load BPE tokenizer."""
    tokenizer_dir = PATHS["tokenizer_save_dir"]
    
    # Check if tokenizer already exists
    if os.path.exists(os.path.join(tokenizer_dir, "tokenizer_config.json")):
        print("Loading existing tokenizer...")
        tokenizer = BPETokenizer()
        tokenizer.load(tokenizer_dir)
        return tokenizer
    
    print("Training new BPE tokenizer...")
    tokenizer = train_tokenizer(
        data_dir=DATASET_CONFIG["data_dir"],
        save_dir=tokenizer_dir,
        vocab_size=BPE_CONFIG["vocab_size"],
        special_tokens=BPE_CONFIG["special_tokens"]
    )
    
    return tokenizer


def pretrain_model(tokenizer: BPETokenizer):
    """Pretrain the GPT model."""
    print("=== Starting GPT Pretraining ===")
    
    # Update config with actual vocab size
    config = GPT_CONFIG.copy()
    config["vocab_size"] = tokenizer.get_vocab_size()
    
    print(f"Model configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    # Create model
    model = create_model(config)
    print(f"Created model with {model.get_num_params():,} parameters")
    
    # Create dataloaders
    print("Creating dataloaders...")
    train_loader, val_loader = create_pretraining_dataloader(
        data_dir=DATASET_CONFIG["data_dir"],
        tokenizer=tokenizer,
        config={
            **DATASET_CONFIG,
            "batch_size": TRAINING_CONFIG["batch_size"],
            "num_workers": 0,
            "pin_memory": False
        }
    )
    
    # Create trainer
    trainer = GPTTrainer(model, tokenizer, TRAINING_CONFIG)
    
    # Train model
    save_dir = PATHS["model_save_dir"]
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=TRAINING_CONFIG["num_epochs"],
        save_dir=save_dir
    )
    
    print("=== Pretraining Completed ===")
    
    # Save final model
    final_model_path = os.path.join(save_dir, "final_model.pt")
    torch.save({
        "model_state_dict": model.state_dict(),
        "config": config,
        "tokenizer_path": PATHS["tokenizer_save_dir"],
        "training_history": history
    }, final_model_path)
    
    print(f"Final model saved to: {final_model_path}")
    
    # Test generation
    print("\n=== Testing Text Generation ===")
    test_prompts = [
        "The future of artificial intelligence",
        "Machine learning is",
        "Natural language processing"
    ]
    
    for prompt in test_prompts:
        try:
            generated = trainer.generate_text(
                prompt=prompt,
                max_new_tokens=50,
                temperature=0.8,
                top_k=50
            )
            print(f"Prompt: {prompt}")
            print(f"Generated: {generated}")
            print("-" * 50)
        except Exception as e:
            print(f"Generation failed for '{prompt}': {e}")
    
    return final_model_path


def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(description="GPT Training Pipeline")
    parser.add_argument("--stage", choices=["tokenizer", "pretrain", "finetune", "all"], 
                       default="all", help="Training stage to run")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--device", type=str, default="auto", help="Device to use")
    parser.add_argument("--skip_pretrain", action="store_true", help="Skip pretraining")
    
    args = parser.parse_args()
    
    print("=== GPT Training Pipeline ===")
    print(f"Stage: {args.stage}")
    print(f"Device: {args.device}")
    print(f"Seed: {args.seed}")
    print()
    
    # Set seed
    set_seed(args.seed)
    
    # Create directories
    create_directories()
    
    # Check datasets
    if not check_datasets():
        print("Dataset check failed. Please add text files to the datasets directory.")
        return
    
    # Stage 1: Train tokenizer
    if args.stage in ["tokenizer", "all"]:
        print("Stage 1: Training BPE Tokenizer")
        tokenizer = train_bpe_tokenizer()
        print(f"Tokenizer vocabulary size: {tokenizer.get_vocab_size()}")
        print()
    else:
        # Load existing tokenizer
        tokenizer = BPETokenizer()
        tokenizer.load(PATHS["tokenizer_save_dir"])
    
    # Stage 2: Pretrain model
    if args.stage in ["pretrain", "all"] and not args.skip_pretrain:
        print("Stage 2: Pretraining GPT Model")
        model_path = pretrain_model(tokenizer)
        print()
    else:
        print("Skipping pretraining stage")
        model_path = None
    
    # Stage 3: Fine-tuning information
    if args.stage in ["finetune", "all"]:
        print("Stage 3: Fine-tuning Information")
        print("For fine-tuning with Unsloth and reinforcement learning:")
        print(f"1. Run: python finetune_unsloth.py")
        print(f"2. Recommended RL method: {RECOMMENDED_RL_METHOD}")
        print(f"3. Make sure to install: pip install unsloth trl peft")
        print()
        
        print("Fine-tuning configuration:")
        print("- Instruction fine-tuning with LoRA")
        print("- PPO for conversational alignment (recommended)")
        print("- ORPO for preference optimization")
        print("- RGPO for reward-guided optimization")
        print()
        
        print("For tool calling capabilities:")
        print("- Prepare conversation data with function calls")
        print("- Use special tokens for function calls and results")
        print("- Train with PPO using a reward model that evaluates tool usage")
        print()
    
    print("=== Training Pipeline Complete ===")
    
    # Print summary
    print("\nSummary:")
    print(f"- Tokenizer: {PATHS['tokenizer_save_dir']}")
    if model_path:
        print(f"- Pretrained model: {model_path}")
    print(f"- Logs: {PATHS['logs_dir']}")
    print(f"- Checkpoints: {PATHS['checkpoints_dir']}")
    
    print("\nNext steps:")
    print("1. Review the generated model and logs")
    print("2. Prepare instruction/conversation data for fine-tuning")
    print("3. Run fine-tuning with: python finetune_unsloth.py")
    print("4. Evaluate the model on your specific tasks")


if __name__ == "__main__":
    main()