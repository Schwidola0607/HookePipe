# Copyright (c) Meta Platforms, Inc. and affiliates

# Minimum effort to run this example:
# $ torchrun --nproc-per-node 4 pippy_bert.py

import argparse
import os

import torch
import torch.distributed as dist
import torch.optim as optim

from torch.utils.data import DataLoader, Dataset
from pippy.IR import Pipe, SplitPoint, annotate_split_points
from pippy.PipelineStage import PipelineStage

from transformers import BertForMaskedLM, BertConfig, BertTokenizer

from pippy.microbatch import sum_reducer, TensorChunkSpec
from hf_utils import generate_inputs_for_model, get_number_of_params
from datasets import load_dataset
from tqdm import tqdm

def add_split_points(bert, nranks):
    layers_per_rank = bert.config.num_hidden_layers // nranks
    for i in range(1, nranks):
        annotate_split_points(
            bert, {f"bert.encoder.layer.{i * layers_per_rank}": SplitPoint.BEGINNING})


def run(args):
    # Model configs
    config = BertConfig()
    print("Using device:", args.device)

    datasets = load_dataset("wikitext", "wikitext-2-raw-v1")

    # Create model
    model_class = BertForMaskedLM
    model_name = "BertForMaskedLM"
    bert = BertForMaskedLM.from_pretrained('bert-base-uncased')
    bert.to(args.device)

    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    def tokenize_function(examples):
      return tokenizer(examples["text"])

    tokenized_datasets = datasets.map(tokenize_function, batched=True, num_proc=4, remove_columns=["text"])

    block_size = 128
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
    
    lm_datasets = WikiTextDataset(datasets['train'], tokenizer)
    bert.train()
    if args.rank == 0:
        print(bert.config)
        print(f"Total number of params = {get_number_of_params(bert) // 10 ** 6}M")
        print(bert)

    # Input configs
    example_inputs = generate_inputs_for_model(
        model_class, bert, model_name, args.batch_size, args.device, include_loss_args=True)
    
    print(example_inputs)
    # exit()

    # Annotate split points
    add_split_points(bert, args.world_size)
    
    # output_chunk_spec = {"loss": sum_reducer,
    #   "logits": TensorChunkSpec(0)}
    # Create pipeline
    bert_pipe = Pipe.from_tracing(
        bert,
        num_chunks=args.chunks,
        example_args=(),
        example_kwargs=example_inputs,
    )
    nstages = len(list(bert_pipe.split_gm.children()))
    assert nstages == args.world_size, f"nstages = {nstages} nranks = {args.world_size}"
    if args.rank == 0:
        for i, sm in enumerate(bert_pipe.split_gm.children()):
            print(f"Pipeline stage {i} {get_number_of_params(sm) // 10 ** 6}M params")

    # Create schedule runtime
    stage = PipelineStage(
        bert_pipe,
        args.rank,
        device=args.device,
    )
    optimizer = optim.SGD(stage.submod.parameters(), lr=0.0001)

    N_TRAINING_STEPS = 3

    lm_dataloader = DataLoader(lm_datasets, shuffle=True, batch_size=args.batch_size)

    print(args.world_size)
    for epoch in range(N_TRAINING_STEPS):
      for batch in tqdm(lm_dataloader, desc=f"Epoch {epoch+1}/{N_TRAINING_STEPS}"):
          batch = [item.to(args.device) for item in batch]
          inputs, attention_mask = batch
          # exit()

          optimizer.zero_grad()
          if args.rank == 0:
              stage(input_ids=inputs, attention_mask=attention_mask, labels=inputs)
          elif args.rank == args.world_size - 1:
              pipe_loss = stage()
              optimizer.step()
          else:
              stage()

          if args.rank == args.world_size - 1:
              log_info = f" Training step {i}, loss: {pipe_loss}"
              print(log_info.center(80, "*"))

    print(" Pipeline parallel model ran successfully! ".center(80, "*"))

    # # Run
    # if args.rank == 0:
    #     stage(**example_inputs)
    # elif args.rank == args.world_size - 1:
    #     out = stage()
    # else:
    #     stage()

    # print(f"Rank {args.rank} completes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--world_size', type=int, default=int(os.getenv("WORLD_SIZE", 4)))
    parser.add_argument('--rank', type=int, default=int(os.getenv("RANK", -1)))
    parser.add_argument('--master_addr', type=str, default=os.getenv('MASTER_ADDR', 'localhost'))
    parser.add_argument('--master_port', type=str, default=os.getenv('MASTER_PORT', '29500'))
    parser.add_argument('--schedule', type=str, default="FillDrain")
    parser.add_argument('--cuda', type=int, default=int(torch.cuda.is_available()))
    parser.add_argument("--chunks", type=int, default=4)
    parser.add_argument('--batch_size', type=int, default=4)
    parser.add_argument('--batches', type=int, default=1)

    args = parser.parse_args()

    if args.cuda:
        dev_id = args.rank % torch.cuda.device_count()
        args.device = torch.device(f"cuda:{dev_id}")
    else:
        args.device = torch.device("cpu")

    # Init process group
    backend = "nccl" if args.cuda else "gloo"
    dist.init_process_group(
        backend=backend,
        rank=args.rank,
        world_size=args.world_size,
    )

    run(args)
