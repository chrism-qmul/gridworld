import json
import numpy
import os
import pandas
import shutil
import sys
sys.path.insert(0, '../../')
import unittest
from gridworld.data.iglu_dataset import IGLUDataset, SingleTurnIGLUDataset


class IGLUDatasetMock(IGLUDataset):
    """Class that mocks the download method to use test data."""

    TEST_DATA_PATH = 'test_input_data'

    @classmethod
    def get_data_path(cls):
        """Returns the path with a mock dataset used for testing.
        """
        return cls.TEST_DATA_PATH

    def download_dataset(self, data_path, force_download):
        pass


class IGLUDatasetTest(unittest.TestCase):
    """Test output format of multi-turn IGLU data.
    """
    USED_DIALOG_COLUMNS = [
        'PartitionKey',
        'structureId',
        'StepId',
        'IsHITQualified',
        'instruction',
        'Answer4ClarifyingQuestion',
        'ClarifyingQuestion'
    ]
    BUILDER_DATA_DIRPATH = os.path.join(
        IGLUDatasetMock.get_data_path(), 'builder-data'
    )
    DIALOGS_FILEPATH = os.path.join(
        IGLUDatasetMock.get_data_path(), 'dialogs.csv')

    @staticmethod
    def normal_architect_row(step):
        return {
            'IsHITQualified': True, 'instruction': f"Instruction {step}",
            'Answer4ClarifyingQuestion': None, 'ClarifyingQuestion': None
        }

    @staticmethod
    def normal_builder_row():
        return {
            'IsHITQualified': True, 'instruction': None,
            'Answer4ClarifyingQuestion': None, 'ClarifyingQuestion': None
        }

    def create_normal_builder_step_file(self, session, step, final_grid_state):
        """Creates the json file associated with a builder step."""
        dirpath = os.path.join(self.BUILDER_DATA_DIRPATH, session)
        # Create directory if it doesn't exists
        os.makedirs(dirpath, exist_ok=True)

        filepath = os.path.join(dirpath, f'step-{step}')
        with open(filepath, 'w') as step_file:
            json.dump(final_grid_state, step_file)

    def tearDown(self) -> None:
        try:
            shutil.rmtree(self.BUILDER_DATA_DIRPATH, ignore_errors=True)
            os.remove(self.DIALOGS_FILEPATH)
        except Exception as e:
            print("tearDown failed")
            print(e)
            pass
        return super().tearDown()

    def create_normal_input_files(self, session, structure, block_sequence):
        data = []
        total_steps = len(block_sequence) * 2
        for step in range(1, total_steps + 1):
            # Data common to all rows
            row = {'PartitionKey': 'session', 'StepId': step,
                   'structureId': structure}
            if step % 2 == 1:
                row.update(self.normal_architect_row(step))
            else:
                row.update(self.normal_builder_row())
                self.create_normal_builder_step_file(
                    session, step, block_sequence[step])
            data.append(row)

        dialogs = pandas.DataFrame(data=data)
        dialogs.to_csv(self.DIALOGS_FILEPATH, index=False)
        self.assertEqual(set(self.USED_DIALOG_COLUMNS), set(dialogs.columns))
        return total_steps

    def test_normal_long_session(self):
        """Tests the output format for a session with 2 architect and 2 builder
        steps.
        """
        # Block files have more information, but these keys are the only ones
        # used on the script.
        block_sequence = {2: {
            "worldEndingState": {
                "blocks": [
                    [1, 63, 2, 47],
                    [2, 63, 2, 47],
                    [3, 63, 2, 47]
                ],
            },
            "clarification_question": None
        },
        4: {
            "worldEndingState": {
                "blocks": [
                    [1, 63, 2, 47],
                    [2, 63, 2, 47],
                    [3, 63, 2, 47],
                    [4, 63, 4, 47],
                    [5, 63, 4, 47],
                ],
            },
            "clarification_question": None
        },
        6: {
            "worldEndingState": {
                "blocks": [
                    [1, 63, 2, 47],
                    [2, 63, 2, 47],
                    [5, 63, 4, 47],
                    [-1, 63, -1, 45],
                    [-2, 63, -1, 45],
                ],
            },
            "clarification_question": None
        }}
        session = 'session'
        structure = 's1'
        total_steps = self.create_normal_input_files(
            session, structure, block_sequence)

        iglu_dataset = IGLUDatasetMock()
        self.assertEqual(1, len(iglu_dataset.tasks),
                         msg="There is more than one structure in dataset")
        self.assertIn(structure, iglu_dataset.tasks)
        self.assertEqual(1, len(iglu_dataset.tasks[structure]))

        created_task = iglu_dataset.tasks[structure][0]

        # Test blocks
        final_structure = created_task.structure_seq
        self.assertEqual(len(block_sequence), len(final_structure))
        for i, step in enumerate(range(2, total_steps + 1, 2)):
            step_blocks = block_sequence[step]['worldEndingState']['blocks']
            for j, block in enumerate(step_blocks):
                expected_x, _, expected_z, _ = block
                x, _, z, _ = final_structure[i][j]
                self.assertEqual(expected_x, x)
                self.assertEqual(expected_z, z)

        # Test utterances
        self.assertEqual(total_steps // 2, len(created_task.dialog))
        for i, step_utterances in enumerate(created_task.dialog):
            # There are no clarifying questions, so each step has only the
            # architect instruction.
            self.assertEqual(1, len(step_utterances))
            self.assertIn(self.normal_architect_row(i*2 + 1)['instruction'],
                          step_utterances[0])

    def test_single_step_session(self):
        """Tests the dataset is empty for sessions with only one step.
        """
        # Block files have more information, but these keys are the only ones
        # used on the script.
        block_sequence = {2: {
            "worldEndingState": {
                "blocks": [],
            },
            "clarification_question": None
        }}
        session = 'session'
        structure = 's1'
        self.create_normal_input_files(
            session, structure, block_sequence)
        iglu_dataset = IGLUDatasetMock()
        self.assertEqual(0, len(iglu_dataset.tasks),
                         msg="There is an empty task")

    # TODO test for clarifying questions, empty block changes and
    # not approved hits.


class SingleTurnIGLUDatasetMock(IGLUDatasetMock, SingleTurnIGLUDataset):
    pass


class SingleTurnIGLUDatasetTest(unittest.TestCase):
    DIALOGS_FILEPATH = os.path.join(
        SingleTurnIGLUDatasetMock.get_data_path(),
        SingleTurnIGLUDatasetMock.SINGLE_TURN_INSTRUCTION_FILENAME)

    def tearDown(self) -> None:
        try:
            shutil.rmtree(SingleTurnIGLUDatasetMock.get_data_path(),
                          ignore_errors=True)
        except Exception as e:
            print("tearDown failed")
            print(e)
            pass
        return super().tearDown()

    def test_normal_session(self):
        base_data_dir = SingleTurnIGLUDatasetMock.get_data_path()
        structure_id = 'c1'
        initial_world_filename = SingleTurnIGLUDataset.MULTI_TURN_DIRNAME + \
            f'/builder-data/23-{structure_id}/step-2'
        target_world_dir = 'mturk-single-turn/builder-data/actionHit/game-1/'
        game_id = 'game-1'
        instruction = 'Instruction 1'
        # Create dialogs file
        row = {
            'PartitionKey': game_id,
            'InitializedWorldPath': initial_world_filename,
            'IsHITQualified': True,
            'InitializedWorldStructureId': structure_id,
            'ActionDataPath': target_world_dir,
            'InitializedWorldGameId': None, 'InputInstruction': instruction
        }
        dialogs = pandas.DataFrame(data=[row])
        dialogs.to_csv(self.DIALOGS_FILEPATH, index=False)

        # Create initial world file
        os.makedirs(os.path.join(
            base_data_dir, os.path.dirname(initial_world_filename)),
            exist_ok=True)
        initial_world_filepath = os.path.join(
            base_data_dir, initial_world_filename)
        initial_block_list = [[1, 63, 2, 47], [2, 63, 2, 47]]
        initial_blocks = {
            "worldEndingState": {
                "blocks": initial_block_list,
            }
        }
        with open(initial_world_filepath, 'w') as initial_world_file:
            json.dump(initial_blocks, initial_world_file)

        # Create target world file
        os.makedirs(os.path.join(base_data_dir, target_world_dir),
                    exist_ok=True)
        target_world_filepath = os.path.join(
            base_data_dir, target_world_dir, f'{game_id}-step-action'
        )
        block_list = [[1, 63, 2, 47], [2, 63, 2, 47], [3, 63, 2, 47]]
        target_blocks = {
            "worldEndingState": {
                "blocks": block_list,
            }
        }
        with open(target_world_filepath, 'w') as target_world_file:
            json.dump(target_blocks, target_world_file)

        iglu_dataset = SingleTurnIGLUDatasetMock()
        self.assertEqual(1, len(iglu_dataset.tasks),
                         msg="There is more than one structure in dataset")
        self.assertIn(structure_id, iglu_dataset.tasks)
        self.assertEqual(1, len(iglu_dataset.tasks[structure_id]))

        task = iglu_dataset.tasks[structure_id][0]

        # Test utterances
        self.assertEqual('', task.chat)
        self.assertEqual(instruction, task.last_instruction)

        # Test initial blocks
        self.assertEqual(len(initial_block_list),
                         len(task.starting_grid))
        for block in initial_block_list:
            x, y, z, block_id = SingleTurnIGLUDataset.transform_block(block)
            grid_block = task.target_grid[
                y+1, x + task.target_grid.shape[1] // 2,
                z + task.target_grid.shape[2] // 2]
            self.assertEqual(block_id, grid_block)

        # Test target blocks
        self.assertEqual(len(block_list), numpy.count_nonzero(task.target_grid))
        for block in block_list:
            x, y, z, block_id = SingleTurnIGLUDataset.transform_block(block)
            grid_block = task.target_grid[
                y+1, x + task.target_grid.shape[1] // 2,
                z + task.target_grid.shape[2] // 2]
            self.assertEqual(block_id, grid_block)

    # TODO test for missing files, empty block changes and not approved hits.

if __name__ == '__main__':
    unittest.main()