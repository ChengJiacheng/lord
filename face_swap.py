import argparse
import pickle
import random
import os

import numpy as np
import imageio

import dataset
from data import FacePreprocessor

from assets import AssetManager
from model.network import FaceConverter
from config import default_config


def preprocess(args):
	assets = AssetManager(args.base_dir)

	face_set = dataset.get_dataset(args.dataset, args.dataset_path)
	identity_map = face_set.get_identity_map()

	face_preprocessor = FacePreprocessor(args.segmentation_model_path, tuple(args.crop_size), tuple(args.target_size))

	imgs = dict()
	for i, identity in enumerate(identity_map.keys()):
		print('processing identity: %s' % identity)

		identity_imgs, identity_masks = face_preprocessor.preprocess_imgs(identity_map[identity])
		imgs[identity] = dict(imgs=identity_imgs, masks=identity_masks)

	with open(assets.get_preprocess_file_path(args.data_name), 'wb') as fd:
		pickle.dump(imgs, fd)


def train(args):
	assets = AssetManager(args.base_dir)
	model_dir = assets.recreate_model_dir(args.model_name)
	tensorboard_dir = assets.recreate_tensorboard_dir(args.model_name)

	with open(assets.get_preprocess_file_path(args.data_name), 'rb') as fd:
		train_imgs = pickle.load(fd)

	face_converter = FaceConverter.build(
		img_shape=default_config['img_shape'],

		content_dim=default_config['content_dim'],
		identity_dim=default_config['identity_dim'],

		n_adain_layers=default_config['n_adain_layers'],
		adain_dim=default_config['adain_dim']
	)

	face_converter.train(
		imgs=train_imgs,
		batch_size=default_config['batch_size'],

		n_epochs=default_config['n_epochs'],
		n_iterations_per_epoch=default_config['n_iterations_per_epoch'],
		n_epochs_per_checkpoint=default_config['n_epochs_per_checkpoint'],

		model_dir=model_dir,
		tensorboard_dir=tensorboard_dir
	)

	face_converter.save(model_dir)

#
# def convert(args):
# 	assets = AssetManager(args.base_dir)
# 	model_dir = assets.get_model_dir(args.model_name)
# 	prediction_dir = assets.create_prediction_dir(args.model_name)
#
# 	with open(assets.get_preprocess_file_path(args.data_name), 'rb') as fd:
# 		train_images = pickle.load(fd)
#
# 		for k in train_images.keys():
# 			train_images[k] = (train_images[k] / 255) * 2 - 1
#
# 	face_converter = FaceConverter.load(model_dir)
#
# 	for i in range(args.num_of_samples):
# 		source_identity_id = random.choice(list(train_images.keys()))
# 		target_identity_id = random.choice(list(train_images.keys()))
#
# 		source_img = train_images[source_identity_id][0]
# 		target_img = train_images[target_identity_id][0]
#
# 		converted_img = face_converter.converter.predict([
# 			np.expand_dims(source_img, axis=0), np.expand_dims(target_img, axis=0)
# 		])[0]
#
# 		merged_img = np.concatenate((source_img, target_img, converted_img), axis=1)
# 		imageio.imwrite(os.path.join(prediction_dir, '%d.png' % i), merged_img)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-bd', '--base-dir', type=str, required=True)

	action_parsers = parser.add_subparsers(dest='action')
	action_parsers.required = True

	preprocess_parser = action_parsers.add_parser('preprocess')
	preprocess_parser.add_argument('-ds', '--dataset', type=str, choices=dataset.supported_datasets, required=True)
	preprocess_parser.add_argument('-dp', '--dataset-path', type=str, required=True)
	preprocess_parser.add_argument('-dn', '--data-name', type=str, required=True)
	preprocess_parser.add_argument('-smp', '--segmentation-model-path', type=str, required=True)
	preprocess_parser.add_argument('-cs', '--crop-size', type=int, nargs=2, required=True)
	preprocess_parser.add_argument('-ts', '--target-size', type=int, nargs=2, required=True)
	preprocess_parser.add_argument('-g', '--gpus', type=int, default=1)
	preprocess_parser.set_defaults(func=preprocess)

	train_parser = action_parsers.add_parser('train')
	train_parser.add_argument('-dn', '--data-name', type=str, required=True)
	train_parser.add_argument('-mn', '--model-name', type=str, required=True)
	train_parser.add_argument('-g', '--gpus', type=int, default=1)
	train_parser.set_defaults(func=train)

	# convert_parser = action_parsers.add_parser('convert')
	# convert_parser.add_argument('-dn', '--data-name', type=str, required=True)
	# convert_parser.add_argument('-mn', '--model-name', type=str, required=True)
	# convert_parser.add_argument('-ns', '--num-of-samples', type=int, required=True)
	# convert_parser.set_defaults(func=convert)

	args = parser.parse_args()
	args.func(args)


if __name__ == '__main__':
	main()
