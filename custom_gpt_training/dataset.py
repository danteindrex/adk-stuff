# Dataset handling for GPT training
# Handles loading and preprocessing of training data

import os
import json
import random
from typing import List, Tuple, Dict, Optional
import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np


class GPTDataset(Dataset):
    """Dataset class for GPT training."""
    
    def __init__(self, token_ids: List[int], max_length: int, stride: int):
        self.input_ids = []
        self.target_ids = []
        
        # Create sliding window chunks
        for i in range(0, len(token_ids) - max_length, stride):
            input_chunk = token_ids[i:i + max_length]
            target_chunk = token_ids[i + 1:i + max_length + 1]
            
            self.input_ids.append(torch.tensor(input_chunk, dtype=torch.long))
            self.target_ids.append(torch.tensor(target_chunk, dtype=torch.long))
    
    def __len__(self):
        return len(self.input_ids)
    
    def __getitem__(self, idx):
        return self.input_ids[idx], self.target_ids[idx]


class InstructionDataset(Dataset):
    """Dataset for instruction fine-tuning."""
    
    def __init__(self, data: List[Dict], tokenizer, max_length: int = 2000):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.encoded_texts = []
        
        for entry in data:
            # Format the instruction data
            formatted_text = self._format_instruction(entry)
            
            # Tokenize
            token_ids = tokenizer.encode(formatted_text)
            
            # Truncate if too long
            if len(token_ids) > max_length:
                token_ids = token_ids[:max_length]
            
            self.encoded_texts.append(token_ids)
    
    def _format_instruction(self, entry: Dict) -> str:
        """Format instruction data into a standard format."""
        instruction = entry.get('instruction', '')
        input_text = entry.get('input', '')
        output = entry.get('output', '')
        
        if input_text:
            formatted = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n{output}"
        else:
            formatted = f"### Instruction:\n{instruction}\n\n### Response:\n{output}"
        
        return formatted
    
    def __len__(self):
        return len(self.encoded_texts)
    
    def __getitem__(self, idx):
        return self.encoded_texts[idx]


class ConversationDataset(Dataset):
    """Dataset for conversational training with tool calling support."""
    
    def __init__(self, conversations: List[Dict], tokenizer, max_length: int = 2000):
        self.conversations = conversations
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.encoded_conversations = []
        
        for conv in conversations:
            formatted_conv = self._format_conversation(conv)
            token_ids = tokenizer.encode(formatted_conv)
            
            if len(token_ids) > max_length:
                token_ids = token_ids[:max_length]
            
            self.encoded_conversations.append(token_ids)
    
    def _format_conversation(self, conversation: Dict) -> str:
        """Format conversation data with tool calling support."""
        messages = conversation.get('messages', [])
        formatted_parts = []
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                formatted_parts.append(f"<|system|>\n{content}\n")
            elif role == 'user':
                formatted_parts.append(f"<|user|>\n{content}\n")
            elif role == 'assistant':
                # Check for tool calls
                tool_calls = message.get('tool_calls', [])
                if tool_calls:
                    formatted_parts.append(f"<|assistant|>\n")
                    for tool_call in tool_calls:
                        function_name = tool_call.get('function', {}).get('name', '')
                        function_args = tool_call.get('function', {}).get('arguments', '')
                        formatted_parts.append(f"<|function_call|>\n{function_name}({function_args})\n<|/function_call|>\n")
                    if content:
                        formatted_parts.append(f"{content}\n")
                else:
                    formatted_parts.append(f"<|assistant|>\n{content}\n")
            elif role == 'tool':
                tool_name = message.get('name', 'unknown')
                formatted_parts.append(f"<|function_result|>\n{tool_name}: {content}\n<|/function_result|>\n")
        
        return ''.join(formatted_parts)
    
    def __len__(self):
        return len(self.encoded_conversations)
    
    def __getitem__(self, idx):
        return self.encoded_conversations[idx]


def collate_fn(batch, pad_token_id: int = 0, max_length: Optional[int] = None):
    """Custom collate function for batching variable length sequences."""
    if isinstance(batch[0], tuple):
        # For (input, target) pairs
        inputs, targets = zip(*batch)
        
        # Pad sequences
        max_len = max(len(seq) for seq in inputs)
        if max_length is not None:
            max_len = min(max_len, max_length)
        
        padded_inputs = []
        padded_targets = []
        
        for inp, tgt in zip(inputs, targets):
            if len(inp) > max_len:
                inp = inp[:max_len]
                tgt = tgt[:max_len]
            
            pad_len = max_len - len(inp)
            padded_inp = torch.cat([inp, torch.full((pad_len,), pad_token_id, dtype=torch.long)])
            padded_tgt = torch.cat([tgt, torch.full((pad_len,), -100, dtype=torch.long)])  # -100 is ignored in loss
            
            padded_inputs.append(padded_inp)
            padded_targets.append(padded_tgt)
        
        return torch.stack(padded_inputs), torch.stack(padded_targets)
    
    else:
        # For single sequences
        max_len = max(len(seq) for seq in batch)
        if max_length is not None:
            max_len = min(max_len, max_length)
        
        padded_batch = []
        for seq in batch:
            if len(seq) > max_len:
                seq = seq[:max_len]
            
            pad_len = max_len - len(seq)
            padded_seq = torch.cat([torch.tensor(seq, dtype=torch.long), 
                                  torch.full((pad_len,), pad_token_id, dtype=torch.long)])
            padded_batch.append(padded_seq)
        
        return torch.stack(padded_batch)


def load_text_files(data_dir: str) -> List[str]:
    """Load all text files from a directory."""
    texts = []
    
    if not os.path.exists(data_dir):
        print(f"Warning: Directory {data_dir} does not exist")
        return texts
    
    for filename in os.listdir(data_dir):
        if filename.endswith(('.txt', '.md')):
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        texts.append(content)
                print(f"Loaded {filename}: {len(content)} characters")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    return texts


def load_json_files(data_dir: str) -> List[Dict]:
    """Load JSON files containing structured data."""
    data = []
    
    if not os.path.exists(data_dir):
        print(f"Warning: Directory {data_dir} does not exist")
        return data
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    
                    if isinstance(json_data, list):
                        data.extend(json_data)
                    elif isinstance(json_data, dict):
                        data.append(json_data)
                
                print(f"Loaded {filename}: {len(json_data) if isinstance(json_data, list) else 1} items")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    return data


def create_pretraining_dataloader(data_dir: str, tokenizer, config: Dict) -> Tuple[DataLoader, DataLoader]:
    """Create dataloaders for pretraining."""
    # Load text data
    texts = load_text_files(data_dir)
    
    if not texts:
        raise ValueError(f"No text files found in {data_dir}")
    
    # Tokenize all texts
    all_token_ids = []
    end_token_id = tokenizer.get_special_token_id("<|endoftext|>")
    
    for text in texts:
        token_ids = tokenizer.encode(text)
        if end_token_id is not None:
            token_ids.append(end_token_id)  # Add end token between documents
        all_token_ids.extend(token_ids)
    
    print(f"Total tokens: {len(all_token_ids):,}")
    
    # Split into train/val
    split_idx = int(len(all_token_ids) * config["train_split"])
    train_token_ids = all_token_ids[:split_idx]
    val_token_ids = all_token_ids[split_idx:]
    
    # Create datasets
    train_dataset = GPTDataset(
        train_token_ids, 
        config["max_length"], 
        config["stride"]
    )
    
    val_dataset = GPTDataset(
        val_token_ids, 
        config["max_length"], 
        config["stride"]
    )
    
    print(f"Train dataset size: {len(train_dataset)}")
    print(f"Val dataset size: {len(val_dataset)}")
    
    # Create dataloaders
    pad_token_id = tokenizer.get_special_token_id("<|pad|>") or 0
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.get("batch_size", 4),
        shuffle=True,
        drop_last=True,
        collate_fn=lambda batch: collate_fn(batch, pad_token_id, config["max_length"]),
        num_workers=config.get("num_workers", 0),
        pin_memory=config.get("pin_memory", False)
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=config.get("batch_size", 4),
        shuffle=False,
        drop_last=False,
        collate_fn=lambda batch: collate_fn(batch, pad_token_id, config["max_length"]),
        num_workers=config.get("num_workers", 0),
        pin_memory=config.get("pin_memory", False)
    )
    
    return train_loader, val_loader


def create_instruction_dataloader(data_dir: str, tokenizer, config: Dict) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """Create dataloaders for instruction fine-tuning."""
    # Load JSON data
    data = load_json_files(data_dir)
    
    if not data:
        raise ValueError(f"No JSON files found in {data_dir}")
    
    # Shuffle data
    random.shuffle(data)
    
    # Split data
    train_size = int(len(data) * 0.8)
    val_size = int(len(data) * 0.1)
    
    train_data = data[:train_size]
    val_data = data[train_size:train_size + val_size]
    test_data = data[train_size + val_size:]
    
    print(f"Train data: {len(train_data)}")
    print(f"Val data: {len(val_data)}")
    print(f"Test data: {len(test_data)}")
    
    # Create datasets
    train_dataset = InstructionDataset(train_data, tokenizer, config["max_length"])
    val_dataset = InstructionDataset(val_data, tokenizer, config["max_length"])
    test_dataset = InstructionDataset(test_data, tokenizer, config["max_length"])
    
    # Create dataloaders
    pad_token_id = tokenizer.get_special_token_id("<|pad|>") or 0
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.get("batch_size", 4),
        shuffle=True,
        drop_last=True,
        collate_fn=lambda batch: collate_fn(batch, pad_token_id, config["max_length"]),
        num_workers=config.get("num_workers", 0)
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=config.get("batch_size", 4),
        shuffle=False,
        drop_last=False,
        collate_fn=lambda batch: collate_fn(batch, pad_token_id, config["max_length"]),
        num_workers=config.get("num_workers", 0)
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=config.get("batch_size", 4),
        shuffle=False,
        drop_last=False,
        collate_fn=lambda batch: collate_fn(batch, pad_token_id, config["max_length"]),
        num_workers=config.get("num_workers", 0)
    )
    
    return train_loader, val_loader, test_loader


def create_conversation_dataloader(data_dir: str, tokenizer, config: Dict) -> Tuple[DataLoader, DataLoader]:
    """Create dataloaders for conversational training."""
    # Load conversation data
    conversations = load_json_files(data_dir)
    
    if not conversations:
        raise ValueError(f"No conversation files found in {data_dir}")
    
    # Filter conversations that have the expected format
    valid_conversations = []
    for conv in conversations:
        if 'messages' in conv and isinstance(conv['messages'], list):
            valid_conversations.append(conv)
    
    print(f"Valid conversations: {len(valid_conversations)}")
    
    # Shuffle and split
    random.shuffle(valid_conversations)
    split_idx = int(len(valid_conversations) * 0.9)
    
    train_conversations = valid_conversations[:split_idx]
    val_conversations = valid_conversations[split_idx:]
    
    # Create datasets
    train_dataset = ConversationDataset(train_conversations, tokenizer, config["max_length"])
    val_dataset = ConversationDataset(val_conversations, tokenizer, config["max_length"])
    
    # Create dataloaders
    pad_token_id = tokenizer.get_special_token_id("<|pad|>") or 0
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.get("batch_size", 4),
        shuffle=True,
        drop_last=True,
        collate_fn=lambda batch: collate_fn(batch, pad_token_id, config["max_length"]),
        num_workers=config.get("num_workers", 0)
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=config.get("batch_size", 4),
        shuffle=False,
        drop_last=False,
        collate_fn=lambda batch: collate_fn(batch, pad_token_id, config["max_length"]),
        num_workers=config.get("num_workers", 0)
    )
    
    return train_loader, val_loader


if __name__ == "__main__":
    # Test dataset creation
    from config import DATASET_CONFIG, PATHS
    from tokenizer import BPETokenizer
    
    # Create test data
    os.makedirs(DATASET_CONFIG["data_dir"], exist_ok=True)
    
    test_file = os.path.join(DATASET_CONFIG["data_dir"], "test.txt")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("This is a test document. " * 1000)
    
    # Create tokenizer
    tokenizer = BPETokenizer()
    tokenizer.vocab = {i: str(i) for i in range(1000)}
    tokenizer.inverse_vocab = {str(i): i for i in range(1000)}
    tokenizer.special_tokens = {"<|endoftext|>": 999, "<|pad|>": 998}
    
    # Test dataloader creation
    try:
        train_loader, val_loader = create_pretraining_dataloader(
            DATASET_CONFIG["data_dir"], 
            tokenizer, 
            DATASET_CONFIG
        )
        print(f"Created dataloaders successfully")
        print(f"Train batches: {len(train_loader)}")
        print(f"Val batches: {len(val_loader)}")
        
        # Test a batch
        batch = next(iter(train_loader))
        print(f"Batch shape: {batch[0].shape}, {batch[1].shape}")
        
    except Exception as e:
        print(f"Error creating dataloaders: {e}")