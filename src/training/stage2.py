from typing import Tuple

import neptune.new as neptune
import torch
import torch.nn as nn

import src.models as models
from src.data import dataloader_split
from src.models import Generator, GlobalDiscriminator, LocalDiscriminator
from src.logger import log
from src.training.common import *


def get_criterion(config: dict) -> torch.nn.Module:
    return [criterion_opts[config['stage2']['loss'].lower()]() for _ in range(2)]


def get_epochs(config: dict) -> int:
    return config['stage2']['epochs']


def get_optimizers(
    netG: nn.Module, 
    netGD: nn.Module, 
    netLD: nn.Module, 
    config: dict
) -> torch.nn.Module:
    optimizers = []
    for net, model in zip(['netG', 'netGD', 'netLD'], [netG, netGD, netLD]):
        optim = optimizer_opts[config['stage2'][net]['optimizer']]
        optim = optim(
            model.parameters(),
            lr=config['stage2'][net]['lr'],
            weight_decay=config['stage2'][net]['weight_decay']
        )
        optimizers.append(optim)
    return optimizers


def get_labels(
    dataloader: torch.utils.data.DataLoader,
    device: torch.device
) -> Tuple[torch.Tensor, torch.Tensor]:
    shape = (dataloader.batch_size, 1)
    real = torch.ones(shape, device=device)
    fake = torch.zeros(shape, device=device)
    return real, fake



def main(
    netG: Generator,
    netGD: GlobalDiscriminator,
    netLD: LocalDiscriminator,
    dataloader: torch.utils.data.Dataset,
    device: torch.device, 
    config: dict, 
    debug: bool, 
    run: neptune.Run
) -> None:
    criterionGD, criterionLD = get_criterion(config)
    optim_netG, optim_netGD, optim_netLD = get_optimizers(netG, netGD, netLD, config)
    epochs = get_epochs(config)
    log.stage2.init(run, optim_netG, optim_netGD, optim_netLD, criterionGD, epochs)

    real_label, fake_label = get_labels(dataloader, device)   

    for e in range(epochs):
        netG.train(); netGD.train(), netLD.train()
        for idx, (img_input, img_target, coords) in enumerate(dataloader):
            img_input, img_target = tensors_to_device([img_input, img_target], device)
                 
            netGD.zero_grad()   
            img_real_GD = netGD(img_target)
            loss_GD_real = criterionGD(img_real_GD, real_label)
            loss_GD_real.backward()
            
            img_fake = netG(img_input)
            img_fake_GD = netGD(img_fake.detach())
            loss_GD_fake = criterionGD(img_fake_GD, fake_label)
            loss_GD_fake.backward()
            
            lossGD = loss_GD_real + loss_GD_fake
            
            optim_netGD.step()
            
            netG.zero_grad()
            img_fake_G = netGD(img_fake)
            loss_G = criterionGD(img_fake_G, real_label)
            loss_G.backward()
    
            optim_netG.step()
                    