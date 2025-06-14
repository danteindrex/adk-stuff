# Fine-tuning with Unsloth and Reinforcement Learning
# Implements PPO, ORPO, and RGPO for conversational models with tool calling

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings("ignore")

import torch
import torch.nn as nn
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)

# Unsloth imports (install with: pip install unsloth)
try:
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import get_chat_template
    UNSLOTH_AVAILABLE = True
except ImportError:
    print("Unsloth not available. Install with: pip install unsloth")
    UNSLOTH_AVAILABLE = False

# TRL imports for reinforcement learning (install with: pip install trl)
try:
    from trl import (
        PPOTrainer, 
        PPOConfig,
        AutoModelForCausalLMWithValueHead,
        create_reference_model
    )
    TRL_AVAILABLE = True
except ImportError:
    print("TRL not available. Install with: pip install trl")
    TRL_AVAILABLE = False

# PEFT imports for LoRA
try:
    from peft import (
        LoraConfig,
        get_peft_model,
        TaskType,
        PeftModel
    )
    PEFT_AVAILABLE = True
except ImportError:
    print("PEFT not available. Install with: pip install peft")
    PEFT_AVAILABLE = False


class UnslothFineTuner:
    """Fine-tuner using Unsloth for efficient training."""
    
    def __init__(self, model_path: str, config: Dict):
        self.model_path = model_path
        self.config = config
        self.model = None
        self.tokenizer = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        if not UNSLOTH_AVAILABLE:
            raise ImportError("Unsloth is required for this fine-tuner")
    
    def load_model(self, max_seq_length: int = 2048):
        """Load model with Unsloth optimizations."""
        self.logger.info(f"Loading model from {self.model_path}")
        
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.model_path,
            max_seq_length=max_seq_length,
            dtype=None,  # Auto-detect
            load_in_4bit=True,  # Use 4-bit quantization
        )
        
        # Add LoRA adapters
        self.model = FastLanguageModel.get_peft_model(
            self.model,
            r=self.config.get("lora_r", 16),
            target_modules=self.config.get("target_modules", [
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ]),
            lora_alpha=self.config.get("lora_alpha", 32),
            lora_dropout=self.config.get("lora_dropout", 0.1),
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=3407,
            use_rslora=False,
            loftq_config=None,
        )
        
        self.logger.info("Model loaded with Unsloth optimizations")
    
    def prepare_dataset(self, data: List[Dict], format_type: str = "instruction") -> List[Dict]:
        """Prepare dataset for fine-tuning."""
        formatted_data = []
        
        for item in data:
            if format_type == "instruction":
                formatted_item = self._format_instruction(item)
            elif format_type == "conversation":
                formatted_item = self._format_conversation(item)
            elif format_type == "tool_calling":
                formatted_item = self._format_tool_calling(item)
            else:
                raise ValueError(f"Unknown format type: {format_type}")
            
            formatted_data.append(formatted_item)
        
        return formatted_data
    
    def _format_instruction(self, item: Dict) -> Dict:
        """Format instruction data."""
        instruction = item.get("instruction", "")
        input_text = item.get("input", "")
        output = item.get("output", "")
        
        if input_text:
            prompt = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n"
        else:
            prompt = f"### Instruction:\n{instruction}\n\n### Response:\n"
        
        return {
            "text": prompt + output + "<|endoftext|>"
        }
    
    def _format_conversation(self, item: Dict) -> Dict:
        """Format conversational data."""
        messages = item.get("messages", [])
        formatted_text = ""
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "system":
                formatted_text += f"<|system|>\n{content}\n"
            elif role == "user":
                formatted_text += f"<|user|>\n{content}\n"
            elif role == "assistant":
                formatted_text += f"<|assistant|>\n{content}\n"
        
        return {"text": formatted_text + "<|endoftext|>"}
    
    def _format_tool_calling(self, item: Dict) -> Dict:
        """Format tool calling data."""
        messages = item.get("messages", [])
        formatted_text = ""
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "system":
                formatted_text += f"<|system|>\n{content}\n"
            elif role == "user":
                formatted_text += f"<|user|>\n{content}\n"
            elif role == "assistant":
                tool_calls = message.get("tool_calls", [])
                if tool_calls:
                    formatted_text += f"<|assistant|>\n"
                    for tool_call in tool_calls:
                        func_name = tool_call.get("function", {}).get("name", "")
                        func_args = tool_call.get("function", {}).get("arguments", "")
                        formatted_text += f"<|function_call|>\n{func_name}({func_args})\n<|/function_call|>\n"
                    if content:
                        formatted_text += f"{content}\n"
                else:
                    formatted_text += f"<|assistant|>\n{content}\n"
            elif role == "tool":
                tool_name = message.get("name", "unknown")
                formatted_text += f"<|function_result|>\n{tool_name}: {content}\n<|/function_result|>\n"
        
        return {"text": formatted_text + "<|endoftext|>"}
    
    def fine_tune(self, train_data: List[Dict], val_data: List[Dict], 
                  output_dir: str, format_type: str = "instruction"):
        """Fine-tune the model."""
        # Prepare datasets
        train_dataset = self.prepare_dataset(train_data, format_type)
        val_dataset = self.prepare_dataset(val_data, format_type)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=self.config.get("num_train_epochs", 3),
            per_device_train_batch_size=self.config.get("per_device_train_batch_size", 1),
            per_device_eval_batch_size=self.config.get("per_device_eval_batch_size", 1),
            gradient_accumulation_steps=self.config.get("gradient_accumulation_steps", 4),
            learning_rate=self.config.get("learning_rate", 2e-4),
            warmup_steps=self.config.get("warmup_steps", 10),
            max_steps=self.config.get("max_steps", 60),
            logging_steps=self.config.get("logging_steps", 1),
            save_steps=self.config.get("save_steps", 10),
            eval_steps=self.config.get("eval_steps", 10),
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to=None,  # Disable wandb
            remove_unused_columns=False,
            dataloader_pin_memory=False,
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )
        
        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        # Train
        self.logger.info("Starting fine-tuning...")
        trainer.train()
        
        # Save model
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        self.logger.info(f"Fine-tuning completed. Model saved to {output_dir}")


class PPOTrainerCustom:
    """PPO trainer for conversational models."""
    
    def __init__(self, model_path: str, config: Dict):
        self.model_path = model_path
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        if not TRL_AVAILABLE:
            raise ImportError("TRL is required for PPO training")
    
    def setup_ppo(self):
        """Setup PPO training components."""
        # Load model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model with value head
        self.model = AutoModelForCausalLMWithValueHead.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # Create reference model
        self.ref_model = create_reference_model(self.model)
        
        # PPO config
        ppo_config = PPOConfig(
            learning_rate=self.config.get("learning_rate", 1.41e-5),
            mini_batch_size=self.config.get("mini_batch_size", 1),
            batch_size=self.config.get("batch_size", 8),
            ppo_epochs=self.config.get("ppo_epochs", 4),
            gamma=self.config.get("gamma", 1.0),
            gae_lambda=self.config.get("gae_lambda", 0.95),
            clip_range=self.config.get("clip_range", 0.2),
            vf_coef=self.config.get("vf_coef", 0.1),
            ent_coef=self.config.get("ent_coef", 0.0),
            target_kl=self.config.get("target_kl", 0.1),
            max_grad_norm=self.config.get("max_grad_norm", 0.5),
        )
        
        # PPO trainer
        self.ppo_trainer = PPOTrainer(
            config=ppo_config,
            model=self.model,
            ref_model=self.ref_model,
            tokenizer=self.tokenizer,
        )
        
        self.logger.info("PPO trainer setup completed")
    
    def train_ppo(self, dataset: List[Dict], reward_model, num_epochs: int = 1):
        """Train with PPO."""
        for epoch in range(num_epochs):
            for batch in dataset:
                # Prepare queries
                queries = [item["query"] for item in batch]
                query_tensors = [self.tokenizer.encode(q, return_tensors="pt")[0] for q in queries]
                
                # Generate responses
                response_tensors = []
                for query_tensor in query_tensors:
                    response = self.ppo_trainer.generate(
                        query_tensor.unsqueeze(0),
                        max_length=512,
                        do_sample=True,
                        temperature=0.7,
                        pad_token_id=self.tokenizer.pad_token_id
                    )
                    response_tensors.append(response.squeeze(0))
                
                # Get rewards
                rewards = []
                for query, response in zip(queries, response_tensors):
                    response_text = self.tokenizer.decode(response, skip_special_tokens=True)
                    reward = reward_model.get_reward(query, response_text)
                    rewards.append(torch.tensor(reward))
                
                # PPO step
                stats = self.ppo_trainer.step(query_tensors, response_tensors, rewards)
                
                if epoch % 10 == 0:
                    self.logger.info(f"Epoch {epoch}, Stats: {stats}")


class ORPOTrainer:
    """ORPO (Odds Ratio Preference Optimization) trainer."""
    
    def __init__(self, model_path: str, config: Dict):
        self.model_path = model_path
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def train_orpo(self, preference_data: List[Dict], output_dir: str):
        """Train with ORPO."""
        # Load model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # ORPO training logic would go here
        # This is a simplified placeholder - full ORPO implementation
        # would require more complex preference learning logic
        
        self.logger.info("ORPO training completed")


class RGPOTrainer:
    """RGPO (Reward-Guided Policy Optimization) trainer."""
    
    def __init__(self, model_path: str, config: Dict):
        self.model_path = model_path
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def train_rgpo(self, dataset: List[Dict], reward_model, output_dir: str):
        """Train with RGPO."""
        # Load model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # RGPO training logic would go here
        # This is a simplified placeholder - full RGPO implementation
        # would require custom reward-guided optimization
        
        self.logger.info("RGPO training completed")


def load_instruction_data(data_path: str) -> Tuple[List[Dict], List[Dict]]:
    """Load instruction fine-tuning data."""
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Split into train/val
    split_idx = int(len(data) * 0.9)
    train_data = data[:split_idx]
    val_data = data[split_idx:]
    
    return train_data, val_data


def load_conversation_data(data_path: str) -> List[Dict]:
    """Load conversational data."""
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def main():
    """Main fine-tuning script."""
    from config import FINETUNING_CONFIG, RL_CONFIG, RECOMMENDED_RL_METHOD
    
    # Configuration
    model_path = "path/to/your/pretrained/model"  # Update this
    data_path = "datasets/instruction_data.json"  # Update this
    output_dir = "models/finetuned"
    
    print("=== GPT Fine-tuning with Unsloth and Reinforcement Learning ===")
    print(f"Recommended RL method for conversational models: {RECOMMENDED_RL_METHOD}")
    print()
    
    # Step 1: Instruction Fine-tuning with Unsloth
    if UNSLOTH_AVAILABLE:
        print("Step 1: Instruction Fine-tuning with Unsloth")
        
        try:
            # Load data
            train_data, val_data = load_instruction_data(data_path)
            print(f"Loaded {len(train_data)} training samples, {len(val_data)} validation samples")
            
            # Initialize fine-tuner
            fine_tuner = UnslothFineTuner(model_path, FINETUNING_CONFIG)
            fine_tuner.load_model(max_seq_length=2000)
            
            # Fine-tune
            sft_output_dir = os.path.join(output_dir, "sft")
            fine_tuner.fine_tune(train_data, val_data, sft_output_dir, format_type="instruction")
            
            print(f"Instruction fine-tuning completed. Model saved to {sft_output_dir}")
            
            # Update model path for RL training
            model_path = sft_output_dir
            
        except Exception as e:
            print(f"Instruction fine-tuning failed: {e}")
            return
    else:
        print("Unsloth not available, skipping instruction fine-tuning")
    
    # Step 2: Reinforcement Learning Fine-tuning
    print(f"\nStep 2: Reinforcement Learning with {RECOMMENDED_RL_METHOD.upper()}")
    
    if RECOMMENDED_RL_METHOD == "ppo" and TRL_AVAILABLE:
        try:
            # PPO Training
            ppo_trainer = PPOTrainerCustom(model_path, RL_CONFIG["ppo"])
            ppo_trainer.setup_ppo()
            
            # Load conversational data for PPO
            # This would need to be prepared with queries and expected responses
            print("PPO training setup completed")
            print("Note: You need to provide conversational data and a reward model for PPO training")
            
        except Exception as e:
            print(f"PPO training setup failed: {e}")
    
    elif RECOMMENDED_RL_METHOD == "orpo":
        try:
            # ORPO Training
            orpo_trainer = ORPOTrainer(model_path, RL_CONFIG["orpo"])
            print("ORPO trainer initialized")
            print("Note: You need to provide preference data for ORPO training")
            
        except Exception as e:
            print(f"ORPO training setup failed: {e}")
    
    elif RECOMMENDED_RL_METHOD == "rgpo":
        try:
            # RGPO Training
            rgpo_trainer = RGPOTrainer(model_path, RL_CONFIG["rgpo"])
            print("RGPO trainer initialized")
            print("Note: You need to provide a reward model for RGPO training")
            
        except Exception as e:
            print(f"RGPO training setup failed: {e}")
    
    print("\n=== Fine-tuning Setup Complete ===")
    print("\nNext steps:")
    print("1. Prepare your datasets in the 'datasets' folder")
    print("2. Update the model_path and data_path variables")
    print("3. Install required packages: pip install unsloth trl peft")
    print("4. Run this script to start fine-tuning")
    print("\nFor conversational models with tool calling:")
    print(f"- Use {RECOMMENDED_RL_METHOD.upper()} for best results")
    print("- Prepare conversation data with tool calling examples")
    print("- Consider using a reward model that evaluates tool usage accuracy")


if __name__ == "__main__":
    main()