import argparse
import os

import socket

import torch
import torch.nn as nn
import torch.nn.parallel
import torch.optim
import torch.utils.data as data
import torch.utils.data.distributed
import torchvision.datasets as datasets
import torchvision.models as models
import torchvision.transforms as transforms
import datetime

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

parser = argparse.ArgumentParser(description='PyTorch ImageNet Training')
parser.add_argument('--epochs',  type=int, metavar='E', nargs='?', default=2)
parser.add_argument('--save_every',  type=int, metavar='c', nargs='?', default=1)
parser.add_argument("--batch_size", type=int, default=64)
parser.add_argument("--dist", type=str2bool, default=False)
parser.add_argument("--model", default="resnet50")
parser.add_argument("--enable_log", type=str2bool, default=False)
parser.add_argument('data', metavar='DIR', nargs='?', default='imagenet',
                    help='path to dataset (default: imagenet)')

def my_log_print(string):
    print(string)

def my_log_no_print(string): 
    return

my_log = my_log_no_print

def main():
    global my_log

    args = parser.parse_args()

    my_log = my_log_print if args.enable_log else my_log_no_print
    # global best_acc1

    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)

    my_log(f"Data path: {args.data}")
    my_log(f"Number of Epochs: {args.epochs}")
    my_log(f"Save Every: {args.save_every}")

    global_rank, train_loader, train_sampler, model, criterion, optimizer, device_id, args = load_training_objects(args)

    my_log(f"{datetime.datetime.now()}: Training begin")

    for epoch in range(1, args.epochs + 1):

        my_log(f"{datetime.datetime.now()}: Training epoch {epoch}")

        if train_sampler != None:
            train_sampler.set_epoch(epoch)

        my_log(f"Training epoch {epoch}")
        # train for one epoch
        acc1, acc5 = train(train_loader, model, criterion, optimizer, epoch, device_id, args)

        my_log(f"{datetime.datetime.now()}: Trained epoch {epoch}")
        my_log(f"{datetime.datetime.now()}: Accuracy top1: {acc1}; Accuracy top5: {acc5}")

        # evaluate on validation set
        # acc1 = validate(val_loader, model, criterion, args)

        if global_rank == 0 and (args.save_every != 0 and epoch % args.save_every == 0):
            ckp = model.state_dict()
            PATH = f"checkpoint_epoch_{epoch}_{global_rank}.pt"
            my_log(f"{datetime.datetime.now()}: Epoch {epoch} | Saving checkpoint at {PATH}")
            torch.save(ckp, PATH)
            my_log(f"{datetime.datetime.now()}: Epoch {epoch} | Checkpoint saved at {PATH}")

        
        #scheduler.step()

def load_training_objects(args):

    traindir = os.path.join(args.data, 'train')
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])

    # transformations to apply to all images

    train_dataset = datasets.ImageFolder(
        traindir,
        transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            normalize,
        ]))

    model = models.__dict__[args.model]() # NOTE: model definition

    if args.dist:

        torch.distributed.init_process_group(backend='nccl')

        device_id = int(os.environ["LOCAL_RANK"])

        torch.cuda.set_device(device_id)

        train_sampler = torch.utils.data.distributed.DistributedSampler(train_dataset, shuffle=True)

        model = model.cuda(device_id)
        model = torch.nn.parallel.DistributedDataParallel(model,device_ids=[device_id])

        global_rank = int(os.environ["RANK"])
        #global_rank = 0

    else:

        device_id = torch.device("cuda")
        train_sampler = None
        model = model.cuda(device_id)

        global_rank = 0

    # define loss function (criterion), optimizer, and learning rate scheduler
    criterion = nn.CrossEntropyLoss().cuda(device_id)

    optimizer = torch.optim.SGD(model.parameters(), 0.1,
                                momentum=0.9,
                                weight_decay=1e-4)

    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=args.batch_size, shuffle=(train_sampler is None),
        num_workers=4, pin_memory=True, sampler=train_sampler)

    return global_rank, train_loader, train_sampler, model, criterion, optimizer, device_id, args


def train(train_loader, model, criterion, optimizer, epoch, device_id, args):
    global my_log

    acc1_val = 0.0
    acc5_val = 0.0

    acc_count = 0

    # switch to train mode
    model.train()

    for i, (images, target) in enumerate(train_loader):

        # move data to the same device as model
        images = images.cuda(device_id, non_blocking=True)
        target = target.cuda(device_id, non_blocking=True)

        # compute output
        output = model(images)
        loss = criterion(output, target)

        acc1, acc5 = accuracy(output, target, (1,5))

        acc1_val += acc1
        acc5_val += acc5

        acc_count += 1

        # compute gradient and do SGD step
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    return acc1_val/acc_count, acc5_val/acc_count


def accuracy(output, target, topk=(1,)):
    """Computes the accuracy over the k top predictions for the specified values of k"""
    with torch.no_grad():
        maxk = max(topk)
        batch_size = target.size(0)

        _, pred = output.topk(maxk, 1, True, True)
        pred = pred.t()
        correct = pred.eq(target.view(1, -1).expand_as(pred))

        res = []
        for k in topk:
            correct_k = correct[:k].reshape(-1).float().sum(0, keepdim=True)
            res.append(correct_k.mul_(100.0 / batch_size))
        return res


if __name__ == '__main__':
    main()
    print("End Main")