# BPE Tokenizer Implementation
# Custom BPE tokenizer for training from scratch

import json
import os
import re
from collections import Counter, defaultdict
from typing import List, Dict, Set, Optional, Tuple
import pickle


class BPETokenizer:
    """Byte Pair Encoding tokenizer implementation."""
    
    def __init__(self):
        self.vocab = {}  # token_id -> token_str
        self.inverse_vocab = {}  # token_str -> token_id
        self.bpe_merges = {}  # (token1, token2) -> merged_token_id
        self.bpe_ranks = {}  # (token1, token2) -> rank (for GPT-2 style)
        self.special_tokens = {}
        self.pat = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+""")
        
    def train(self, texts: List[str], vocab_size: int, special_tokens: List[str] = None):
        """Train the BPE tokenizer on the given texts."""
        if special_tokens is None:
            special_tokens = ["<|endoftext|>", "<|pad|>", "<|unk|>"]
            
        print(f"Training BPE tokenizer with vocab size {vocab_size}")
        
        # Initialize vocabulary with byte-level tokens (0-255)
        self.vocab = {i: bytes([i]).decode('latin1') for i in range(256)}
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}
        
        # Add special tokens
        for token in special_tokens:
            if token not in self.inverse_vocab:
                token_id = len(self.vocab)
                self.vocab[token_id] = token
                self.inverse_vocab[token] = token_id
                self.special_tokens[token] = token_id
        
        # Tokenize all texts into bytes
        all_tokens = []
        for text in texts:
            # Add end of document token
            text_with_end = text + special_tokens[0] if special_tokens else text
            byte_tokens = list(text_with_end.encode('utf-8'))
            all_tokens.extend(byte_tokens)
        
        print(f"Total tokens before BPE: {len(all_tokens)}")
        
        # Convert to token IDs
        token_ids = [self.inverse_vocab[bytes([b]).decode('latin1')] for b in all_tokens]
        
        # BPE training loop
        target_merges = vocab_size - len(self.vocab)
        print(f"Performing {target_merges} merges...")
        
        for merge_idx in range(target_merges):
            if merge_idx % 1000 == 0:
                print(f"Merge {merge_idx}/{target_merges}")
                
            # Count all adjacent pairs
            pairs = Counter(zip(token_ids, token_ids[1:]))
            
            if not pairs:
                print("No more pairs to merge")
                break
                
            # Find most frequent pair
            most_frequent_pair = pairs.most_common(1)[0][0]
            
            # Create new token ID
            new_token_id = len(self.vocab)
            
            # Record the merge
            self.bpe_merges[most_frequent_pair] = new_token_id
            
            # Create the merged token string
            token1_str = self.vocab[most_frequent_pair[0]]
            token2_str = self.vocab[most_frequent_pair[1]]
            merged_token_str = token1_str + token2_str
            
            # Add to vocabulary
            self.vocab[new_token_id] = merged_token_str
            self.inverse_vocab[merged_token_str] = new_token_id
            
            # Replace all occurrences of the pair in token_ids
            new_token_ids = []
            i = 0
            while i < len(token_ids):
                if (i < len(token_ids) - 1 and 
                    token_ids[i] == most_frequent_pair[0] and 
                    token_ids[i + 1] == most_frequent_pair[1]):
                    new_token_ids.append(new_token_id)
                    i += 2
                else:
                    new_token_ids.append(token_ids[i])
                    i += 1
            
            token_ids = new_token_ids
            
        print(f"Training complete. Final vocab size: {len(self.vocab)}")
        print(f"Compression ratio: {len(all_tokens) / len(token_ids):.2f}x")
        
    def encode(self, text: str, allowed_special: Set[str] = None) -> List[int]:
        """Encode text into token IDs."""
        if allowed_special is None:
            allowed_special = set(self.special_tokens.keys())
            
        # Handle special tokens
        special_pattern = None
        if allowed_special:
            special_pattern = '|'.join(re.escape(token) for token in sorted(allowed_special, key=len, reverse=True))
        
        token_ids = []
        
        if special_pattern:
            # Split text by special tokens
            parts = re.split(f'({special_pattern})', text)
            for part in parts:
                if part in allowed_special:
                    token_ids.append(self.special_tokens[part])
                elif part:
                    token_ids.extend(self._encode_chunk(part))
        else:
            token_ids = self._encode_chunk(text)
            
        return token_ids
    
    def _encode_chunk(self, text: str) -> List[int]:
        """Encode a chunk of text without special tokens."""
        # Convert to bytes
        byte_tokens = list(text.encode('utf-8'))
        
        # Convert to initial token IDs
        token_ids = []
        for byte_val in byte_tokens:
            byte_str = bytes([byte_val]).decode('latin1')
            if byte_str in self.inverse_vocab:
                token_ids.append(self.inverse_vocab[byte_str])
            else:
                # Fallback to unknown token
                token_ids.append(self.special_tokens.get('<|unk|>', 0))
        
        # Apply BPE merges
        while len(token_ids) > 1:
            # Find all possible pairs and their merge priorities
            pairs_in_text = []
            for i in range(len(token_ids) - 1):
                pair = (token_ids[i], token_ids[i + 1])
                if pair in self.bpe_merges:
                    pairs_in_text.append((i, pair))
            
            if not pairs_in_text:
                break
                
            # Apply the first merge found (in order of creation)
            merge_pos, merge_pair = pairs_in_text[0]
            new_token_id = self.bpe_merges[merge_pair]
            
            # Replace the pair with the merged token
            new_token_ids = (token_ids[:merge_pos] + 
                           [new_token_id] + 
                           token_ids[merge_pos + 2:])
            token_ids = new_token_ids
            
        return token_ids
    
    def decode(self, token_ids: List[int]) -> str:
        """Decode token IDs back to text."""
        tokens = []
        for token_id in token_ids:
            if token_id in self.vocab:
                tokens.append(self.vocab[token_id])
            else:
                tokens.append('<|unk|>')
        
        # Join tokens and decode from bytes
        text = ''.join(tokens)
        
        # Try to decode as UTF-8, fallback to latin1
        try:
            # Convert back from latin1 to bytes, then decode as UTF-8
            byte_data = text.encode('latin1')
            return byte_data.decode('utf-8', errors='replace')
        except:
            return text
    
    def save(self, save_dir: str):
        """Save the tokenizer to disk."""
        os.makedirs(save_dir, exist_ok=True)
        
        # Save vocabulary
        vocab_path = os.path.join(save_dir, 'vocab.json')
        with open(vocab_path, 'w', encoding='utf-8') as f:
            # Convert keys to strings for JSON serialization
            vocab_str_keys = {str(k): v for k, v in self.vocab.items()}
            json.dump(vocab_str_keys, f, ensure_ascii=False, indent=2)
        
        # Save merges
        merges_path = os.path.join(save_dir, 'merges.json')
        with open(merges_path, 'w', encoding='utf-8') as f:
            # Convert tuple keys to strings
            merges_str_keys = {f"{k[0]},{k[1]}": v for k, v in self.bpe_merges.items()}
            json.dump(merges_str_keys, f, indent=2)
        
        # Save special tokens
        special_path = os.path.join(save_dir, 'special_tokens.json')
        with open(special_path, 'w', encoding='utf-8') as f:
            json.dump(self.special_tokens, f, indent=2)
        
        # Save tokenizer config
        config_path = os.path.join(save_dir, 'tokenizer_config.json')
        config = {
            'vocab_size': len(self.vocab),
            'special_tokens': list(self.special_tokens.keys())
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
            
        print(f"Tokenizer saved to {save_dir}")
    
    def load(self, save_dir: str):
        """Load the tokenizer from disk."""
        # Load vocabulary
        vocab_path = os.path.join(save_dir, 'vocab.json')
        with open(vocab_path, 'r', encoding='utf-8') as f:
            vocab_str_keys = json.load(f)
            self.vocab = {int(k): v for k, v in vocab_str_keys.items()}
            self.inverse_vocab = {v: int(k) for k, v in vocab_str_keys.items()}
        
        # Load merges
        merges_path = os.path.join(save_dir, 'merges.json')
        with open(merges_path, 'r', encoding='utf-8') as f:
            merges_str_keys = json.load(f)
            self.bpe_merges = {}
            for k, v in merges_str_keys.items():
                token1, token2 = map(int, k.split(','))
                self.bpe_merges[(token1, token2)] = v
        
        # Load special tokens
        special_path = os.path.join(save_dir, 'special_tokens.json')
        with open(special_path, 'r', encoding='utf-8') as f:
            self.special_tokens = json.load(f)
            
        print(f"Tokenizer loaded from {save_dir}")
        print(f"Vocab size: {len(self.vocab)}")
    
    def get_vocab_size(self) -> int:
        """Get the vocabulary size."""
        return len(self.vocab)
    
    def get_special_token_id(self, token: str) -> Optional[int]:
        """Get the ID of a special token."""
        return self.special_tokens.get(token)


def load_datasets(data_dir: str) -> List[str]:
    """Load all text files from the datasets directory."""
    texts = []
    
    if not os.path.exists(data_dir):
        print(f"Warning: Dataset directory {data_dir} does not exist")
        return texts
    
    print(f"Loading datasets from {data_dir}")
    
    for filename in os.listdir(data_dir):
        if filename.endswith(('.txt', '.md', '.json')):
            filepath = os.path.join(data_dir, filename)
            print(f"Loading {filename}")
            
            try:
                if filename.endswith('.json'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    # Extract text from common fields
                                    text = item.get('text', item.get('content', item.get('body', '')))
                                    if text:
                                        texts.append(str(text))
                                elif isinstance(item, str):
                                    texts.append(item)
                        elif isinstance(data, dict):
                            text = data.get('text', data.get('content', data.get('body', '')))
                            if text:
                                texts.append(str(text))
                else:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            texts.append(content)
                            
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                continue
    
    print(f"Loaded {len(texts)} documents")
    total_chars = sum(len(text) for text in texts)
    print(f"Total characters: {total_chars:,}")
    
    return texts


def train_tokenizer(data_dir: str, save_dir: str, vocab_size: int = 50257, 
                   special_tokens: List[str] = None) -> BPETokenizer:
    """Train a BPE tokenizer on the dataset."""
    if special_tokens is None:
        special_tokens = ["<|endoftext|>", "<|pad|>", "<|unk|>"]
    
    # Load datasets
    texts = load_datasets(data_dir)
    
    if not texts:
        raise ValueError(f"No texts found in {data_dir}")
    
    # Add end-of-document tokens
    processed_texts = []
    for text in texts:
        # Add end of document token at the end of each document
        processed_texts.append(text + special_tokens[0])
    
    # Train tokenizer
    tokenizer = BPETokenizer()
    tokenizer.train(processed_texts, vocab_size, special_tokens)
    
    # Save tokenizer
    tokenizer.save(save_dir)
    
    return tokenizer


if __name__ == "__main__":
    # Test the tokenizer
    from config import BPE_CONFIG, DATASET_CONFIG, PATHS
    
    # Create test data if datasets directory doesn't exist
    os.makedirs(DATASET_CONFIG["data_dir"], exist_ok=True)
    
    test_file = os.path.join(DATASET_CONFIG["data_dir"], "test.txt")
    if not os.path.exists(test_file):
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("This is a test document for training the tokenizer. " * 100)
        print(f"Created test file: {test_file}")
    
    # Train tokenizer
    tokenizer = train_tokenizer(
        data_dir=DATASET_CONFIG["data_dir"],
        save_dir=PATHS["tokenizer_save_dir"],
        vocab_size=BPE_CONFIG["vocab_size"],
        special_tokens=BPE_CONFIG["special_tokens"]
    )
    
    # Test encoding/decoding
    test_text = "Hello, world! This is a test."
    encoded = tokenizer.encode(test_text)
    decoded = tokenizer.decode(encoded)
    
    print(f"Original: {test_text}")
    print(f"Encoded: {encoded}")
    print(f"Decoded: {decoded}")
    print(f"Match: {test_text == decoded}")