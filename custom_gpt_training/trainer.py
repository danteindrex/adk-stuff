# Training utilities for GPT model
# Handles the main training loop and evaluation

import os
import time
import math
import pickle
from contextlib import nullcontext
from typing import Dict, Tuple, Optional, List
import logging

import torch
import torch.nn as nn
from torch.nn import functional as F
from torch.utils.data import DataLoader
import numpy as np


class GPTTrainer:
    """Main trainer class for GPT model."""
    
    def __init__(self, model, tokenizer, config: Dict, device: str = "auto"):
        self.model = model
        self.tokenizer = tokenizer
        self.config = config
        
        # Device setup
        if device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        self.model.to(self.device)
        
        # Training state
        self.step = 0
        self.epoch = 0
        self.best_val_loss = float('inf')
        
        # Setup logging
        self.setup_logging()
        
        # Setup optimizer and scheduler
        self.setup_optimizer()
        
        # Mixed precision setup
        self.use_amp = config.get("mixed_precision") in ["fp16", "bf16"]
        if self.use_amp:
            self.scaler = torch.cuda.amp.GradScaler(enabled=(config.get("mixed_precision") == "fp16"))
            self.autocast_dtype = torch.float16 if config.get("mixed_precision") == "fp16" else torch.bfloat16
        else:
            self.scaler = None
            self.autocast_dtype = torch.float32
        
        self.logger.info(f"Trainer initialized on device: {self.device}")
        self.logger.info(f"Model parameters: {self.model.get_num_params():,}")
        self.logger.info(f"Mixed precision: {config.get('mixed_precision', 'disabled')}")
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_dir = self.config.get("logs_dir", "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.config.get("log_level", "INFO")),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, "training.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_optimizer(self):
        """Setup optimizer and learning rate scheduler."""
        # Create optimizer
        decay_params = []
        no_decay_params = []
        
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                if any(nd in name for nd in ["bias", "norm"]):
                    no_decay_params.append(param)
                else:
                    decay_params.append(param)
        
        optim_groups = [
            {"params": decay_params, "weight_decay": self.config.get("weight_decay", 0.1)},
            {"params": no_decay_params, "weight_decay": 0.0}
        ]
        
        self.optimizer = torch.optim.AdamW(
            optim_groups, 
            lr=self.config.get("learning_rate", 5e-4),
            betas=(0.9, 0.95)
        )
        
        # Learning rate scheduler
        self.scheduler = None
        if self.config.get("warmup_steps", 0) > 0:
            self.scheduler = self.get_lr_scheduler()
    
    def get_lr_scheduler(self):
        """Create learning rate scheduler with warmup and cosine decay."""
        def lr_lambda(step):
            warmup_steps = self.config.get("warmup_steps", 1000)
            max_steps = self.config.get("max_steps", 10000)
            min_lr_ratio = self.config.get("min_lr", 6e-5) / self.config.get("max_lr", 6e-4)
            
            if step < warmup_steps:
                return step / warmup_steps
            elif step < max_steps:
                progress = (step - warmup_steps) / (max_steps - warmup_steps)
                return min_lr_ratio + (1 - min_lr_ratio) * 0.5 * (1 + math.cos(math.pi * progress))
            else:
                return min_lr_ratio
        
        return torch.optim.lr_scheduler.LambdaLR(self.optimizer, lr_lambda)
    
    def train_step(self, batch) -> Dict[str, float]:
        """Perform a single training step."""
        self.model.train()
        
        inputs, targets = batch
        inputs = inputs.to(self.device)
        targets = targets.to(self.device)
        
        # Forward pass with mixed precision
        with torch.cuda.amp.autocast(enabled=self.use_amp, dtype=self.autocast_dtype):
            logits, loss = self.model(inputs, targets)
        
        # Backward pass
        if self.use_amp:
            self.scaler.scale(loss).backward()
            
            # Gradient clipping
            if self.config.get("gradient_clip", 0) > 0:
                self.scaler.unscale_(self.optimizer)
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), 
                    self.config.get("gradient_clip", 1.0)
                )
            
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            loss.backward()
            
            # Gradient clipping
            if self.config.get("gradient_clip", 0) > 0:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), 
                    self.config.get("gradient_clip", 1.0)
                )
            
            self.optimizer.step()
        
        self.optimizer.zero_grad(set_to_none=True)
        
        # Update learning rate
        if self.scheduler is not None:
            self.scheduler.step()
        
        self.step += 1
        
        return {
            "loss": loss.item(),
            "lr": self.optimizer.param_groups[0]["lr"],
            "step": self.step
        }
    
    @torch.no_grad()
    def evaluate(self, dataloader: DataLoader, max_batches: Optional[int] = None) -> Dict[str, float]:
        """Evaluate the model on a dataset."""
        self.model.eval()
        
        total_loss = 0.0
        total_tokens = 0
        num_batches = 0
        
        for i, batch in enumerate(dataloader):
            if max_batches is not None and i >= max_batches:
                break
            
            inputs, targets = batch
            inputs = inputs.to(self.device)
            targets = targets.to(self.device)
            
            with torch.cuda.amp.autocast(enabled=self.use_amp, dtype=self.autocast_dtype):
                logits, loss = self.model(inputs, targets)
            
            # Count valid tokens (not padding or ignore tokens)
            valid_tokens = (targets != -100).sum().item()
            
            total_loss += loss.item() * valid_tokens
            total_tokens += valid_tokens
            num_batches += 1
        
        avg_loss = total_loss / total_tokens if total_tokens > 0 else float('inf')
        perplexity = math.exp(avg_loss) if avg_loss < 10 else float('inf')
        
        return {
            "loss": avg_loss,
            "perplexity": perplexity,
            "batches": num_batches,
            "tokens": total_tokens
        }
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader, 
              num_epochs: int, save_dir: str) -> Dict[str, List[float]]:
        """Main training loop."""
        os.makedirs(save_dir, exist_ok=True)
        
        train_losses = []
        val_losses = []
        learning_rates = []
        
        self.logger.info(f"Starting training for {num_epochs} epochs")
        self.logger.info(f"Train batches per epoch: {len(train_loader)}")
        self.logger.info(f"Val batches: {len(val_loader)}")
        
        start_time = time.time()
        
        for epoch in range(num_epochs):
            self.epoch = epoch
            epoch_start_time = time.time()
            
            # Training
            epoch_train_loss = 0.0
            num_train_batches = 0
            
            for batch_idx, batch in enumerate(train_loader):
                step_result = self.train_step(batch)
                
                epoch_train_loss += step_result["loss"]
                num_train_batches += 1
                
                # Logging
                if self.step % self.config.get("eval_freq", 100) == 0:
                    # Evaluate
                    val_result = self.evaluate(val_loader, self.config.get("eval_iter", 10))
                    
                    train_losses.append(step_result["loss"])
                    val_losses.append(val_result["loss"])
                    learning_rates.append(step_result["lr"])
                    
                    # Estimate MFU
                    if hasattr(self.model, 'estimate_mfu'):
                        dt = time.time() - start_time
                        mfu = self.model.estimate_mfu(self.step, dt)
                        mfu_str = f", MFU: {mfu*100:.2f}%"
                    else:
                        mfu_str = ""
                    
                    self.logger.info(
                        f"Step {self.step:6d} | "
                        f"Train Loss: {step_result['loss']:.4f} | "
                        f"Val Loss: {val_result['loss']:.4f} | "
                        f"Val PPL: {val_result['perplexity']:.2f} | "
                        f"LR: {step_result['lr']:.2e}"
                        f"{mfu_str}"
                    )
                    
                    # Save best model
                    if val_result["loss"] < self.best_val_loss:
                        self.best_val_loss = val_result["loss"]
                        self.save_checkpoint(save_dir, "best_model.pt")
                        self.logger.info(f"New best model saved with val loss: {self.best_val_loss:.4f}")
                
                # Save checkpoint
                if self.step % self.config.get("save_freq", 1000) == 0:
                    self.save_checkpoint(save_dir, f"checkpoint_step_{self.step}.pt")
            
            # End of epoch
            avg_train_loss = epoch_train_loss / num_train_batches
            epoch_time = time.time() - epoch_start_time
            
            self.logger.info(
                f"Epoch {epoch + 1}/{num_epochs} completed in {epoch_time:.2f}s | "
                f"Avg Train Loss: {avg_train_loss:.4f}"
            )
            
            # Save epoch checkpoint
            self.save_checkpoint(save_dir, f"epoch_{epoch + 1}.pt")
        
        total_time = time.time() - start_time
        self.logger.info(f"Training completed in {total_time:.2f}s")
        
        return {
            "train_losses": train_losses,
            "val_losses": val_losses,
            "learning_rates": learning_rates
        }
    
    def save_checkpoint(self, save_dir: str, filename: str):
        """Save model checkpoint."""
        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict() if self.scheduler else None,
            "step": self.step,
            "epoch": self.epoch,
            "best_val_loss": self.best_val_loss,
            "config": self.config,
        }
        
        if self.use_amp:
            checkpoint["scaler_state_dict"] = self.scaler.state_dict()
        
        torch.save(checkpoint, os.path.join(save_dir, filename))
    
    def load_checkpoint(self, checkpoint_path: str):
        """Load model checkpoint."""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        
        if checkpoint.get("scheduler_state_dict") and self.scheduler:
            self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        
        if checkpoint.get("scaler_state_dict") and self.use_amp:
            self.scaler.load_state_dict(checkpoint["scaler_state_dict"])
        
        self.step = checkpoint.get("step", 0)
        self.epoch = checkpoint.get("epoch", 0)
        self.best_val_loss = checkpoint.get("best_val_loss", float('inf'))
        
        self.logger.info(f"Checkpoint loaded from {checkpoint_path}")
        self.logger.info(f"Resumed from step {self.step}, epoch {self.epoch}")
    
    @torch.no_grad()
    def generate_text(self, prompt: str, max_new_tokens: int = 100, 
                     temperature: float = 1.0, top_k: Optional[int] = None) -> str:
        """Generate text from a prompt."""
        self.model.eval()
        
        # Encode prompt
        token_ids = self.tokenizer.encode(prompt)
        input_ids = torch.tensor(token_ids, dtype=torch.long, device=self.device).unsqueeze(0)
        
        # Generate
        generated_ids = self.model.generate(
            input_ids, 
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k
        )
        
        # Decode
        generated_text = self.tokenizer.decode(generated_ids[0].tolist())
        
        return generated_text


def calculate_loss(model, dataloader, device, max_batches=None):
    """Calculate average loss on a dataset."""
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    num_batches = 0
    
    with torch.no_grad():
        for i, batch in enumerate(dataloader):
            if max_batches is not None and i >= max_batches:
                break
            
            inputs, targets = batch
            inputs = inputs.to(device)
            targets = targets.to(device)
            
            logits, loss = model(inputs, targets)
            
            # Count valid tokens
            valid_tokens = (targets != -100).sum().item()
            
            total_loss += loss.item() * valid_tokens
            total_tokens += valid_tokens
            num_batches += 1
    
    return total_loss / total_tokens if total_tokens > 0 else float('inf')


def estimate_loss(model, train_loader, val_loader, device, eval_iters=10):
    """Estimate train and validation loss."""
    out = {}
    model.eval()
    
    for split, dataloader in [("train", train_loader), ("val", val_loader)]:
        losses = torch.zeros(eval_iters)
        for k in range(eval_iters):
            try:
                batch = next(iter(dataloader))
                inputs, targets = batch
                inputs = inputs.to(device)
                targets = targets.to(device)
                
                with torch.no_grad():
                    logits, loss = model(inputs, targets)
                losses[k] = loss.item()
            except StopIteration:
                break
        
        out[split] = losses.mean().item()
    
    model.train()
    return out


if __name__ == "__main__":
    # Test trainer
    from config import GPT_CONFIG, TRAINING_CONFIG
    from model import create_model
    from tokenizer import BPETokenizer
    
    # Create dummy tokenizer
    tokenizer = BPETokenizer()
    tokenizer.vocab = {i: str(i) for i in range(1000)}
    tokenizer.inverse_vocab = {str(i): i for i in range(1000)}
    tokenizer.special_tokens = {"<|endoftext|>": 999, "<|pad|>": 998}
    
    # Create model
    model = create_model(GPT_CONFIG)
    
    # Create trainer
    trainer = GPTTrainer(model, tokenizer, TRAINING_CONFIG)
    
    print(f"Trainer created successfully")
    print(f"Device: {trainer.device}")
    print(f"Model parameters: {model.get_num_params():,}")
    
    # Test text generation
    test_prompt = "Hello, world!"
    try:
        generated = trainer.generate_text(test_prompt, max_new_tokens=10)
        print(f"Generated: {generated}")
    except Exception as e:
        print(f"Generation test failed: {e}")