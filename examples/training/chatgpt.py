import torch
from transformers import BertTokenizer, BertForMaskedLM
from torch.utils.data import DataLoader, Dataset
from datasets import load_dataset
from tqdm import tqdm

# Load WikiText-2 dataset
wikitext = load_dataset("wikitext", "wikitext-2-raw-v1")
train_dataset = wikitext["train"]

# Preprocess data
class WikiTextDataset(Dataset):
    def __init__(self, dataset, tokenizer, max_length=512):
        self.dataset = dataset
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        text = self.dataset[idx]["text"]
        inputs = self.tokenizer.encode_plus(
            text, 
            add_special_tokens=True, 
            truncation=True, 
            max_length=self.max_length,
            padding="max_length"
        )
        return torch.tensor(inputs["input_ids"]), torch.tensor(inputs["attention_mask"])

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
train_data = WikiTextDataset(train_dataset, tokenizer)

# Initialize BERT model
model = BertForMaskedLM.from_pretrained('bert-base-uncased')

# Training settings
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
train_loader = DataLoader(train_data, batch_size=4, shuffle=True)

# Training loop
num_epochs = 3
for epoch in range(num_epochs):
    model.train()
    total_loss = 0
    for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{num_epochs}"):
        batch = [item.to(device) for item in batch]
        inputs, attention_masks = batch
        print(inputs)
        optimizer.zero_grad()
        outputs = model(inputs, attention_mask=attention_masks, labels=inputs)
        loss = outputs.loss
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f"Epoch {epoch+1}/{num_epochs}, Loss: {total_loss/len(train_loader)}")

# Save the trained model
model.save_pretrained("trained_bert_wikitext2")
