from emlp.nn import MLP,EMLP,MLPH,EMLPH,InvarianceLayer_objax
from emlp.groups import SO2eR3,O2eR3,DkeR3,Trivial
from emlp.reps import Scalar
from trainer.hamiltonian_dynamics import IntegratedDynamicsTrainer,DoubleSpringPendulum,hnnScalars_trial
from torch.utils.data import DataLoader
from oil.utils.utils import cosLr,FixedNumpySeed,FixedPytorchSeed
from trainer.utils import LoaderTo
from oil.datasetup.datasets import split_dataset
from oil.tuning.args import argupdated_config
import torch.nn as nn
import logging
import emlp
import emlp.reps
import objax


levels = {'critical': logging.CRITICAL,'error': logging.ERROR,
          'warn': logging.WARNING,'warning': logging.WARNING,
          'info': logging.INFO,'debug': logging.DEBUG}


def makeTrainerScalars(*,dataset=DoubleSpringPendulum,network=EMLPH,num_epochs=2000,ndata=5000,seed=2021, 
                bs=500,lr=3e-3,device='cuda',split={'train':500,'val':.1,'test':.1},
                net_config={'n_layers':3,'n_hidden':300}, log_level='info',
                trainer_config={'log_dir':'/home/','log_args':{'minPeriod':.02,'timeFrac':.75},},
                #'early_stop_metric':'val_MSE'},
                save=True,):
    logging.getLogger().setLevel(levels[log_level])
    # Prep the datasets splits, model, and dataloaders
    with FixedNumpySeed(seed),FixedPytorchSeed(seed):
        base_ds = dataset(n_systems=ndata,chunk_len=5)
        datasets = split_dataset(base_ds,splits=split)
     
    model = InvarianceLayer_objax(**net_config)
    dataloaders = {k:LoaderTo(DataLoader(v,batch_size=min(bs,len(v)),shuffle=(k=='train'),
                num_workers=0,pin_memory=False)) for k,v in datasets.items()}
    dataloaders['Train'] = dataloaders['train']
    opt_constr = objax.optimizer.Adam
    lr_sched = lambda e: lr#*cosLr(num_epochs)(e)#*min(1,e/(num_epochs/10))
    return IntegratedDynamicsTrainer(model,dataloaders,opt_constr,lr_sched,**trainer_config)

if __name__ == "__main__":
    Trial = hnnScalars_trial(makeTrainerScalars)
    cfg,outcome = Trial(argupdated_config(makeTrainerScalars.__kwdefaults__,namespace=(emlp.groups,emlp.nn)))
    print(outcome)
