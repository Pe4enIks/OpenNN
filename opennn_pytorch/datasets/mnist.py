import torchvision
import torch


def mnist(tr_part, va_part, transform):
    '''
    Return splited into train, val, test parts mnist dataset.

    Parameterts
    -----------
    tr_part : float
        percent of train data.

    va_part : float
        percent of valid data.

    transform : torchvision.transforms
        torchvision transforms object with augmentations.
    '''
    dataset = torchvision.datasets.MNIST('.', download=True, transform=transform)
    tr_part = int(tr_part * len(dataset))
    va_part = int(va_part * len(dataset))
    train_dataset, valid_dataset, test_dataset = torch.utils.data.random_split(dataset, [tr_part, va_part, len(dataset) - tr_part - va_part])
    return train_dataset, valid_dataset, test_dataset


def fashion_mnist(tr_part, va_part, transform):
    '''
    Return splited into train, val, test parts fashion mnist dataset.

    Parameterts
    -----------
    tr_part : float
        percent of train data.

    va_part : float
        percent of valid data.

    transform : torchvision.transforms
        torchvision transforms object with augmentations.
    '''
    dataset = torchvision.datasets.FashionMNIST('.', download=True, transform=transform)
    tr_part = int(tr_part * len(dataset))
    va_part = int(va_part * len(dataset))
    train_dataset, valid_dataset, test_dataset = torch.utils.data.random_split(dataset, [tr_part, va_part, len(dataset) - tr_part - va_part])
    return train_dataset, valid_dataset, test_dataset
