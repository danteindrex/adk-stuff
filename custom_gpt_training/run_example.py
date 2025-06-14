# Example script to demonstrate the training pipeline
# This creates sample data and runs a quick training example

import os
import json
import torch
from config import *
from main import main as run_main


def create_sample_datasets():
    """Create sample datasets for demonstration."""
    print("Creating sample datasets...")
    
    # Create datasets directory
    os.makedirs(DATASET_CONFIG["data_dir"], exist_ok=True)
    
    # Sample text data for pretraining
    sample_texts = [
        """
        Artificial intelligence is transforming the world. Machine learning algorithms can learn patterns from data.
        Deep learning uses neural networks with multiple layers. Natural language processing helps computers understand text.
        Large language models like GPT can generate human-like text. Training these models requires massive datasets.
        """,
        """
        The transformer architecture revolutionized natural language processing. Attention mechanisms allow models to focus on relevant parts of input.
        Self-attention computes relationships between all positions in a sequence. Multi-head attention processes information in parallel.
        Positional encoding helps models understand sequence order. Layer normalization stabilizes training.
        """,
        """
        Python is a popular programming language for machine learning. Libraries like PyTorch and TensorFlow make deep learning accessible.
        Data preprocessing is crucial for model performance. Feature engineering can improve model accuracy.
        Cross-validation helps evaluate model generalization. Hyperparameter tuning optimizes model performance.
        """,
        """
        Reinforcement learning trains agents through interaction with environments. Policy gradient methods optimize action selection.
        Q-learning estimates action values. Actor-critic methods combine value and policy learning.
        Exploration vs exploitation is a key challenge. Reward shaping can guide learning.
        """,
        """
        Computer vision processes and analyzes visual information. Convolutional neural networks excel at image recognition.
        Object detection identifies and locates objects in images. Semantic segmentation classifies each pixel.
        Transfer learning leverages pre-trained models. Data augmentation increases training data diversity.
        """
    ]
    
    # Save text files
    for i, text in enumerate(sample_texts):
        filename = os.path.join(DATASET_CONFIG["data_dir"], f"sample_text_{i+1}.txt")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text.strip() * 20)  # Repeat for more training data
    
    # Sample instruction data for fine-tuning
    instruction_data = [
        {
            "instruction": "Explain what machine learning is",
            "input": "",
            "output": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed for every task."
        },
        {
            "instruction": "What is the difference between supervised and unsupervised learning?",
            "input": "",
            "output": "Supervised learning uses labeled data to train models, while unsupervised learning finds patterns in data without labels. Supervised learning predicts outcomes, unsupervised learning discovers hidden structures."
        },
        {
            "instruction": "Describe neural networks",
            "input": "",
            "output": "Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons) organized in layers that process information and learn patterns from data."
        },
        {
            "instruction": "How do transformers work?",
            "input": "",
            "output": "Transformers use self-attention mechanisms to process sequences in parallel. They can focus on different parts of the input simultaneously, making them very effective for natural language processing tasks."
        },
        {
            "instruction": "What is reinforcement learning?",
            "input": "",
            "output": "Reinforcement learning is a type of machine learning where an agent learns to make decisions by interacting with an environment and receiving rewards or penalties for its actions."
        }
    ] * 10  # Repeat for more training data
    
    instruction_file = os.path.join(DATASET_CONFIG["data_dir"], "instruction_data.json")
    with open(instruction_file, 'w', encoding='utf-8') as f:
        json.dump(instruction_data, f, indent=2)
    
    # Sample conversation data
    conversation_data = [
        {
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant that explains technical concepts clearly."},
                {"role": "user", "content": "What is deep learning?"},
                {"role": "assistant", "content": "Deep learning is a subset of machine learning that uses neural networks with multiple layers (hence 'deep') to model and understand complex patterns in data. It's particularly effective for tasks like image recognition, natural language processing, and speech recognition."}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": "Can you help me understand attention mechanisms?"},
                {"role": "assistant", "content": "Attention mechanisms allow neural networks to focus on specific parts of the input when making predictions. Think of it like highlighting important words in a sentence - the model learns to 'pay attention' to the most relevant information for the current task."}
            ]
        },
        {
            "messages": [
                {"role": "user", "content": "What's the weather like today?"},
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "get_weather",
                                "arguments": "{\"location\": \"current\"}"
                            }
                        }
                    ]
                },
                {"role": "tool", "name": "get_weather", "content": "Sunny, 75°F, light breeze"},
                {"role": "assistant", "content": "The weather today is sunny with a temperature of 75°F and a light breeze. Perfect weather for outdoor activities!"}
            ]
        }
    ] * 5  # Repeat for more training data
    
    conversation_file = os.path.join(DATASET_CONFIG["data_dir"], "conversation_data.json")
    with open(conversation_file, 'w', encoding='utf-8') as f:
        json.dump(conversation_data, f, indent=2)
    
    print(f"Sample datasets created in {DATASET_CONFIG['data_dir']}")
    print(f"- Text files: {len(sample_texts)}")
    print(f"- Instruction data: {len(instruction_data)} examples")
    print(f"- Conversation data: {len(conversation_data)} examples")


def run_quick_example():
    """Run a quick training example with small settings."""
    print("=== Quick Training Example ===")
    print("This will run a minimal training example to test the pipeline.")
    print()
    
    # Modify configs for quick testing
    global GPT_CONFIG, TRAINING_CONFIG, BPE_CONFIG
    
    # Smaller model for quick testing
    GPT_CONFIG = GPT_CONFIG.copy()
    GPT_CONFIG.update({
        "context_length": 256,  # Smaller context
        "emb_dim": 128,        # Smaller embedding
        "n_heads": 4,          # Fewer heads
        "n_layers": 2,         # Fewer layers
    })
    
    # Shorter training for quick testing
    TRAINING_CONFIG = TRAINING_CONFIG.copy()
    TRAINING_CONFIG.update({
        "num_epochs": 1,       # Just 1 epoch
        "batch_size": 2,       # Small batch
        "eval_freq": 10,       # Evaluate more frequently
        "save_freq": 50,       # Save less frequently
    })
    
    # Smaller tokenizer for quick testing
    BPE_CONFIG = BPE_CONFIG.copy()
    BPE_CONFIG.update({
        "vocab_size": 1000,    # Much smaller vocab
    })
    
    print("Modified configurations for quick testing:")
    print(f"- Model: {GPT_CONFIG['emb_dim']}d, {GPT_CONFIG['n_layers']} layers")
    print(f"- Context: {GPT_CONFIG['context_length']} tokens")
    print(f"- Vocab: {BPE_CONFIG['vocab_size']} tokens")
    print(f"- Training: {TRAINING_CONFIG['num_epochs']} epoch")
    print()
    
    # Create sample data
    create_sample_datasets()
    
    # Run training
    print("Starting quick training example...")
    try:
        # Import and run main with modified configs
        import sys
        sys.argv = ['run_example.py', '--stage', 'all']
        run_main()
        print("Quick example completed successfully!")
    except Exception as e:
        print(f"Quick example failed: {e}")
        print("This is normal for a demonstration - you may need to adjust settings for your hardware.")


def print_next_steps():
    """Print information about next steps."""
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    
    print("\n1. REVIEW THE GENERATED FILES:")
    print("   - Check models/ for saved models")
    print("   - Check tokenizers/ for the trained tokenizer")
    print("   - Check logs/ for training logs")
    
    print("\n2. CUSTOMIZE FOR YOUR USE CASE:")
    print("   - Add your own datasets to datasets/")
    print("   - Modify config.py for your requirements")
    print("   - Adjust model size based on your hardware")
    
    print("\n3. FULL TRAINING:")
    print("   - Run: python main.py --stage all")
    print("   - Monitor training progress in logs/")
    print("   - Use larger datasets for better results")
    
    print("\n4. FINE-TUNING:")
    print("   - Prepare instruction/conversation data")
    print("   - Install Unsloth: pip install unsloth")
    print("   - Run: python finetune_unsloth.py")
    
    print("\n5. REINFORCEMENT LEARNING:")
    print("   - Use PPO for conversational models (recommended)")
    print("   - Prepare reward models for tool calling")
    print("   - Install TRL: pip install trl")
    
    print("\n6. EVALUATION:")
    print("   - Test generation quality")
    print("   - Evaluate on downstream tasks")
    print("   - Compare with baseline models")
    
    print("\n" + "="*60)
    print("HARDWARE RECOMMENDATIONS")
    print("="*60)
    
    print("\nFor this example (small model):")
    print("   - GPU: 4GB+ (GTX 1660, RTX 3060)")
    print("   - RAM: 8GB+")
    print("   - Storage: 2GB+")
    
    print("\nFor full GPT-2 Small training:")
    print("   - GPU: 8GB+ (RTX 3070, RTX 4060)")
    print("   - RAM: 16GB+")
    print("   - Storage: 10GB+")
    
    print("\nFor production training:")
    print("   - GPU: 16GB+ (RTX 4080, A100)")
    print("   - RAM: 32GB+")
    print("   - Storage: 100GB+")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run training example")
    parser.add_argument("--create-data-only", action="store_true", 
                       help="Only create sample datasets")
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick training example")
    
    args = parser.parse_args()
    
    if args.create_data_only:
        create_sample_datasets()
    elif args.quick:
        run_quick_example()
        print_next_steps()
    else:
        print("GPT Training Pipeline Example")
        print("=============================")
        print()
        print("This script demonstrates the complete GPT training pipeline.")
        print()
        print("Options:")
        print("  --create-data-only    Create sample datasets only")
        print("  --quick              Run quick training example")
        print()
        print("For full training, run: python main.py")
        print()
        
        # Show current configuration
        print("Current Configuration:")
        print(f"  Model: GPT-2 Small ({GPT_CONFIG['emb_dim']}d, {GPT_CONFIG['n_layers']} layers)")
        print(f"  Context: {GPT_CONFIG['context_length']} tokens")
        print(f"  Vocab: {BPE_CONFIG['vocab_size']} tokens")
        print(f"  No dropout: {GPT_CONFIG['drop_rate'] == 0.0}")
        print()
        
        print("Features:")
        print("  ✓ BPE tokenizer training")
        print("  ✓ GPT-2 Small architecture")
        print("  ✓ Custom context length (2000)")
        print("  ✓ No dropout for max capacity")
        print("  ✓ Unsloth fine-tuning support")
        print("  ✓ PPO/ORPO/RGPO reinforcement learning")
        print("  ✓ Tool calling capabilities")
        print()
        
        choice = input("Run quick example? (y/n): ").lower().strip()
        if choice == 'y':
            run_quick_example()
            print_next_steps()
        else:
            print("To get started:")
            print("1. python run_example.py --create-data-only")
            print("2. python run_example.py --quick")
            print("3. python main.py --stage all")