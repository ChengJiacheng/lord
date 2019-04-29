import io

import numpy as np
from PIL import Image

import tensorflow as tf
from keras.callbacks import TensorBoard


class EvaluationCallback(TensorBoard):

	def __init__(self, imgs, identities, pose_embedding, identity_embedding, identity_modulation, generator, tensorboard_dir):
		super().__init__(log_dir=tensorboard_dir)
		super().set_model(generator)

		self.__imgs = imgs
		self.__identities = identities

		self.__pose_embedding = pose_embedding
		self.__identity_embedding = identity_embedding
		self.__identity_modulation = identity_modulation
		self.__generator = generator

		self.__n_identities = 5
		self.__n_poses = 5

	def on_epoch_end(self, epoch, logs={}):
		super().on_epoch_end(epoch, logs)

		identities = np.random.choice(self.__identities.max() + 1, size=self.__n_identities, replace=False)
		reference_identity = identities[0]

		reference_identity_img_ids = np.where(self.__identities == reference_identity)[0]
		img_ids = np.random.choice(reference_identity_img_ids, size=self.__n_poses, replace=False)

		pose_codes = self.__pose_embedding.predict(img_ids)
		identity_codes = self.__identity_embedding.predict(identities)
		identity_adain_params = self.__identity_modulation.predict(identity_codes)

		rows = []
		for i in range(self.__n_identities):
			row = []
			for j in range(self.__n_poses):
				img = self.model.predict([pose_codes[[j]], identity_adain_params[[i]]])[0]
				row.append(img)

			rows.append(np.concatenate(row, axis=1))

		merged_img = np.concatenate(rows, axis=0)

		summary = tf.Summary(value=[tf.Summary.Value(tag='sample', image=self.make_image(merged_img))])
		self.writer.add_summary(summary, global_step=epoch)
		self.writer.flush()

	@staticmethod
	def make_image(tensor):
		height, width, channels = tensor.shape
		image = Image.fromarray((np.squeeze(tensor) * 255).astype(np.uint8))

		with io.BytesIO() as out:
			image.save(out, format='PNG')
			image_string = out.getvalue()

		return tf.Summary.Image(height=height, width=width, colorspace=channels, encoded_image_string=image_string)
