import os
import yaml

import torch
import torch.nn as nn

import neptune.new as neptune

from .models import utils
from .models import Generator
from .models import GlobalDiscriminator
from .models import LocalDiscriminator


def get_run(
    cfg_dir: str = 'cfg', 
    neptune_yaml: str = 'neptune.yaml',
    debug: bool = False
) -> neptune.Run:
    yaml_path = os.path.join(cfg_dir, neptune_yaml)
    with open(yaml_path, 'r') as fd:
        secrets = yaml.safe_load(fd)
    return neptune.init(
        project=secrets['project'],
        api_token=secrets['api_token'],
        mode='debug' if debug else 'async'
    )


def log_metrics(
    run: neptune.Run, 
    metrics: dict, 
    stage: str, 
    phase: str
) -> None:
    for key, value in metrics.items():
        run[f"{stage}/{phase}/{key}"].log(value)


class log:
    @staticmethod
    def models(
        run: neptune.Run,
        netG: Generator,
        netGD: GlobalDiscriminator,
        netLD: LocalDiscriminator,
        device: torch.device
    ) -> None:
        for name, net in zip(['netG', 'netGD', 'netLD'], [netG, netGD, netLD]):
            run[f"models/{name}/model"] = str(net)
            run[f"models/{name}/parameters"] = utils.count_parameters(net)
        run["device"] = device
    
    class stage1:
        @staticmethod
        def init(
            run: neptune.Run, 
            optimizer: torch.optim.Optimizer, 
            criterion: nn.Module,
            epochs: int,
            iter_limit: int
        ) -> None:
            run["stage1/learning_rate"] = optimizer.defaults['lr']
            run["stage1/weight_decay"] = optimizer.defaults['weight_decay']
            run["stage1/optimizer"] = type(optimizer).__name__
            run["stage1/criterion"] = type(criterion).__name__ 
            run["stage1/epochs"] = epochs
            run["stage1/iter_limit"] = iter_limit
            
        class epoch:
            @staticmethod
            def train(run: neptune.Run, metrics: dict) -> None:
                log_metrics(run, metrics, "stage1", "train")
                
            @staticmethod
            def test(run: neptune.Run, metrics: dict) -> None:
                log_metrics(run, metrics, "stage1", "test")
    
    class stage2:
        @staticmethod
        def init(
            run: neptune.Run,
            optim_netG: torch.optim.Optimizer, 
            optim_netGD: torch.optim.Optimizer, 
            optim_netLD: torch.optim.Optimizer, 
            criterion: nn.Module,
            config: dict
        ) -> None:
            for net in ['netG', 'netGD', 'netLD']:
                optim = eval(f'optim_{net}')
                run[f"stage2/{net}/optimizer"] = type(optim).__name__
                run[f"stage2/{net}/learning_rate"] = optim.defaults['lr']
                run[f"stage2/{net}/weight_decay"] = optim.defaults['weight_decay']
                run[f"stage2/{net}/train_every"] = config['stage2'][net]['train_every']
                
            run["stage2/criterion"] = type(criterion).__name__ 
            run["stage2/epochs"] = config['stage2']['epochs']
            run["stage2/iter_limit"] = config['stage2']['limit_iters']
        
        class epoch:
            @staticmethod
            def train(run: neptune.Run, metrics: dict) -> None:
                log_metrics(run, metrics, "stage2", "train")
                
            @staticmethod
            def test(run: neptune.Run, metrics: dict) -> None:
                log_metrics(run, metrics, "stage2", "test")
                