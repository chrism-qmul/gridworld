import sys
sys.path.insert(0, '../')
from gridworld.data import CDMDataset, IGLUDataset, SingleTurnIGLUDataset

# cdm_dataset = CDMDataset(task_kwargs={'invariant': False})
# dataset = IGLUDataset(task_kwargs={'invariant': False})
dataset = SingleTurnIGLUDataset(task_kwargs={'invariant': False})

for task_id, n, m, subtask in dataset:
    print(f'structure id: {task_id}, session id: {n}, '
          f'substructure id: {m}, instruction len: {len(subtask.last_instruction)}')