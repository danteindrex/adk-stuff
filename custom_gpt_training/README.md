# Custom GPT Training Pipeline

A complete implementation for training GPT-style models from scratch with the following specifications:

- **Architecture**: GPT-2 Small (768 dim, 12 layers, 12 heads)
- **Context Size**: 2000 tokens
- **No Dropout**: For maximum model capacity
- **BPE Tokenizer**: Trained from scratch on your data
- **Fine-tuning**: Unsloth integration with LoRA
- **Reinforcement Learning**: PPO, ORPO, and RGPO support
- **Tool Calling**: Conversational AI with function calling capabilities

## Features

### 🚀 **Pretraining**
- GPT-2 Small architecture (124M parameters)
- Custom context length of 2000 tokens
- Byte Pair Encoding (BPE) tokenizer training
- Efficient training with mixed precision
- Automatic dataset loading from `datasets/` folder
- End-of-document token handling

### 🎯 **Fine-tuning**
- **Unsloth** integration for 2x faster training
- **LoRA** (Low-Rank Adaptation) for parameter-efficient fine-tuning
- Support for instruction following, conversations, and tool calling
- Multiple data formats (instruction, conversation, tool calling)

### 🏆 **Reinforcement Learning**
- **PPO** (Proximal Policy Optimization) - **Recommended for conversational models**
- **ORPO** (Odds Ratio Preference Optimization) - For alignment
- **RGPO** (Reward-Guided Policy Optimization) - Custom implementation
- Tool calling reward modeling

## Quick Start

### 1. Installation

```bash
# Clone or download the files
cd custom_gpt_training

# Install dependencies
pip install -r requirements.txt

# Optional: Install Unsloth for efficient fine-tuning
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# Optional: Install TRL for reinforcement learning
pip install trl
```

### 2. Prepare Your Data

Create a `datasets/` folder and add your text files:

```
datasets/
├── document1.txt
├── document2.txt
├── conversation_data.json
└── instruction_data.json
```

**Text files** (`.txt`, `.md`): Raw text for pretraining
**JSON files**: Structured data for fine-tuning

#### Instruction Data Format:
```json
[
  {
    "instruction": "Explain machine learning",
    "input": "",
    "output": "Machine learning is a subset of AI..."
  }
]
```

#### Conversation Data Format:
```json
[
  {
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"},
      {"role": "assistant", "content": "Hi! How can I help you?"}
    ]
  }
]
```

#### Tool Calling Data Format:
```json
[
  {
    "messages": [
      {"role": "user", "content": "What's the weather like?"},
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
      {"role": "tool", "name": "get_weather", "content": "Sunny, 72°F"},
      {"role": "assistant", "content": "It's sunny and 72°F today!"}
    ]
  }
]
```

### 3. Run Training

#### Full Pipeline:
```bash
python main.py --stage all
```

#### Individual Stages:
```bash
# Train tokenizer only
python main.py --stage tokenizer

# Pretrain model only
python main.py --stage pretrain

# Fine-tuning info
python main.py --stage finetune
```

#### Fine-tuning with Unsloth:
```bash
python finetune_unsloth.py
```

### 4. Configuration

Edit `config.py` to customize:

- **Model size**: Change `emb_dim`, `n_layers`, `n_heads`
- **Context length**: Modify `context_length`
- **Training parameters**: Adjust learning rates, batch sizes
- **RL methods**: Configure PPO, ORPO, RGPO settings

## Architecture Details

### Model Configuration (GPT-2 Small)
```python
GPT_CONFIG = {
    "vocab_size": 50257,        # Updated after BPE training
    "context_length": 2000,     # Custom context size
    "emb_dim": 768,            # Embedding dimension
    "n_heads": 12,             # Attention heads
    "n_layers": 12,            # Transformer layers
    "drop_rate": 0.0,          # No dropout
    "qkv_bias": False          # No bias in attention
}
```

### Training Features
- **Mixed Precision**: FP16/BF16 support
- **Gradient Checkpointing**: Memory efficient training
- **Learning Rate Scheduling**: Warmup + cosine decay
- **Gradient Clipping**: Stable training
- **Automatic Evaluation**: Regular validation checks

## File Structure

```
custom_gpt_training/
├── config.py              # Configuration settings
├── model.py               # GPT model implementation
├── tokenizer.py           # BPE tokenizer implementation
├── dataset.py             # Dataset handling
├── trainer.py             # Training utilities
├── finetune_unsloth.py    # Unsloth fine-tuning
├── main.py                # Main training script
├── requirements.txt       # Dependencies
└── README.md             # This file

# Generated during training:
├── datasets/              # Your training data
├── models/               # Saved models
├── tokenizers/           # Trained tokenizers
├── logs/                 # Training logs
└── checkpoints/          # Training checkpoints
```

## Reinforcement Learning Methods

### PPO (Recommended for Conversational AI)
- **Best for**: General conversation, tool calling
- **Stability**: High
- **Implementation**: Full TRL integration
- **Use case**: Chat models, assistants

### ORPO (Preference Optimization)
- **Best for**: Alignment, safety
- **Stability**: Medium
- **Implementation**: Custom implementation
- **Use case**: Preference learning, safety alignment

### RGPO (Reward-Guided)
- **Best for**: Task-specific optimization
- **Stability**: Medium
- **Implementation**: Custom implementation
- **Use case**: Specific reward functions

## Tool Calling Support

The model supports function calling with special tokens:

```
<|function_call|>
function_name(arguments)
<|/function_call|>

<|function_result|>
function_name: result
<|/function_result|>
```

### Training for Tool Calling:
1. Prepare conversation data with tool calls
2. Use PPO with a reward model that evaluates:
   - Correct function selection
   - Proper argument formatting
   - Appropriate response generation

## Performance Tips

### Memory Optimization:
- Use gradient checkpointing
- Enable mixed precision (FP16/BF16)
- Reduce batch size if OOM
- Use Unsloth for 2x speedup

### Training Efficiency:
- Start with smaller vocab size for testing
- Use learning rate scheduling
- Monitor validation loss for early stopping
- Save checkpoints frequently

### Hardware Requirements:
- **Minimum**: 8GB GPU (RTX 3070/4060)
- **Recommended**: 16GB+ GPU (RTX 4080/A100)
- **CPU**: 16GB+ RAM for data loading

## Troubleshooting

### Common Issues:

1. **Out of Memory**:
   - Reduce batch size
   - Enable gradient checkpointing
   - Use smaller model size

2. **Slow Training**:
   - Install Unsloth
   - Use mixed precision
   - Increase batch size (if memory allows)

3. **Poor Generation Quality**:
   - Check tokenizer training
   - Increase training steps
   - Adjust temperature/top_k

4. **Import Errors**:
   - Install missing packages
   - Check CUDA compatibility
   - Use virtual environment

### Getting Help:

1. Check the logs in `logs/training.log`
2. Verify dataset format
3. Test with smaller data first
4. Monitor GPU memory usage

## Advanced Usage

### Custom Tokenizer:
```python
from tokenizer import BPETokenizer

tokenizer = BPETokenizer()
tokenizer.train(texts, vocab_size=30000)
tokenizer.save("my_tokenizer")
```

### Custom Model Size:
```python
# Modify config.py
GPT_CONFIG = {
    "emb_dim": 1024,    # Larger model
    "n_layers": 24,     # More layers
    "n_heads": 16,      # More heads
    # ...
}
```

### Custom Training Loop:
```python
from trainer import GPTTrainer

trainer = GPTTrainer(model, tokenizer, config)
history = trainer.train(train_loader, val_loader, epochs=10, save_dir="models")
```

## License

This implementation is based on the "Build a Large Language Model From Scratch" book and follows the same Apache 2.0 license.

## Citation

If you use this code, please cite:

```bibtex
@book{build-llms-from-scratch-book,
  author       = {Sebastian Raschka},
  title        = {Build A Large Language Model (From Scratch)},
  publisher    = {Manning},
  year         = {2024},
  isbn         = {978-1633437166}
}
```