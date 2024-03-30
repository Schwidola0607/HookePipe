# Copyright (c) Meta Platforms, Inc. and affiliates
import torch
from typing import Any
import time
import os
from tqdm import tqdm

start = time.time()

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

import torch.distributed as dist
dist.init_process_group(backend="gloo")

local_rank = int(os.environ["LOCAL_RANK"])
rank = int(os.environ["RANK"])
world_size = int(os.environ["WORLD_SIZE"])
batch_size = 16
N_TRAINING_STEPS = 10
num_minibatches = 100
num_hidden_layers = 1000

mn = MyNetwork(512, [512] + [1024] * num_hidden_layers + [256])

from pippy.IR import annotate_split_points, PipeSplitWrapper, Pipe
mn.to(torch.device("cpu"))


layers_per_rank = num_hidden_layers // world_size
for i in range(1, world_size):
    annotate_split_points(
        mn, {f"layer{i * layers_per_rank}": PipeSplitWrapper.SplitPoint.END})


from pippy.PipelineStage import PipelineStage 
import torch.optim as optim


from pippy.IR import LossWrapper

class ModelLossWrapper(LossWrapper):
    def forward(self, x, target):
        output = self.module(x)
        return output, self.loss_fn(output, target)

loss_wrapper = ModelLossWrapper(
    module=mn, loss_fn=torch.nn.MSELoss(reduction="sum")
)



# TODO: these might be necessary for the loss wrapper

from pippy.microbatch import sum_reducer
from pippy.microbatch import TensorChunkSpec

output_chunk_spec = (TensorChunkSpec(0), sum_reducer)

example_x = torch.randn(batch_size, 512)
example_target = torch.randn(batch_size, 10)

pipe = Pipe.from_tracing(loss_wrapper, num_chunks=2, 
                            example_args=(example_x,example_target),
                            output_chunk_spec=output_chunk_spec)

stage = PipelineStage(pipe, rank, device=torch.device("cpu"))
print(stage)
optimizer = optim.SGD(stage.submod.parameters(), lr=0.0001)

x = torch.randn(batch_size, 512)
target = torch.randn(batch_size, 10)

print(f'x shape: {x.size()}')
print(f'target shape: {target.size()}')
print(world_size)

for i in tqdm(range(N_TRAINING_STEPS)):
    for j in range(num_minibatches):
      optimizer.zero_grad()
      if rank == 0:
          stage(x)
      elif rank == world_size - 1:
          pipe_loss = stage(target)
          optimizer.step()
      else:
          stage()

      if rank == world_size - 1:
          log_info = f" Training step {i}, loss: {pipe_loss}"
          print(log_info.center(80, "*"))

print(" Pipeline parallel model ran successfully! ".center(80, "*"))

end = time.time()
elapsed = (end-start) / 60
rtdata = open("traintime.txt", "a+")
rtdata.write(f'{elapsed}\n')
rtdata.close()

print(f"Stage {rank} takes {elapsed} minutes")
