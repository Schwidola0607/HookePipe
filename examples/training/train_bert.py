# Copyright (c) Meta Platforms, Inc. and affiliates

# Minimum effort to run this example:
# $ torchrun --nproc-per-node 4 pippy_bert.py

import argparse
import os
import inspect
import torch
import torch.distributed as dist
import torch.optim as optim
import time

from torch.nn.functional import cross_entropy
from torch.utils.data import DataLoader, Dataset
from pippy.IR import Pipe, SplitPoint, LossWrapper, annotate_split_points
from pippy.PipelineStage import PipelineStage

from transformers import AutoModelForSequenceClassification, AutoTokenizer

from pippy.microbatch import sum_reducer, TensorChunkSpec
from hf_utils import generate_inputs_for_model, get_number_of_params
from datasets import load_dataset
from tqdm import tqdm

def add_split_points(bert, nranks):
    layers_per_rank = bert.config.num_hidden_layers // nranks
    for i in range(1, nranks):
        annotate_split_points(
            bert, {f"bert.encoder.layer.{i * layers_per_rank}": SplitPoint.BEGINNING})

def generate_tokenize_dataset():
  datasets = load_dataset("yelp_review_full", split="train[:10%]")
  # Load BERT Tokenizer
  tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-cased")
  # Tokenize and preprocess the data
  def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)
  tokenized_datasets = datasets.map(tokenize_function, batched=True, num_proc=4)
  tokenized_datasets = tokenized_datasets.remove_columns(["text"])
  tokenized_datasets = tokenized_datasets.rename_column("label", "labels")
  tokenized_datasets.set_format("torch")
  print(tokenized_datasets)
  return tokenized_datasets

# hardcode example input generation (cause the provided function does not do what we want)

def run(args):
    tokenized_datasets = generate_tokenize_dataset()
    train_loader = DataLoader(tokenized_datasets, batch_size=4, shuffle=True)

    print("Using device:", args.device)

    # Model
    class ReviewClassifier(torch.nn.Module):
      def __init__(self) -> None:
        super().__init__()
        self.model_class = AutoModelForSequenceClassification
        self.model_name = "AutoModelForSequenceClassification"
        self.model = AutoModelForSequenceClassification.from_pretrained("google-bert/bert-base-cased", num_labels=5)
        self.config = self.model.config
    
      def forward(self, input_ids) -> None:
        output = self.model(input_ids, return_dict=False)
        return output[0]

    bert = ReviewClassifier()
    bert.to(args.device)

    # LossWrapper
    class ModelLossWrapper(LossWrapper):
      def forward(self, input_ids, labels):
        output = self.module(input_ids)
        return output, self.loss_fn(output, labels)

    loss_wrapper = ModelLossWrapper(
      module=bert, loss_fn=cross_entropy
    ) 

    # bert.train()

    if args.rank == 0:
        print(bert.config)
        print(f"Total number of params = {get_number_of_params(bert) // 10 ** 6}M")
        print(bert)

    # Input configs
    example_inputs = generate_inputs_for_model(
        bert.model_class, bert, bert.model_name, args.batch_size, args.device, include_loss_args=True)

    # Annotate split points
    add_split_points(bert, args.world_size)
    
    output_chunk_spec = (TensorChunkSpec(0), sum_reducer)
    # Create pipeline
    bert_pipe = Pipe.from_tracing(
        loss_wrapper,
        num_chunks=args.chunks,
        example_args=(example_inputs['input_ids'], example_inputs['labels']),
        output_chunk_spec=output_chunk_spec
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

    # Define optimzer
    optimizer = optim.AdamW(stage.submod.parameters(), lr=5e-5)

    N_TRAINING_STEPS = 3
    print(args.world_size)
    for epoch in range(N_TRAINING_STEPS):
      for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{N_TRAINING_STEPS}"):

          optimizer.zero_grad()
          if args.rank == 0:
              stage(input_ids=batch["input_ids"], labels=batch["labels"])
          elif args.rank == args.world_size - 1:
              pipe_loss = stage()
              log_info = f" Training step {i}, loss: {pipe_loss}"
              print(log_info.center(80, "*"))
              optimizer.step()
          else:
              stage()

    print(" Pipeline parallel model ran successfully! ".center(80, "*"))


if __name__ == "__main__":
    start = time.time()
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
    )
  
    run(args)
    end = time.time()
    elapsed = (end-start) / 60
    rtdata = open("traintime.txt", "a+")
    rtdata.write(f'{elapsed}\n')
    rtdata.close()

    print(f"Stage {args.rank} takes {elapsed} minutes")
