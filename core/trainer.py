import logging
import hydra
import torch
import torch.nn as nn
from tqdm import tqdm
from omegaconf import DictConfig
from core.models.TransductionModel import TransductionModel
from core.dataset.TransductionDataset import TransductionDataset

log = logging.getLogger(__name__)

class Trainer:
  """
  Handles interface between:
    - TransductionModel
    - Dataset
    - Checkpoint?
    - Visualizer?
  """

  def __init__(self, cfg: DictConfig):

    self._cfg = cfg
    self._instantiate()

  def _instantiate(self):

    self._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    log.info("DEVICE: {}".format(self._device))

    self._dataset = TransductionDataset(self._cfg, self._device)
    log.info(self._dataset)

    self._model = TransductionModel(self._cfg, self._dataset, self._device)
    log.info(self._model)
  
  def train(self):

    log.info("Beginning training")

    lr = self._cfg.training.lr
    optimizer = torch.optim.SGD(self._model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss(weight=None)

    for epoch in range(self._cfg.training.epochs):

      log.info("EPOCH %i / %i", epoch + 1, self._cfg.training.epochs)

      self._model.train()
      with tqdm(self._dataset.iterators['train']) as T:
        for batch in T:

          optimizer.zero_grad()

          # Loss expects:
          #   output:  [batch_size, classes, seq_len]
          #   target: [batch_size, seq_len]
          output = self._model(batch)
          target = batch.target.permute(1, 0)
          loss = criterion(output, target)

          loss.backward()

          optimizer.step()

          T.set_postfix(trn_loss=loss.item())
