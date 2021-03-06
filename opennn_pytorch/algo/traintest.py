from tqdm import tqdm
import torch
import torch.nn.functional as F
import numpy as np
import os


def train(train_dataloader, valid_dataloader, model, optimizer, scheduler, loss_fn, metrics, epochs, checkpoints, logs, device, save_every, one_hot, nc):
    '''
    Train pipeline.

    Parameterts
    -----------
    train_dataloader : torch.utils.data.DataLoader
        train dataloader.

    valid_dataloader : torch.utils.data.DataLoader
        valid dataloader.

    model : Any
        pytorch model.

    optimizer : torch.optim.Optimizer
        optimizer for this model.

    scheduler : torch.optim.lr_scheduler
        scheduler for this optimizer.

    loss_fn : Any
        loss function.

    metrics : list[Any]
        list of metric functions.

    epochs : int
        epochs number.

    checkpoints : str
        folder for checkpoints.

    logs : str
        folder for logs.

    device : str
        device ['cpu', 'cuda'].

    save_every : int
        every save_every epoch save model weights.

    one_hot : bool
        one_hot for labels.

    nc : int
        classes number.
    '''
    checkpoints_folder = list(map(int, os.listdir(checkpoints)))
    checkpoints_folder = max(checkpoints_folder) + 1 if checkpoints_folder != [] else 0
    os.mkdir(f'{checkpoints}/{checkpoints_folder}', mode=0o777)
    checkpoints = f'{checkpoints}/{checkpoints_folder}'

    logs_folder = list(map(int, os.listdir(logs)))
    logs_folder = max(logs_folder) + 1 if logs_folder != [] else 0
    os.mkdir(f'{logs}/{logs_folder}', mode=0o777)
    logs = f'{logs}/{logs_folder}'

    tqdm_iter = tqdm(range(epochs))
    best_loss = 99999999.0
    best_epoch = 0

    for epoch in tqdm_iter:
        model.train()
        train_loss = 0.0
        valid_loss = 0.0
        metric_names = [metric.name() for metric in metrics]
        train_mvct = [0.0] * len(metrics)
        valid_mvct = [0.0] * len(metrics)

        for batch in train_dataloader:
            imgs, labels = batch
            imgs = imgs.to(device)
            labels = labels.to(device)

            if one_hot:
                labels = F.one_hot(labels, nc).float()

            preds = model(imgs)
            loss = loss_fn(preds, labels)

            for mi, metric in enumerate(metrics):
                train_mvct[mi] += metric.calc(preds, labels).cpu()

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        model.eval()
        with torch.no_grad():
            for batch in valid_dataloader:
                imgs, labels = batch
                imgs = imgs.to(device)
                labels = labels.to(device)

                if one_hot:
                    labels = F.one_hot(labels, nc).float()

                preds = model(imgs)
                loss = loss_fn(preds, labels)

                for mi, metric in enumerate(metrics):
                    valid_mvct[mi] += metric.calc(preds, labels).cpu()

                valid_loss += loss.item()

        train_mvct = np.array(train_mvct) / len(train_dataloader)
        valid_mvct = np.array(valid_mvct) / len(valid_dataloader)
        train_loss /= len(train_dataloader)
        valid_loss /= len(valid_dataloader)

        if epoch % save_every == 0 or epoch == epochs - 1:
            state_dict = model.state_dict()
            torch.save(state_dict, checkpoints + '/plan_{}_{:.2f}.pt'.format(epoch, valid_loss))

        if valid_loss < best_loss:
            best_epoch = epoch
            best_loss = valid_loss
            state_dict = model.state_dict()
            torch.save(state_dict, checkpoints + '/best.pt')

        tqdm_dct = {}
        train_str = ''
        valid_str = ''

        tqdm_dct['train loss'] = train_loss
        for i, metric in enumerate(train_mvct):
            tqdm_dct[f'train_{metric_names[i]}'] = metric
            train_str += f'train_{metric_names[i]}: {metric} '

        tqdm_dct['valid loss'] = valid_loss
        for i, metric in enumerate(valid_mvct):
            tqdm_dct[f'valid_{metric_names[i]}'] = metric
            if i != len(valid_mvct) - 1:
                valid_str += f'valid_{metric_names[i]}: {metric} '
            else:
                valid_str += f'valid_{metric_names[i]}: {metric}\n'

        tqdm_iter.set_postfix(tqdm_dct, refresh=True)

        with open(logs + '/trainval.log', 'a') as in_f:
            in_f.write(f'epoch: {epoch + 1}/{epochs} train loss: {train_loss} valid loss: {valid_loss} ' + train_str + valid_str)

        scheduler.step()
        tqdm_iter.refresh()
    os.rename(checkpoints + '/best.pt', checkpoints + '/best_{}_{:.2f}.pt'.format(best_epoch, best_loss))


def test(test_dataloader, model, loss_fn, metrics, logs, device, one_hot, nc):
    '''
    Test pipeline.

    Parameterts
    -----------
    test_dataloader : torch.utils.data.DataLoader
        test dataloader.

    model : Any
        pytorch model.

    loss_fn : Any
        loss function.

    metrics : list[Any]
        list of metric functions.

    logs : str
        folder for logs.

    device : str
        device ['cpu', 'cuda'].

    one_hot : bool
        one_hot for labels.

    nc : int
        classes number.
    '''
    logs_folder = list(map(int, os.listdir(logs)))
    logs_folder = max(logs_folder) + 1 if logs_folder != [] else 0
    os.mkdir(f'{logs}/{logs_folder}', mode=0o777)
    logs = f'{logs}/{logs_folder}'

    model.eval()
    test_loss = 0.0
    metric_names = [metric.name() for metric in metrics]
    test_mvct = [0.0] * len(metrics)

    with torch.no_grad():
        for batch in test_dataloader:
            imgs, labels = batch
            imgs = imgs.to(device)
            labels = labels.to(device)

            if one_hot:
                labels = F.one_hot(labels, nc).float()

            preds = model(imgs)
            loss = loss_fn(preds, labels)

            for mi, metric in enumerate(metrics):
                test_mvct[mi] += metric.calc(preds, labels).cpu()

            test_loss += loss.item()

    test_mvct = np.array(test_mvct) / len(test_dataloader)
    test_loss /= len(test_dataloader)
    test_str = ''

    for i, metric in enumerate(test_mvct):
        if i != len(test_mvct) - 1:
            test_str += f'{metric_names[i]}: {metric} '
        else:
            test_str += f'{metric_names[i]}: {metric}\n'

    with open(logs + '/test.log', 'a') as in_f:
        in_f.write(f'test loss: {test_loss} ' + test_str)

    return logs
