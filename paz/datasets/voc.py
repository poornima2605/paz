import os
from xml.etree import ElementTree
from .utils import get_class_names

import numpy as np
from ..core import Loader


class VOC(Loader):
    def __init__(self, path=None, split='train', class_names='all',
                 name='VOC2007', with_difficult_objects=True):

        super(VOC, self).__init__(path, split, class_names, name)

        self.with_difficult_objects = with_difficult_objects
        self._class_names = class_names
        if class_names == 'all':
            self._class_names = get_class_names('VOC')
        self.images_path = None
        self.arg_to_class = None

    def load_data(self):
        if self.name == 'VOC2007':
            ground_truth_data = self._load_VOC(self.name, self.split)
        if self.name == 'VOC2012':
            ground_truth_data = self._load_VOC(self.name, self.split)
        if isinstance(self.name, list):
            if not isinstance(self.split, list):
                raise Exception("'split' should also be a list")
            if set(self.name).issubset(['VOC2007', 'VOC2012']):
                data_A = self._load_VOC(self.name[0], self.split[0])
                data_B = self._load_VOC(self.name[1], self.split[1])
                ground_truth_data = data_A + data_B
        return ground_truth_data

    def _load_VOC(self, dataset_name, split):
        self.parser = VOCParser(dataset_name,
                                split,
                                self._class_names,
                                self.with_difficult_objects,
                                self.path)
        self.images_path = self.parser.images_path
        self.arg_to_class = self.parser.arg_to_class
        ground_truth_data = self.parser.load_data()
        return ground_truth_data


class VOCParser(object):
    """ Preprocess the VOC2007 xml annotations data.

    # TODO: Add background label

    # Arguments
        data_path: Data path to VOC2007 annotations

    # Return
        data: Dictionary which keys correspond to the image names
        and values are numpy arrays of shape (num_objects, 4 + num_classes)
        num_objects refers to the number of objects in that specific image
    """

    def __init__(self, dataset_name='VOC2007', split='train',
                 class_names='all', with_difficult_objects=True,
                 dataset_path='../datasets/VOCdevkit/'):

        if dataset_name not in ['VOC2007', 'VOC2012']:
            raise Exception('Invalid dataset name.')

        if split not in ['train', 'val', 'trainval', 'test', 'all']:
            raise Exception('Invalid split name.')

        # creating data set prefix paths variables
        self.dataset_name = dataset_name
        self.dataset_path = os.path.join(dataset_path, dataset_name)
        self.split = split
        self.split_prefix = os.path.join(self.dataset_path, 'ImageSets/Main/')
        self.annotations_path = os.path.join(self.dataset_path, 'Annotations/')
        self.images_path = os.path.join(self.dataset_path, 'JPEGImages/')
        self.with_difficult_objects = with_difficult_objects

        self.class_names = class_names
        if self.class_names == 'all':
            self.class_names = get_class_names('VOC')
        self.num_classes = len(self.class_names)
        class_keys = np.arange(self.num_classes)
        self.arg_to_class = dict(zip(class_keys, self.class_names))
        self.class_to_arg = {value: key for key, value
                             in self.arg_to_class.items()}
        self.data = []
        self._preprocess_XML()

    def _load_filenames(self):
        split_file = os.path.join(self.split_prefix, self.split) + '.txt'
        splitted_filenames = []
        for line in open(split_file):
            filename = line.strip() + '.xml'
            splitted_filenames.append(filename)
        return splitted_filenames

    def _preprocess_XML(self):
        filenames = self._load_filenames()
        for filename in filenames:
            filename_path = self.annotations_path + filename
            tree = ElementTree.parse(filename_path)
            root = tree.getroot()
            image_name = root.find('filename').text

            box_data = []
            difficulties = []

            size_tree = root.find('size')
            width = float(size_tree.find('width').text)
            height = float(size_tree.find('height').text)
            for object_tree in root.findall('object'):
                difficulty = int(object_tree.find('difficult').text)

                if difficulty == 1 and not(self.with_difficult_objects):
                    continue

                class_name = object_tree.find('name').text
                if class_name in self.class_names:
                    class_arg = self.class_to_arg[class_name]
                    bounding_box = object_tree.find('bndbox')
                    xmin = float(bounding_box.find('xmin').text) / width
                    ymin = float(bounding_box.find('ymin').text) / height
                    xmax = float(bounding_box.find('xmax').text) / width
                    ymax = float(bounding_box.find('ymax').text) / height

                    box_data.append([xmin, ymin, xmax, ymax, class_arg])
                    difficulties.append(difficulty)

            if len(box_data) == 0:
                continue

            # self.data[self.images_path + image_name] = label_data
            inputs = {'image': self.images_path + image_name}
            targets = {'box_data': box_data}
            sample = {'inputs': inputs, 'targets': targets}
            self.data.append(sample)

    def load_data(self):
        return self.data


def merge_two_dictionaries(dict_1, dict_2):
    merged_dict = dict_1.copy()
    merged_dict.update(dict_2)
    return merged_dict
