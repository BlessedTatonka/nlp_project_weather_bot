from transformers import BertModel, BertTokenizer, AdamW,  get_linear_schedule_with_warmup, set_seed
import torch.nn.functional as F
from torch.utils.data import DataLoader , Dataset
import torch.nn as nn 
import torch
import numpy as np
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
import random

import glob
import os
import pandas as pd

def seed_all(seed_value):
    random.seed(seed_value) 
    np.random.seed(seed_value) 
    torch.manual_seed(seed_value)
    
    if torch.cuda.is_available(): 
        torch.cuda.manual_seed(seed_value)
        torch.cuda.manual_seed_all(seed_value)
        torch.backends.cudnn.deterministic = True 
        torch.backends.cudnn.benchmark = False
        
seed = 42
seed_all(seed)


class ModelConfig:
    NB_EPOCHS = 50
    LR = 3e-5
    EPS = 1e-8
    MAX_LEN = 32
    N_SPLITS = 2
    TRAIN_BS = 64
    VALID_BS = 32
    MODEL_NAME = 'cointegrated/rubert-tiny-sentiment-balanced'
    TOKENIZER = BertTokenizer.from_pretrained('cointegrated/rubert-tiny-sentiment-balanced')


class IntentsDataset(Dataset):
    def __init__(self, messages, targets=None, is_test=False):
        self.messages = messages
        self.targets = targets
        self.is_test = is_test
        self.tokenizer = ModelConfig.TOKENIZER
        self.max_len = ModelConfig.MAX_LEN
    
    def __len__(self):
        return len(self.messages)
    
    def __getitem__(self, idx):
        message = str(self.messages[idx])
        message = ' '.join(message.split())
       
        inputs = self.tokenizer(
                            message,
                            add_special_tokens=True,
                            max_length=self.max_len,
                            padding="max_length" ,
                            truncation = True ,
                            pad_to_max_length=True, 
                            )
        
        ids = torch.tensor(inputs['input_ids'], dtype=torch.long)
        mask = torch.tensor(inputs['attention_mask'], dtype=torch.long)
        token_type = torch.tensor(inputs['token_type_ids'], dtype=torch.long)
     
        if self.is_test:
            return {
                'ids': ids,
                'mask': mask,
                'token_type': token_type,
            }
        else:    
            targets = torch.tensor(self.targets[idx], dtype=torch.long)
            return {
                'ids': ids,
                'mask': mask,
                'token_type': token_type,
                'targets': targets
            }


def IntentsDataloader(df, batch_size, is_test=False):
    dataset = IntentsDataset(df["message"].values,
                         df["label"].values,
                         is_test)
    dataloader = DataLoader(dataset, batch_size, shuffle=False)
    return dataloader


class IntentsClassifier(nn.Module):
    def __init__(self, n_classes):
        super(IntentsClassifier, self).__init__()
        self.bert = BertModel.from_pretrained(ModelConfig.MODEL_NAME, return_dict=False)
        self.drop = nn.Dropout(p=0.8)
        self.out = nn.Linear(312, n_classes)

    def forward(self, input_ids, attention_mask, token_type_ids):
        
        _, output = self.bert(input_ids, attention_mask, token_type_ids)
        output = self.drop(output)
        output = self.out(output)
    
        return output


def loss_fn(outputs, labels):
    return nn.CrossEntropyLoss()(outputs, labels)

def f1_macro(outputs, targets):
    pred = np.argmax(outputs.cpu().detach().numpy(), axis=1).flatten()
    targets = targets.cpu().detach().numpy()
    return f1_score(pred, targets, average='macro')


def yield_optimizer(model):
    param_optimizer = list(model.named_parameters())
    no_decay = ["bias", "LayerNorm.bias", "LayerNorm.weight"]

    optimizer_parameters = [
        {
            "params": [
                p for n, p in param_optimizer if not any(nd in n for nd in no_decay)
            ],
            "weight_decay": 0.001,
        },
        {
            "params": [
                p for n, p in param_optimizer if any(nd in n for nd in no_decay)
            ],
            "weight_decay": 0.0,
        },
    ]
    return torch.optim.AdamW(optimizer_parameters, lr=ModelConfig.LR, eps=ModelConfig.EPS) 


def train_epoch(model, data_loader, loss_fn, optimizer, device, scheduler, n_examples):
    model.train()
    losses = []
    correct_predictions = []

    for step , d in enumerate(data_loader):
        input_ids = d['ids'].to(device) 
        token_type_ids = d['token_type'].to(device)
        attention_mask = d['mask'].to(device)
        targets = d['targets'].to(device)

        outputs = model(
             input_ids ,
            attention_mask ,
            token_type_ids,
            )
        
        loss = loss_fn(outputs, targets)
        correct_predictions.append(f1_macro(outputs, targets))
        losses.append(loss.item())

        loss.backward()
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad()
        
    return np.mean(correct_predictions, axis=0), np.mean(losses)


def eval_model (model, data_loader, loss_fn, device, n_examples):
    model.eval()
  
    losses = []
    correct_predictions = []

    with torch.no_grad():
        for step , d in enumerate(data_loader):
            
            input_ids = d['ids'].to(device)
            token_type_ids = d['token_type'].to(device)
            attention_mask = d['mask'].to(device)
            targets = d['targets'].to(device)
        
            outputs = model(
                   input_ids ,
                attention_mask ,
                token_type_ids,
                )

            loss = loss_fn(outputs , targets)
            correct_predictions.append(f1_macro(outputs, targets))
            losses.append(loss.item())

    return np.mean(correct_predictions, axis=0), np.mean(losses)


def train(model, df, epochs, device, model_name):
    best_accuracy = 0
    
    for epoch in range(epochs):
        # if epoch % 10 == 0:
        print(f'Epoch {epoch + 1}')

        kf = StratifiedKFold(n_splits=ModelConfig.N_SPLITS, random_state=seed, shuffle=True)

        for step, (train, valid ) in enumerate(kf.split(df , df["label"])) :

            train_data_loader = IntentsDataloader(df.iloc[train], ModelConfig.TRAIN_BS)
            validation_data_loader = IntentsDataloader(df.iloc[valid], ModelConfig.VALID_BS)

            nb_train_steps = int(len(train_data_loader) / ModelConfig.TRAIN_BS * epochs)
            optimizer = yield_optimizer(model)
            scheduler = get_linear_schedule_with_warmup(
                                        optimizer,
                                        num_warmup_steps=0,
                                        num_training_steps=nb_train_steps)

            train_acc, train_loss = train_epoch(model, train_data_loader, loss_fn, optimizer, device, scheduler, len(df.iloc[train])) 
            val_acc, val_loss = eval_model(model, validation_data_loader, loss_fn,device, len(df.iloc[valid]))


            if  val_acc > best_accuracy:
                torch.save(model.state_dict(), model_name + '.bin')
                best_accuracy = val_acc
                print(f"Best accuracy {best_accuracy}")

