from __future__ import annotations

import pandas as pd
import pickle
import torch

from dataset import WaldoDataset
from model import Model
from pathlib import Path
from torch.utils.data import DataLoader
from trainer import Trainer
from transformation import Transformation
from waldo.constant import DATASET


def main() -> None:
    current = Path.cwd()

    csv = DATASET.joinpath('waldo.csv')

    annotation = pd.read_csv(csv)

    device = torch.device(
        'cuda'
        if torch.cuda.is_available()
        else 'cpu'
    )

    transformation = Transformation(device=device)

    dataset = WaldoDataset()
    dataset.annotation = annotation
    dataset.current = current
    dataset.device = device
    dataset.transformation = transformation

    length = len(dataset)

    trl = int(length * 0.80)
    tel = int(length * 0.10)
    val = length - (trl + tel)

    train, test, validation = torch.utils.data.random_split(
        dataset,
        [trl, tel, val]
    )

    batch_size = 16

    training = DataLoader(
        dataset=train,
        batch_size=batch_size,
        shuffle=True
    )

    testing = DataLoader(
        dataset=test,
        batch_size=batch_size,
        shuffle=False
    )

    validating = DataLoader(
        dataset=validation,
        batch_size=batch_size,
        shuffle=False
    )

    model = Model()
    model.device = device

    optimizer = torch.optim.AdamW(
        [
            {
                'lr': 0.000001,
                'params': model.classification.parameters(),
                'weight_decay': 0.075
            },
            {
                'lr': 0.001,
                'params': model.box.parameters(),
                'weight_decay': 0.025
            },
            {
                'lr': 0.0001,
                'params': model.base.parameters(),
                'weight_decay': 0.025
            },
            {
                'lr': 0.0001,
                'params': model.dense.parameters(),
                'weight_decay': 0.025
            }
        ]
    )

    torch.backends.cudnn.benchmark = True

    trainer = Trainer()
    trainer.device = device
    trainer.epoch = 15
    trainer.model = model
    trainer.optimizer = optimizer
    trainer.testing = testing
    trainer.training = training
    trainer.validating = validating
    history = trainer.start()

    torch.save(
        model.state_dict(),
        'state/model.pth'
    )

    with open('state/trainer.pkl', 'wb') as handle:
        pickle.dump(trainer, handle)

    with open('state/history.pkl', 'wb') as handle:
        pickle.dump(history, handle)


if __name__ == '__main__':
    main()
