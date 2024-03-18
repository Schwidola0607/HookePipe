# Copyright (c) Meta Platforms, Inc. and affiliates
import torch
from typing import Any


class MyNetworkBlock(torch.nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.lin = torch.nn.Linear(in_dim, out_dim)

    def forward(self, x):
        x = self.lin(x)
        x = torch.relu(x)
        return x


class MyNetwork(torch.nn.Module):
    def __init__(self, in_dim, layer_dims):
        super().__init__()

        prev_dim = in_dim
        for i, dim in enumerate(layer_dims):
            setattr(self, f"layer{i}", MyNetworkBlock(prev_dim, dim))
            prev_dim = dim

        self.num_layers = len(layer_dims)
        # 10 output classes
        self.output_proj = torch.nn.Linear(layer_dims[-1], 10)

    def forward(self, x):
        for i in range(self.num_layers):
            x = getattr(self, f"layer{i}")(x)

        return self.output_proj(x)


mn = MyNetwork(512, [512, 1024, 256])

from pippy.IR import annotate_split_points, PipeSplitWrapper, Pipe

annotate_split_points(
    mn,
    {
        "layer0": PipeSplitWrapper.SplitPoint.END,
        "layer1": PipeSplitWrapper.SplitPoint.END,
    },
)

import argparse
import os
from pippy.PipelineStage import PipelineStage 
import torch.optim as optim

import torch.distributed as dist
from pippy.IR import LossWrapper

class ModelLossWrapper(LossWrapper):
    def forward(self, x, target):
        return self.loss_fn(self.module(x), target)

def run(args):
    loss_wrapper = ModelLossWrapper(
        module=mn, loss_fn=torch.nn.MSELoss(reduction="sum")
    )

 
    # TODO: these might be necessary for the loss wrapper

    # from pippy.microbatch import LossReducer
    # from pippy.microbatch import TensorChunkSpec

    # output_chunk_spec: Any = LossReducer(0.0, lambda a, b: a + b)
    # args_chunk_spec: Any = (TensorChunkSpec(0), TensorChunkSpec(0))
    # kwargs_chunk_spec: Any = {}

    example_x = torch.randn(512, 512)
    example_target = torch.randn(512, 10)
    pipe = Pipe.from_tracing(loss_wrapper, args.chunks, 
                             example_args=(example_x,example_target))

    stage = PipelineStage(pipe, args.rank, args.device)
    print(stage)
    optimizer = optim.SGD(stage.parameters(), lr=0.01)


    N_TRAINING_STEPS = 100

    x = torch.randn(512, 512)
    target = torch.randn(512, 10)
    for i in range(N_TRAINING_STEPS):
        optimizer.zero_grad()
        
        if args.rank == 0:
          pipe_loss = stage(x)
        elif args.rank == args.world_size - 1:
          pipe_loss = stage(target)
        else:
          pipe_loss = stage()
        optimizer.step()

        log_info = f" Training step {i}, loss: {pipe_loss}"
        print(log_info.center(80, "*"))

    print(" Pipeline parallel model ran successfully! ".center(80, "*"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--world_size', type=int, default=int(os.getenv("WORLD_SIZE", 4)))
    parser.add_argument('--rank', type=int, default=int(os.getenv("RANK", -1)))
    parser.add_argument('--master_addr', type=str, default=os.getenv('MASTER_ADDR', 'localhost'))
    parser.add_argument('--master_port', type=str, default=os.getenv('MASTER_PORT', '29500'))
    parser.add_argument('--schedule', type=str, default="FillDrain")
    parser.add_argument('--cuda', type=int, default=int(torch.cuda.is_available()))
    parser.add_argument("--chunks", type=int, default=8)
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
    print(f'rank = {args.rank}\nworld_size = {args.world_size}')
    dist.init_process_group(
        backend=backend,
    )
    print("finish running process group")
    run(args)