"""
Fine-tune ViT5 (Vietnamese T5) model cho NL2SQL task
"""
import json
import os
from typing import List, Dict
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    T5ForConditionalGeneration,
    T5Tokenizer,
    get_linear_schedule_with_warmup
)
from torch.optim import AdamW
from tqdm import tqdm


class NL2SQLDataset(Dataset):
    """Dataset for NL2SQL training"""
    
    def __init__(self, examples: List[Dict], tokenizer, schema: Dict, max_length=512):
        self.examples = examples
        self.tokenizer = tokenizer
        self.schema = schema
        self.max_length = max_length
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        example = self.examples[idx]
        
        # Get relevant schema for this intent
        schema_str = self._get_schema_for_intent(example['intent'])
        
        # Input: intent + question + schema
        input_text = f"intent: {example['intent']} | question: {example['question']} | schema: {schema_str}"
        
        # Output: SQL query
        output_text = example['sql']
        
        # Tokenize
        input_encoding = self.tokenizer(
            input_text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        output_encoding = self.tokenizer(
            output_text,
            max_length=256,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        labels = output_encoding['input_ids']
        labels[labels == self.tokenizer.pad_token_id] = -100
        
        return {
            'input_ids': input_encoding['input_ids'].flatten(),
            'attention_mask': input_encoding['attention_mask'].flatten(),
            'labels': labels.flatten()
        }
    
    def _get_schema_for_intent(self, intent: str) -> str:
        """Get relevant schema for intent"""
        intent_tables = {
            "grade_view": ["students", "learned_subjects"],
            "student_info": ["students", "learned_subjects"],
            "subject_info": ["subjects"],
            "class_info": ["classes", "subjects"],
            "schedule_view": ["class_registers", "classes", "subjects"],
            "subject_registration_suggestion": ["subjects", "learned_subjects"],
            "class_registration_suggestion": ["classes", "subjects", "class_registers"],
        }
        
        relevant_tables = intent_tables.get(intent, [])
        schema_str = ""
        
        for table in relevant_tables:
            if table in self.schema:
                cols = ", ".join(self.schema[table]["columns"])
                schema_str += f"{table}({cols}); "
        
        return schema_str.strip()


class NL2SQLTrainer:
    """Trainer for ViT5 NL2SQL model"""
    
    def __init__(
        self,
        model_name: str = "VietAI/vit5-base",
        output_dir: str = "./models/vit5_nl2sql",
        data_path: str = None
    ):
        self.model_name = model_name
        self.output_dir = output_dir
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"   Initializing NL2SQL Trainer...")
        print(f"   Model: {model_name}")
        print(f"   Device: {self.device}")
        print(f"   Output: {output_dir}")
        
        # Load training data
        if data_path is None:
            data_path = r"C:\Users\Admin\student-management\backend\data\nl2sql_training_data.json"
        
        self.training_data = self._load_data(data_path)
        self.schema = self.training_data.get("schema", {})
        self.examples = self.training_data.get("training_examples", [])
        
        print(f"   Loaded {len(self.examples)} training examples")
        
        # Load tokenizer and model
        print("📦 Loading ViT5 model and tokenizer...")
        self.tokenizer = T5Tokenizer.from_pretrained(model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name)
        self.model.to(self.device)
        
        print("   Model and tokenizer loaded")
    
    def _load_data(self, data_path: str) -> Dict:
        """Load training data from JSON"""
        with open(data_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    
    def _augment_data(self, examples: List[Dict]) -> List[Dict]:
        """Augment training data with variations"""
        augmented = list(examples)
        
        # Add variations for each example
        for example in examples[:]:
            # Variation 1: Replace specific entities
            if "IT4040" in example['question']:
                new_ex = example.copy()
                new_ex['question'] = example['question'].replace("IT4040", "MAT1234")
                new_ex['sql'] = example['sql'].replace("IT4040", "MAT1234")
                augmented.append(new_ex)
            
            # Variation 2: Different subject names
            if "Đại số" in example['question']:
                new_ex = example.copy()
                new_ex['question'] = example['question'].replace("Đại số", "Giải tích")
                new_ex['sql'] = example['sql'].replace("Đại số", "Giải tích")
                augmented.append(new_ex)
            
            if "Giải tích 1" in example['question']:
                new_ex = example.copy()
                new_ex['question'] = example['question'].replace("Giải tích 1", "Vật lý đại cương")
                new_ex['sql'] = example['sql'].replace("Giải tích 1", "Vật lý đại cương")
                augmented.append(new_ex)
        
        return augmented
    
    def prepare_datasets(self, train_split=0.8, augment=True):
        """Prepare train and validation datasets"""
        examples = self.examples
        
        # Augment data if requested
        if augment:
            print("   Augmenting training data...")
            examples = self._augment_data(examples)
            print(f"   Total examples after augmentation: {len(examples)}")
        
        # Split into train and validation
        split_idx = int(len(examples) * train_split)
        train_examples = examples[:split_idx]
        val_examples = examples[split_idx:]
        
        print(f"   Dataset split:")
        print(f"   Train: {len(train_examples)} examples")
        print(f"   Validation: {len(val_examples)} examples")
        
        # Create datasets
        train_dataset = NL2SQLDataset(train_examples, self.tokenizer, self.schema)
        val_dataset = NL2SQLDataset(val_examples, self.tokenizer, self.schema)
        
        return train_dataset, val_dataset
    
    def train(
        self,
        num_epochs: int = 10,
        batch_size: int = 8,
        learning_rate: float = 5e-5,
        warmup_steps: int = 100,
        save_steps: int = 100
    ):
        """Train the model"""
        print("\n" + "="*70)
        print("🏋️ STARTING TRAINING")
        print("="*70)
        
        # Prepare datasets
        train_dataset, val_dataset = self.prepare_datasets(augment=True)
        
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False
        )
        
        # Optimizer and scheduler
        optimizer = AdamW(self.model.parameters(), lr=learning_rate)
        total_steps = len(train_loader) * num_epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps
        )
        
        # Training loop
        best_val_loss = float('inf')
        
        for epoch in range(num_epochs):
            print(f"\n   Epoch {epoch + 1}/{num_epochs}")
            
            # Training
            self.model.train()
            train_loss = 0
            
            progress_bar = tqdm(train_loader, desc=f"Training")
            
            for batch in progress_bar:
                # Move to device
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                loss = outputs.loss
                train_loss += loss.item()
                
                # Backward pass
                loss.backward()
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                
                progress_bar.set_postfix({'loss': loss.item()})
            
            avg_train_loss = train_loss / len(train_loader)
            print(f"      Average training loss: {avg_train_loss:.4f}")
            
            # Validation
            self.model.eval()
            val_loss = 0
            
            with torch.no_grad():
                for batch in tqdm(val_loader, desc="Validation"):
                    input_ids = batch['input_ids'].to(self.device)
                    attention_mask = batch['attention_mask'].to(self.device)
                    labels = batch['labels'].to(self.device)
                    
                    outputs = self.model(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        labels=labels
                    )
                    
                    val_loss += outputs.loss.item()
            
            avg_val_loss = val_loss / len(val_loader)
            print(f"      Average validation loss: {avg_val_loss:.4f}")
            
            # Save best model
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                self.save_model(f"{self.output_dir}/best")
                print(f"      Saved best model (val_loss: {avg_val_loss:.4f})")
            
            # Save checkpoint
            if (epoch + 1) % 2 == 0:
                self.save_model(f"{self.output_dir}/checkpoint-{epoch+1}")
        
        print("\n" + "="*70)
        print("   TRAINING COMPLETED")
        print("="*70)
        print(f"Best validation loss: {best_val_loss:.4f}")
        print(f"Model saved to: {self.output_dir}/best")
    
    def save_model(self, path: str):
        """Save model and tokenizer"""
        os.makedirs(path, exist_ok=True)
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
    
    def test_inference(self, questions: List[str], intents: List[str]):
        """Test model inference"""
        print("\n" + "="*70)
        print("   TESTING INFERENCE")
        print("="*70)
        
        self.model.eval()
        
        for question, intent in zip(questions, intents):
            schema_str = self._get_schema_for_intent(intent)
            input_text = f"intent: {intent} | question: {question} | schema: {schema_str}"
            
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                max_length=512,
                truncation=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=256,
                    num_beams=5,
                    early_stopping=True
                )
            
            generated_sql = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            print(f"\n   Question: {question}")
            print(f"   Intent: {intent}")
            print(f"   Generated SQL: {generated_sql}")
    
    def _get_schema_for_intent(self, intent: str) -> str:
        """Get relevant schema for intent"""
        intent_tables = {
            "grade_view": ["students", "learned_subjects"],
            "student_info": ["students", "learned_subjects"],
            "subject_info": ["subjects"],
            "class_info": ["classes", "subjects"],
            "schedule_view": ["class_registers", "classes", "subjects"],
        }
        
        relevant_tables = intent_tables.get(intent, [])
        schema_str = ""
        
        for table in relevant_tables:
            if table in self.schema:
                cols = ", ".join(self.schema[table]["columns"])
                schema_str += f"{table}({cols}); "
        
        return schema_str.strip()


def main():
    """Main training function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fine-tune ViT5 for NL2SQL")
    parser.add_argument("--model_name", type=str, default="VietAI/vit5-base")
    parser.add_argument("--output_dir", type=str, default="./models/vit5_nl2sql")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=5e-5)
    parser.add_argument("--test_only", action="store_true")
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = NL2SQLTrainer(
        model_name=args.model_name,
        output_dir=args.output_dir
    )
    
    if args.test_only:
        # Load best model and test
        trainer.model = T5ForConditionalGeneration.from_pretrained(f"{args.output_dir}/best")
        trainer.model.to(trainer.device)
        
        test_questions = [
            "xem điểm của tôi",
            "các môn bị D",
            "môn tiên quyết của IT4040",
            "danh sách các lớp môn Đại số",
        ]
        test_intents = [
            "grade_view",
            "student_info",
            "subject_info",
            "class_info",
        ]
        
        trainer.test_inference(test_questions, test_intents)
    else:
        # Train model
        trainer.train(
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate
        )
        
        # Test after training
        test_questions = [
            "xem điểm",
            "môn tiên quyết của IT4040",
        ]
        test_intents = [
            "grade_view",
            "subject_info",
        ]
        
        trainer.test_inference(test_questions, test_intents)


if __name__ == "__main__":
    main()
